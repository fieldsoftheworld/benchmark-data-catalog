#!/usr/bin/env python3
"""Tile the root chips table into ``chips.pmtiles``: one feature per chip location.

    uv run python tools/chips_tiles.py                        # from the published table
    uv run python tools/chips_tiles.py --table work/chips.parquet

Writes ``work/chips.pmtiles`` (``--out`` to change); upload it like the table
(README, "Root chips table"). Needs tippecanoe on PATH.

A location is in up to one dataset per year, so the table repeats it. The tiles keep one
feature per chip id, with:

- ``id``, ``block`` and ``split_hash_v1`` (the same in every dataset, by construction);
- ``datasets``: how many datasets have the chip;
- ``legacy_conflict``: true when those datasets' ``split_legacy`` values disagree, i.e.
  the location was test in one dataset and train or val in another before the hash split;
- ``admin0_name``.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chips_table import TABLE_NAME, _sql  # noqa: E402
from common import PUBLIC_BASE, ROOT  # noqa: E402

TILES_NAME = "chips.pmtiles"
ATTRIBUTES = ("id", "block", "split_hash_v1", "datasets", "legacy_conflict", "admin0_name")


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


def build_tiles(table: str, out: Path) -> int:
    """Tile ``table``'s chip locations into ``out``; the number of features."""
    from ftw_dataset_tools.api.tiles import TileSpec, build_pmtiles

    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        locations = Path(tmp) / "locations.parquet"
        count = write_locations(table, locations)
        # 620k locations: drop the densest at low zooms so a tile stays under the size limit
        spec = TileSpec("chips", ATTRIBUTES, 2, 12, False, True)
        try:
            build_pmtiles(locations, out, spec)
        except RuntimeError as err:
            raise ChipsTilesError(str(err)) from err
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--table", default=f"{PUBLIC_BASE}/{TABLE_NAME}",
                        help="the chips table to tile (default: the published one)")
    parser.add_argument("--out", type=Path, default=ROOT / "work" / TILES_NAME)
    args = parser.parse_args(argv)
    try:
        count = build_tiles(args.table, args.out)
    except ChipsTilesError as err:
        sys.exit(f"chips tiles: {err}")
    print(f"wrote {args.out}: {count:,} chip locations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
