#!/usr/bin/env python3
"""Check one dataset's move from ``<id>/`` to ``<source>/<id>/`` in the bucket.

Reads the public bucket anonymously, lists the old and the new folder once,
and checks:

1. every old key exists at its new key;
2. files the move copies as they are (rasters, previews, PMTiles, GeoParquet,
   by ``relayout``'s rule) have the same size and ETag, except the chips
   GeoParquet, which the backfill rewrites with admin names (an object
   uploaded or copied in parts has a compound ETag, so those compare on size);
3. the new folder holds nothing new beyond the field embeddings GeoParquet;
4. every relative href in every JSON under the new folder resolves to an
   object in the bucket. The root ``catalog.json`` and the group's
   ``catalog.json`` must be there too, unless ``--allow-missing-root``
   (the move publishes the root once, at the end).

Writes ``work/migration/<id>.json`` (``ok``, counts, the first problems) and
exits 1 when anything is wrong. Never writes to the bucket.

    uv run python tools/verify_move.py rw_rwanda_ml_2021 --allow-missing-root
    uv run python tools/verify_move.py rw_rwanda_ml_2021 --under _trial
"""
from __future__ import annotations

import argparse
import json
import posixpath
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, dataset_relpath  # noqa: E402

READ_BUCKET = "us-west-2.opendata.source.coop"
READ_PREFIX = "ftw/benchmark-data"
RESULTS = ROOT / "work" / "migration"
FETCH_WORKERS = 64
MAX_PROBLEMS = 50
#: Copy-class files the backfill rewrites, so they may differ from the old ones.
_CHANGED_BY_BACKFILL = ("{id}_chips.parquet",)
#: Files only the new folder has.
_NEW_ALLOWED = ("{id}_field_embeddings.parquet",)


def anonymous_client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client("s3", region_name="us-west-2", config=Config(
        signature_version=UNSIGNED, s3={"addressing_style": "path"},
        max_pool_connections=FETCH_WORKERS, retries={"max_attempts": 10, "mode": "adaptive"}))


def listing(client, prefix: str, *, recursive: bool = True) -> dict[str, tuple[int, str]]:
    """``{key below prefix: (size, etag)}``; only the top level when not ``recursive``."""
    extra = {} if recursive else {"Delimiter": "/"}
    out = {}
    for page in client.get_paginator("list_objects_v2").paginate(
            Bucket=READ_BUCKET, Prefix=prefix, **extra):
        for obj in page.get("Contents", []):
            out[obj["Key"][len(prefix):]] = (obj["Size"], obj["ETag"].strip('"'))
    return out


def _copied_as_is(name: str, dataset_id: str) -> bool:
    from relayout import _COPY_SUFFIXES, _REWRITTEN_NAMES

    if name in _REWRITTEN_NAMES or name in {p.format(id=dataset_id) for p in _CHANGED_BY_BACKFILL}:
        return False
    return name.lower().endswith(_COPY_SUFFIXES)


def same_object(a: tuple[int, str], b: tuple[int, str]) -> bool:
    """Same size and ETag; a compound (multipart) ETag is not an MD5, so those compare on size."""
    if a[0] != b[0]:
        return False
    return a[1] == b[1] or "-" in a[1] or "-" in b[1]


def compare(old: dict, new: dict, dataset_id: str) -> tuple[dict, list[str]]:
    """Counts and problems from the old and new folder listings (keys relative to each)."""
    problems = [f"missing at the new key: {rel}" for rel in sorted(set(old) - set(new))]
    allowed = {p.format(id=dataset_id) for p in _NEW_ALLOWED}
    problems += [f"unexpected new file: {rel}" for rel in sorted(set(new) - set(old) - allowed)]
    identical = changed = 0
    for rel in sorted(set(old) & set(new)):
        if same_object(old[rel], new[rel]):
            identical += 1
            continue
        changed += 1
        if _copied_as_is(rel.rsplit("/", 1)[-1], dataset_id):
            problems.append(f"copied file differs: {rel} {old[rel]} -> {new[rel]}")
    counts = {"old": len(old), "new": len(new), "identical": identical, "changed": changed,
              "new_only": len(set(new) - set(old))}
    return counts, problems


def resolve(doc_rel: str, href: str) -> str | None:
    """``href`` in the JSON at ``doc_rel`` as a path from the catalog root; None if absolute."""
    if "://" in href or href.startswith("/"):
        return None
    href = href.split("#", 1)[0].split("?", 1)[0]
    return posixpath.normpath(posixpath.join(posixpath.dirname(doc_rel), href))


def _hrefs(doc: dict) -> list[str]:
    out = [link.get("href", "") for link in doc.get("links", [])]
    out += [asset.get("href", "") for asset in (doc.get("assets") or {}).values()]
    return [h for h in out if h]


def broken_hrefs(
    docs: dict[str, dict], present: set[str], *, root_targets: set[str], allow_missing_root: bool
) -> tuple[int, list[str]]:
    """``(hrefs checked, problems)``. ``docs`` and ``present`` use paths from the catalog root."""
    checked, problems = 0, []
    for doc_rel, doc in sorted(docs.items()):
        for href in _hrefs(doc):
            target = resolve(doc_rel, href)
            if target is None:
                continue
            checked += 1
            if target in present:
                continue
            if allow_missing_root and target in root_targets:
                continue
            problems.append(f"broken href in {doc_rel}: {href}")
    return checked, problems


def fetch_docs(client, prefix: str, rels: list[str]) -> dict[str, dict]:
    def get(rel: str) -> dict:
        return json.loads(client.get_object(Bucket=READ_BUCKET, Key=prefix + rel)["Body"].read())

    with ThreadPoolExecutor(FETCH_WORKERS) as pool:
        return dict(zip(rels, pool.map(get, rels), strict=True))


def verify(dataset_id: str, *, client=None, under: str = "", allow_missing_root: bool = False,
           group: str | None = None) -> dict:
    """The verification record for ``dataset_id`` (see the module docstring)."""
    client = client or anonymous_client()
    rel = dataset_relpath(dataset_id) if group is None else f"{group}/{dataset_id}"
    group = rel.split("/", 1)[0]
    base = f"{READ_PREFIX}/{under}/" if under else f"{READ_PREFIX}/"
    old = listing(client, f"{READ_PREFIX}/{dataset_id}/")
    new = listing(client, f"{base}{rel}/")
    counts, problems = compare(old, new, dataset_id)
    present = {f"{rel}/{k}" for k in new}
    present |= set(listing(client, base, recursive=False))
    present |= {f"{group}/{k}" for k in listing(client, f"{base}{group}/", recursive=False)}
    docs = fetch_docs(client, f"{base}{rel}/", [k for k in new if k.endswith(".json")])
    checked, href_problems = broken_hrefs(
        {f"{rel}/{k}": d for k, d in docs.items()}, present,
        root_targets={"catalog.json", f"{group}/catalog.json"},
        allow_missing_root=allow_missing_root)
    problems += href_problems
    counts.update(json=len(docs), hrefs=checked)
    return {"id": dataset_id, "group": group, "ok": not problems, "counts": counts,
            "problems": problems[:MAX_PROBLEMS], "problem_count": len(problems),
            "under": under or None, "verified_at": datetime.now(UTC).isoformat()}


def write_record(record: dict, results: Path = RESULTS) -> Path:
    results.mkdir(parents=True, exist_ok=True)
    path = results / f"{record['id']}.json"
    path.write_text(json.dumps(record, indent=2) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="+", metavar="ID")
    parser.add_argument("--under", default="", metavar="NAME", help="the new folder sits below NAME/")
    parser.add_argument("--allow-missing-root", action="store_true",
                        help="accept links to a root or group catalog.json not published yet")
    args = parser.parse_args(argv)
    client = anonymous_client()
    failed = 0
    for dataset_id in args.ids:
        record = verify(dataset_id, client=client, under=args.under,
                        allow_missing_root=args.allow_missing_root)
        path = write_record(record)
        c = record["counts"]
        status = "OK" if record["ok"] else f"FAILED ({record['problem_count']} problem(s))"
        print(f"{dataset_id}: {status}: {c['old']:,} old, {c['new']:,} new, {c['identical']:,} "
              f"identical, {c['changed']:,} changed, {c['json']:,} JSON, {c['hrefs']:,} hrefs; {path}")
        for problem in record["problems"][:10]:
            print(f"  {problem}")
        failed += not record["ok"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
