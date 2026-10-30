#!/usr/bin/env python3
"""Preflight: does each region-year's source exist, and does its filter cover it?

    uv run python tools/check_filters.py                    # every 'include' row
    uv run python tools/check_filters.py be_wal_2022 fi_2020
    uv run python tools/check_filters.py --ftwd-checkout ../ftw-dataset-tools

For each row, reads the year's parquet over HTTPS (one distinct-values query
on the class column) and applies ftwd's own ``ClassFilter`` checks, the same
ones ``ftwd run`` would fail on hours into a build. Writes the outcome into
``tracking.csv``'s ``issues`` column (cleared when the row passes), which
``run_batch.py --next`` skips:

- ``no source``: the year's parquet is not published.
- ``no filter``: the row names no class filter.
- ``filter column missing``: none of the filter's columns are in the data.
- ``filter gap: <codes>``: classes in the data the filter neither includes
  nor excludes.

Filters are read from ``datasets/filters/`` when copied there, else from
``--ftwd-checkout``'s ``configs/filters/``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tracking  # noqa: E402
from common import ROOT  # noqa: E402
from new_dataset import source_urls  # noqa: E402

PREFLIGHT_PREFIXES = ("no source", "no filter", "filter column missing", "filter gap")


def check_row(con, row: dict[str, str], filters: list[Path]) -> str:
    """The row's issue, or "" when it is ready to build."""
    from ftw_dataset_tools.api.config import ClassFilter, ClassFilterError

    url = source_urls(row["harmonized_id"], int(row["year"]))["parquet"]
    try:
        cols = [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{url}')").fetchall()]
    except Exception:  # noqa: BLE001 - duckdb raises a family of IO errors here
        return "no source"
    if not row["filter"]:
        return "no filter"
    path = next((d / row["filter"] for d in filters if (d / row["filter"]).is_file()), None)
    if path is None:
        sys.exit(f"{row['dataset_id']}: filter {row['filter']} not found in {filters}")
    class_filter = ClassFilter.from_file(path)
    try:
        col = class_filter.resolve_column(cols)
    except ClassFilterError:
        return "filter column missing"
    distinct = {
        v[0]
        for v in con.execute(f'SELECT DISTINCT "{col}"::VARCHAR FROM read_parquet(\'{url}\')').fetchall()
    }
    uncovered = sorted(
        v for v in distinct if v is not None and v not in class_filter.include + class_filter.exclude
    )
    if uncovered:
        shown = ", ".join(uncovered[:8]) + (f" (+{len(uncovered) - 8} more)" if len(uncovered) > 8 else "")
        return f"filter gap: {shown}"
    return ""


def main(argv: list[str] | None = None) -> int:
    import duckdb

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="*", help="rows to check (default: every 'include')")
    parser.add_argument("--ftwd-checkout", type=Path, default=None)
    args = parser.parse_args(argv)

    filters = [ROOT / "datasets" / "filters"]
    if args.ftwd_checkout is not None:
        filters.append(args.ftwd_checkout / "configs" / "filters")
    rows = tracking.load()
    targets = [r for r in rows if r["dataset_id"] in args.dataset_ids] if args.dataset_ids else [
        r for r in rows if r["status"] == "include"
    ]
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    problems = 0
    for row in targets:
        issue = check_row(con, row, filters)
        previous = row["issues"]
        # Only replace issues this tool owns; a build failure stays until a rebuild clears it.
        if issue or previous.startswith(PREFLIGHT_PREFIXES):
            tracking.update(row["dataset_id"], issues=issue)
        problems += bool(issue)
        print(f"{'ok   ' if not issue else 'issue'}  {row['dataset_id']}  {issue}")
    print(f"\n{len(targets) - problems}/{len(targets)} ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
