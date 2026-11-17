#!/usr/bin/env python3
"""prune_flat: deleting a dataset's old flat keys after its move is verified.

In a fake bucket: refuses without a passing verification record, refuses a
trial record, refuses when an old key has no new key, refuses an id that is a
group name, deletes only <prefix>/<id>/ keys (not a sibling id, the group or
the root), and a rerun finds nothing left. Dry run deletes nothing. No network.

Run: python3 tests/test_prune_flat.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import prune_flat  # noqa: E402
from fake_s3 import FakeS3  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


P = "benchmark-data"


def bucket() -> FakeS3:
    s3 = FakeS3()
    for rel in ("collection.json", "chips/A/c/c_q1.tif"):
        s3.put(f"{P}/lv_2020/{rel}")
        s3.put(f"{P}/lv/lv_2020/{rel}")
    s3.put(f"{P}/lv_2020x/x.tif")
    s3.put(f"{P}/lv/catalog.json")
    s3.put(f"{P}/catalog.json")
    return s3


def record(results: Path, dataset_id: str, ok=True, under=None) -> None:
    results.mkdir(parents=True, exist_ok=True)
    (results / f"{dataset_id}.json").write_text(json.dumps({"id": dataset_id, "ok": ok, "under": under}))


def run(s3, results, ids=("lv_2020",), confirm=True, groups=frozenset({"lv"})):
    return prune_flat.prune(list(ids), s3, "ftw", P, groups=set(groups),
                            relpath=lambda i: f"lv/{i}", results=results, workers=4, confirm=confirm)


with tempfile.TemporaryDirectory() as tmp:
    results = Path(tmp) / "migration"
    s3 = bucket()
    total, refused = run(s3, results)
    check(total == 0 and refused and not s3.deleted, "no verification record: refused")

    record(results, "lv_2020", ok=False)
    check(run(s3, results)[1] and not s3.deleted, "a failed verification: refused")
    record(results, "lv_2020", under="_trial")
    check(run(s3, results)[1] and not s3.deleted, "a trial verification: refused")

    record(results, "lv_2020")
    gone = bucket()
    del gone.objects[f"{P}/lv/lv_2020/chips/A/c/c_q1.tif"]
    total, refused = run(gone, results)
    check(refused and "no new key" in refused[0] and not gone.deleted,
          f"an old key without its new key: refused, nothing deleted: {refused}")

    record(results, "lv")
    check(run(s3, results, ids=("lv",))[1] and not s3.deleted, "an id that is a group name: refused")

    total, refused = run(s3, results, confirm=False)
    check(total == 2 and not refused and not s3.deleted, "dry run counts and deletes nothing")

    total, refused = run(s3, results)
    check(sorted(s3.deleted) == [f"{P}/lv_2020/chips/A/c/c_q1.tif", f"{P}/lv_2020/collection.json"],
          f"only the flat lv_2020/ keys are deleted: {s3.deleted}")
    check({f"{P}/lv_2020x/x.tif", f"{P}/lv/catalog.json", f"{P}/catalog.json",
           f"{P}/lv/lv_2020/collection.json"} <= set(s3.objects),
          "the sibling id, the group, the root and the new keys stay")
    check(run(s3, results)[0] == 0, "a rerun finds nothing left to delete")

    record(results, "lv_2021")
    record(results, "lv_2022", ok=False)
    record(results, "lv_2023", under="_trial")
    check(prune_flat.verified_ids(results) == ["lv", "lv_2020", "lv_2021"],
          f"--all-verified takes passing real-prefix records: {prune_flat.verified_ids(results)}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: prune_flat deletes only verified flat keys and refuses everything else")
