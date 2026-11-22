#!/usr/bin/env python3
"""Sync the published directory to object storage, 1:1.

``catalog/`` *is* the published catalog: everything under it is published, and
nothing outside it ever is. That boundary is the whole publish contract, and it
is enforced structurally — this script walks ``publish_dir`` and has no flag,
argument, or config key that widens the walk. Config lives in
``catalog.publish.yaml``.

    python3 tools/publish.py            # dry run: what would change
    python3 tools/publish.py --confirm  # upload; needs AWS credentials
    python3 tools/publish.py --confirm --force   # re-upload everything

Change detection compares local size and MD5 against the object's size and
ETag, so a normal publish uploads only what changed. Three caveats, all
inherited from what a bucket listing can tell you:

- A listing carries no Content-Type, so a file whose bytes are unchanged but
  whose content-type mapping changed is skipped. Run ``--force`` after editing
  CONTENT_TYPES.
- Multipart-uploaded objects have a compound ETag that is not an MD5. Those are
  compared on size alone.
- ``--force`` skips the listing entirely.

**It never deletes.** Removing a file from the published directory does not
unpublish it. Delete the object yourself if that is what you meant.

If boto3 is missing or the listing fails, every file is treated as changed and
a dry run still works offline. It never silently skips.

Both AWS calls go through one session, built by ``aws_session`` from the
optional ``profile`` and ``region`` keys. Source Cooperative wants a named
profile, and the default session can select the wrong account without one.
Clients built from that session honour the optional ``endpoint_url`` key too
(see ``s3_client``), which addresses Source Cooperative through its data
proxy instead of AWS's own S3 endpoints.

Uploads run on a bounded thread pool of MAX_UPLOAD_WORKERS threads. A failed
object is named on stderr and the run exits non-zero. One failure does not
stop the other uploads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import queue
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "catalog.publish.yaml"

# Values the template ships with. Publishing while any of these survives would
# upload to a bucket that is not yours, so it is refused before any AWS call.
SENTINELS = ("EXAMPLE-BUCKET", "EXAMPLE-PREFIX", "example.invalid")

CONTENT_TYPES = {
    ".json": "application/json",
    ".geojson": "application/geo+json",
    ".parquet": "application/vnd.apache.parquet",
    ".pmtiles": "application/vnd.pmtiles",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".tif": "image/tiff; application=geotiff; profile=cloud-optimized",
    ".tiff": "image/tiff; application=geotiff; profile=cloud-optimized",
    ".laz": "application/vnd.laszip",
    ".xml": "application/xml",
    ".yaml": "application/yaml",
}
DEFAULT_TYPE = "application/octet-stream"

# MapLibre style documents are .json but carry a more specific type, which is
# what lets a browser dispatch on them.
STYLE_TYPE = "application/vnd.mapbox.style+json"

# A STAC Item is .json but is itself GeoJSON, which is what lets a browser or
# a STAC client dispatch on it instead of treating it as opaque JSON.
ITEM_TYPE = "application/geo+json"

# A catalog is thousands of small JSON objects, and one round trip to
# us-west-2 costs about 238 ms. A serial loop leaves the link idle for that
# whole time. Measured on a real catalog: 4,035 objects took 23 minutes in
# serial, and 16 workers moved the remaining 1,786 objects in 46 seconds.
MAX_UPLOAD_WORKERS = 16

# Progress is printed every this many objects, not once per object, so a
# publish of thousands of files stays readable.
PROGRESS_EVERY = 100


@dataclass(frozen=True)
class Upload:
    """One local file and the object key it publishes to."""

    local: Path
    key: str
    content_type: str


def load_config(path: Path = CONFIG) -> dict[str, str]:
    """Read the flat scalar map in catalog.publish.yaml.

    Deliberately not a YAML parser. The file is a flat map of strings by
    design, so the template publishes with no dependencies at all. Do not add
    nesting to it.

    ``write_prefix``, ``public_base`` and ``publish_dir`` are required.
    ``region``, ``profile`` and ``endpoint_url`` are optional scalars and may
    be absent or empty; every key present in the file passes through
    unfiltered, so no key needs whitelisting here to reach ``aws_session``.
    """
    config: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = value.strip().strip("'\"")
    missing = {"write_prefix", "public_base", "publish_dir"} - config.keys()
    if missing:
        sys.exit(f"{path.name} is missing: {', '.join(sorted(missing))}")
    return config


def split_s3_uri(uri: str) -> tuple[str, str]:
    """Split s3://bucket/some/prefix into ("bucket", "some/prefix")."""
    if not uri.startswith("s3://"):
        sys.exit(f"write_prefix must start with s3:// — got {uri!r}")
    rest = uri[len("s3://"):].strip("/")
    bucket, _, prefix = rest.partition("/")
    if not bucket:
        sys.exit(f"write_prefix names no bucket — got {uri!r}")
    return bucket, prefix


def unedited_sentinels(config: dict[str, str]) -> list[str]:
    """Sentinel values still present in the config, if any."""
    blob = f"{config['write_prefix']} {config['public_base']}"
    return [s for s in SENTINELS if s in blob]


def _is_item_json(parts: tuple[str, ...]) -> bool:
    """True when ``parts`` places a file at least two directories below a square.

    A STAC Item lives at ``<id>/chips/<square>/<item>/<item>.json``: the
    segment right after ``chips`` is the square, the next is the item
    directory, and the file itself sits inside that. Anything deeper (an
    imagery child item under the chip directory) is an Item too.
    ``chips/<square>/catalog.json`` is one level shallower and does not
    match — it stays plain JSON.
    """
    if "chips" not in parts:
        return False
    return parts.index("chips") + 4 <= len(parts)


def content_type_for(path: Path, *, rel: Path | None = None) -> str:
    """The Content-Type an object gets, by suffix and by location.

    ``rel`` is the path relative to the walk root (``publish_dir`` for
    ``publish.py``, ``data_dir`` for ``upload_data.py``) and is what the
    item-JSON rule below is positional on. Both uploaders pass it. When it is
    omitted, the location rules fall back to reading ``path`` itself, which
    keeps this usable on a bare filename.
    """
    parts = rel.parts if rel is not None else path.parts
    if path.suffix == ".json" and (
        path.name.endswith(".style.json") or "styles" in parts
    ):
        return STYLE_TYPE
    if path.suffix == ".json" and _is_item_json(parts):
        return ITEM_TYPE
    return CONTENT_TYPES.get(path.suffix.lower(), DEFAULT_TYPE)


def is_publishable(rel: Path) -> bool:
    """False for paths the publisher skips inside the published directory.

    Dotfiles and dot-directories are skipped, which covers .gitkeep and any
    .portolan tooling state. A template cannot know whether a downstream user's
    .portolan/metadata.yaml holds something they want public, so it publishes
    none of it.
    """
    return not any(part.startswith(".") for part in rel.parts)


def collect_uploads(
    config: dict[str, str], root: Path = ROOT, *, only: set[str] | None = None
) -> list[Upload]:
    """Every file that would be uploaded, in sorted order.

    The walk is rooted at publish_dir and nothing else. This is the function
    that makes "nothing outside the published directory is published" true.
    ``only`` narrows it further, to those datasets' ``<source>/<id>/`` folders
    and their source groups' own files (``<source>/catalog.json``, README,
    AGENTS: a new dataset changes its group's child links), with no root files.
    """
    _, prefix = split_s3_uri(config["write_prefix"])
    base = root / config["publish_dir"]
    if not base.is_dir():
        sys.exit(f"publish_dir does not exist: {base}")
    groups = _groups_of(only, base)
    uploads = []
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if only is not None and not _in_only(rel.parts, only, groups):
            continue
        if not is_publishable(rel):
            continue
        key = f"{prefix}/{rel.as_posix()}" if prefix else rel.as_posix()
        uploads.append(Upload(path, key, content_type_for(path, rel=rel)))
    return uploads


def root_uploads(config: dict[str, str], root: Path = ROOT) -> list[Upload]:
    """The root files (``catalog.json``, README, AGENTS, llms.txt...), directly under publish_dir."""
    return [u for u in collect_uploads(config, root) if "/" not in u.local.relative_to(
        root / config["publish_dir"]).as_posix()]


def new_groups(
    only: set[str], index: dict[str, tuple[int, str]], config: dict[str, str], root: Path = ROOT
) -> set[str]:
    """The ``only`` datasets' source groups whose ``catalog.json`` the bucket does not have yet.

    A new group is reachable only once the root catalog links it, so an
    ``--only`` publish of its first dataset has to carry the root files too.
    """
    _, prefix = split_s3_uri(config["write_prefix"])
    head = f"{prefix}/" if prefix else ""
    return {
        group for group in _groups_of(only, root / config["publish_dir"])
        if f"{head}{group}/catalog.json" not in index
    }


def plan_root_files(
    uploads: list[Upload],
    only: set[str] | None,
    index: dict[str, tuple[int, str]],
    config: dict[str, str],
    root: Path = ROOT,
) -> tuple[list[Upload], str | None]:
    """``uploads`` with the root files added, and a line saying why.

    ``--only`` adds them when a dataset's group is new, so the root links it.
    """
    if only is None:
        return uploads, None
    fresh = new_groups(only, index, config, root)
    if not fresh:
        return uploads, None
    return uploads + root_uploads(config, root), (
        f"new source group(s) {', '.join(sorted(fresh))}: publishing the root files too, "
        "so the root catalog links them")


def missing_data(
    uploads: list[Upload],
    listing: dict[str, tuple[int, str]],
    config: dict[str, str],
    root: Path = ROOT,
) -> dict[str, list[str]]:
    """Data a changed collection links that is neither staged nor in the bucket.

    For each dataset with a changed file in this publish, every relative asset
    href and ``rel: pmtiles`` link of its ``collection.json`` must resolve:
    to a file under ``catalog/<source>/<id>/`` (published by this run), under
    ``staging/<id>/`` (``upload_data.py`` carries it), or to an object at
    ``<prefix>/<source>/<id>/<href>``. Publishing a collection before its data
    is uploaded would put links to missing objects live.

    The root catalog's own data links (``rel: related`` to a root file such as
    ``chips.pmtiles``) are checked when the root catalog or README changes, under
    ``(root)``. A root file must already be in the bucket at ``<prefix>/<href>``:
    staging it is not enough, because a dataset upload never carries it
    (``upload_data.py --only <file>`` does).
    """
    _, prefix = split_s3_uri(config["write_prefix"])
    head = f"{prefix}/" if prefix else ""
    base = root / config["publish_dir"]
    staging = Path(config.get("data_dir") or "staging")
    staging = staging if staging.is_absolute() else root / staging
    changed = {
        u.local.relative_to(base).parts[:2] for u in uploads
        if len(u.local.relative_to(base).parts) >= 3 and not is_unchanged(u, listing)
    }
    missing: dict[str, list[str]] = {}
    for group, dataset_id in sorted(changed):
        collection = base / group / dataset_id / "collection.json"
        if not collection.is_file():
            continue
        for href in _data_hrefs(json.loads(collection.read_text())):
            rel = href.removeprefix("./")
            if (collection.parent / rel).exists() or (staging / dataset_id / rel).exists():
                continue
            if f"{head}{group}/{dataset_id}/{rel}" not in listing:
                missing.setdefault(dataset_id, []).append(rel)
    root_changed = any(u.local.relative_to(base).parts in (("catalog.json",), ("README.md",))
                       and not is_unchanged(u, listing) for u in uploads)
    if root_changed:
        for rel in _root_data_hrefs(json.loads((base / "catalog.json").read_text())):
            if f"{head}{rel}" not in listing:
                missing.setdefault("(root)", []).append(rel)
    return missing


def _root_data_hrefs(doc: dict) -> list[str]:
    """The root files a catalog's ``rel: related`` links point at (``chips.parquet``)."""
    hrefs = []
    for link in doc.get("links", []):
        rel = link.get("href", "").removeprefix("./")
        if (link.get("rel") == "related" and "://" not in rel and "/" not in rel
                and rel.lower().endswith((".parquet", ".pmtiles"))):
            hrefs.append(rel)
    return hrefs


def _data_hrefs(doc: dict) -> list[str]:
    """The relative hrefs of a collection's assets and ``rel: pmtiles`` links."""
    hrefs = [a.get("href", "") for a in (doc.get("assets") or {}).values()]
    hrefs += [l.get("href", "") for l in doc.get("links", []) if l.get("rel") == "pmtiles"]
    return sorted({h for h in hrefs if h and "://" not in h and not h.startswith(("#", "/"))})


def _groups_of(only: set[str] | None, base: Path) -> set[str]:
    """The source groups the ``only`` datasets are published under."""
    if only is None:
        return set()
    from common import published_collections

    return {
        path.parent.parent.name
        for dataset_id, path in published_collections(base).items()
        if dataset_id in only
    }


def _in_only(parts: tuple[str, ...], only: set[str], groups: set[str]) -> bool:
    """True for a file inside an ``only`` dataset, or one of its group's own files."""
    if len(parts) >= 3:
        return parts[0] in groups and parts[1] in only
    return len(parts) == 2 and parts[0] in groups


def md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - matches S3 ETag, not a security use
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_unchanged(upload: Upload, index: dict[str, tuple[int, str]]) -> bool:
    """True when the object already matches the local bytes.

    A compound (multipart) ETag is not an MD5, so those compare on size alone.
    """
    entry = index.get(upload.key)
    if entry is None:
        return False
    size, etag = entry
    if size != upload.local.stat().st_size:
        return False
    etag = etag.strip('"')
    if "-" in etag:
        return True
    return etag == md5(upload.local)


def aws_session(config: dict[str, str]):
    """The one boto3 session every AWS call in this script is built from.

    ``profile`` and ``region`` are optional. An absent or empty value means
    "let boto3 decide", which is the behavior this script had before profiles
    existed. Raises ImportError when boto3 is missing, and ProfileNotFound
    when the named profile is not in the AWS config.

    Returns a ``boto3.Session``, not a client: ``endpoint_url`` is a
    per-client argument, not a session one, so it is applied where clients
    are actually built (``remote_index`` and ``upload_all``) via
    ``s3_client`` below, rather than here.
    """
    import boto3

    return boto3.Session(
        profile_name=config.get("profile") or None,
        region_name=config.get("region") or None,
    )


def s3_client(session, endpoint_url: str | None = None, *, pool_size: int | None = None):
    """An S3 client from ``session``, honouring an optional ``endpoint_url``.

    Source Cooperative is addressed through its data proxy (``endpoint_url``
    in ``catalog.publish.yaml``) rather than AWS's own S3 endpoints. Passing
    ``endpoint_url=None`` to boto3 is safe and means "use the default", but
    the keyword is added only when a value is actually set so that test
    doubles standing in for ``session`` (which only need to support the
    single-argument call boto3 itself accepts) keep working unchanged.

    ``pool_size`` raises the connection pool (botocore's default is 10) for a
    client shared by that many threads.
    """
    kwargs = {}
    config = _client_config(retry=bool(endpoint_url), pool_size=pool_size)
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if config is not None:
        kwargs["config"] = config
    return session.client("s3", **kwargs)


def _client_config(*, retry: bool, pool_size: int | None):
    """The botocore Config for s3_client, or None when nothing is set."""
    settings = {}
    if retry:
        settings["retries"] = {"max_attempts": RETRY_MAX_ATTEMPTS, "mode": "standard"}
    if pool_size:
        settings["max_pool_connections"] = pool_size
    if not settings:
        return None
    try:
        from botocore.config import Config
    except ImportError:
        return None
    return Config(**settings)


# Source Cooperative's data proxy occasionally answers a multipart part with a
# 5xx (a 520 on a 1.5 GB parquet was the first real failure). boto3's default
# retry policy gives up quickly and does not classify every proxy error as
# retryable; the standard mode with more attempts does.
RETRY_MAX_ATTEMPTS = 8
# The proxy closed the connection mid-part on 64 MB parts of a 1.5 GB file
# (SSL EOF on part 9, twice); 16 MB parts with little concurrency get through.
MULTIPART_CHUNK_BYTES = 16 * 1024 * 1024


def _retry_config():
    """A botocore Config with the standard retry mode, or None without botocore."""
    try:
        from botocore.config import Config
    except ImportError:
        return None
    return Config(retries={"max_attempts": RETRY_MAX_ATTEMPTS, "mode": "standard"})


def _transfer_config():
    """A boto3 TransferConfig with large multipart chunks, or None without boto3."""
    try:
        from boto3.s3.transfer import TransferConfig
    except ImportError:
        return None
    return TransferConfig(multipart_chunksize=MULTIPART_CHUNK_BYTES, max_concurrency=2)


# A listing is one page of 1,000 keys per round trip. Listed serially, the
# whole bucket (every collection's chips) took about 7 hours by November 2026.
# The walk lists each folder level with a "/" delimiter and fans out over the
# subfolders, so pages are fetched LIST_WORKERS at a time.
LIST_WORKERS = 32
# Folder levels below write_prefix that are split before a flat listing:
# <source>/<dataset>/chips/<tile>/ in this bucket. Deeper, the folders are single
# chips of a few files each, and one request per chip would cost more than it saves.
LIST_SPLIT_DEPTH = 4
# How deep a dataset's own folder sits below write_prefix: <source>/<dataset>/.
DATASET_DEPTH = 2
# The proxy answers some requests with a 520, which botocore does not retry.
# One failed folder fails the whole listing, so each folder is retried from its
# first page this many times, waiting LIST_RETRY_SECONDS * 2**attempt between.
LIST_ATTEMPTS = 6
LIST_RETRY_SECONDS = 2.0


def remote_index(
    bucket: str,
    prefix: str,
    config: dict[str, str],
    *,
    only: set[str] | None = None,
    root: Path = ROOT,
) -> dict[str, tuple[int, str]]:
    """Size and ETag for every object under the prefix, or {} when unreadable.

    Every key this tool writes is ``<prefix>/<rel>``. The listing covers the
    root files at ``<prefix>/`` and the source groups ``catalog/`` publishes
    (``<prefix>/<source>/``, recursively); any other top-level folder is never
    walked, so it is not split chip by chip. ``only`` narrows that to those datasets'
    ``<source>/<id>/`` folders plus their groups' own files and the root files
    (placed by ``common.dataset_relpath`` against ``root``'s publish_dir).
    """
    from common import dataset_relpath, published_collections

    top = f"{prefix.rstrip('/')}/" if prefix else ""
    catalog = root / config["publish_dir"]
    if only is None:
        groups = sorted({p.parent.parent.name for p in published_collections(catalog).values()})
        roots = [(f"{top}{group}/", 1) for group in groups]
        levels = [top]
    else:
        # A root file named in ``only`` (``chips.parquet``) is in the root level listed below.
        datasets = sorted(name for name in only if "." not in name)
        rels = [dataset_relpath(dataset_id, catalog=catalog, root=root) for dataset_id in datasets]
        roots = [(f"{top}{rel}/", DATASET_DEPTH) for rel in rels]
        levels = [top, *sorted({f"{top}{rel.split('/')[0]}/" for rel in rels})]
    try:
        client = s3_client(
            aws_session(config), config.get("endpoint_url"), pool_size=LIST_WORKERS
        )
        index = _parallel_listing(client, bucket, roots)
        for level in levels:  # the files at this level only, not its folders
            index.update(_list_folder(client, bucket, level, False)[0])
        return index
    except ImportError:
        print("note: boto3 is not installed; treating every file as changed")
        return {}
    except Exception as exc:  # noqa: BLE001 - any failure means "unknown"
        print(f"note: could not list s3://{bucket}/{prefix} ({exc});")
        print("      treating every file as changed")
        return {}


def _list_folder(
    client, bucket: str, prefix: str, flat: bool
) -> tuple[dict[str, tuple[int, str]], list[str]]:
    """The objects under ``prefix``: all of them when flat, else this level and its subfolders.

    A failed request restarts the folder from its first page, up to LIST_ATTEMPTS times.
    """
    for attempt in range(LIST_ATTEMPTS):
        try:
            return _list_folder_once(client, bucket, prefix, flat)
        except Exception:  # noqa: BLE001 - any error is retried, the last one raised
            if attempt == LIST_ATTEMPTS - 1:
                raise
            time.sleep(LIST_RETRY_SECONDS * 2**attempt)
    raise AssertionError("unreachable")


def _list_folder_once(
    client, bucket: str, prefix: str, flat: bool
) -> tuple[dict[str, tuple[int, str]], list[str]]:
    """One attempt at _list_folder."""
    kwargs = {"Bucket": bucket, "Prefix": prefix}
    if not flat:
        kwargs["Delimiter"] = "/"
    objects: dict[str, tuple[int, str]] = {}
    folders: list[str] = []
    for page in client.get_paginator("list_objects_v2").paginate(**kwargs):
        for obj in page.get("Contents", []):
            objects[obj["Key"]] = (obj["Size"], obj["ETag"])
        folders.extend(p["Prefix"] for p in page.get("CommonPrefixes", []))
    return objects, folders


def _parallel_listing(
    client, bucket: str, roots: list[tuple[str, int]]
) -> dict[str, tuple[int, str]]:
    """List each (prefix, depth) root, splitting folders down to LIST_SPLIT_DEPTH.

    Any failed request fails the whole listing: a partial index would make
    files that are in the bucket look missing.
    """
    done: queue.Queue = queue.Queue()
    pool = ThreadPoolExecutor(max_workers=LIST_WORKERS)
    outstanding = 0

    def submit(prefix: str, depth: int) -> None:
        nonlocal outstanding
        outstanding += 1
        future = pool.submit(_list_folder, client, bucket, prefix, depth >= LIST_SPLIT_DEPTH)
        future.add_done_callback(lambda f, d=depth: done.put((f, d)))

    index: dict[str, tuple[int, str]] = {}
    try:
        for prefix, depth in roots:
            submit(prefix, depth)
        while outstanding:
            future, depth = done.get()
            outstanding -= 1
            objects, folders = future.result()
            index.update(objects)
            for folder in folders:
                submit(folder, depth + 1)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return index


def upload_all(
    session, bucket: str, uploads: list[Upload], endpoint_url: str | None = None
) -> list[str]:
    """Upload every object on a bounded pool. Returns the keys that failed.

    Every upload is attempted. One failure does not cancel the rest, so the
    caller reports all of them at once.

    A botocore client is safe to *call* from many threads, but the Session is
    not safe to create clients from concurrently. So each worker thread builds
    its own client once, and a lock covers only that creation. ``endpoint_url``
    is optional so a caller (and a test double standing in for ``session``)
    that never sets it sees no change in behavior.
    """
    thread_state = threading.local()
    new_client = threading.Lock()

    def client() -> object:
        existing = getattr(thread_state, "client", None)
        if existing is not None:
            return existing
        with new_client:
            thread_state.client = s3_client(session, endpoint_url)
        return thread_state.client

    transfer = _transfer_config()

    def put(upload: Upload) -> None:
        kwargs = {"ExtraArgs": {"ContentType": upload.content_type}}
        if transfer is not None:
            kwargs["Config"] = transfer
        client().upload_file(str(upload.local), bucket, upload.key, **kwargs)

    failures: list[str] = []
    done = 0
    total = len(uploads)
    with ThreadPoolExecutor(max_workers=MAX_UPLOAD_WORKERS) as pool:
        futures = {pool.submit(put, u): u for u in uploads}
        for future in as_completed(futures):
            upload = futures[future]
            done += 1
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001 - report, do not abort
                failures.append(upload.key)
                print(f"  FAILED  {upload.key}: {exc}", file=sys.stderr,
                      flush=True)
            if done % PROGRESS_EVERY == 0 or done == total:
                print(f"  {done}/{total} done", flush=True)
    return failures


def pending_data(
    config: dict[str, str],
    index: dict[str, tuple[int, str]],
    root: Path = ROOT,
    *,
    only: set[str] | None = None,
) -> dict[str, int]:
    """Collections in the published directory with staged data not yet in the bucket.

    Keyed by dataset id, valued by how many data files are missing or differ.
    Publishing a collection whose data is not there yet would put links to
    missing objects live (and, for a new collection, its row in the root tables).
    ``split_pending`` decides which of these block a publish.
    """
    # Imported here: upload_data imports this module.
    from upload_data import collect_data_uploads

    from common import published_collections

    published = published_collections(root / config["publish_dir"])
    ids = set(published)
    if only is not None:
        ids &= only
    if not ids:
        return {}
    pending: dict[str, int] = {}
    _, prefix = split_s3_uri(config["write_prefix"])
    for dataset_id in sorted(ids):
        # Staging pruned after upload, or never here: the bucket must hold its mirror.
        if not (data_root(config, root) / dataset_id).is_dir():
            rel = f"{published[dataset_id].parent.parent.name}/{dataset_id}/items.parquet"
            key = f"{prefix}/{rel}" if prefix else rel
            if key not in index:
                pending[dataset_id] = 1
    for upload in collect_data_uploads(config, root, only=ids):
        if not is_unchanged(upload, index):
            dataset_id = upload.local.relative_to(data_root(config, root)).parts[0]
            pending[dataset_id] = pending.get(dataset_id, 0) + 1
    return pending


def collections_to_check(
    uploads: list[Upload],
    listing: dict[str, tuple[int, str]],
    config: dict[str, str],
    root: Path = ROOT,
) -> set[str] | None:
    """The collections whose data must be in the bucket before this publish; None for all.

    A collection whose published files all match the bucket puts nothing new live,
    so a rebuild staging beside it does not hold up the others. The root files are
    the exception: catalogize measures every collection's row in the root tables
    from its staging, so when any root file changes, every collection is checked.
    Compared against the bucket listing, not the upload list, so --force (which
    re-uploads everything) checks the same collections as a normal publish.
    """
    base = root / config["publish_dir"]
    parts = [u.local.relative_to(base).parts for u in uploads if not is_unchanged(u, listing)]
    if any(len(p) == 1 for p in parts):
        return None
    # <source>/<id>/...; a group's own files (<source>/catalog.json) measure nothing.
    return {p[1] for p in parts if len(p) >= 3}


def split_pending(
    uploads: list[Upload],
    listing: dict[str, tuple[int, str]],
    config: dict[str, str],
    root: Path = ROOT,
    *,
    only: set[str] | None = None,
) -> tuple[dict[str, int], dict[str, int]]:
    """Pending data as (blocking this publish, in collections this publish leaves alone).

    With ``only``, the listing covers those datasets alone, so no other is checked.
    """
    pending = pending_data(config, listing, root, only=only)
    only = collections_to_check(uploads, listing, config, root)
    if only is None:
        return pending, {}
    blocking = {k: v for k, v in pending.items() if k in only}
    return blocking, {k: v for k, v in pending.items() if k not in only}


def data_root(config: dict[str, str], root: Path = ROOT) -> Path:
    """The staged data directory (``data_dir``), as upload_data.py walks it."""
    from upload_data import data_root as upload_data_root

    return upload_data_root(config, root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync the published directory to object storage, 1:1.",
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
        help="publish only this dataset's folder and its source group's files, listing only "
             "them (repeatable; root files only when the group is new)",
    )
    args = parser.parse_args()
    only = set(args.only) if args.only else None

    config = load_config()

    stale = unedited_sentinels(config)
    if stale:
        print("catalog.publish.yaml still carries template values:")
        for value in stale:
            print(f"  {value}")
        print("\nEdit write_prefix and public_base, then see README.md.")
        return 1

    bucket, prefix = split_s3_uri(config["write_prefix"])
    uploads = collect_uploads(config, only=only)
    if not uploads:
        print(f"nothing under {config['publish_dir']}/ to publish",
              file=sys.stderr)
        return 1

    index = {} if args.force else remote_index(bucket, prefix, config, only=only)
    uploads, why = plan_root_files(uploads, only, index, config)
    if why:
        print(why)
    changed = [u for u in uploads if args.force or not is_unchanged(u, index)]

    print(f"publish_dir: {config['publish_dir']}/")
    print(f"target:      s3://{bucket}/{prefix}")
    print(f"aws profile: {config.get('profile') or '(default session)'}")
    print(f"{len(uploads)} file(s) published, {len(changed)} to upload")
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

    # The data check needs the listing even when --force skipped it for the diff.
    listing = remote_index(bucket, prefix, config, only=only) if args.force else index
    if not listing:
        print("cannot list the bucket, so cannot confirm the data is uploaded; not publishing",
              file=sys.stderr)
        return 1
    missing = missing_data(uploads, listing, config)
    if missing:
        print("\nnot publishing: these collections (or the root) link data that is neither "
              "staged nor at its new bucket key; copy or upload the data first:", file=sys.stderr)
        for dataset_id, hrefs in sorted(missing.items()):
            shown = ", ".join(hrefs[:5]) + (f" and {len(hrefs) - 5} more" if len(hrefs) > 5 else "")
            print(f"  {dataset_id}: {shown}", file=sys.stderr)
        return 1
    pending, unchanged_pending = split_pending(uploads, listing, config, only=only)
    if pending and collections_to_check(uploads, listing, config) is None:
        print("\na root file changed, and the root tables are measured from staging, so every "
              "collection's data is checked", file=sys.stderr)
    if unchanged_pending:
        print("\nnot checked (this publish leaves their catalog as it is), data not all in the "
              "bucket:", file=sys.stderr)
        for dataset_id, count in sorted(unchanged_pending.items()):
            print(f"  {dataset_id}: {count} file(s)", file=sys.stderr)
    if pending:
        print("\nnot publishing: these collections' data is not all uploaded yet:",
              file=sys.stderr)
        for dataset_id, count in sorted(pending.items()):
            print(f"  {dataset_id}: {count} file(s)  (upload_data.py --only {dataset_id})",
                  file=sys.stderr)
        return 1

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
