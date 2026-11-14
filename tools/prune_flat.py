#!/usr/bin/env python3
"""Delete a dataset's old flat ``<id>/`` keys once its move is verified.

For each dataset this refuses unless ``work/migration/<id>.json`` (from
``tools/verify_move.py``) says ``ok`` for the real prefix, then lists the old
and the new folder again and refuses if any old key has no new key. Only keys
starting with ``<prefix>/<id>/`` are deleted, so a sibling id (``lv_2020x``),
the source groups and the root files are never touched; an id that is also a
source group's name is refused.

The proxy has no DeleteObjects, so this sends one DeleteObject per key from a
thread pool. A rerun deletes whatever is left. Dry run by default.

    uv run python tools/prune_flat.py rw_rwanda_ml_2021            # dry run
    uv run python tools/prune_flat.py --all-verified --confirm
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CATALOG, dataset_relpath  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "work" / "migration"
DELETE_ATTEMPTS = 5


class PruneRefused(Exception):
    """A dataset's flat keys may not be deleted (yet)."""


def verified_ids(results: Path = RESULTS) -> list[str]:
    """Datasets whose verification record says ok for the real prefix."""
    out = []
    for path in sorted(results.glob("*.json")):
        record = json.loads(path.read_text())
        if record.get("ok") and not record.get("under"):
            out.append(record["id"])
    return out


def check_record(dataset_id: str, results: Path = RESULTS) -> None:
    path = results / f"{dataset_id}.json"
    if not path.exists():
        raise PruneRefused(f"{dataset_id}: not verified (no {path}); run tools/verify_move.py")
    record = json.loads(path.read_text())
    if not record.get("ok") or record.get("under"):
        raise PruneRefused(f"{dataset_id}: its verification did not pass for the real prefix")


def keys_below(client, bucket: str, prefix: str) -> list[str]:
    return [obj["Key"] for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix) for obj in page.get("Contents", [])]


def flat_keys_to_delete(
    client, bucket: str, prefix: str, dataset_id: str, rel: str, groups: set[str]
) -> list[str]:
    """The old keys of ``dataset_id``, after checking each has its new key."""
    if dataset_id in groups or "/" in dataset_id or not dataset_id:
        raise PruneRefused(f"{dataset_id!r} is not a dataset id that can be pruned")
    old_head, new_head = f"{prefix}/{dataset_id}/", f"{prefix}/{rel}/"
    old = keys_below(client, bucket, old_head)
    new = {k[len(new_head):] for k in keys_below(client, bucket, new_head)}
    missing = [k for k in old if k[len(old_head):] not in new]
    if missing:
        raise PruneRefused(f"{dataset_id}: {len(missing):,} old key(s) have no new key, "
                           f"e.g. {missing[0]}")
    stray = [k for k in old if not k.startswith(old_head)]
    if stray:  # cannot happen with a correct listing; refuse rather than trust it
        raise PruneRefused(f"{dataset_id}: listing returned keys outside {old_head}")
    return old


def delete_keys(client, bucket: str, keys: list[str], workers: int) -> int:
    def delete(key: str) -> None:
        for attempt in range(DELETE_ATTEMPTS):
            try:
                client.delete_object(Bucket=bucket, Key=key)
                return
            except Exception:
                if attempt == DELETE_ATTEMPTS - 1:
                    raise
                time.sleep(2**attempt)

    with ThreadPoolExecutor(workers) as pool:
        for _ in pool.map(delete, keys):
            pass
    return len(keys)


def prune(dataset_ids, client, bucket, prefix, *, groups, relpath, results=RESULTS,
          workers=64, confirm=False) -> tuple[int, list[str]]:
    """``(keys deleted or that would be, refusals)`` over ``dataset_ids``."""
    total, refused = 0, []
    for dataset_id in dataset_ids:
        try:
            check_record(dataset_id, results)
            keys = flat_keys_to_delete(client, bucket, prefix, dataset_id, relpath(dataset_id),
                                       groups)
        except PruneRefused as err:
            refused.append(str(err))
            print(f"refused  {err}")
            continue
        if confirm and keys:
            delete_keys(client, bucket, keys, workers)
        verb = "deleted" if confirm else "would delete"
        print(f"{dataset_id}: {verb} {len(keys):,} flat key(s)", flush=True)
        total += len(keys)
    return total, refused


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="*", metavar="ID")
    parser.add_argument("--all-verified", action="store_true",
                        help="every dataset with a passing work/migration/<id>.json")
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--confirm", action="store_true", help="actually delete (default: dry run)")
    args = parser.parse_args(argv)
    ids = list(args.ids) + (verified_ids() if args.all_verified else [])
    if not ids:
        parser.error("name dataset ids or pass --all-verified")

    from publish import aws_session, load_config, s3_client, split_s3_uri

    config = load_config()
    bucket, prefix = split_s3_uri(config["write_prefix"])
    client = s3_client(aws_session(config), config.get("endpoint_url"), pool_size=args.workers)
    groups = {p.name for p in CATALOG.iterdir() if p.is_dir() and (p / "catalog.json").exists()}
    total, refused = prune(sorted(set(ids)), client, bucket, prefix.rstrip("/"), groups=groups,
                           relpath=dataset_relpath, workers=args.workers, confirm=args.confirm)
    print(f"{total:,} flat key(s) {'deleted' if args.confirm else 'to delete'}; "
          f"{len(refused)} dataset(s) refused")
    if not args.confirm:
        print("\ndry run. re-run with --confirm to delete.")
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
