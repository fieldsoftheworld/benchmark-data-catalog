#!/usr/bin/env python3
"""Render a collection's manifest-chosen style into ``catalog/<id>/thumbnail.webp``.

Uses a running chiitiler (https://github.com/Kanahiro/chiitiler) tile server to
rasterize the style server-side, frames a 3:2 window on the densest cluster of
the source data, gates the result on a blank probe, and converts the PNG to
WebP with Pillow before registering it as the collection's ``thumbnail`` asset.

Start chiitiler first (``tools/chiitiler.sh``, or by hand — see that script),
then:

    uv run python tools/thumbnail.py lu             # writes catalog/lu/thumbnail.webp
    uv run python tools/thumbnail.py lu --zoom 13   # override the window zoom
    uv run python tools/thumbnail.py lu --rank 1    # second-densest cluster
    uv run python tools/thumbnail.py lu --style outline

Look at the image afterwards (the Read tool, or any viewer). The blank-probe
gate only proves that some data landed in the frame, not that the picture is
good.

Chiitiler mechanism (verified against ``.cache/chiitiler/src`` and by
rendering ``lu`` end to end):

* Rendering: ``POST /clip.{ext}?bbox=minLon,minLat,maxLon,maxLat&size=N`` with
  the style JSON as the request body (``{"style": {...}}``) — the "POST the
  JSON inline" form documented in chiitiler's README. ``size`` is the
  longest edge in pixels; a 3:2 bbox at ``size=1024`` renders 1024x683.
* Local PMTiles: chiitiler's PMTiles source handler
  (``src/source/pmtiles.ts``) only ever receives request URLs of the form
  ``pmtiles://<path>/{z}/{x}/{y}`` — it strips a trailing ``/<z>/<x>/<y>``
  with a regex and, when ``<path>`` has no ``http(s)://``/``s3://`` prefix,
  opens it as a local file path via Node's ``fs``. It never resolves a bare
  ``pmtiles://<path>`` the way MapLibre GL JS's browser-side PMTiles
  *protocol* plugin does (fetching a synthesized TileJSON first) — there is
  no such protocol registered in the renderer's ``maplibre-native`` request
  hook. So a vector source written as ``{"url": "pmtiles://../x.pmtiles"}``
  (the form used for the in-browser map, resolved relative to the style
  file) will not resolve here: it must instead be a ``tiles`` array
  templated on an *absolute* local path, e.g.
  ``{"type": "vector", "tiles": ["pmtiles:///abs/staging/lu/chips.pmtiles/{z}/{x}/{y}"], "minzoom": ..., "maxzoom": ...}``.
  ``rewrite_style()`` below performs exactly that rewrite, reading
  minzoom/maxzoom from the PMTiles header.
* The catalog's styles reference their PMTiles one directory up from the
  style file (``pmtiles://../chips.pmtiles``, i.e. ``catalog/<id>/`` were it
  there) but the archives are not copied into ``catalog/`` — they live in
  ``staging/<id>/`` until upload. ``rewrite_style()`` resolves the archive's
  basename against ``STAGING/<id>/`` rather than the style file's real
  parent, matching how this repository actually lays the files out.
"""
from __future__ import annotations

import argparse
import copy
import io
import math
import sys
from pathlib import Path

import duckdb
import requests
from PIL import Image, ImageChops

from common import CATALOG, STAGING, load_manifest, read_json, write_json

DEFAULT_PORT = 13579
DEFAULT_SIZE = 1024
TARGET_ASPECT = 1.5  # 3:2
BACKGROUND = "#ffffff"
BLANK_TOLERANCE = 24  # per-pixel grayscale difference below this counts as background
MIN_NONBLANK_FRACTION = 0.02

# Web Mercator constants, used only to size the framing window in metres.
R = 6378137.0
EARTH_CIRC = 40075016.686

# Styles drawn from the field boundaries rather than the chip grid.
FIELD_STYLES = {"crops", "outline"}


def mx(lon: float) -> float:
    return math.radians(lon) * R


def my(lat: float) -> float:
    lat = max(min(lat, 85.05112878), -85.05112878)
    return R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def inv_mx(x: float) -> float:
    return math.degrees(x / R)


def inv_my(y: float) -> float:
    return math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


def span_for_zoom(z: float, size_px: int) -> float:
    """The width, in Web Mercator metres, that ``size_px`` pixels covers at zoom ``z``."""
    return EARTH_CIRC * size_px / (256 * 2**z)


def window(clon: float, clat: float, z: float, size_px: int = DEFAULT_SIZE) -> list[float]:
    """A 3:2 window at zoom ``z`` centred on ``(clon, clat)``, in degrees."""
    span = span_for_zoom(z, size_px)
    hw, hh = span / 2, span / (2 * TARGET_ASPECT)
    cx, cy = mx(clon), my(clat)
    return [inv_mx(cx - hw), inv_my(cy - hh), inv_mx(cx + hw), inv_my(cy + hh)]


def _quote(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def pmtiles_header(path: Path) -> dict:
    """The min/max zoom a PMTiles archive declares, read straight from its header."""
    header = path.read_bytes()[:127]
    if header[:7] != b"PMTiles":
        sys.exit(f"{path} is not a PMTiles archive")
    return {"min_zoom": header[100], "max_zoom": header[101]}


def densest_cluster(parquet: Path, zoom: float, rank: int, size_px: int = DEFAULT_SIZE) -> tuple[float, float, int]:
    """(lon, lat, count) of the ``rank``-th densest window at ``zoom``, via the bbox column.

    Coordinates in this catalog's GeoParquet are always EPSG:4326 (degrees),
    so the frame's half-span (computed in Web Mercator metres for
    ``window()``) is converted to degrees at the data's mean latitude before
    bucketing feature centroids into a grid.
    """
    con = duckdb.connect()
    half_span_m = span_for_zoom(zoom, size_px) / 2
    mid_lat = con.execute(
        f"SELECT avg((bbox.ymin + bbox.ymax) / 2) FROM read_parquet({_quote(parquet)})"
    ).fetchone()[0]
    cell_y = half_span_m / 110_540.0
    cell_x = half_span_m / max(111_320.0 * math.cos(math.radians(mid_lat or 0.0)), 1.0)
    row = con.execute(
        f"""
        WITH c AS (
          SELECT (bbox.xmin + bbox.xmax) / 2 AS x, (bbox.ymin + bbox.ymax) / 2 AS y
          FROM read_parquet({_quote(parquet)})
        ), g AS (
          SELECT floor(x / {cell_x}) AS gx, floor(y / {cell_y}) AS gy, count(*) AS n FROM c GROUP BY 1, 2
        ), top AS (
          SELECT gx, gy FROM g ORDER BY n DESC LIMIT 1 OFFSET {int(rank)}
        )
        SELECT count(*), avg(x), avg(y) FROM c, top
        WHERE x BETWEEN (gx - 1) * {cell_x} AND (gx + 2) * {cell_x}
          AND y BETWEEN (gy - 1) * {cell_y} AND (gy + 2) * {cell_y}
        """
    ).fetchone()
    n, lon, lat = row
    if n is None or lon is None:
        sys.exit(f"{parquet}: rank {rank} has no cluster (dataset may be smaller than expected)")
    return lon, lat, int(n)


def rewrite_style(style: dict, dataset_id: str) -> dict:
    """A copy of ``style`` with every ``pmtiles://../x.pmtiles`` source rewritten
    to an absolute ``tiles`` template chiitiler's PMTiles source handler can read
    (see the module docstring), symbol layers stripped (they need glyphs/sprites
    this renderer does not serve), and an opaque background layer inserted first
    so the blank probe has a known colour to compare against.
    """
    render = copy.deepcopy(style)
    for source in render.get("sources", {}).values():
        url = source.pop("url", None)
        if not url or not url.startswith("pmtiles://"):
            continue
        name = Path(url.removeprefix("pmtiles://")).name
        pmtiles_path = (STAGING / dataset_id / name).resolve()
        if not pmtiles_path.exists():
            sys.exit(f"{pmtiles_path} not found (expected the built archive in staging/)")
        header = pmtiles_header(pmtiles_path)
        source["type"] = "vector"
        source["tiles"] = [f"pmtiles://{pmtiles_path}/{{z}}/{{x}}/{{y}}"]
        source["minzoom"] = header["min_zoom"]
        source["maxzoom"] = header["max_zoom"]
    layers = [layer for layer in render.get("layers", []) if layer.get("type") != "symbol"]
    background = {"id": "__background", "type": "background", "paint": {"background-color": BACKGROUND}}
    render["layers"] = [background, *layers]
    return render


def clip(style: dict, bbox: list[float], size: int, port: int, fmt: str = "png", quality: int = 100) -> bytes:
    url = (
        f"http://localhost:{port}/clip.{fmt}?bbox={','.join(f'{v:.6f}' for v in bbox)}"
        f"&size={size}&quality={quality}"
    )
    r = requests.post(url, json={"style": style}, timeout=600)
    if r.status_code != 200:
        sys.exit(f"chiitiler returned {r.status_code}: {r.text[:300]}")
    return r.content


def blank_fraction(img: Image.Image, background: str = BACKGROUND, tolerance: int = BLANK_TOLERANCE) -> float:
    """The fraction of ``img``'s pixels that differ from ``background`` by more than ``tolerance``.

    Pure Pillow (no chiitiler, no numpy) so it can be unit-tested against
    generated images.
    """
    rgb = img.convert("RGB")
    bg_color = tuple(int(background.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    bg_img = Image.new("RGB", rgb.size, bg_color)
    diff = ImageChops.difference(rgb, bg_img).convert("L")
    total = rgb.size[0] * rgb.size[1]
    if total == 0:
        return 0.0
    differing = sum(diff.histogram()[tolerance + 1 :])
    return differing / total


def write_webp(img: Image.Image, path: Path, quality: int = 80) -> None:
    img.convert("RGB").save(path, "WEBP", quality=quality)


def register_asset(collection_path: Path, coll: dict, dataset_id: str, style_asset: dict) -> None:
    """Add or update the ``thumbnail`` asset on ``collection.json``, in place.

    Only the ``assets.thumbnail`` key is touched; every other key (and, for an
    existing ``thumbnail`` entry, its position in ``assets``) is left alone —
    idempotent and safe to run alongside other tools editing the same file.
    """
    title = coll.get("title") or dataset_id
    coll.setdefault("assets", {})["thumbnail"] = {
        "href": "./thumbnail.webp",
        "type": "image/webp",
        "roles": ["thumbnail"],
        "title": f"{title} — {style_asset.get('title', style_asset['href'])}",
    }
    write_json(collection_path, coll)


def render(
    dataset_id: str,
    *,
    style: str | None = None,
    zoom: float | None = None,
    rank: int | None = None,
    port: int = DEFAULT_PORT,
    size: int = DEFAULT_SIZE,
) -> Path | None:
    """Render and write ``catalog/<dataset_id>/thumbnail.webp``.

    Returns the output path, or ``None`` if the dataset is not built yet
    (not an error — this is the normal state before ``tools/build.py`` and
    ``tools/catalogize.py`` have run for it).
    """
    manifest = load_manifest()
    if dataset_id not in (manifest.get("datasets") or {}):
        sys.exit(f"{dataset_id} is not in datasets.yaml")
    thumb_cfg = manifest["datasets"][dataset_id].get("thumbnail") or {}
    style_id = style or thumb_cfg.get("style")
    zoom = zoom if zoom is not None else thumb_cfg.get("zoom")
    rank = rank if rank is not None else thumb_cfg.get("rank", 0)
    if not style_id or zoom is None:
        sys.exit(f"{dataset_id}: no thumbnail.style/zoom in datasets.yaml (and none given on the CLI)")

    cdir = CATALOG / dataset_id
    collection_path = cdir / "collection.json"
    if not collection_path.exists():
        print(f"{dataset_id}: not built yet ({collection_path} missing), skipping")
        return None

    coll = read_json(collection_path)
    style_key = f"style-{style_id}"
    style_asset = (coll.get("assets") or {}).get(style_key)
    if not style_asset:
        sys.exit(f"{dataset_id}: no {style_key} asset on catalog/{dataset_id}/collection.json")
    style_path = cdir / style_asset["href"]
    if not style_path.exists():
        sys.exit(f"{dataset_id}: style file missing: {style_path}")

    parquet_name = "fields" if style_id in FIELD_STYLES else "chips"
    parquet = STAGING / dataset_id / f"{dataset_id}_{parquet_name}.parquet"
    if not parquet.exists():
        sys.exit(f"{dataset_id}: {parquet} not found; build the dataset first")

    try:
        requests.get(f"http://localhost:{port}/health", timeout=5)
    except requests.RequestException:
        sys.exit(f"chiitiler is not reachable on port {port}; run tools/chiitiler.sh first")

    clon, clat, n = densest_cluster(parquet, zoom, rank, size)
    bbox = window(clon, clat, zoom, size)
    render_style = rewrite_style(read_json(style_path), dataset_id)
    png_bytes = clip(render_style, bbox, size, port)
    img = Image.open(io.BytesIO(png_bytes))

    fraction = blank_fraction(img)
    if fraction < MIN_NONBLANK_FRACTION:
        sys.exit(
            f"{dataset_id}: blank-probe failed — only {fraction:.1%} of pixels differ from the "
            f"background (need >= {MIN_NONBLANK_FRACTION:.0%}); not writing thumbnail.webp. "
            "Try a different --zoom/--rank/--style."
        )

    out = cdir / "thumbnail.webp"
    write_webp(img, out)
    register_asset(collection_path, coll, dataset_id, style_asset)
    print(
        f"{dataset_id}: wrote {out} (style={style_id} zoom={zoom} rank={rank} "
        f"center=({clon:.5f},{clat:.5f}) features_in_window={n} nonblank={fraction:.1%})"
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("datasets", nargs="+", help="dataset ids from datasets.yaml, e.g. lu")
    parser.add_argument("--style", help="style id override (default: datasets.yaml thumbnail.style)")
    parser.add_argument("--zoom", type=float, help="window zoom override (default: datasets.yaml thumbnail.zoom)")
    parser.add_argument("--rank", type=int, help="densest-cluster rank override (0 = densest)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="chiitiler port")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="longest edge in pixels")
    args = parser.parse_args()

    for dataset_id in args.datasets:
        render(dataset_id, style=args.style, zoom=args.zoom, rank=args.rank, port=args.port, size=args.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
