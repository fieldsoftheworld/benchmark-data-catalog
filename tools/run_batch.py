#!/usr/bin/env python3
"""Build a batch of region-year datasets from ``tracking.csv``, up to upload.

    uv run python tools/run_batch.py be_wal_2022 de_sl_2026 --jobs 2
    uv run python tools/run_batch.py --next 10 --jobs 4        # next 10 unbuilt 'include' rows
    uv run python tools/run_batch.py be_wal_2022 --imagery     # second pass: imagery
    uv run python tools/run_batch.py be_wal_2022 --mark-published

The metadata pass runs, per dataset, the steps in README's "Adding a
dataset": scaffold the recipe when missing (``tools/new_dataset.py``), build
``--through stac``, build ``--only docs``, ``catalogize.py <id>``. Datasets run
concurrently (``--jobs``), each logging to ``logs/<id>.log``. Then, once for
the whole batch: ``catalogize.py --root``, thumbnails one at a time through a
single chiitiler (started here if none is running), and the gates.

The imagery pass runs ``--from select_images``, ``--only docs`` and
``catalogize.py <id>`` per dataset.

Never uploads. It prints the upload commands for the datasets that built;
run them yourself, then ``--mark-published``.

``tracking.csv`` records the outcome per row: ``built`` / ``imagery_done``
get the date and ``ftwd_commit`` the installed ftwd on success; ``issues``
names the failed step and its log otherwise.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tracking  # noqa: E402
from build import subprocess_env  # noqa: E402
from common import ROOT, installed_ftwd  # noqa: E402

LOGS = ROOT / "logs"
CHIITILER_HEALTH = "http://localhost:13579/health"

METADATA_STEPS = (
    ("build --through stac", ["build.py", "{id}", "--through", "stac"]),
    ("build --only docs", ["build.py", "{id}", "--only", "docs"]),
    ("catalogize", ["catalogize.py", "{id}"]),
)
IMAGERY_STEPS = (
    ("build --from select_images", ["build.py", "{id}", "--from", "select_images"]),
    ("build --only docs", ["build.py", "{id}", "--only", "docs"]),
    ("catalogize", ["catalogize.py", "{id}"]),
)


def tool_argv(template: list[str], dataset_id: str) -> list[str]:
    """``python tools/<script> ...`` with ``{id}`` filled in."""
    script, *args = template
    return [sys.executable, str(ROOT / "tools" / script)] + [
        a.replace("{id}", dataset_id) for a in args
    ]


def next_ids(rows: list[dict[str, str]], n: int, *, imagery: bool) -> list[str]:
    """The first ``n`` 'include' rows still waiting for this pass."""
    if imagery:
        waiting = [r for r in rows if r["built"] and not r["imagery_done"]]
    else:
        waiting = [r for r in rows if not r["built"]]
    return [r["dataset_id"] for r in waiting if r["status"] == "include"][:n]


def _run(argv: list[str], log) -> int:
    log.write(f"\n$ {' '.join(argv)}\n")
    log.flush()
    return subprocess.run(
        argv, cwd=ROOT, env=subprocess_env(), stdout=log, stderr=subprocess.STDOUT, check=False
    ).returncode


def run_dataset(dataset_id: str, steps, *, scaffold: bool) -> str | None:
    """Run ``steps`` for one dataset; the failed step's name, or None."""
    LOGS.mkdir(exist_ok=True)
    with (LOGS / f"{dataset_id}.log").open("a") as log:
        log.write(f"\n=== {date.today().isoformat()} {dataset_id}\n")
        if scaffold and not (ROOT / "datasets" / f"{dataset_id}.yaml").exists():
            if _run(tool_argv(["new_dataset.py", "{id}"], dataset_id), log) != 0:
                return "new_dataset"
        for name, template in steps:
            started = time.monotonic()
            code = _run(tool_argv(template, dataset_id), log)
            log.write(f"--- {name}: exit {code} after {time.monotonic() - started:.0f}s\n")
            if code != 0:
                return name
    return None


def _chiitiler_up() -> bool:
    try:
        with urllib.request.urlopen(CHIITILER_HEALTH, timeout=2) as resp:
            return resp.status == 200
    except OSError:
        return False


def start_chiitiler() -> subprocess.Popen | None:
    """Start chiitiler unless one is already up; the process we started, if any."""
    if _chiitiler_up():
        return None
    LOGS.mkdir(exist_ok=True)
    proc = subprocess.Popen(
        [str(ROOT / "tools" / "chiitiler.sh")],
        cwd=ROOT,
        stdout=(LOGS / "chiitiler.log").open("a"),
        stderr=subprocess.STDOUT,
    )
    for _ in range(300):  # first run clones and npm-installs
        if _chiitiler_up():
            return proc
        time.sleep(1)
    proc.terminate()
    sys.exit("chiitiler did not come up in 5 minutes; see logs/chiitiler.log")


def thumbnails(dataset_ids: list[str]) -> dict[str, str]:
    """Render each thumbnail; failures as {id: message}."""
    failed = {}
    proc = start_chiitiler()
    try:
        for dataset_id in dataset_ids:
            with (LOGS / f"{dataset_id}.log").open("a") as log:
                if _run(tool_argv(["thumbnail.py", "{id}"], dataset_id), log) != 0:
                    failed[dataset_id] = f"thumbnail failed, see logs/{dataset_id}.log"
    finally:
        if proc is not None:
            subprocess.run(["pkill", "-f", "tile-server --port 13579"], check=False)
    return failed


def _ftwd_commit() -> str:
    pin = installed_ftwd()
    return pin.value[:8] if pin is not None else ""


def run_pass(dataset_ids: list[str], *, imagery: bool, jobs: int) -> list[str]:
    """Run one pass over ``dataset_ids``; the ids that succeeded."""
    steps = IMAGERY_STEPS if imagery else METADATA_STEPS
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = dict(
            zip(
                dataset_ids,
                pool.map(lambda d: run_dataset(d, steps, scaffold=not imagery), dataset_ids),
                strict=True,
            )
        )
    failures = {d: f"{step} failed, see logs/{d}.log" for d, step in results.items() if step}
    ok = [d for d in dataset_ids if d not in failures]

    if ok and not imagery:
        subprocess.run(tool_argv(["catalogize.py", "--root"], ""), cwd=ROOT, check=False)
        failures |= thumbnails(ok)
        ok = [d for d in ok if d not in failures]

    today, commit = date.today().isoformat(), _ftwd_commit()
    done_column = "imagery_done" if imagery else "built"
    for d in dataset_ids:
        if d in failures:
            tracking.update(d, issues=failures[d])
        else:
            tracking.update(d, **{done_column: today, "ftwd_commit": commit, "issues": ""})
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="*", help="region-year ids from tracking.csv")
    parser.add_argument("--next", type=int, default=0, help="take the next N waiting rows")
    parser.add_argument("--jobs", type=int, default=2, help="datasets built concurrently")
    parser.add_argument("--imagery", action="store_true", help="run the imagery pass")
    parser.add_argument(
        "--mark-published", action="store_true", help="record the ids as uploaded; build nothing"
    )
    args = parser.parse_args(argv)

    rows = tracking.load()
    ids = args.dataset_ids or next_ids(rows, args.next, imagery=args.imagery)
    if not ids:
        sys.exit("nothing to do: name dataset ids or pass --next N")
    for d in ids:
        tracking.row(d, rows)

    if args.mark_published:
        for d in ids:
            tracking.update(d, published=date.today().isoformat())
        return 0

    print(f"{'imagery' if args.imagery else 'metadata'} pass: {', '.join(ids)}")
    ok = run_pass(ids, imagery=args.imagery, jobs=args.jobs)
    failed = [d for d in ids if d not in ok]

    gates = subprocess.run([sys.executable, str(ROOT / "tests" / "run_all.py")], cwd=ROOT)
    print(f"\nbuilt: {', '.join(ok) or 'none'}")
    if failed:
        print(f"failed: {', '.join(failed)} (see tracking.csv issues and logs/)")
    if gates.returncode != 0:
        print("gates FAILED; fix before uploading")
        return 1
    if ok:
        only = " ".join(f"--only {d}" for d in ok)
        print("\nreview, commit, then upload with the maintainer's say-so:")
        print(f"  uv run python tools/upload_data.py {only} --confirm")
        print("  uv run python tools/publish.py --confirm")
        print(f"  uv run python tools/run_batch.py {' '.join(ok)} --mark-published")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
