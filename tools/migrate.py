#!/usr/bin/env python3
"""Move datasets into their source groups in the bucket, with the backfill, on a builder.

For each dataset id, in order, stopping that dataset at the first failed step:

1. ``backfill.py --read-flat <id>``: fetch from the old ``<id>/`` folder, add
   admin names and field embeddings, re-catalogize into ``<source>/<id>/``;
2. copy plan: list the old folder and split it with ``relayout.bucket_moves``
   into ``work/migration/<id>.copy.tsv``;
3. ``bucket_copy.py``: server-side copies of the files the move leaves as they are;
4. ``upload_data.py --only <id> --confirm``: the staged files that changed;
5. ``publish.py --only <id> --no-root --confirm``: the catalog files;
6. ``verify_move.py <id> --allow-missing-root``.

Every step is safe to repeat, so a rerun resumes; a dataset whose
verification already passed is skipped unless ``--redo``. A failed dataset is
logged and the next one starts. Never deletes anything (``prune_flat.py``
does that, later). Each finished dataset leaves ``work/migration/<id>.patch``
(``catalog/<source>/<id>/`` and ``datasets/<id>.yaml``, against HEAD) to
apply where the catalog repository is committed.

    uv run python tools/migrate.py lv_2020 lv_2021
    uv run python tools/migrate.py --ids-file work/migration/batch-3.txt --workers 16
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, dataset_relpath  # noqa: E402

RESULTS = ROOT / "work" / "migration"
READ_PREFIX = "ftw/benchmark-data"


class StepFailed(Exception):
    def __init__(self, step: str, detail: str) -> None:
        super().__init__(f"{step}: {detail}")
        self.step = step


def _tool(name: str) -> list[str]:
    return [sys.executable, str(ROOT / "tools" / name)]


def steps(dataset_id: str, *, workers: int, plan: Path) -> list[tuple[str, list[str] | None]]:
    """``(name, argv)`` for each step; argv None for the in-process copy plan."""
    return [
        ("backfill", [*_tool("backfill.py"), "--read-flat", "--workers", str(workers), dataset_id]),
        ("copy plan", None),
        ("copy", [*_tool("bucket_copy.py"), str(plan), "--only", dataset_id, "--confirm"]),
        ("upload data", [*_tool("upload_data.py"), "--only", dataset_id, "--confirm"]),
        ("publish", [*_tool("publish.py"), "--only", dataset_id, "--no-root", "--confirm"]),
        ("verify", [*_tool("verify_move.py"), dataset_id, "--allow-missing-root"]),
    ]


def write_copy_plan(dataset_id: str, plan: Path, *, client=None) -> int:
    """Write ``dataset_id``'s copy pairs from a fresh listing of its old folder; the count."""
    from relayout import bucket_moves
    from verify_move import READ_BUCKET, anonymous_client

    client = client or anonymous_client()
    head = f"{READ_PREFIX}/{dataset_id}/"
    keys = [obj["Key"] for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=READ_BUCKET, Prefix=head) for obj in page.get("Contents", [])]
    group = dataset_relpath(dataset_id).split("/", 1)[0]
    copy, _ = bucket_moves(keys, {dataset_id: group}, READ_PREFIX)
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("".join(f"{old}\t{new}\n" for old, new in copy))
    return len(copy)


def is_verified(dataset_id: str, results: Path = RESULTS) -> bool:
    path = results / f"{dataset_id}.json"
    if not path.exists():
        return False
    record = json.loads(path.read_text())
    return bool(record.get("ok")) and not record.get("under")


def write_patch(
    dataset_id: str, rel: str | None = None, results: Path = RESULTS, root: Path = ROOT
) -> Path:
    """``git diff`` (with new files) of the dataset's catalog folder and recipe, against HEAD."""
    rel = rel or dataset_relpath(dataset_id)
    paths = [f"catalog/{rel}", f"datasets/{dataset_id}.yaml"]
    git = ["git", "-C", str(root)]
    subprocess.run([*git, "add", "--intent-to-add", "--", *paths], check=True)
    diff = subprocess.run([*git, "diff", "--binary", "HEAD", "--", *paths],
                          check=True, capture_output=True, text=True).stdout
    out = results / f"{dataset_id}.patch"
    out.write_text(diff)
    return out


def run_dataset(dataset_id: str, *, workers: int, results: Path = RESULTS, runner=subprocess.run,
                copy_plan=write_copy_plan) -> None:
    """Every step for one dataset, logging to ``<results>/<id>.log``; raises StepFailed."""
    results.mkdir(parents=True, exist_ok=True)
    plan = results / f"{dataset_id}.copy.tsv"
    with (results / f"{dataset_id}.log").open("a") as log:
        for name, argv in steps(dataset_id, workers=workers, plan=plan):
            started = time.monotonic()
            log.write(f"\n=== {name} ({time.strftime('%Y-%m-%dT%H:%M:%S')})\n")
            log.flush()
            if argv is None:
                try:
                    log.write(f"{copy_plan(dataset_id, plan):,} pair(s) to copy -> {plan}\n")
                except Exception as err:  # a listing failure ends this dataset, not the run
                    raise StepFailed(name, repr(err)) from err
                continue
            code = runner(argv, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT).returncode
            log.write(f"=== {name}: exit {code} in {time.monotonic() - started:,.0f} s\n")
            log.flush()
            if code:
                raise StepFailed(name, f"exit {code}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="*", metavar="ID")
    parser.add_argument("--ids-file", type=Path, help="one dataset id per line")
    parser.add_argument("--workers", type=int, default=16, help="backfill embedding threads")
    parser.add_argument("--redo", action="store_true", help="also rerun verified datasets")
    args = parser.parse_args(argv)
    ids = list(args.ids)
    if args.ids_file:
        ids += [s.strip() for s in args.ids_file.read_text().splitlines() if s.strip()]
    if not ids:
        parser.error("name dataset ids or pass --ids-file")

    done, skipped, failed = [], [], []
    for dataset_id in ids:
        if not args.redo and is_verified(dataset_id):
            skipped.append(dataset_id)
            print(f"{dataset_id}: already verified, skipped", flush=True)
            continue
        started = time.monotonic()
        try:
            run_dataset(dataset_id, workers=args.workers)
        except StepFailed as err:
            failed.append((dataset_id, str(err)))
            print(f"{dataset_id}: FAILED at {err} (see {RESULTS / dataset_id}.log)", flush=True)
            continue
        patch = write_patch(dataset_id)
        done.append(dataset_id)
        print(f"{dataset_id}: done in {time.monotonic() - started:,.0f} s; {patch}", flush=True)
    print(f"\n{len(done)} done, {len(skipped)} already verified, {len(failed)} failed")
    for dataset_id, why in failed:
        print(f"  {dataset_id}: {why}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
