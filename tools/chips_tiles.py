#!/usr/bin/env python3
"""Tile the root chips table into ``chips.pmtiles``: every chip location, at every zoom.

    uv run python tools/chips_tiles.py                        # from the published table
    uv run python tools/chips_tiles.py --table work/chips.parquet
    uv run python tools/chips_tiles.py --thumbnail            # render catalog/thumbnail.webp

Writes ``work/chips.pmtiles`` (``--out`` to change); upload it like the table
(README, "Root chips table"). Needs tippecanoe on PATH.

A location is in every collection that covers it (other years, and a few overlapping
regions), so the table repeats it. Four layers, none dropping a location:

``chips`` (zoom 7-12): one polygon per chip id, with
- ``id``, ``block``, ``split_hash_v1`` and ``split_admin2_v1`` (the same in every
  dataset, by construction);
- ``datasets``: how many datasets have the chip;
- ``presence_only``: true when any of them is presence-only;
- ``legacy_conflict``: true when those datasets' ``split_legacy`` values disagree (any
  two of train, val and test);
- ``admin0_name``.

``overview_train``, ``overview_val`` and ``overview_test`` (zoom 0-6): the chip centres of
each ``split_admin2_v1``, clustered where they crowd, each split on its own so a cluster
never mixes splits and the whole catalog shows at once. Each point (or cluster) sums
``chips`` (locations), ``conflicts`` (locations with ``legacy_conflict``) and
``datasets`` (chip-collection pairs).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chips_table import TABLE_NAME, _sql  # noqa: E402
from common import PUBLIC_BASE, ROOT  # noqa: E402

TILES_NAME = "chips.pmtiles"
STYLE = ROOT / "catalog" / "chips.style.json"
THUMBNAIL = ROOT / "catalog" / "thumbnail.webp"
# The whole catalog in one frame, rendered large and shrunk so the clusters stay crisp.
THUMBNAIL_BBOX = (-130, -45, 150, 72)
THUMBNAIL_RENDER_SIZE = 2400
THUMBNAIL_SIZE = 1200
ATTRIBUTES = ("id", "block", "split_hash_v1", "split_admin2_v1", "datasets", "presence_only",
              "legacy_conflict", "admin0_name")
SPLITS = ("train", "val", "test")
OVERVIEW_LAYERS = tuple(f"overview_{split}" for split in SPLITS)
OVERVIEW_SUMS = ("chips", "conflicts", "datasets")
CHIPS_ZOOMS = (7, 12)
# tippecanoe turns sub-pixel polygons into dust, which can lose them. At zoom 7 a chip of
# this area is about 10 tile units across, far above that; real chips are 4 km2 or more.
MIN_CHIP_KM2 = 0.5
OVERVIEW_ZOOMS = (0, 6)


class ChipsTilesError(Exception):
    """The table can't be tiled."""


def write_locations(table: str, out: Path) -> int:
    """One row per chip id from ``table`` as GeoParquet at ``out``; the number of rows.

    Refuses a table where one chip id has more than one hash or admin2 split or geometry, which the
    one-feature-per-location tiles would hide, or a footprint below MIN_CHIP_KM2.
    """
    import geoparquet_io as gpio
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    try:
        bad = con.execute(f"""
            SELECT id FROM read_parquet({_sql(table)}) GROUP BY id
            HAVING count(DISTINCT split_hash_v1) > 1 OR count(DISTINCT split_admin2_v1) > 1
                OR count(DISTINCT ST_AsWKB(geometry)) > 1
            LIMIT 1""").fetchone()
        if bad:
            raise ChipsTilesError(f"chip {bad[0]} has more than one hash or admin2 split or "
                                  f"footprint")
        unsplit = con.execute(f"""
            SELECT id FROM read_parquet({_sql(table)})
            WHERE split_admin2_v1 IS NULL OR split_admin2_v1 NOT IN {SPLITS} LIMIT 1""").fetchone()
        if unsplit:
            raise ChipsTilesError(f"chip {unsplit[0]} has no admin2 split; the overview would "
                                  f"leave it out")
        tiny = con.execute(f"""
            SELECT id, ST_Area_Spheroid(ST_FlipCoordinates(geometry)) / 1e6 AS km2
            FROM read_parquet({_sql(table)})
            WHERE ST_Area_Spheroid(ST_FlipCoordinates(geometry)) / 1e6 < {MIN_CHIP_KM2}
            LIMIT 1""").fetchone()
        if tiny:
            raise ChipsTilesError(f"chip {tiny[0]} covers {tiny[1]:.3f} km2, below "
                                  f"{MIN_CHIP_KM2} km2: the tiles could lose it at zoom "
                                  f"{CHIPS_ZOOMS[0]}")
        tmp = out.with_suffix(".tmp.parquet")
        con.execute(f"""
            COPY (SELECT id, any_value(block) AS block,
                         any_value(split_hash_v1) AS split_hash_v1,
                         any_value(split_admin2_v1) AS split_admin2_v1,
                         count(*)::INTEGER AS datasets,
                         bool_or(presence_only) AS presence_only,
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


def write_overview(locations: Path, out: Path, split: str) -> int:
    """The centres of ``split``'s chips with the counts the overview sums, as GeoJSONSeq;
    the number of points."""
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    where = f"FROM read_parquet({_sql(str(locations))}) WHERE split_admin2_v1 = {_sql(split)}"
    try:
        con.execute(f"""
            COPY (SELECT 1 AS chips, legacy_conflict::INTEGER AS conflicts, datasets,
                         ST_Centroid(geometry) AS geometry {where})
            TO {_sql(str(out))} WITH (FORMAT GDAL, DRIVER 'GeoJSONSeq')""")
        return con.execute(f"SELECT count(*) {where}").fetchone()[0]
    finally:
        con.close()


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as err:
        detail = getattr(err, "stderr", "") or str(err)
        raise ChipsTilesError(f"{cmd[0]} failed: {detail.strip()[:500]}") from err


def overview_command(seq: Path, out: Path, layer: str) -> list[str]:
    """tippecanoe for an overview layer: cluster crowded points, summing every count, drop none."""
    cmd = ["tippecanoe", "-o", str(out), "-l", layer, "--force", "--quiet",
           f"-Z{OVERVIEW_ZOOMS[0]}", f"-z{OVERVIEW_ZOOMS[1]}", "-r1",
           "--cluster-densest-as-needed", "--cluster-distance=2"]
    cmd += [f"--accumulate-attribute={name}:sum" for name in OVERVIEW_SUMS]
    return [*cmd, str(seq)]


def check_no_drops(archive: Path, layer: str) -> None:
    """Refuse an archive whose tippecanoe run dropped features at any zoom."""
    from pmtiles.reader import MmapSource, Reader

    with archive.open("rb") as f:
        strategies = Reader(MmapSource(f)).metadata().get("strategies", [])
    if isinstance(strategies, str):
        strategies = json.loads(strategies)
    for zoom, strategy in enumerate(strategies):
        dropped = {k: v for k, v in (strategy or {}).items() if k.startswith("dropped")}
        if dropped:
            raise ChipsTilesError(f"tippecanoe dropped {layer} features at zoom {zoom}: {dropped}; "
                                  f"every location must be kept")


def build_tiles(table: str, out: Path) -> int:
    """Tile ``table``'s chip locations into ``out``; the number of locations."""
    from ftw_dataset_tools.api.tiles import TileSpec, build_pmtiles

    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        tmp = Path(tmp)
        locations = tmp / "locations.parquet"
        count = write_locations(table, locations)
        chips = tmp / "chips.pmtiles"
        # from zoom 7 the densest tile is a quarter of the size limit; a drop is refused
        spec = TileSpec("chips", ATTRIBUTES, *CHIPS_ZOOMS, False, True)
        try:
            build_pmtiles(locations, chips, spec)
        except RuntimeError as err:
            raise ChipsTilesError(str(err)) from err
        check_no_drops(chips, "chips")
        overviews, points = [], 0
        for split, layer in zip(SPLITS, OVERVIEW_LAYERS):
            seq, archive = tmp / f"{layer}.geojsonseq", tmp / f"{layer}.pmtiles"
            n = write_overview(locations, seq, split)
            if not n:
                continue
            points += n
            _run(overview_command(seq, archive, layer))
            check_no_drops(archive, layer)
            overviews.append(str(archive))
        if points != count:
            raise ChipsTilesError(f"the overview has {points:,} of {count:,} locations")
        _run(["tile-join", "-o", str(out), "--force", "--quiet", "--no-tile-size-limit",
              "-n", "Chips of every collection",
              "-N", "Fields of the World benchmark chip locations with their splits",
              str(chips), *overviews])
    return count


def render_thumbnail(out: Path = THUMBNAIL, *, style: Path = STYLE,
                     tiles_url: str = f"{PUBLIC_BASE}/{TILES_NAME}",
                     server: str = "http://localhost:13579") -> Path:
    """Render the root style over the published tiles with chiitiler into ``out`` (WebP).

    Needs a running chiitiler (``tools/chiitiler.sh``). Refuses an image with no data in it.
    """
    import io
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
    if all(low == high for low, high in image.getextrema()):
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
