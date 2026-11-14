#!/usr/bin/env python3
"""verify_move: an old flat dataset folder against its new <source>/<id>/ folder.

Builds both folders in a fake bucket and checks that a correct move passes,
and that a missing key, a changed copied file, an unexpected file and a broken
href each fail, while the backfill's expected changes (rewritten JSON, the
chips GeoParquet, the new embeddings GeoParquet, a multipart ETag) and, with
--allow-missing-root, a root not published yet do not. No network.

Run: python3 tests/test_verify_move.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import verify_move  # noqa: E402
from fake_s3 import FakeS3  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


P = "ftw/benchmark-data"
ID, G = "lv_2020", "lv"


def bucket(*, root_published=True) -> FakeS3:
    s3 = FakeS3()
    item_old = {"links": [{"rel": "root", "href": "../../../../catalog.json"},
                          {"rel": "parent", "href": "../catalog.json"}],
                "assets": {"image": {"href": "./c_q1.tif"}}}
    item_new = {"links": [{"rel": "root", "href": "../../../../../catalog.json"},
                          {"rel": "parent", "href": "../catalog.json"},
                          {"rel": "license", "href": "https://example.org/x"}],
                "assets": {"image": {"href": "./c_q1.tif"}}}
    coll = {"links": [{"rel": "root", "href": "../../catalog.json"},
                      {"rel": "parent", "href": "../catalog.json"},
                      {"rel": "child", "href": "./chips/A/catalog.json"}],
            "assets": {"chips": {"href": "./lv_2020_chips.parquet#frag"}}}
    sub = {"links": [{"rel": "item", "href": "./c/c.json"}]}
    for base, item in ((f"{P}/{ID}", item_old), (f"{P}/{G}/{ID}", item_new)):
        s3.put(f"{base}/chips/A/c/c.json", item)
        s3.put(f"{base}/chips/A/c/c_q1.tif", b"tif", etag="t1")
        s3.put(f"{base}/chips/A/catalog.json", sub)
        s3.put(f"{base}/fields.parquet", b"f" * 10, etag="abc-3")
    s3.put(f"{P}/{ID}/collection.json", {"links": []})
    s3.put(f"{P}/{G}/{ID}/collection.json", coll)
    s3.put(f"{P}/{ID}/lv_2020_chips.parquet", b"old")
    s3.put(f"{P}/{G}/{ID}/lv_2020_chips.parquet", b"new with admin")
    s3.put(f"{P}/{G}/{ID}/lv_2020_field_embeddings.parquet", b"emb")
    s3.objects[f"{P}/{G}/{ID}/fields.parquet"] = (10, "def-2", b"f" * 10)  # copied in parts
    s3.put(f"{P}/{ID}x/x.tif", b"sibling")
    s3.put(f"{P}/{G}/catalog.json", {"links": []})
    if root_published:
        s3.put(f"{P}/catalog.json", {"links": []})
    return s3


def run(s3, **kw):
    return verify_move.verify(ID, client=s3, group=G, **kw)


record = run(bucket())
check(record["ok"], f"a correct move passes: {record['problems']}")
check(record["counts"]["old"] == 6 and record["counts"]["new"] == 7 and record["counts"]["json"] == 3,
      f"sibling ids stay out of both listings: {record['counts']}")

record = run(bucket(root_published=False))
check(not record["ok"] and any("catalog.json" in p for p in record["problems"]),
      "a root catalog not in the bucket is a broken href")
check(run(bucket(root_published=False), allow_missing_root=True)["ok"],
      "--allow-missing-root accepts the root published last")

s3 = bucket()
del s3.objects[f"{P}/{G}/{ID}/chips/A/c/c_q1.tif"]
problems = run(s3)["problems"]
check(any("missing at the new key: chips/A/c/c_q1.tif" in p for p in problems)
      and any("broken href" in p and "c_q1.tif" in p for p in problems),
      f"a key not copied is reported, and so is the href to it: {problems}")

s3 = bucket()
s3.put(f"{P}/{G}/{ID}/chips/A/c/c_q1.tif", b"tif", etag="other")
check(any("copied file differs" in p for p in run(s3)["problems"]),
      "a copied raster with another ETag is reported")

s3 = bucket()
s3.put(f"{P}/{G}/{ID}/stray.txt", b"?")
check(any("unexpected new file: stray.txt" in p for p in run(s3)["problems"]),
      "a file only the new folder has, beyond the embeddings, is reported")

check(verify_move.resolve("g/d/chips/A/c/c.json", "../../../../../catalog.json") == "catalog.json"
      and verify_move.resolve("g/d/x.json", "https://a/b") is None,
      "hrefs resolve from the catalog root; absolute ones are skipped")

with tempfile.TemporaryDirectory() as tmp:
    path = verify_move.write_record(run(bucket()), Path(tmp))
    saved = json.loads(path.read_text())
    check(path.name == "lv_2020.json" and saved["ok"] and saved["group"] == "lv" and saved["verified_at"],
          "the record is written per dataset")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: verify_move passes a correct move and reports what is missing, changed or broken")
