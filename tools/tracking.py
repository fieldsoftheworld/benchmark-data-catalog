#!/usr/bin/env python3
"""Read and update ``tracking.csv``, the queue of region-year datasets.

One row per region-year (``dataset_id`` like ``at_2018``). The planning columns
(``status``, ``imagery``, ``filter``, ...) are edited by hand; the progress
columns (``built``, ``published``, ``imagery_done``, ``ftwd_commit``,
``issues``) are written by ``tools/run_batch.py``. Rows keep their file order,
so a diff shows only what changed.

``status`` is one of:

- ``include``: build and publish it.
- ``skip-no-imagery``: no Sentinel-2 for that year; not published at all.
- ``blocked``: wanted, but cannot be built yet; the notes say what it waits for
  (e.g. no quarterly mosaics for that year).
- ``discuss`` / ``exclude``: not built until someone decides otherwise.

``imagery`` is ``scenes+mosaics`` (2018-2025 except 2023, whose Q2 mosaic is
missing), ``scenes`` (2015-2017, 2023, 2026) or ``none`` (before 2015): the
imagery that exists for the year. ``mosaics`` builds only the quarterly mosaics
of a ``scenes+mosaics`` year, for releases that leave the scenes out.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT  # noqa: E402

TRACKING = ROOT / "tracking.csv"

STATUSES = ("include", "skip-no-imagery", "blocked", "discuss", "exclude")
IMAGERY = {
    "scenes+mosaics": ("scenes", "mosaics"),
    "mosaics": ("mosaics",),
    "scenes": ("scenes",),
    "none": (),
}


def load(path: Path = TRACKING) -> list[dict[str, str]]:
    """Every row of ``tracking.csv``, in file order."""
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def save(rows: list[dict[str, str]], path: Path = TRACKING) -> None:
    """Write ``rows`` back with the header of the first row."""
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def row(dataset_id: str, rows: list[dict[str, str]] | None = None) -> dict[str, str]:
    """The row for ``dataset_id``; exits when there is none."""
    for r in rows if rows is not None else load():
        if r["dataset_id"] == dataset_id:
            return r
    sys.exit(f"{dataset_id!r} is not in tracking.csv")


def update(dataset_id: str, path: Path = TRACKING, **fields: str) -> None:
    """Set ``fields`` on one row and write the file back.

    Re-reads the file first so that concurrent builds of different datasets,
    each updating its own row when it finishes, do not drop each other's
    writes (the window between read and write is a few milliseconds).
    """
    rows = load(path)
    target = row(dataset_id, rows)
    unknown = set(fields) - set(target)
    if unknown:
        raise KeyError(f"tracking.csv has no column(s) {sorted(unknown)}")
    target.update(fields)
    save(rows, path)


#: ``filter`` value for a source with no class column to filter on (lu): every parcel is a field.
NO_FILTER = "none"


def filter_file(r: dict[str, str]) -> str | None:
    """The row's class filter file name; None when it has none (yet, or by design)."""
    return r["filter"] if r["filter"] not in ("", NO_FILTER) else None


def source_stem(r: dict[str, str]) -> str:
    """The harmonized file stem: ``<stem>-<year>.parquet`` under ``<harmonized_id>/year=<year>/``.

    Usually the collection id itself. A collection that publishes one file per
    sub-region (Switzerland's cantons, ``ch_ag-2025.parquet``) names the
    sub-region in ``source_stem``, and each sub-region is its own dataset.
    """
    return r.get("source_stem") or r["harmonized_id"]


def imagery_modes(r: dict[str, str]) -> tuple[str, ...]:
    """The ftwd imagery modes a row's ``imagery`` value asks for."""
    try:
        return IMAGERY[r["imagery"]]
    except KeyError:
        sys.exit(f"{r['dataset_id']}: unknown imagery {r['imagery']!r} (one of {list(IMAGERY)})")
