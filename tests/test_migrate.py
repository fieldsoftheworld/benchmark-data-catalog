#!/usr/bin/env python3
"""migrate: the per-dataset chain on a builder.

Checks the step order and arguments (publish with --no-root, verify with
--allow-missing-root, no prune), that a failed step stops that dataset and
is logged, that the copy plan holds only the files copied as they are, that a
verified dataset is skipped, and that the patch carries the dataset's catalog
folder and recipe, new files included. Runs no tool and touches no bucket.

Run: python3 tests/test_migrate.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import migrate  # noqa: E402
from fake_s3 import FakeS3  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


class Runner:
    def __init__(self, fail_at=None):
        self.calls, self.fail_at = [], fail_at

    def __call__(self, argv, stdout, stderr, cwd):
        name = Path(argv[1]).name
        self.calls.append([name, *argv[2:]])
        stdout.write(f"ran {name}\n")
        return subprocess.CompletedProcess(argv, 1 if name == self.fail_at else 0)


with tempfile.TemporaryDirectory() as tmp:
    results = Path(tmp)
    planned = []
    runner = Runner()
    migrate.run_dataset("lv_2020", workers=8, results=results, runner=runner,
                        copy_plan=lambda i, p: planned.append((i, p)) or 3)
    names = [c[0] for c in runner.calls]
    check(names == ["backfill.py", "bucket_copy.py", "upload_data.py", "publish.py", "verify_move.py"],
          f"the chain runs in order and never prunes: {names}")
    check(planned == [("lv_2020", results / "lv_2020.copy.tsv")]
          and runner.calls[1][1:] == [str(results / "lv_2020.copy.tsv"), "--only", "lv_2020", "--confirm"],
          f"the copy runs from the plan written just before: {runner.calls[1]}")
    check(runner.calls[0][1:] == ["--read-flat", "--workers", "8", "lv_2020"],
          f"the backfill reads the old flat folder: {runner.calls[0]}")
    check("--no-root" in runner.calls[3] and "--allow-missing-root" in runner.calls[4],
          "publish leaves the root out and verify accepts the root published last")
    log = (results / "lv_2020.log").read_text()
    check("=== copy plan" in log and "3 pair(s) to copy" in log and "=== verify: exit 0" in log,
          "each step is logged")

    runner = Runner(fail_at="upload_data.py")
    try:
        migrate.run_dataset("lv_2021", workers=8, results=results, runner=runner,
                            copy_plan=lambda i, p: 0)
        check(False, "a failed step raises")
    except migrate.StepFailed as err:
        check(err.step == "upload data" and [c[0] for c in runner.calls][-1] == "upload_data.py",
              f"a failed step stops the dataset there: {err}")

    (results / "lv_2020.json").write_text(json.dumps({"id": "lv_2020", "ok": True, "under": None}))
    (results / "lv_2022.json").write_text(json.dumps({"id": "lv_2022", "ok": True, "under": "_trial"}))
    check(migrate.is_verified("lv_2020", results) and not migrate.is_verified("lv_2022", results)
          and not migrate.is_verified("lv_2023", results),
          "only a passing real-prefix verification counts as done")

# copy plan: rw_rwanda_ml_2021 is published under rw_rwanda_ml in the real catalog
s3 = FakeS3()
for rel in ("collection.json", "README.md", "items.parquet", "rw_rwanda_ml_2021_chips.parquet",
            "chips.pmtiles", "chips/A/c/c.json", "chips/A/c/c_q1.tif", "chips/A/README.md"):
    s3.put(f"ftw/benchmark-data/rw_rwanda_ml_2021/{rel}")
s3.put("ftw/benchmark-data/rw_rwanda_ml_2021x/x.tif")
with tempfile.TemporaryDirectory() as tmp:
    plan = Path(tmp) / "p.tsv"
    count = migrate.write_copy_plan("rw_rwanda_ml_2021", plan, client=s3)
    lines = plan.read_text().splitlines()
    check(count == 3 and sorted(line.split("\t")[0].rsplit("/", 1)[1] for line in lines)
          == ["c_q1.tif", "chips.pmtiles", "rw_rwanda_ml_2021_chips.parquet"],
          f"the plan copies only data files of that dataset: {lines}")
    check(all(line.split("\t")[1].startswith("ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021/")
              for line in lines), "new keys sit under the source group")

# patch: catalog folder and recipe, with a new file, against HEAD
with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp) / "repo"
    (repo / "catalog/lv/lv_2020").mkdir(parents=True)
    (repo / "datasets").mkdir()
    (repo / "catalog/lv/lv_2020/collection.json").write_text("{}\n")
    (repo / "catalog/lv/catalog.json").write_text("{}\n")
    (repo / "datasets/lv_2020.yaml").write_text("a: 1\n")
    git = ["git", "-C", str(repo)]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
    (repo / "catalog/lv/lv_2020/collection.json").write_text('{"a": 1}\n')
    (repo / "catalog/lv/lv_2020/llms.txt").write_text("new\n")
    (repo / "catalog/lv/catalog.json").write_text('{"group": 1}\n')
    (repo / "datasets/lv_2020.yaml").write_text("a: 2\n")
    patch = migrate.write_patch("lv_2020", "lv/lv_2020", Path(tmp), repo).read_text()
    check("catalog/lv/lv_2020/collection.json" in patch and "catalog/lv/lv_2020/llms.txt" in patch
          and "datasets/lv_2020.yaml" in patch and "catalog/lv/catalog.json" not in patch,
          f"the patch holds the dataset folder (new files too) and recipe, not the group: {patch}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: migrate chains backfill, copy, upload, publish and verify per dataset, never pruning")
