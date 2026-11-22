#!/usr/bin/env python3
"""Tile the root chips table into ``chips.pmtiles``: every chip location, at every zoom.

    uv run python tools/chips_tiles.py                        # from the published table
    uv run python tools/chips_tiles.py --table work/chips.parquet
    uv run python tools/chips_tiles.py --thumbnail            # render catalog/thumbnail.webp

A wrapper over ``ftwd chips-tiles`` (``ftw_dataset_tools.api.chips_tiles``, which owns the
layers, their zooms and attributes, and the drop check). Writes ``work/chips.pmtiles``
(``--out`` to change); upload it like the table (README, "Root chips table"). Needs
tippecanoe on PATH.

``--thumbnail`` renders ``catalog/thumbnail.webp`` with ``catalog/chips.style.json`` over
the published ``chips.pmtiles``, through a running chiitiler (``tools/chiitiler.sh``).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import PUBLIC_BASE, ROOT  # noqa: E402
from ftw_dataset_tools.api.chips_table import TABLE_NAME  # noqa: E402
from ftw_dataset_tools.api.chips_tiles import (  # noqa: E402
    DEFAULT_SERVER,
    TILES_NAME,
    ChipsTilesError,
    build_tiles,
    render_thumbnail,
)

STYLE = ROOT / "catalog" / "chips.style.json"
THUMBNAIL = ROOT / "catalog" / "thumbnail.webp"
TILES_URL = f"{PUBLIC_BASE}/{TILES_NAME}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--table", default=f"{PUBLIC_BASE}/{TABLE_NAME}",
                        help="the chips table to tile (default: the published one)")
    parser.add_argument("--out", type=Path, default=ROOT / "work" / TILES_NAME)
    parser.add_argument("--thumbnail", action="store_true",
                        help="render catalog/thumbnail.webp from the published tiles instead")
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
