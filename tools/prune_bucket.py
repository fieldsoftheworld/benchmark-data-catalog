#!/usr/bin/env python3
"""Delete a dataset's objects that its current build no longer publishes.

A rebuilt dataset can drop chips (a new class filter or chip rule changes the
chip set). ``upload_data.py`` and ``publish.py`` never delete, so the dropped
chips' files would stay in the bucket, unlinked from the catalog. This lists
``<write_prefix>/<id>/`` and deletes every key that neither the staged data
(``upload_data.collect_data_uploads``) nor the published catalog
(``publish.collect_uploads``) would write.

    uv run python tools/prune_bucket.py at_2018 at_2019            # dry run
    uv run python tools/prune_bucket.py at_2018 at_2019 --confirm  # delete

Run it after the dataset's new data is uploaded and its catalog published.
Source Cooperative's proxy has no DeleteObjects, so keys go one at a time.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from publish import (  # noqa: E402
    aws_session,
    collect_uploads,
    load_config,
    remote_index,
    s3_client,
    split_s3_uri,
)
from upload_data import collect_data_uploads, data_root  # noqa: E402


def stale_keys(dataset_id: str, config: dict[str, str], remote: dict) -> list[str]:
    """Keys under the dataset's prefix that the current build does not publish."""
    _, prefix = split_s3_uri(config["write_prefix"])
    under = f"{prefix}/{dataset_id}/" if prefix else f"{dataset_id}/"
    if not (data_root(config) / dataset_id).is_dir():
        sys.exit(f"{dataset_id}: no staging to compare against; refusing to prune")
    wanted = {u.key for u in collect_data_uploads(config, only={dataset_id})}
    wanted |= {u.key for u in collect_uploads(config) if u.key.startswith(under)}
    if not any(k.endswith("/collection.json") for k in wanted):
        sys.exit(
            f"{dataset_id}: the build publishes no collection.json; refusing to prune"
        )
    return sorted(k for k in remote if k.startswith(under) and k not in wanted)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="+")
    parser.add_argument("--confirm", action="store_true", help="actually delete")
    args = parser.parse_args()

    config = load_config()
    bucket, prefix = split_s3_uri(config["write_prefix"])
    client = s3_client(aws_session(config), config.get("endpoint_url"))
    status = 0
    for dataset_id in args.dataset_ids:
        remote = remote_index(bucket, prefix, config, only={dataset_id})
        stale = stale_keys(dataset_id, config, remote)
        print(
            f"{dataset_id}: {len(remote)} object(s) in the bucket, {len(stale)} stale"
        )
        for key in stale[:5]:
            print(f"  {key}")
        if not args.confirm or not stale:
            continue

        def delete(key: str) -> str | None:
            try:
                client.delete_object(Bucket=bucket, Key=key)
            except Exception as err:  # report and carry on
                return f"{key}: {err}"
            return None

        with ThreadPoolExecutor(32) as pool:
            errors = [e for e in pool.map(delete, stale) if e]
        print(f"  deleted {len(stale) - len(errors)}, {len(errors)} error(s)")
        for e in errors[:5]:
            print(f"  {e}")
        status |= bool(errors)
    if not args.confirm:
        print("\ndry run. re-run with --confirm to delete.")
    return status


if __name__ == "__main__":
    sys.exit(main())
