#!/usr/bin/env python3
"""Copy objects server-side from their flat keys to their grouped keys.

Reads a ``<keys>.copy.tsv`` from ``tools/relayout.py --bucket-plan`` (``old
key<TAB>new key`` per line) and runs one CopyObject per pair through the
catalog's write endpoint, so no bytes pass through this machine. The write
endpoint has no server-side multipart copy (UploadPartCopy), so an object over
5 GB is relayed instead: read from the public bucket in the same region, then
uploaded in parts.

Resumable: the destination folders are listed first, and a pair whose new key
already holds an object of the source's size is skipped. The source is never
deleted; ``tools/prune_bucket.py`` and the flat-key prune do that later.

    uv run python tools/bucket_copy.py keys.txt.copy.tsv --only rw_rwanda_ml_2021
    uv run python tools/bucket_copy.py keys.txt.copy.tsv --only rw_rwanda_ml_2021 \\
        --under _trial --confirm      # copy below <prefix>/_trial/ instead
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

#: Largest object a single CopyObject accepts.
SINGLE_COPY_BYTES = 5 * 1024**3
#: Part size for the multipart upload of relayed objects.
MULTIPART_CHUNK_BYTES = 512 * 1024**2
COPY_ATTEMPTS = 5


@dataclass(frozen=True)
class Pair:
    old: str  # key below the write prefix, e.g. at_2018/chips/...
    new: str  # e.g. at/at_2018/chips/...

    @property
    def dataset_id(self) -> str:
        return self.old.split("/", 1)[0]


def _relative(key: str, bucket: str, prefix: str) -> str:
    """``key`` below ``prefix``, accepting the read bucket's ``<bucket>/<prefix>/`` form too."""
    for head in (f"{bucket}/{prefix}/", f"{prefix}/"):
        if key.startswith(head):
            return key[len(head):]
    raise ValueError(f"{key!r} is not below {prefix}/")


def read_pairs(path: Path, bucket: str, prefix: str, only: set[str] | None = None) -> list[Pair]:
    pairs = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        old, new = line.split("\t")
        pair = Pair(_relative(old, bucket, prefix), _relative(new, bucket, prefix))
        if only is None or pair.dataset_id in only:
            pairs.append(pair)
    return pairs


def _list_sizes(client, bucket: str, prefix: str) -> dict[str, int]:
    paginator = client.get_paginator("list_objects_v2")
    return {
        obj["Key"]: obj["Size"]
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
        for obj in page.get("Contents", [])
    }


def _folders(keys, depth: int) -> set[str]:
    """The folder ``depth`` levels down each key sits in: 1 for ``<id>/``, 2 for ``<source>/<id>/``."""
    return {"/".join(key.split("/")[:depth]) + "/" for key in keys}


def sizes_below(client, bucket: str, prefix: str, folders: set[str]) -> dict[str, int]:
    """``{key below prefix: size}`` for every object in ``folders``."""
    sizes: dict[str, int] = {}
    for folder in sorted(folders):
        listed = _list_sizes(client, bucket, f"{prefix}/{folder}")
        sizes.update({k[len(prefix) + 1:]: v for k, v in listed.items()})
    return sizes


def todo(pairs: list[Pair], source: dict[str, int], dest: dict[str, int], under: str):
    """``(pending pairs, missing sources)``: pairs not yet copied, and sources not in the bucket."""
    pending, missing = [], []
    for pair in pairs:
        if pair.old not in source:
            missing.append(pair)
        elif dest.get(_dest(pair, under)) != source[pair.old]:
            pending.append(pair)
    return pending, missing


def _dest(pair: Pair, under: str) -> str:
    return f"{under}/{pair.new}" if under else pair.new


def _transfer_config():
    from boto3.s3.transfer import TransferConfig

    return TransferConfig(multipart_threshold=MULTIPART_CHUNK_BYTES,
                          multipart_chunksize=MULTIPART_CHUNK_BYTES)


def relay_one(client, reader, bucket: str, prefix: str, pair: Pair, under: str) -> None:
    """Copy one large object by reading it from the public bucket and uploading it in parts."""
    from verify_move import READ_BUCKET

    public_key = f"{bucket}/{prefix}/{pair.old}"
    content_type = reader.head_object(Bucket=READ_BUCKET, Key=public_key).get("ContentType")
    extra = {"ContentType": content_type} if content_type else {}
    config = _transfer_config()
    with tempfile.TemporaryFile() as buffer:
        reader.download_fileobj(READ_BUCKET, public_key, buffer, Config=config)
        buffer.seek(0)
        client.upload_fileobj(buffer, bucket, f"{prefix}/{_dest(pair, under)}",
                              ExtraArgs=extra, Config=config)


def copy_one(client, bucket: str, prefix: str, pair: Pair, size: int, under: str,
             reader=None) -> None:
    src = {"Bucket": bucket, "Key": f"{prefix}/{pair.old}"}
    dst = f"{prefix}/{_dest(pair, under)}"
    for attempt in range(COPY_ATTEMPTS):
        try:
            if size > SINGLE_COPY_BYTES:
                relay_one(client, reader, bucket, prefix, pair, under)
            else:
                client.copy_object(CopySource=src, Bucket=bucket, Key=dst, MetadataDirective="COPY")
            return
        except Exception:
            if attempt == COPY_ATTEMPTS - 1:
                raise
            time.sleep(2**attempt)


def run_copies(client, bucket, prefix, pending, source, under, workers, reader=None) -> int:
    if reader is None and any(source[p.old] > SINGLE_COPY_BYTES for p in pending):
        from verify_move import anonymous_client

        reader = anonymous_client()
    done = 0
    with ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(copy_one, client, bucket, prefix, p, source[p.old], under, reader)
                   for p in pending]
        for future in futures:
            future.result()
            done += 1
            if done % 10000 == 0:
                print(f"  {done:,}/{len(pending):,} copied", flush=True)
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pairs", type=Path, help="a .copy.tsv from relayout.py --bucket-plan")
    parser.add_argument("--only", action="append", metavar="DATASET",
                        help="copy only this dataset's pairs (repeatable)")
    parser.add_argument("--under", default="", metavar="NAME",
                        help="write below <prefix>/NAME/ instead of <prefix>/ (for a trial)")
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--confirm", action="store_true", help="actually copy (default: dry run)")
    args = parser.parse_args(argv)

    from publish import aws_session, load_config, s3_client, split_s3_uri

    config = load_config()
    bucket, prefix = split_s3_uri(config["write_prefix"])
    prefix = prefix.rstrip("/")
    pairs = read_pairs(args.pairs, bucket, prefix, set(args.only) if args.only else None)
    client = s3_client(aws_session(config), config.get("endpoint_url"), pool_size=args.workers)
    source = sizes_below(client, bucket, prefix, _folders((p.old for p in pairs), 1))
    dest_folders = _folders((p.new for p in pairs), 2)
    if args.under:
        dest_folders = {f"{args.under}/{f}" for f in dest_folders}
    dest = sizes_below(client, bucket, prefix, dest_folders)
    pending, missing = todo(pairs, source, dest, args.under)
    total = sum(source[p.old] for p in pending)
    print(f"{len(pairs):,} pair(s): {len(pending):,} to copy ({total / 1e9:,.1f} GB), "
          f"{len(pairs) - len(pending) - len(missing):,} already there, "
          f"{len(missing):,} missing at the source")
    for pair in missing[:10]:
        print(f"  missing: {pair.old}")
    if missing:
        print("refusing: the plan names objects the bucket no longer has; list again")
        return 1
    if not args.confirm:
        print("\ndry run. re-run with --confirm to copy.")
        return 0
    started = time.monotonic()
    done = run_copies(client, bucket, prefix, pending, source, args.under, args.workers)
    print(f"copied {done:,} object(s) in {time.monotonic() - started:,.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
