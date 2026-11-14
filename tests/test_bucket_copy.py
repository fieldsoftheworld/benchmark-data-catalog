#!/usr/bin/env python3
"""bucket_copy: server-side copies from flat keys to grouped keys.

Uses a fake S3 client: reads a plan in both key forms, lists the source and
destination folders, skips pairs already copied, refuses a plan naming objects
the bucket lacks, copies below a trial folder, and sends objects over 5 GB
through the multipart copy. No network, no AWS.

Run: python3 tests/test_bucket_copy.py
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import bucket_copy  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


class FakePaginator:
    def __init__(self, objects):
        self.objects = objects

    def paginate(self, Bucket, Prefix):
        yield {"Contents": [{"Key": k, "Size": s} for k, s in sorted(self.objects.items())
                            if k.startswith(Prefix)]}


class FakeClient:
    def __init__(self, objects):
        self.objects = dict(objects)
        self.single, self.multipart, self.prefixes = [], [], []

    def get_paginator(self, name):
        return FakePaginator(self.objects)

    def copy_object(self, CopySource, Bucket, Key, MetadataDirective):
        self.single.append((CopySource["Key"], Key))
        self.objects[Key] = self.objects[CopySource["Key"]]

    def copy(self, src, bucket, key, Config):
        self.multipart.append((src["Key"], key))
        self.objects[key] = self.objects[src["Key"]]


P = "benchmark-data"
BIG = 6 * 1024**3
OBJECTS = {
    f"{P}/lv_2020/chips/A/c/c_q1.tif": 10,
    f"{P}/lv_2020/lv_2020_fields.parquet": BIG,
    f"{P}/lv_2020x/x.tif": 3,
    f"{P}/lv/lv_2020/chips/A/c/c_q1.tif": 10,  # already copied
}

with tempfile.TemporaryDirectory() as tmp:
    plan = Path(tmp) / "keys.copy.tsv"
    plan.write_text(
        f"ftw/{P}/lv_2020/chips/A/c/c_q1.tif\tftw/{P}/lv/lv_2020/chips/A/c/c_q1.tif\n"
        f"{P}/lv_2020/lv_2020_fields.parquet\t{P}/lv/lv_2020/lv_2020_fields.parquet\n"
        f"{P}/lv_2020x/x.tif\t{P}/lv/lv_2020x/x.tif\n"
    )
    pairs = bucket_copy.read_pairs(plan, "ftw", P, {"lv_2020"})
    check([p.old for p in pairs] == ["lv_2020/chips/A/c/c_q1.tif", "lv_2020/lv_2020_fields.parquet"],
          f"both key forms read, --only keeps one dataset and not a sibling id: {pairs}")
    check(bucket_copy._folders((p.old for p in pairs), 1) == {"lv_2020/"}
          and bucket_copy._folders((p.new for p in pairs), 2) == {"lv/lv_2020/"},
          "the old and new dataset folders are listed, nothing wider")

    client = FakeClient(OBJECTS)
    source = bucket_copy.sizes_below(client, "ftw", P, {"lv_2020/"})
    check("lv_2020x/x.tif" not in source, "listing a dataset folder leaves a sibling id out")
    dest = bucket_copy.sizes_below(client, "ftw", P, {"lv/lv_2020/"})
    pending, missing = bucket_copy.todo(pairs, source, dest, "")
    check([p.old for p in pending] == ["lv_2020/lv_2020_fields.parquet"] and not missing,
          f"a pair whose destination already has the size is skipped: {pending}")

    bucket_copy.run_copies(client, "ftw", P, pending, source, "", 4)
    check(client.multipart == [(f"{P}/lv_2020/lv_2020_fields.parquet",
                                f"{P}/lv/lv_2020/lv_2020_fields.parquet")] and not client.single,
          f"an object over 5 GB goes through the multipart copy: {client.multipart}")

    client = FakeClient(OBJECTS)
    pending, _ = bucket_copy.todo(pairs, source, {}, "_trial")
    bucket_copy.run_copies(client, "ftw", P, pending[:1], source, "_trial", 2)
    check(client.single == [(f"{P}/lv_2020/chips/A/c/c_q1.tif",
                             f"{P}/_trial/lv/lv_2020/chips/A/c/c_q1.tif")],
          f"--under writes below the trial folder: {client.single}")

    gone = {k: v for k, v in source.items() if not k.endswith(".tif")}
    _, missing = bucket_copy.todo(pairs, gone, {}, "")
    check([p.old for p in missing] == ["lv_2020/chips/A/c/c_q1.tif"],
          "a plan naming an object the bucket lacks is reported")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: bucket copies skip what is there, refuse what is gone and split large objects")
