#!/usr/bin/env python3
"""Upload staged data files to the same bucket prefix the catalog publishes to.

``tools/publish.py`` walks ``publish_dir`` and nothing else. That boundary is
the publish contract and this script does not widen it. GeoParquet partitions
and PMTiles archives are too large for git, so they live outside ``catalog/``
and never reach the bucket. This script carries them there.

Every rule the two scripts share comes from ``publish.py``. This file imports
the sentinel guard, the content types, the change detection, the AWS session,
and the upload pool. It adds one thing, a second walk root.

    python3 tools/upload_data.py            # dry run: what would change
    python3 tools/upload_data.py --confirm  # upload; needs AWS credentials
    python3 tools/upload_data.py --confirm --force   # re-upload everything

Set ``data_dir`` in ``catalog.publish.yaml`` to the staging directory that
holds the data. The template ships no staging tree, so this script exits with
a message until you set that key.

Two gates decide what uploads. The path gate admits only files under
``data_dir``. The extension gate admits only the suffixes in
PUBLISHABLE_SUFFIXES. Both apply. A third rule then removes anything git
already owns: when the same relative path exists under ``publish_dir``, the
git-tracked copy always wins and the staged one is skipped rather than
uploaded over it (``git_owned``). It never deletes, exactly as ``publish.py``
never deletes.

**Change detection is weaker here than it is for the catalog.**
``is_unchanged`` compares a compound ETag on size alone, because a multipart
ETag is not an MD5. A catalog file is small and uploads in one part, so it
compares by hash. A multi-gigabyte partition uploads in many parts, so it
compares by size. A truncated object of the correct size stays accepted on
every later run. Use ``--force`` to re-upload the data and clear that state.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from publish import (  # noqa: E402
    ROOT,
    Upload,
    aws_session,
    content_type_for,
    is_publishable,
    is_unchanged,
    load_config,
    remote_index,
    split_s3_uri,
    unedited_sentinels,
    upload_all,
)

# The suffixes that may reach the bucket. This is an allow-list, and it names
# what may pass rather than what may not. A staging tree grows new scratch
# files over time. An allow-list stays correct when it does, and a deny-list
# does not. One catalog staged 45 GB of GeoJSON that tippecanoe reads and
# nobody should download. An allow-list keeps that 45 GB out with no edit.
#
# .json is here because ftwd stages STAC item trees and sub-catalogs
# (chips/<square>/<item>/<item>.json, chips/<square>/catalog.json) as data,
# not as git-owned catalog metadata. .yaml, .md, .geojsonseq and .txt stay
# barred: resolved configs, run summaries, tippecanoe scratch and notes are
# not publishable data.
PUBLISHABLE_SUFFIXES = {
    ".parquet",
    ".pmtiles",
    ".tif",
    ".tiff",
    ".laz",
    ".json",
    # Chip previews. Without these the item JSON advertises a thumbnail the
    # browser then 404s on, which is what every chip card showed until now.
    # .webp is admitted ahead of ftwd emitting it, so the switch needs no edit here.
    ".jpg",
    ".jpeg",
    ".webp",
}


def data_root(config: dict[str, str], root: Path = ROOT) -> Path:
    """The staging directory this script walks.

    Reads the optional ``data_dir`` key. A relative value resolves against the
    repository root. Exits with a message when the key is absent or when the
    directory does not exist.
    """
    configured = config.get("data_dir", "")
    if not configured:
        sys.exit(
            "catalog.publish.yaml sets no data_dir, so there is nothing to "
            "upload.\nSet data_dir to the directory that holds your data "
            "files.\nSee the commented example in catalog.publish.yaml."
        )
    base = Path(configured)
    if not base.is_absolute():
        base = root / base
    base = base.resolve()
    if not base.is_dir():
        sys.exit(f"data_dir does not exist: {base}")
    return base


def is_data_publishable(rel: Path) -> bool:
    """True for a staged file that both gates admit.

    The path gate runs in ``collect_data_uploads``. This is the second gate.
    It applies the dotfile rule of ``publish.py`` and then the suffix
    allow-list.
    """
    return is_publishable(rel) and rel.suffix.lower() in PUBLISHABLE_SUFFIXES


def git_owned(rel: Path, root: Path, config: dict[str, str]) -> bool:
    """True when the git-owned catalog already has this relative path.

    ``catalog/`` always wins: a STAC item tree or sub-catalog that ftwd
    regenerated in staging is skipped here, not uploaded over the tracked
    file at the same path under ``publish_dir``.
    """
    return (root / config["publish_dir"] / rel).exists()


def collect_data_uploads(
    config: dict[str, str],
    root: Path = ROOT,
    *,
    skipped: list[Path] | None = None,
    only: set[str] | None = None,
) -> list[Upload]:
    """Every staged data file that would be uploaded, in sorted order.

    ``only`` restricts the walk to the named dataset directories directly
    under ``data_dir`` (``{"lu"}`` uploads ``staging/lu/**`` alone), so one
    dataset can be published while another is still being built.

    The walk is rooted at ``data_dir`` and nothing else. Keys go under the
    same ``write_prefix`` the catalog publishes to, so the data sits beside
    the metadata that describes it. A staged file whose relative path is
    already git-owned (see ``git_owned``) is skipped rather than uploaded;
    pass ``skipped`` to collect the relative paths that were.
    """
    _, prefix = split_s3_uri(config["write_prefix"])
    base = data_root(config, root)
    uploads = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if only is not None and (not rel.parts or rel.parts[0] not in only):
            continue
        if not is_data_publishable(rel):
            continue
        if git_owned(rel, root, config):
            if skipped is not None:
                skipped.append(rel)
            continue
        key = f"{prefix}/{rel.as_posix()}" if prefix else rel.as_posix()
        uploads.append(Upload(path, key, content_type_for(path, rel=rel)))
    return uploads


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload staged data files to the catalog's bucket prefix.",
        epilog="Dry run by default. Never deletes.",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="actually upload"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-upload everything; skip the remote listing",
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="DATASET",
        help="upload only this dataset directory under data_dir (repeatable)",
    )
    args = parser.parse_args()

    config = load_config()
    base = data_root(config)

    stale = unedited_sentinels(config)
    if stale:
        print("catalog.publish.yaml still carries template values:")
        for value in stale:
            print(f"  {value}")
        print("\nEdit write_prefix and public_base, then see README.md.")
        return 1

    bucket, prefix = split_s3_uri(config["write_prefix"])
    skipped: list[Path] = []
    only = set(args.only) if args.only else None
    uploads = collect_data_uploads(config, skipped=skipped, only=only)
    if skipped:
        print(f"{len(skipped)} staged file(s) skipped because catalog/ owns them")
    if not uploads:
        print(f"nothing under {base}/ to upload", file=sys.stderr)
        return 1

    index = {} if args.force else remote_index(bucket, prefix, config)
    changed = [u for u in uploads if args.force or not is_unchanged(u, index)]

    print(f"data_dir:    {base}/")
    print(f"target:      s3://{bucket}/{prefix}")
    print(f"aws profile: {config.get('profile') or '(default session)'}")
    print(f"suffixes:    {', '.join(sorted(PUBLISHABLE_SUFFIXES))}")
    print(f"{len(uploads)} file(s) staged, {len(changed)} to upload")
    print("this never deletes; removing a file here does not unpublish it")

    if not args.confirm:
        for upload in changed[:20]:
            print(f"  would upload  {upload.key}")
        if len(changed) > 20:
            print(f"  ... and {len(changed) - 20} more")
        print("\ndry run. re-run with --confirm to upload.")
        return 0

    if not changed:
        print("nothing to upload")
        return 0

    # A dry run tolerates a broken session, but an upload cannot. Report the
    # reason here instead of raising a traceback out of the pool.
    try:
        session = aws_session(config)
    except ImportError:
        sys.exit("boto3 is required to upload. Run: pip install boto3")
    except Exception as exc:  # noqa: BLE001 - stop before any upload
        sys.exit(f"cannot build an AWS session: {exc}")

    failed = upload_all(session, bucket, changed, config.get("endpoint_url"))
    if failed:
        print(f"\n{len(failed)} of {len(changed)} file(s) failed:",
              file=sys.stderr)
        for key in sorted(failed):
            print(f"  {key}", file=sys.stderr)
        return 1
    print(f"\nuploaded {len(changed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
