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
dataset was built from, found at ``<dir>/<harmonized_id>/year=<year>/<stem>-<year>.parquet`` (the
harmonized catalog's staging, rebuilt with names). The join is by field id and refuses
any field whose crop:code differs there (ftwd ``api.crop_names``). Give the option on
every later run too: each run fetches the published field files again, and the backfill
record lists the steps of the latest run.
``--crop-names-by code`` names each field from its crop code instead, for an edition
named from a code table whose ids no longer match the benchmark's (fr_2024: IGN
replaced RPG 3.0 with RPG 4.0); it refuses a code with more than one name, and it takes
one dataset per run so no other dataset loses the per-field check by mistake.
es_2025 and es_po_2025 can only be named by code: their merge rewrote the ids (and the
regional gap parcels have no crop:code, so they stay unnamed).

The field assets' size, checksum and columns are always read from the staged files,
so the collection describes the files that will be uploaded either way. A run without
the option keeps the earlier run's crop-names record while the fetched field files
still carry crop:name. The names are joined first, into temp files that replace the
field files only when every join succeeded, so a dataset whose names are refused is
left as fetched (as published): it is reported and skipped, and the run carries on
with the others and exits 1.

The bucket is read at ``<source>/<id>/``; ``--read-flat`` reads the old flat
``<id>/`` instead, for the pass that moves a dataset into its source group.

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
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    CATALOG,
    ROOT,
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

# Top-level files the backfill reads. Everything under chips/ that is JSON is read too.
_TOP_LEVEL_ASSETS = ("chips", "fields", "fields_filtered", "boundary_lines")
# The files that carry each field's crop columns, so its crop names.
FIELD_ASSETS = ("fields", "fields_filtered", "boundary_lines")
# Read when published, so a rerun keeps it instead of recomputing hours of embeddings.
_OPTIONAL_ASSETS = ("field_embeddings",)
# Files the backfill writes itself, so they may differ from the bucket or be new.
_OUTPUTS = ("items.parquet", "{id}_field_embeddings.parquet")
_OUTPUT_DIRS = ("{id}_field_embeddings.parquet.partial",)
# The chips stage flags a rebuild needs to keep what the backfill adds.
RECIPE_STEPS = ("admin_names", "field_embeddings")


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
    dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG, read_flat: bool = False
) -> int:
    """Make ``staging/<id>`` hold what the backfill reads, as published. Returns files fetched.

    Reads ``<prefix>/<source>/<id>/``, or the old flat ``<prefix>/<id>/`` with ``read_flat``.
    """
    catalog_dir = dataset_dir(dataset_id, catalog=catalog)
    doc = read_json(catalog_dir / "collection.json")
    top_level = _asset_names(doc, _TOP_LEVEL_ASSETS)
    client = _client()
    remote_rel = dataset_id if read_flat else dataset_relpath(dataset_id, catalog=catalog)
    listing = _listing(client, remote_rel)
    missing = sorted(top_level - set(listing))
    if missing:
        raise SystemExit(f"{dataset_id}: not in the bucket: {', '.join(missing)}")
    top_level |= _asset_names(doc, _OPTIONAL_ASSETS) & set(listing)
    root = staging / dataset_id
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


def enable_recipe_steps(recipe: Path) -> bool:
    """Turn the backfilled steps on in a recipe, so a rebuild keeps them. True if edited.

    Edits the text under ``stages: chips:`` (comments stay), adding each missing flag
    and setting one found false to true.
    """
    lines = recipe.read_text().splitlines(keepends=True)
    try:
        at = next(i for i, line in enumerate(lines) if line.rstrip() == "  chips:")
    except StopIteration:
        raise SystemExit(f"{recipe}: no 'stages: chips:' block to turn the steps on in") from None
    end = next(
        (i for i in range(at + 1, len(lines))
         if lines[i].strip() and not lines[i].startswith("    ")),
        len(lines),
    )
    edited = False
    for step in RECIPE_STEPS:
        found = [i for i in range(at + 1, end) if lines[i].strip().startswith(f"{step}:")]
        if found:
            if lines[found[0]].split(":", 1)[1].strip() != "true":
                lines[found[0]] = f"    {step}: true\n"
                edited = True
            continue
        lines.insert(end, f"    {step}: true\n")
        end += 1
        edited = True
    if edited:
        recipe.write_text("".join(lines))
    return edited


def harmonized_edition(dataset_id: str, harmonized_staging: Path) -> Path:
    """The harmonized edition a dataset was built from, under ``harmonized_staging``."""
    import tracking

    r = tracking.row(dataset_id)
    year = r["year"]
    return (
        harmonized_staging / r["harmonized_id"] / f"year={year}"
        / f"{tracking.source_stem(r)}-{year}.parquet"
    )


def field_files(doc: dict, root: Path) -> dict[str, Path]:
    """The dataset's staged field files, by asset key."""
    return {
        key: root / str(doc["assets"][key]["href"]).removeprefix("./")
        for key in FIELD_ASSETS
        if key in doc["assets"]
    }


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


def earlier_crop_names(doc: dict, files: dict[str, Path]) -> dict | None:
    """The crop-names record of the last backfill, while the field files still have names."""
    import pyarrow.parquet as pq

    from ftw_dataset_tools.api.backfill import BACKFILL_KEY

    runs = (doc.get("ftw:config") or {}).get(BACKFILL_KEY) or []
    earlier = runs[-1].get("crop_names") if runs else None
    if not earlier or not files:
        return None
    if all("crop:name" in pq.read_schema(path).names for path in files.values()):
        return earlier
    return None


def backfill_dataset(
    dataset_id: str,
    *,
    workers: int,
    manifest: dict,
    staging: Path = STAGING,
    read_flat: bool = False,
    crop_names_from: Path | None = None,
    crop_names_by: str = "id",
) -> None:
    """Fetch, enrich and catalogize one published dataset."""
    from catalogize import catalogize

    from ftw_dataset_tools.api import admin_names, backfill, field_embeddings

    start = time.monotonic()
    fetched = fetch(dataset_id, staging=staging, read_flat=read_flat)
    root = staging / dataset_id
    collection_path = root / "collection.json"
    doc = read_json(collection_path)
    year = _year(doc)
    chips = root / str(doc["assets"]["chips"]["href"]).removeprefix("./")
    fields = root / str(doc["assets"]["fields"]["href"]).removeprefix("./")
    embeddings = root / f"{dataset_id}_field_embeddings.parquet"
    print(f"{dataset_id}: fetched {fetched:,} file(s)", flush=True)

    # First, so a refusal leaves staging as fetched (as published).
    files = field_files(doc, root)
    if crop_names_from is not None:
        source = harmonized_edition(dataset_id, crop_names_from)
        add_crop_names(dataset_id, files, source, crop_names_by)
        crop_names = {
            "source": source.relative_to(crop_names_from).as_posix(),
            "by": crop_names_by,
        }
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
        field_files=files,
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
    parser.add_argument("--read-flat", action="store_true",
                        help="read the bucket's old flat <id>/ folder (the move into source groups)")
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

    manifest = load_manifest()
    for dataset_id in args.dataset_ids:
        if not (dataset_dir(dataset_id) / "collection.json").is_file():
            parser.error(f"{dataset_id} is not published (no catalog/<source>/{dataset_id}/collection.json)")
        _check_recipe(dataset_id)
        if args.crop_names_from is not None:
            edition = harmonized_edition(dataset_id, args.crop_names_from)
            if not edition.is_file():
                parser.error(f"{dataset_id}: no harmonized edition at {edition}")
    from ftw_dataset_tools.api.source import installed_git_commit

    if installed_git_commit() is None and not args.allow_uncommitted_ftwd:
        parser.error("ftwd is not installed from a git commit, so the collections could not "
                     "record which ftwd added the columns (--allow-uncommitted-ftwd to test)")
    from ftw_dataset_tools.api.crop_names import CropNameError

    refused = []
    for dataset_id in args.dataset_ids:
        try:
            backfill_dataset(
                dataset_id,
                workers=args.workers,
                manifest=manifest,
                read_flat=args.read_flat,
                crop_names_from=args.crop_names_from,
                crop_names_by=args.crop_names_by or "id",
            )
        except CropNameError as err:
            print(f"{dataset_id}: crop names refused, skipped (staging/{dataset_id} left as "
                  f"fetched): {err}", file=sys.stderr, flush=True)
            refused.append(dataset_id)
            continue
        if enable_recipe_steps(ROOT / "datasets" / f"{dataset_id}.yaml"):
            print(f"{dataset_id}: turned on {', '.join(RECIPE_STEPS)} in its recipe", flush=True)
    if refused:
        print(f"crop names refused for {len(refused)} dataset(s): {', '.join(refused)}",
              file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
