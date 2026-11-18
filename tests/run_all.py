#!/usr/bin/env python3
"""Run every gate. Exit non-zero if any fails.

The list is explicit rather than globbed so that the gates are visible in one
place and adding one is a deliberate edit. Run from anywhere:

    python3 tests/run_all.py

``--skip-slow`` leaves out the gates that read the whole catalog, and
``--only-slow`` runs just those (see tests/scope.py). CI runs the first once
and the second once per source group.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TESTS = [
    "test_manifest.py",
    "test_common.py",
    "test_overlay.py",
    "test_scope.py",
    "test_ftwd_pin.py",
    "test_build.py",
    "test_batch_tools.py",
    "test_filters.py",
    "test_catalogize.py",
    "test_thumbnails.py",
    "test_links.py",
    "test_publish.py",
    "test_upload_data.py",
    "test_prune_bucket.py",
    "test_merge_es_2025.py",
    "test_label_extent.py",
    "test_catalog_stats.py",
    "test_backfill.py",
    "test_relayout.py",
    "test_bucket_copy.py",
    "test_verify_move.py",
    "test_prune_flat.py",
    "test_migrate.py",
    "test_stac_valid.py",
    "test_conformance.py",
]

# They read every STAC object, so they take a scope (tests/scope.py).
SLOW = {"test_links.py", "test_stac_valid.py", "test_conformance.py"}

MODES = {
    (): TESTS,
    ("--skip-slow",): [t for t in TESTS if t not in SLOW],
    ("--only-slow",): [t for t in TESTS if t in SLOW],
}
selected = MODES.get(tuple(sys.argv[1:]))
if selected is None:
    raise SystemExit("usage: python3 tests/run_all.py [--skip-slow | --only-slow]")

failed = []
for name in selected:
    path = HERE / name
    if not path.exists():
        print(f"error  missing gate: {name}")
        failed.append(name)
        continue
    print(f"\n=== {name} " + "=" * (60 - len(name)), flush=True)
    if subprocess.run([sys.executable, str(path)]).returncode != 0:
        failed.append(name)

print()
if failed:
    print("FAILED: " + ", ".join(failed))
    raise SystemExit(1)
print("all gates passed")
