#!/usr/bin/env python3
"""The prune contract: delete only what the current build no longer publishes.

tools/prune_bucket.py compares a dataset's bucket listing with the keys the
staged data and the published catalog would write, and deletes the rest. This
gate builds a real staging and catalog tree and checks that kept files, the
catalog's own files and a sibling dataset with a shared name prefix are never
stale, and that the script refuses a dataset with no staging.

No network, no AWS, no credentials.

Run: python3 tests/test_prune_bucket.py
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import prune_bucket  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = {
        "write_prefix": "s3://ftw/benchmark-data",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }
    touch(root / "staging/d1/chips/A/c1/c1_semantic_2_class.tif")
    touch(root / "staging/d1/chips/A/c1/c1.json")
    touch(root / "catalog/d1/collection.json")
    touch(root / "catalog/d1/chips/A/catalog.json")
    touch(root / "catalog/d10/collection.json")

    real = (prune_bucket.data_root, prune_bucket.collect_data_uploads, prune_bucket.collect_uploads)
    prune_bucket.data_root = lambda c: real[0](c, root)
    prune_bucket.collect_data_uploads = lambda c, only: real[1](c, root, only=only)
    prune_bucket.collect_uploads = lambda c: real[2](c, root)
    try:
        keep = {
            "benchmark-data/d1/chips/A/c1/c1_semantic_2_class.tif",
            "benchmark-data/d1/chips/A/c1/c1.json",
            "benchmark-data/d1/collection.json",
            "benchmark-data/d1/chips/A/catalog.json",
        }
        drop = {
            "benchmark-data/d1/chips/B/c9/c9_semantic_2_class.tif",
            "benchmark-data/d1/chips/B/catalog.json",
        }
        remote = dict.fromkeys(keep | drop | {"benchmark-data/d10/collection.json"}, (1, "e"))
        stale = set(prune_bucket.stale_keys("d1", config, remote))
        check(stale == drop, f"only the dropped chip's files are stale, got {sorted(stale)}")

        try:
            prune_bucket.stale_keys("d2", config, remote)
            check(False, "a dataset without staging is refused")
        except SystemExit as err:
            check("no staging" in str(err), f"the refusal says why, got {err}")
    finally:
        prune_bucket.data_root, prune_bucket.collect_data_uploads, prune_bucket.collect_uploads = real

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: prune contract holds")
