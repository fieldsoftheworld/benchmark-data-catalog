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

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import catalogize  # noqa: E402
import prune_bucket  # noqa: E402
from upload_data import collect_data_uploads  # noqa: E402

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
    touch(root / "catalog/g/d1/collection.json")
    touch(root / "catalog/g/d1/chips/A/catalog.json")
    touch(root / "catalog/g/d10/collection.json")

    keep = {
        "benchmark-data/g/d1/chips/A/c1/c1_semantic_2_class.tif",
        "benchmark-data/g/d1/chips/A/c1/c1.json",
        "benchmark-data/g/d1/collection.json",
        "benchmark-data/g/d1/chips/A/catalog.json",
    }
    drop = {
        "benchmark-data/g/d1/chips/B/c9/c9_semantic_2_class.tif",
        "benchmark-data/g/d1/chips/B/catalog.json",
    }
    others = {"benchmark-data/g/d10/collection.json", "benchmark-data/d1/collection.json"}
    remote = dict.fromkeys(keep | drop | others, (1, "e"))
    stale = set(prune_bucket.stale_keys("d1", config, remote, root))
    check(stale == drop, f"only the dropped chip's files are stale, got {sorted(stale)}")

    try:
        touch(root / "catalog/g/d2/collection.json")
        prune_bucket.stale_keys("d2", config, remote, root)
        check(False, "a dataset without staging is refused")
    except SystemExit as err:
        check("no staging" in str(err), f"the refusal says why, got {err}")

# A style the collection no longer references (v1's split.json, still staged because
# ftwd never deletes it) is neither committed, uploaded nor kept in the bucket.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = {
        "write_prefix": "s3://ftw/benchmark-data",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }
    staged = root / "staging/d3"
    published = root / "catalog/g/d3"
    staged.mkdir(parents=True)
    (staged / "collection.json").write_text(json.dumps(
        {"type": "Collection", "id": "d3", "assets": {"style-outline": {"href": "./styles/outline.json"}}}))
    for name in ("outline", "split"):
        touch(staged / "styles" / f"{name}.json")
        touch(published / "styles" / f"{name}.json")
    (published / "collection.json").write_text("{}")

    with redirect_stdout(io.StringIO()):
        catalogize.copy_committed("d3", staging=root / "staging", catalog=root / "catalog")
    styles = sorted(p.name for p in (published / "styles").iterdir())
    check(styles == ["outline.json"], f"catalogize leaves only the referenced style, got {styles}")

    uploads = {u.key for u in collect_data_uploads(config, root, only={"d3"})}
    check(not any("/styles/" in key for key in uploads), f"upload_data uploads no styles, got {sorted(uploads)}")

    remote = dict.fromkeys(
        ["benchmark-data/g/d3/collection.json", "benchmark-data/g/d3/styles/outline.json",
         "benchmark-data/g/d3/styles/split.json"], (1, "e"))
    stale = prune_bucket.stale_keys("d3", config, remote, root)
    check(stale == ["benchmark-data/g/d3/styles/split.json"],
          f"the bucket's split.json is stale and outline.json is kept, got {stale}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: prune contract holds")
