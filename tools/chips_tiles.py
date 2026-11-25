#!/usr/bin/env python3
"""Tile the chips table into ``chips.pmtiles``: every chip location, at every zoom.

    uv run python tools/chips_tiles.py                        # from the published table
    uv run python tools/chips_tiles.py --table work/chips.parquet
    uv run python tools/chips_tiles.py --thumbnail            # render catalog/chips/thumbnail.webp

A wrapper over ``ftwd chips-tiles`` (``ftw_dataset_tools.api.chips_tiles``, which owns the
layers, their zooms and attributes, and the drop check). Writes ``work/chips.pmtiles``
(``--out`` to change); upload it like the table (README, "Chips collection"). Needs
tippecanoe on PATH. The table, the tiles, the style and the thumbnail all belong to the
all-chips collection, ``catalog/chips/`` (``tools/chips_collection.py``).

``--thumbnail`` renders ``catalog/chips/thumbnail.webp`` with
``catalog/chips/styles/split-admin2.json`` over the published ``chips.pmtiles``, through
a running chiitiler (``tools/chiitiler.sh``).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chips_collection import STYLE as STYLE_PATH, THUMBNAIL as THUMBNAIL_NAME  # noqa: E402
from common import ALL_CHIPS, CATALOG, PUBLIC_BASE, ROOT  # noqa: E402
from ftw_dataset_tools.api.chips_table import TABLE_NAME  # noqa: E402
from ftw_dataset_tools.api.chips_tiles import (  # noqa: E402
    DEFAULT_SERVER,
    TILES_NAME,
    ChipsTilesError,
    build_tiles,
    render_thumbnail,
)

STYLE = CATALOG / ALL_CHIPS / STYLE_PATH
THUMBNAIL = CATALOG / ALL_CHIPS / THUMBNAIL_NAME
TABLE_URL = f"{PUBLIC_BASE}/{ALL_CHIPS}/{TABLE_NAME}"
TILES_URL = f"{PUBLIC_BASE}/{ALL_CHIPS}/{TILES_NAME}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--table", default=TABLE_URL,
                        help="the chips table to tile (default: the published one)")
    parser.add_argument("--out", type=Path, default=ROOT / "work" / TILES_NAME)
    parser.add_argument("--thumbnail", action="store_true",
                        help="render catalog/chips/thumbnail.webp from the published tiles "
                             "instead")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="chiitiler's URL")
    args = parser.parse_args(argv)
    try:
        if args.thumbnail:
            out = render_thumbnail(THUMBNAIL, style=STYLE, tiles_url=TILES_URL,
                                   server=args.server)
            print(f"wrote {out}")
            return 0
        count = build_tiles(args.table, args.out)
    except ChipsTilesError as err:
        sys.exit(f"chips tiles: {err}")
    print(f"wrote {args.out}: {count:,} chip locations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
