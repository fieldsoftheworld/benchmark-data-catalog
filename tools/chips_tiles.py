#!/usr/bin/env python3
"""Tile the root chips table into ``chips.pmtiles``: every chip location, at every zoom.

    uv run python tools/chips_tiles.py                        # from the published table
    uv run python tools/chips_tiles.py --table work/chips.parquet
    uv run python tools/chips_tiles.py --thumbnail            # render catalog/thumbnail.webp

Writes ``work/chips.pmtiles`` (``--out`` to change); upload it like the table
(README, "Root chips table"). Needs tippecanoe on PATH.

A location is in every collection that covers it (other years, and a few overlapping
regions), so the table repeats it. Two layers, neither dropping a location:

``chips`` (zoom 6-12): one polygon per chip id, with
- ``id``, ``block`` and ``split_hash_v1`` (the same in every dataset, by construction);
- ``datasets``: how many datasets have the chip;
- ``legacy_conflict``: true when those datasets' ``split_legacy`` values disagree (any
  two of train, val and test);
- ``admin0_name``.

``overview`` (zoom 2-5): chip centres, clustered where they crowd, so the whole catalog
shows at once. Each point (or cluster) sums ``chips`` (locations), ``train``, ``val``,
``test`` (by ``split_hash_v1``), ``conflicts`` (locations with ``legacy_conflict``) and
``datasets`` (chip-collection pairs).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chips_table import TABLE_NAME, _sql  # noqa: E402
from common import PUBLIC_BASE, ROOT  # noqa: E402

TILES_NAME = "chips.pmtiles"
STYLE = ROOT / "catalog" / "styles" / "chips.json"
THUMBNAIL = ROOT / "catalog" / "thumbnail.webp"
# The whole catalog in one frame. chiitiler picks the zoom from size and bbox, and the
# tiles start at zoom 2, so render large and shrink.
THUMBNAIL_BBOX = (-130, -45, 150, 72)
THUMBNAIL_RENDER_SIZE = 2400
THUMBNAIL_SIZE = 1200
ATTRIBUTES = ("id", "block", "split_hash_v1", "datasets", "legacy_conflict", "admin0_name")
OVERVIEW_SUMS = ("chips", "train", "val", "test", "conflicts", "datasets")
CHIPS_ZOOMS = (6, 12)
OVERVIEW_ZOOMS = (2, 5)


class ChipsTilesError(Exception):
    """The table can't be tiled."""


def write_locations(table: str, out: Path) -> int:
    """One row per chip id from ``table`` as GeoParquet at ``out``; the number of rows.

    Refuses a table where one chip id has more than one hash split or geometry, which the
    one-feature-per-location tiles would hide.
    """
    import geoparquet_io as gpio
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    try:
        bad = con.execute(f"""
            SELECT id FROM read_parquet({_sql(table)}) GROUP BY id
            HAVING count(DISTINCT split_hash_v1) > 1 OR count(DISTINCT ST_AsWKB(geometry)) > 1
            LIMIT 1""").fetchone()
        if bad:
            raise ChipsTilesError(f"chip {bad[0]} has more than one hash split or footprint")
        tmp = out.with_suffix(".tmp.parquet")
        con.execute(f"""
            COPY (SELECT id, any_value(block) AS block,
                         any_value(split_hash_v1) AS split_hash_v1,
                         count(*)::INTEGER AS datasets,
                         count(DISTINCT split_legacy) > 1 AS legacy_conflict,
                         any_value(admin0_name) AS admin0_name,
                         any_value(geometry) AS geometry
                  FROM read_parquet({_sql(table)}) GROUP BY id ORDER BY id)
            TO {_sql(str(tmp))} (FORMAT parquet)""")
        gpio.read(str(tmp)).write(str(out))
        tmp.unlink()
        return con.execute(f"SELECT count(*) FROM read_parquet({_sql(str(out))})").fetchone()[0]
    finally:
        con.close()


def write_overview(locations: Path, out: Path) -> int:
    """Chip centres with the counts the overview sums, as GeoJSONSeq; the number of points."""
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    try:
        con.execute(f"""
            COPY (SELECT 1 AS chips, (split_hash_v1 = 'train')::INTEGER AS train,
                         (split_hash_v1 = 'val')::INTEGER AS val,
                         (split_hash_v1 = 'test')::INTEGER AS test,
                         legacy_conflict::INTEGER AS conflicts, datasets,
                         ST_Centroid(geometry) AS geometry
                  FROM read_parquet({_sql(str(locations))}))
            TO {_sql(str(out))} WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq')""")
        return con.execute(
            f"SELECT count(*) FROM read_parquet({_sql(str(locations))})").fetchone()[0]
    finally:
        con.close()


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as err:
        detail = getattr(err, "stderr", "") or str(err)
        raise ChipsTilesError(f"{cmd[0]} failed: {detail.strip()[:500]}") from err


def overview_command(seq: Path, out: Path) -> list[str]:
    """tippecanoe for the overview: cluster crowded points, summing every count, drop none."""
    cmd = ["tippecanoe", "-o", str(out), "-l", "overview", "--force", "--quiet",
           f"-Z{OVERVIEW_ZOOMS[0]}", f"-z{OVERVIEW_ZOOMS[1]}", "-r1",
           "--cluster-densest-as-needed", "--cluster-distance=2"]
    cmd += [f"--accumulate-attribute={name}:sum" for name in OVERVIEW_SUMS]
    return [*cmd, str(seq)]


def build_tiles(table: str, out: Path) -> int:
    """Tile ``table``'s chip locations into ``out``; the number of locations."""
    from ftw_dataset_tools.api.tiles import TileSpec, build_pmtiles

    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        tmp = Path(tmp)
        locations = tmp / "locations.parquet"
        count = write_locations(table, locations)
        chips, overview = tmp / "chips.pmtiles", tmp / "overview.pmtiles"
        # from zoom 6 a tile fits every chip; the flag is a guard, and drops nothing there
        spec = TileSpec("chips", ATTRIBUTES, *CHIPS_ZOOMS, False, True)
        try:
            build_pmtiles(locations, chips, spec)
        except RuntimeError as err:
            raise ChipsTilesError(str(err)) from err
        seq = tmp / "overview.geojsonseq"
        write_overview(locations, seq)
        _run(overview_command(seq, overview))
        _run(["tile-join", "-o", str(out), "--force", "--quiet", "--no-tile-size-limit",
              str(chips), str(overview)])
    return count


def render_thumbnail(out: Path = THUMBNAIL, *, style: Path = STYLE,
                     tiles_url: str = f"{PUBLIC_BASE}/{TILES_NAME}",
                     server: str = "http://localhost:13579") -> Path:
    """Render the root style over the published tiles with chiitiler into ``out`` (WebP).

    Needs a running chiitiler (``tools/chiitiler.sh``). Refuses an image with no data in it.
    """
    import io
    import json
    import urllib.request

    from PIL import Image

    doc = json.loads(style.read_text())
    doc["sources"]["data"] = {"type": "vector", "minzoom": OVERVIEW_ZOOMS[0],
                              "maxzoom": CHIPS_ZOOMS[1],
                              "tiles": [f"pmtiles://{tiles_url}/{{z}}/{{x}}/{{y}}"]}
    bbox = ",".join(str(v) for v in THUMBNAIL_BBOX)
    request = urllib.request.Request(
        f"{server}/clip.png?bbox={bbox}&size={THUMBNAIL_RENDER_SIZE}",
        data=json.dumps({"style": doc}).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            image = Image.open(io.BytesIO(response.read())).convert("RGB")
    except OSError as err:
        raise ChipsTilesError(f"chiitiler at {server} failed: {err}") from err
    if len(image.getcolors(maxcolors=1 << 16) or ()) < 2:
        raise ChipsTilesError("the thumbnail is blank: no tiles rendered")
    image.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
    image.save(out, "WEBP", quality=85)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--table", default=f"{PUBLIC_BASE}/{TABLE_NAME}",
                        help="the chips table to tile (default: the published one)")
    parser.add_argument("--out", type=Path, default=ROOT / "work" / TILES_NAME)
    parser.add_argument("--thumbnail", action="store_true",
                        help="render catalog/thumbnail.webp from the published tiles instead")
    args = parser.parse_args(argv)
    if args.thumbnail:
        try:
            print(f"wrote {render_thumbnail()}")
        except ChipsTilesError as err:
            sys.exit(f"chips tiles: {err}")
        return 0
    try:
        count = build_tiles(args.table, args.out)
    except ChipsTilesError as err:
        sys.exit(f"chips tiles: {err}")
    print(f"wrote {args.out}: {count:,} chip locations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
