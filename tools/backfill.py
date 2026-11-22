#!/usr/bin/env python3
"""Add admin names and per-field embeddings to datasets that are already published.

New builds get both from ftwd (``stages.chips.admin_names`` and
``stages.chips.field_embeddings``). This brings a published dataset to the same
state without rebuilding it, working in ``staging/<id>/``:

1. fetch: the published item JSON, sub-catalogs and the chips and fields
   GeoParquet, from the bucket (anonymous reads; a file already on disk with the
   published size and MD5 is kept), plus ``collection.json`` from ``catalog/<source>/<id>/``;
2. add the admin name columns to the chips file, and write
   ``<id>_field_embeddings.parquet`` (kept when it already matches the fields);
3. set ``ftw:admin*`` on every chip item, and update the collection: the chips
   asset, the GAUL link, the field embeddings asset with its links and license link;
4. rebuild ``items.parquet``, rewrite the styles, README.md and AGENTS.md from the
   updated files, then ``catalogize`` into ``catalog/<source>/<id>/``.

``--crop-names-from <dir>`` also joins ``crop:name`` (and ``crop:name_en``) onto the
fields, fields_filtered and boundary_lines files from the harmonized edition the
dataset was built from, found at ``<dir>/<harmonized_id>/year=<year>/<stem>-<year>.parquet``
(the harmonized catalog's staging, rebuilt with names; the record gives the edition's
published URL). The join is by field id and refuses any field whose crop:code differs
there (ftwd ``api.crop_names``). Give the option on every later run too: each run
fetches the published field files again, and the backfill record lists the steps of the
latest run.
``--crop-names-by code`` names each field from its crop code instead, for an edition
named from a code table whose ids no longer match the benchmark's (fr_2024: IGN
replaced RPG 3.0 with RPG 4.0); it refuses a code with more than one name, and it takes
one dataset per run so no other dataset loses the per-field check by mistake.
es_2025 and es_po_2025 can only be named by code: their merge rewrote the ids (and the
regional gap parcels have no crop:code, so they stay unnamed).

The field assets' size, checksum and columns are always read from the staged files,
so the collection describes the files that will be uploaded either way. A run without
the option reads neither the boundary lines (they stay as published) nor any edition,
and keeps the earlier run's crop-names record while the fetched fields and
fields_filtered still carry crop:name. The names are joined first, into temp files that
replace the field files only when every join succeeded, so a dataset whose names are refused is
left as fetched (as published): it is reported and skipped, and the run carries on
with the others and exits 1.

Nothing is uploaded. Publish afterwards the usual way:

    uv run python tools/backfill.py rw_rwanda_ml_2021 --workers 32
    uv run python tools/upload_data.py --only rw_rwanda_ml_2021 --confirm
    uv run python tools/publish.py --only rw_rwanda_ml_2021 --confirm

Rasters and PMTiles are never fetched: nothing here changes them.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    CATALOG,
    STAGING,
    dataset_dir,
    dataset_relpath,
    read_json,
    write_json,
)

# Anonymous reads go straight to the bucket behind Source Cooperative's proxy, which is
# much faster for many small objects. Writes still go through the proxy (publish.py).
READ_BUCKET = "us-west-2.opendata.source.coop"
READ_PREFIX = "ftw/benchmark-data"
FETCH_WORKERS = 64
FETCH_ATTEMPTS = 4
# Larger objects go through boto3's transfer manager (ranged, parallel parts); smaller
# ones are a single GET, which costs far less per object.
SMALL_OBJECT_BYTES = 8 * 1024 * 1024

# The field polygons: read and refreshed by every run, with the chips file. Everything
# under chips/ that is JSON is read too.
POLYGON_ASSETS = ("fields", "fields_filtered")
# Every file that carries the fields' crop columns. The boundary lines are read only to
# join crop names into them; they are as large as the fields, so not otherwise.
FIELD_ASSETS = (*POLYGON_ASSETS, "boundary_lines")
# Where the harmonized editions are published, for the crop-names record.
HARMONIZED_PREFIX = "ftw/harmonized-field-data"
HARMONIZED = f"https://data.source.coop/{HARMONIZED_PREFIX}"
# Read when published, so a rerun keeps it instead of recomputing hours of embeddings.
_OPTIONAL_ASSETS = ("field_embeddings",)
# Files the backfill writes itself, so they may differ from the bucket or be new.
_OUTPUTS = ("items.parquet", "{id}_field_embeddings.parquet")
_OUTPUT_DIRS = ("{id}_field_embeddings.parquet.partial",)


@dataclass(frozen=True)
class Remote:
    key: str
    size: int
    etag: str


def _client():
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    return boto3.client(
        "s3",
        region_name="us-west-2",
        config=Config(
            signature_version=UNSIGNED,
            s3={"addressing_style": "path"},
            max_pool_connections=FETCH_WORKERS,
            retries={"max_attempts": 10, "mode": "adaptive"},
        ),
    )


def _listing(client, remote_rel: str) -> dict[str, Remote]:
    """Relative path to the published object, for every object under ``<prefix>/<remote_rel>/``."""
    prefix = f"{READ_PREFIX}/{remote_rel}/"
    out: dict[str, Remote] = {}
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=READ_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            out[obj["Key"][len(prefix):]] = Remote(obj["Key"], obj["Size"], obj["ETag"].strip('"'))
    return out


def wanted(rel: str, top_level: set[str]) -> bool:
    """Whether the backfill reads this published file."""
    parts = rel.split("/")
    if parts[0] == "chips":
        return rel.endswith(".json")
    return len(parts) == 1 and rel in top_level


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - compared with S3 ETags, not used for security
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def is_current(path: Path, remote: Remote) -> bool:
    """A local copy matches the published object (on size alone for multipart uploads)."""
    if not path.is_file() or path.stat().st_size != remote.size:
        return False
    return "-" in remote.etag or _md5(path) == remote.etag


def _get(client, remote: Remote, tmp: Path) -> None:
    """One object to ``tmp``: a plain GET for small ones, which most are (item JSON)."""
    if remote.size > SMALL_OBJECT_BYTES:
        client.download_file(READ_BUCKET, remote.key, str(tmp))
        return
    body = client.get_object(Bucket=READ_BUCKET, Key=remote.key)["Body"].read()
    if len(body) != remote.size:
        raise OSError(f"{remote.key}: got {len(body)} bytes, expected {remote.size}")
    tmp.write_bytes(body)


def _download(client, remote: Remote, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    for attempt in range(FETCH_ATTEMPTS):
        try:
            _get(client, remote, tmp)
            break
        except Exception:
            if attempt == FETCH_ATTEMPTS - 1:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(2 ** attempt)
    tmp.replace(path)


def _asset_names(doc: dict, keys: tuple[str, ...]) -> set[str]:
    assets = doc.get("assets", {})
    return {str(assets[key]["href"]).removeprefix("./") for key in keys if key in assets}


# Part sizes of the harmonized uploads: the harmonized catalog's upload_data.py (64 MiB),
# this repo's publish.py (16 MiB), and 8 MiB, boto3's and the AWS CLI's default.
_PART_SIZES = (64 << 20, 16 << 20, 8 << 20)


def multipart_etag(path: Path, part_size: int) -> str:
    """The ETag S3 gives ``path`` uploaded in ``part_size`` parts: md5 of the parts' md5s."""
    digests = []
    with path.open("rb") as f:
        for block in iter(lambda: f.read(part_size), b""):
            digests.append(hashlib.md5(block).digest())  # noqa: S324 - S3's ETag, not security
    joined = hashlib.md5(b"".join(digests)).hexdigest()  # noqa: S324
    return f"{joined}-{len(digests)}"


# An S3 ETag of plain MD5s: one hex digest, and the part count of a multipart upload.
_ETAG = re.compile(r"[0-9a-f]{32}(-[1-9][0-9]*)?")


def differs_from(path: Path, remote: Remote) -> str | None:
    """How ``path`` differs from the published object, or None when it holds its bytes.

    A multipart ETag is recomputed from the file in each part size that gives its part
    count; one part needs no size.
    """
    if not path.is_file():
        return "is missing"
    if path.stat().st_size != remote.size:
        return f"is {path.stat().st_size:,} bytes, the published one {remote.size:,}"
    if not _ETAG.fullmatch(remote.etag):
        return f"cannot be compared: unexpected ETag {remote.etag}"
    digest, _, count = remote.etag.partition("-")
    if not count:
        return None if _md5(path) == digest else "has other bytes (MD5 differs)"
    parts = int(count)
    sizes = [size for size in _PART_SIZES if -(-remote.size // size) == parts]
    if parts == 1:
        sizes = [max(remote.size, 1)]
    if not sizes:
        return f"cannot be compared: {parts} parts of no known part size"
    if any(multipart_etag(path, size) == remote.etag for size in sizes):
        return None
    return "has other bytes (multipart ETag differs), or was uploaded in another part size"


def check_staging(
    root: Path, listing: dict[str, Remote], *, catalog_dir: Path, top_level: set[str]
) -> None:
    """Refuse a staging tree that holds data the bucket does not, such as an unpublished rebuild.

    The backfill replaces the files it reads with the published ones, but leaves the
    rest; ``upload_data.py`` would then upload a rebuild's masks or images beside the
    published items. Only files ``upload_data.py`` would upload are checked: any the
    bucket lacks, and ones the fetch leaves alone whose size differs from the bucket's
    (the ones it reads are replaced with the published copy when they differ).
    """
    from upload_data import is_data_publishable

    dataset_id = root.name
    outputs = {name.format(id=dataset_id) for name in _OUTPUTS}
    output_dirs = {name.format(id=dataset_id) for name in _OUTPUT_DIRS}
    odd: list[str] = []
    for path in sorted(root.rglob("*")) if root.is_dir() else []:
        rel = path.relative_to(root)
        if not path.is_file() or rel.parts[0] in output_dirs or rel.as_posix() in outputs:
            continue
        if not is_data_publishable(rel) or (catalog_dir / rel).exists():
            continue
        remote = listing.get(rel.as_posix())
        if remote is None:
            odd.append(rel.as_posix())
        elif not wanted(rel.as_posix(), top_level) and path.stat().st_size != remote.size:
            odd.append(rel.as_posix())
    if odd:
        shown = ", ".join(odd[:5]) + (f" and {len(odd) - 5:,} more" if len(odd) > 5 else "")
        raise SystemExit(
            f"{dataset_id}: staging holds data that is not published ({shown}); "
            f"move staging/{dataset_id} aside before backfilling it"
        )


def fetch(
    dataset_id: str,
    *,
    staging: Path = STAGING,
    catalog: Path = CATALOG,
    boundary_lines: bool = False,
) -> int:
    """Make ``staging/<id>`` hold what the backfill reads, as published. Returns files fetched.

    Reads ``<prefix>/<source>/<id>/``.
    ``boundary_lines`` reads the boundary lines too, to name them; staged ones are made
    the published copy again either way.
    """
    catalog_dir = dataset_dir(dataset_id, catalog=catalog)
    doc = read_json(catalog_dir / "collection.json")
    root = staging / dataset_id
    top_level = _asset_names(doc, ("chips", *POLYGON_ASSETS))
    lines = _asset_names(doc, ("boundary_lines",))
    # Also when staged: lines a naming run left un-uploaded go back to the published copy.
    if boundary_lines or any((root / rel).is_file() for rel in lines):
        top_level |= lines
    client = _client()
    listing = _listing(client, dataset_relpath(dataset_id, catalog=catalog))
    missing = sorted(top_level - set(listing))
    if missing:
        raise SystemExit(f"{dataset_id}: not in the bucket: {', '.join(missing)}")
    top_level |= _asset_names(doc, _OPTIONAL_ASSETS) & set(listing)
    check_staging(root, listing, catalog_dir=catalog_dir, top_level=top_level)
    todo = [
        (remote, root / rel)
        for rel, remote in sorted(listing.items())
        if wanted(rel, top_level)
    ]
    with ThreadPoolExecutor(FETCH_WORKERS) as pool:
        stale = [
            pair for pair, ok in zip(
                todo, pool.map(lambda p: is_current(p[1], p[0]), todo), strict=True
            ) if not ok
        ]
        list(pool.map(lambda p: _download(client, *p), stale))
    write_json(root / "collection.json", doc)
    return len(stale)


def _year(doc: dict) -> int:
    year = ((doc.get("ftw:config") or {}).get("config") or {}).get("year")
    if not isinstance(year, int):
        raise SystemExit(f"{doc.get('id')}: ftw:config has no year")
    return year


def update_items(root: Path, chips_file: Path, year: int) -> tuple[int, int]:
    """Set ``ftw:admin*`` on every chip item under ``root/chips``. Returns (changed, items)."""
    from ftw_dataset_tools.api import backfill

    properties = backfill.chip_item_properties(chips_file, year=year)
    seen = changed = 0
    for path in sorted(root.glob("chips/*/*/*.json")):
        if path.stem != path.parent.name or path.stem not in properties:
            continue
        item = read_json(path)
        if item.get("type") != "Feature" or item.get("id") not in properties:
            continue
        seen += 1
        if backfill.update_item(item, properties[item["id"]]):
            write_json(path, item)
            changed += 1
    if seen != len(properties):
        raise SystemExit(
            f"{root.name}: found {seen:,} chip items for {len(properties):,} chips; "
            "the fetch is incomplete"
        )
    return changed, seen


def staged_collection(doc: dict, host: dict | None = None) -> dict:
    """The collection as ftwd's docs stage sees it in a build, before ``catalogize``.

    The via link goes back to the harmonized collection's JSON endpoint (``catalogize``
    turns it into the human page again and names the source in the README from it).
    The thumbnail and the host provider (``host``, the manifest's), which only
    ``catalogize`` adds, are left out; ``catalogize`` adds them back.
    """
    staged = copy.deepcopy(doc)
    staged.get("assets", {}).pop("thumbnail", None)
    if host is not None and "providers" in staged:
        staged["providers"] = [
            p for p in staged["providers"]
            if not (p.get("name") == host.get("name") and "host" in (p.get("roles") or []))
        ]
    source_via = ((doc.get("ftw:config") or {}).get("config") or {}).get("source_via")
    for link in staged.get("links", []):
        if source_via and link.get("rel") == "via":
            link["href"] = source_via
            link["type"] = "application/json"
    return staged


def write_chip_items_parquet(
    dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG
) -> None:
    """``items.parquet`` with the chip items only, as ftwd's stac stage writes it.

    The docs measure item properties from it; the imagery child items in the
    published mirror would add their own properties and a null split. ``catalogize``
    rebuilds the full mirror afterwards.
    """
    import rustac
    from catalogize import _ensure_geoparquet_metadata, _item_documents

    path = staging / dataset_id / "items.parquet"
    items = [
        doc for doc in _item_documents(
            dataset_relpath(dataset_id, catalog=catalog), staging / dataset_id / "chips"
        )
        if "ftw:season" not in (doc.get("properties") or {})
    ]
    tmp = path.with_name(path.name + ".tmp")
    rustac.write_sync(str(tmp), items, format="parquet")
    _ensure_geoparquet_metadata(tmp)
    tmp.replace(path)


def harmonized_edition(dataset_id: str, harmonized_staging: Path) -> Path:
    """The harmonized edition a dataset was built from, under ``harmonized_staging``."""
    import tracking

    r = tracking.row(dataset_id)
    year = r["year"]
    return (
        harmonized_staging / r["harmonized_id"] / f"year={year}"
        / f"{tracking.source_stem(r)}-{year}.parquet"
    )


def field_files(
    doc: dict, root: Path, keys: tuple[str, ...] = POLYGON_ASSETS
) -> dict[str, Path]:
    """The dataset's staged field files, by asset key."""
    return {
        key: root / str(doc["assets"][key]["href"]).removeprefix("./")
        for key in keys
        if key in doc["assets"]
    }


def staged_field_files(
    doc: dict, root: Path, *, naming: bool
) -> tuple[dict[str, Path], dict[str, Path]]:
    """The field files to name, and the ones whose asset to refresh.

    The boundary lines are named only when naming, but refreshed whenever staged: the
    fetch has made staged lines the published copy, which a collection catalogized from
    an un-uploaded naming run does not describe.
    """
    named = field_files(doc, root, FIELD_ASSETS if naming else POLYGON_ASSETS)
    refreshed = {
        key: path for key, path in field_files(doc, root, FIELD_ASSETS).items()
        if key in named or path.is_file()
    }
    return named, refreshed


def _named_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.named")


def add_crop_names(
    dataset_id: str, files: dict[str, Path], source: Path, by: str = "id"
) -> None:
    """Join the crop names onto the dataset's field files, all of them or none.

    Each file is joined into a temp file first; the field files are replaced only
    once every join has succeeded, and only those whose names changed, so an
    unchanged file keeps its bytes (and its published checksum).
    """
    from ftw_dataset_tools.api import crop_names

    changed = []
    try:
        for key, path in files.items():
            result = crop_names.add_crop_names(path, source, _named_path(path), by=by)
            print(f"{dataset_id}: {key}: {', '.join(result.columns)} on {result.named:,} of "
                  f"{result.rows:,} fields{'' if result.changed else ' (unchanged)'}", flush=True)
            if result.changed:
                changed.append(path)
        for path in changed:
            _named_path(path).replace(path)
    finally:
        for path in files.values():
            _named_path(path).unlink(missing_ok=True)


def crop_names_record(source: Path, crop_names_from: Path, by: str) -> dict:
    """The crop-names record: the edition's published URL, and what the join was by."""
    return {"source": f"{HARMONIZED}/{source.relative_to(crop_names_from).as_posix()}", "by": by}


def unpublished_edition(edition: Path, crop_names_from: Path, client=None) -> str | None:
    """Why the local edition is not the published one, or None when it is.

    The record names the published edition, so the names must come from that very file.
    """
    rel = edition.relative_to(crop_names_from).as_posix()
    client = client or _client()
    key = f"{HARMONIZED_PREFIX}/{rel}"
    try:
        head = client.head_object(Bucket=READ_BUCKET, Key=key)
    except Exception as err:  # noqa: BLE001 - botocore's ClientError, imported lazily
        return f"{HARMONIZED}/{rel} cannot be read ({err})"
    remote = Remote(key, head["ContentLength"], head["ETag"].strip('"'))
    why = differs_from(edition, remote)
    if why is None:
        return None
    if why == "is missing":
        return f"no harmonized edition at {edition}"
    if why.startswith("cannot be compared"):
        return f"{edition} {why} with the published {HARMONIZED}/{rel}"
    return f"{edition} is not the published {HARMONIZED}/{rel}: it {why}; upload it first"


def earlier_crop_names(doc: dict, files: dict[str, Path]) -> dict | None:
    """The crop-names record of the last backfill, while the field files still have names.

    ``files`` are the field polygons: datasets named before the boundary lines were have
    names in those only.
    """
    import pyarrow.parquet as pq

    from ftw_dataset_tools.api.backfill import BACKFILL_KEY

    runs = (doc.get("ftw:config") or {}).get(BACKFILL_KEY) or []
    earlier = runs[-1].get("crop_names") if runs else None
    if not earlier or not files:
        return None
    if not all("crop:name" in pq.read_schema(path).names for path in files.values()):
        return None
    source = earlier.get("source")
    # Records written before they named the published URL give the path under it.
    if source and "://" not in source:
        return {**earlier, "source": f"{HARMONIZED}/{source.lstrip('/')}"}
    return earlier


def backfill_dataset(
    dataset_id: str,
    *,
    workers: int,
    manifest: dict,
    staging: Path = STAGING,
    crop_names_from: Path | None = None,
    crop_names_by: str = "id",
) -> None:
    """Fetch, enrich and catalogize one published dataset."""
    from catalogize import catalogize

    from ftw_dataset_tools.api import admin_names, backfill, field_embeddings

    start = time.monotonic()
    naming = crop_names_from is not None
    fetched = fetch(dataset_id, staging=staging, boundary_lines=naming)
    root = staging / dataset_id
    collection_path = root / "collection.json"
    doc = read_json(collection_path)
    year = _year(doc)
    chips = root / str(doc["assets"]["chips"]["href"]).removeprefix("./")
    fields = root / str(doc["assets"]["fields"]["href"]).removeprefix("./")
    embeddings = root / f"{dataset_id}_field_embeddings.parquet"
    print(f"{dataset_id}: fetched {fetched:,} file(s)", flush=True)

    # First, so a refusal leaves staging as fetched (as published).
    files, refreshed = staged_field_files(doc, root, naming=naming)
    if naming:
        source = harmonized_edition(dataset_id, crop_names_from)
        add_crop_names(dataset_id, files, source, crop_names_by)
        crop_names = crop_names_record(source, crop_names_from, crop_names_by)
    else:
        crop_names = earlier_crop_names(doc, files)

    admin_names.add_admin_names(chips)
    if field_embeddings.is_current(embeddings, fields, year=year):
        print(f"{dataset_id}: keeping {embeddings.name}", flush=True)
    else:
        result = field_embeddings.add_field_embeddings(fields, embeddings, year=year, workers=workers)
        print(f"{dataset_id}: {field_embeddings.field_embeddings_summary(result)}", flush=True)

    changed, items = update_items(root, chips, year)
    print(f"{dataset_id}: admin names on {changed:,} of {items:,} chip items changed", flush=True)

    backfill.update_collection(
        doc,
        chips_file=chips,
        admin_names_added=True,
        field_embeddings_file=embeddings,
        field_files=refreshed,
        crop_names=crop_names,
    )
    # The stac stage describes its chip-only mirror; catalogize later swaps in the full
    # one and refreshes only its size, so the columns come from this file, as in a build.
    write_chip_items_parquet(dataset_id, staging=staging)
    backfill.refresh_parquet_asset(doc, "items", root / "items.parquet")
    write_json(collection_path, staged_collection(doc, manifest.get("host")))
    backfill.rewrite_docs(root, collection_path)
    catalogize(dataset_id, manifest=manifest, staging=staging)
    print(f"{dataset_id}: done in {time.monotonic() - start:,.0f}s", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("dataset_ids", nargs="+", metavar="ID")
    parser.add_argument(
        "--workers", type=int, default=16, help="threads reading embeddings (default 16)"
    )
    parser.add_argument("--crop-names-from", type=Path, metavar="DIR",
                        help="the harmonized catalog's staging, rebuilt with crop names: join "
                             "crop:name onto the field files from each dataset's edition")
    parser.add_argument("--crop-names-by", choices=("id", "code"),
                        help="join the names by field id (default), or by crop code for an "
                             "edition named from a code table whose ids no longer match "
                             "(one dataset per run)")
    parser.add_argument("--allow-uncommitted-ftwd", action="store_true",
                        help="run with an ftwd that is not installed from a git commit (testing)")
    args = parser.parse_args(argv)
    if args.crop_names_by is not None and args.crop_names_from is None:
        parser.error("--crop-names-by needs --crop-names-from")
    if args.crop_names_by == "code" and len(args.dataset_ids) > 1:
        parser.error("--crop-names-by code takes one dataset per run")

    from build import _check_recipe
    from common import load_manifest

    from ftw_dataset_tools.api.source import installed_git_commit

    if installed_git_commit() is None and not args.allow_uncommitted_ftwd:
        parser.error("ftwd is not installed from a git commit, so the collections could not "
                     "record which ftwd added the columns (--allow-uncommitted-ftwd to test)")
    manifest = load_manifest()
    for dataset_id in args.dataset_ids:
        if not (dataset_dir(dataset_id) / "collection.json").is_file():
            parser.error(f"{dataset_id} is not published (no catalog/<source>/{dataset_id}/collection.json)")
        _check_recipe(dataset_id)
        if args.crop_names_from is not None:
            edition = harmonized_edition(dataset_id, args.crop_names_from)
            if not edition.is_file():
                parser.error(f"{dataset_id}: no harmonized edition at {edition}")
            why = unpublished_edition(edition, args.crop_names_from)
            if why:
                parser.error(f"{dataset_id}: {why}")
    from ftw_dataset_tools.api.crop_names import CropNameError

    refused = []
    for dataset_id in args.dataset_ids:
        try:
            backfill_dataset(
                dataset_id,
                workers=args.workers,
                manifest=manifest,
                crop_names_from=args.crop_names_from,
                crop_names_by=args.crop_names_by or "id",
            )
        except CropNameError as err:
            print(f"{dataset_id}: crop names refused, skipped (staging/{dataset_id} left as "
                  f"fetched): {err}", file=sys.stderr, flush=True)
            refused.append(dataset_id)
    if refused:
        print(f"crop names refused for {len(refused)} dataset(s): {', '.join(refused)}",
              file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
