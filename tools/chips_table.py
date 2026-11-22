#!/usr/bin/env python3
"""Build the root chips table: every chip of every published dataset, with its splits.

    uv run python tools/chips_table.py                    # frozen splits from the published table
    uv run python tools/chips_table.py --staged pt_2021   # read pt_2021's chips from staging/

A wrapper over ``ftwd chips-table`` (``ftw_dataset_tools.api.chips_table``, which owns the
columns, the split schemes, the refusals and ``LICENSES``) with this catalog's inputs:
the root ``catalog/catalog.json``, data files served from ``PUBLIC_BASE``, and each
``--staged`` id read from ``staging/<id>`` as an ftwd ``--local`` directory. A staged id
not published yet goes in the group its recipe's ``source_via`` names.

Writes ``work/chips.parquet`` (``--out`` to change), so a dataset's upload never publishes
it; copy it to ``staging/`` and upload it on its own (README, "Root chips table").
"""
from __future__ import annotations

import argparse
import sys

import duckdb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog_stats import published_datasets  # noqa: E402
from common import CATALOG, PUBLIC_BASE, ROOT, STAGING, LayoutError, recipe_group  # noqa: E402
from ftw_dataset_tools.api.chips_table import (  # noqa: E402
    TABLE_NAME,
    ChipsTableError,
    build_chips_table,
    resolve_inputs,
)

__all__ = ["TABLE_NAME", "main", "staged_inputs"]


def staged_inputs(staged: list[str], *, catalog: Path = CATALOG, staging: Path = STAGING,
                  root: Path = ROOT) -> tuple[list[Path], dict[str, str]]:
    """ftwd's ``local_dirs`` and ``groups`` for the staged ids: a group only for the
    ids the catalog doesn't publish yet (ftwd takes a published one's group from it)."""
    published = {relpath.rpartition("/")[2] for relpath in published_datasets(catalog / "catalog.json")}
    local_dirs = [staging / dataset_id for dataset_id in staged]
    groups = {dataset_id: recipe_group(dataset_id, root)
              for dataset_id in staged if dataset_id not in published}
    return local_dirs, groups


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--staged", nargs="*", default=[],
                        help="dataset ids to read from staging/ instead of the bucket")
    parser.add_argument("--previous", default=f"{PUBLIC_BASE}/{TABLE_NAME}",
                        help="the table to carry frozen splits from (default: the published one)")
    parser.add_argument("--drop", nargs="*", default=[],
                        help="datasets whose frozen splits may be lost: left out entirely, or "
                             "chips a rebuild no longer has")
    parser.add_argument("--out", type=Path, default=ROOT / "work" / TABLE_NAME)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    try:
        local_dirs, groups = staged_inputs(sorted(set(args.staged)))
        inputs = resolve_inputs(CATALOG / "catalog.json", PUBLIC_BASE, local_dirs, groups)
        rows = build_chips_table(inputs, args.out, args.previous, drop=args.drop,
                                 workers=args.workers)
    except (ChipsTableError, LayoutError, OSError, duckdb.Error) as err:
        sys.exit(f"chips table: {err}")
    print(f"wrote {args.out}: {rows:,} chips from {len(inputs)} datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
