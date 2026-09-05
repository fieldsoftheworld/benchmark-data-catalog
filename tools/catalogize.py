#!/usr/bin/env python3
"""Copy staging metadata into the published catalog, with published links.

``tools/build.py`` writes a self-contained Portolan collection into
``staging/<id>/``. This script takes the git-owned slice of that output
(``collection.json``, ``README.md``, ``AGENTS.md``, ``styles/*.json``,
``chips/*/catalog.json``) and republishes it under ``catalog/<id>/`` with
every ``root`` link pointed at the published root catalog instead of the
staging copy of ``collection.json``. It also rewrites ``items.parquet`` (which
stays in staging; it is data, uploaded by ``upload_data.py``, never
committed) so its links and asset hrefs are public URLs instead of
build-machine paths, enriches the collection with the host provider, a
version, an ``updated`` stamp, and the FTW 1.0 comparison, and — with
``--root`` — regenerates the root catalog's child links and the ``##
Collections`` tables in the root docs.

    uv run python tools/catalogize.py lu            # one dataset
    uv run python tools/catalogize.py lu --root      # + regenerate the root
    uv run python tools/catalogize.py --root         # root only (e.g. after
                                                      # removing a dataset)

Nothing here touches ``staging/<id>/chips/*/*/`` item directories or rasters;
those stay bucket-only, uploaded by ``tools/upload_data.py``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CATALOG, ROOT, STAGING, public_url, read_json, write_json  # noqa: E402

from ftw_dataset_tools.api.stac import PORTOLAN_SCHEMA_URI  # noqa: E402

# Files copied verbatim from staging/<id>/ to catalog/<id>/, plus the two glob
# patterns below (styles/*.json, chips/*/catalog.json). Everything else under
# staging/<id>/ is data: bucket-only, never committed.
COMMITTED = ("collection.json", "README.md", "AGENTS.md")

# An item id looks like ftw-<mgrs square><4-digit sequence>[_<year>]. The
# square is whatever sits between "ftw-" and the first run of 4 digits.
_SQUARE_RE = re.compile(r"^ftw-(?P<square>.+?)\d{4}(_|$)")

# The markers regenerate_root fills between, in catalog/README.md,
# catalog/AGENTS.md and catalog/llms.txt.
_MARK_START = "<!-- collections:start -->"
_MARK_END = "<!-- collections:end -->"

# The only document types rewrite_staging_items touches. Anything else under
# staging/<id>/chips/ is not ftwd's own output and is left alone.
_STAC_TYPES = {"Feature", "Catalog", "Collection"}


# --- copying the git-owned slice of staging into the catalog --------------


def _committed_relpaths(dataset_root: Path) -> list[Path]:
    """Relative paths under ``dataset_root`` that catalogize copies."""
    rels = [Path(name) for name in COMMITTED if (dataset_root / name).is_file()]
    rels += [p.relative_to(dataset_root) for p in sorted(dataset_root.glob("styles/*.json"))]
    rels += [p.relative_to(dataset_root) for p in sorted(dataset_root.glob("chips/*/catalog.json"))]
    return rels


def copy_committed(dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG) -> list[Path]:
    """Copy the git-owned metadata files from ``staging/<id>`` to ``catalog/<id>``.

    Returns the catalog-side paths written. Only ``COMMITTED`` and the two
    glob patterns (``styles/*.json``, ``chips/*/catalog.json``) are copied;
    item directories and every data file stay in staging.
    """
    src_root = staging / dataset_id
    dst_root = catalog / dataset_id
    written = []
    for rel in _committed_relpaths(src_root):
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((src_root / rel).read_bytes())
        written.append(dst)
    return written


# --- rewriting `root` links to point at the published root ----------------


def rewrite_root_links(doc: dict, depth: int) -> None:
    """Point every ``rel: root`` link in ``doc`` at the root catalog, in place.

    ``depth`` is how many directories ``doc``'s own location sits below the
    dataset directory (1 for ``collection.json``, 3 for a chips sub-catalog,
    4 for an item, 5 for an imagery child item) — equivalently, one more than
    the number of directories between the dataset root and this document.
    ``rel: self`` links are dropped everywhere; Portolan forbids them because
    a static catalog that hardcodes its own location cannot be mirrored.
    """
    href = "../" * depth + "catalog.json"
    links = []
    for link in doc.get("links", []):
        if link.get("rel") == "self":
            continue
        if link.get("rel") == "root":
            link = {**link, "href": href, "type": "application/json"}
        links.append(link)
    doc["links"] = links


def rewrite_staging_items(dataset_id: str, *, staging: Path = STAGING) -> list[Path]:
    """Rewrite `root` links under ``staging/<id>/chips/``, in place.

    Every JSON document under ``chips/`` — sub-catalogs, items, and imagery
    child items alike — sits at some depth below the dataset root, and
    ``rewrite_root_links`` is applied at exactly that depth. Sub-catalogs are
    also copied to ``catalog/`` by ``copy_committed``; rewriting them here
    first means the copy is already correct, so the git-owned-wins rule in
    ``upload_data.py`` skips a byte-identical staged copy rather than a
    differing one.

    A JSON file under ``chips/`` that is not a dict with a STAC ``type``
    (``Feature``, ``Catalog`` or ``Collection``) is not ftwd's own output and
    is skipped rather than rewritten or made to error; the number skipped is
    printed as a note.
    """
    chips_root = staging / dataset_id / "chips"
    touched = []
    skipped = 0
    if not chips_root.is_dir():
        return touched
    for path in sorted(chips_root.rglob("*.json")):
        doc = read_json(path)
        if not isinstance(doc, dict) or doc.get("type") not in _STAC_TYPES:
            skipped += 1
            continue
        rel = path.relative_to(staging / dataset_id)
        rewrite_root_links(doc, depth=len(rel.parts))
        write_json(path, doc)
        touched.append(path)
    if skipped:
        print(f"note   rewrite_staging_items: skipped {skipped} non-STAC JSON file(s) under {chips_root}")
    return touched


# --- rewriting items.parquet to public URLs --------------------------------


def _square_for_item(item_id: str, links: list[dict]) -> str:
    """The MGRS square an item belongs to, from its id or its parent link.

    Most ids match ``_SQUARE_RE`` directly. When one doesn't, the item's
    ``parent`` link (still an absolute build-machine path at this point)
    names the sub-catalog, and the sub-catalog's own directory is the
    square.
    """
    match = _SQUARE_RE.match(item_id)
    if match:
        return match.group("square")
    parent = next((link for link in links if link.get("rel") == "parent"), None)
    if parent is None:
        raise ValueError(f"cannot determine the square for item {item_id!r}: no parent link")
    return Path(parent["href"]).parent.name


def _rewrite_item_links(dataset_id: str, square: str, links: list[dict]) -> list[dict]:
    targets = {
        "root": public_url("catalog.json"),
        "collection": public_url(f"{dataset_id}/collection.json"),
        "parent": public_url(f"{dataset_id}/chips/{square}/catalog.json"),
    }
    new_links = []
    for link in links:
        rel = link.get("rel")
        if rel == "self":
            continue
        if rel in targets:
            link = {**link, "href": targets[rel]}
        new_links.append(link)
    return new_links


def _rewrite_item_assets(dataset_id: str, item_id: str, square: str, assets: dict) -> dict:
    """Rewrite every ``./file`` asset href to its public URL.

    ``assets`` is a struct-of-structs, the shape rustac writes: a fixed set
    of asset keys (e.g. ``instance_mask``) shared by every row, with a value
    of ``None`` where that row has no such asset. A ``None`` asset is passed
    through unchanged.
    """
    prefix = f"{dataset_id}/chips/{square}/{item_id}"
    new_assets = {}
    for key, asset in assets.items():
        href = (asset or {}).get("href", "")
        if href.startswith("./"):
            asset = {**asset, "href": public_url(f"{prefix}/{href[2:]}")}
        new_assets[key] = asset
    return new_assets


def _geoparquet_metadata(existing: dict | None, *, geometry_column: str = "geometry") -> dict:
    """Schema metadata with a GeoParquet 1.1 ``geo`` key added, everything else kept.

    rustac writes ``geometry`` as WKB with Parquet's own ``GEOMETRY`` logical
    type and no GeoParquet ``geo`` key; DuckDB reads that column as
    ``GEOMETRY('OGC:CRS84')`` on the strength of that logical type alone.
    pyarrow has no API for writing that logical type, so a plain
    ``pq.write_table`` of a table read back with pyarrow silently downgrades
    the column to a binary blob — confirmed against a real ``rustac``-written
    file, where DuckDB reports ``BLOB`` after such a round trip. Writing the
    ``geo`` key is the fix: any GeoParquet-aware reader, DuckDB included,
    recognizes the column as geometry from that key just as well as from the
    Parquet logical type. No ``crs`` entry means OGC:CRS84, which is what
    ftwd writes.
    """
    meta = dict(existing or {})
    meta[b"geo"] = json.dumps(
        {
            "version": "1.1.0",
            "primary_column": geometry_column,
            "columns": {geometry_column: {"encoding": "WKB", "geometry_types": []}},
        }
    ).encode()
    return meta


def rewrite_items_parquet(dataset_id: str, *, staging: Path = STAGING) -> Path:
    """Rewrite ``staging/<id>/items.parquet`` links and asset hrefs to public URLs.

    Reads the table, transforms the ``links`` and ``assets`` columns as plain
    Python objects, and writes back with the original schema — simpler and
    safer than reconstructing the file through DuckDB's ``COPY``. Existing
    schema metadata is kept, and a GeoParquet ``geo`` key is added (see
    ``_geoparquet_metadata``) so the ``geometry`` column stays recognizable
    as geometry after the pyarrow round trip.
    """
    path = staging / dataset_id / "items.parquet"
    table = pq.read_table(path)
    schema = table.schema

    ids = table.column("id").to_pylist()
    links_col = table.column("links").to_pylist()
    assets_col = table.column("assets").to_pylist()

    new_links, new_assets = [], []
    for item_id, links, assets in zip(ids, links_col, assets_col, strict=True):
        square = _square_for_item(item_id, links)
        new_links.append(_rewrite_item_links(dataset_id, square, links))
        new_assets.append(_rewrite_item_assets(dataset_id, item_id, square, assets))

    links_field = schema.field("links")
    assets_field = schema.field("assets")
    table = table.set_column(
        schema.get_field_index("links"), links_field, pa.array(new_links, type=links_field.type)
    )
    table = table.set_column(
        schema.get_field_index("assets"), assets_field, pa.array(new_assets, type=assets_field.type)
    )
    if "geometry" in schema.names:
        table = table.replace_schema_metadata(_geoparquet_metadata(schema.metadata))
    else:
        table = table.replace_schema_metadata(schema.metadata)

    pq.write_table(table, str(path))
    return path


# --- enriching the collection ----------------------------------------------


def _load_recipe(dataset_id: str) -> dict:
    import yaml

    return yaml.safe_load((ROOT / "datasets" / f"{dataset_id}.yaml").read_text())


def _now_iso(now: datetime | None) -> str:
    dt = now or datetime.now(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_host_provider(doc: dict, manifest: dict) -> None:
    providers = doc.setdefault("providers", [])
    if any("host" in (p.get("roles") or []) for p in providers):
        return
    host = manifest["host"]
    providers.append({"name": host["name"], "roles": list(host["roles"]), "url": host["url"]})


def _ensure_version(doc: dict, manifest: dict) -> None:
    if not doc.get("version"):
        doc["version"] = manifest["catalog"]["version"]


def _ensure_via(doc: dict, recipe: dict) -> None:
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "via" for link in links):
        return
    source_via = recipe.get("source_via")
    if source_via:
        links.append({"rel": "via", "href": source_via, "type": "application/json", "title": "Source collection"})


def _ensure_license_link(doc: dict, recipe: dict) -> None:
    if doc.get("license") != "other":
        return
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "license" for link in links):
        return
    license_url = (recipe.get("metadata") or {}).get("license_url")
    if license_url:
        links.append({"rel": "license", "href": license_url, "type": "text/html", "title": "License terms"})


def _chip_counts(chips_parquet: Path) -> dict[str, int]:
    """Total chips and the per-split count, from a chips parquet's ``split`` column."""
    con = duckdb.connect()
    total, train, val, test = con.execute(
        "SELECT count(*), "
        "count(*) FILTER (split = 'train'), "
        "count(*) FILTER (split = 'val'), "
        "count(*) FILTER (split = 'test') "
        "FROM read_parquet(?)",
        [str(chips_parquet)],
    ).fetchone()
    return {"total": total, "train": train, "val": val, "test": test}


def _row_count(parquet_path: Path) -> int:
    con = duckdb.connect()
    (count,) = con.execute("SELECT count(*) FROM read_parquet(?)", [str(parquet_path)]).fetchone()
    return count


def ftw1_section(dataset_id: str, spec: dict, *, staging: Path, recipe: dict) -> str:
    """The '## Compared with Fields of the World 1.0' section, or "" without an ftw1 block.

    Every number for *this* collection is measured, never typed in: chip and
    split counts come from ``<id>_chips.parquet``, the field count from
    ``<id>_fields.parquet``, and the edition year from the recipe's own
    description (``... (edition YYYY)``).
    """
    ftw1 = spec.get("ftw1")
    if not ftw1:
        return ""
    counts = _chip_counts(staging / dataset_id / f"{dataset_id}_chips.parquet")
    n_fields = _row_count(staging / dataset_id / f"{dataset_id}_fields.parquet")
    description = (recipe.get("metadata") or {}).get("description") or ""
    match = re.search(r"edition (\d{4})", description)
    edition_year = match.group(1) if match else "?"

    text = (
        f"Fields of the World 1.0 published `{spec['ftw1_name']}` with `{ftw1['chips']}` chips "
        f"(`{ftw1['train']}` train / `{ftw1['val']}` val / `{ftw1['test']}` test) cut from "
        f"`{ftw1['parcels']}` parcels declared for `{ftw1['year']}`, under `{ftw1['license']}`. "
        f"This collection has `{counts['total']}` chips "
        f"(`{counts['train']}`/`{counts['val']}`/`{counts['test']}`) cut from `{n_fields}` fields "
        f"declared for `{edition_year}`."
    )
    return f"\n## Compared with Fields of the World 1.0\n\n{text}\n"


def enrich_collection(
    dataset_id: str,
    *,
    catalog: Path,
    staging: Path,
    manifest: dict,
    recipe: dict,
    now: datetime | None = None,
) -> list[Path]:
    """Enrich the just-copied ``catalog/<id>/collection.json`` (and README.md).

    Fixes the collection's own ``root`` link (depth 1), appends the host
    provider once, fills in ``version`` and ``updated``, ensures a ``via``
    link and — for an "other" license — a ``license`` link exist, and, when
    the manifest carries an ``ftw1`` block for this dataset, appends the FTW
    1.0 comparison to README.md.
    """
    collection_path = catalog / dataset_id / "collection.json"
    doc = read_json(collection_path)
    rewrite_root_links(doc, depth=1)
    _append_host_provider(doc, manifest)
    _ensure_version(doc, manifest)
    _ensure_via(doc, recipe)
    _ensure_license_link(doc, recipe)
    doc["updated"] = _now_iso(now)
    write_json(collection_path, doc)
    written = [collection_path]

    spec = (manifest.get("datasets") or {}).get(dataset_id) or {}
    section = ftw1_section(dataset_id, spec, staging=staging, recipe=recipe)
    if section:
        readme_path = catalog / dataset_id / "README.md"
        text = readme_path.read_text()
        if not text.endswith("\n"):
            text += "\n"
        readme_path.write_text(text + section)
        written.append(readme_path)

    return written


# --- llms.txt for one collection -------------------------------------------


def write_llms(dataset_id: str, *, catalog: Path = CATALOG) -> Path:
    """Write ``catalog/<id>/llms.txt``: title, blurb, and public URLs of the metadata."""
    doc = read_json(catalog / dataset_id / "collection.json")
    title = doc.get("title", dataset_id)
    description = (doc.get("description") or "").strip().split(". ")[0].rstrip(".") + "."

    lines = [
        f"# {title}",
        "",
        f"> {description}",
        "",
        f"- [Collection]({public_url(f'{dataset_id}/collection.json')})",
        f"- [README]({public_url(f'{dataset_id}/README.md')})",
        f"- [Agent guide]({public_url(f'{dataset_id}/AGENTS.md')})",
    ]
    for key, asset in sorted((doc.get("assets") or {}).items()):
        href = asset.get("href", "")
        if not href.endswith((".parquet", ".pmtiles")):
            continue
        filename = href[2:] if href.startswith("./") else href
        title_ = asset.get("title", key)
        lines.append(f"- [{title_}]({public_url(f'{dataset_id}/{filename}')})")

    path = catalog / dataset_id / "llms.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


# --- the root catalog: child links and the marker-delimited tables --------


def _built_collections(catalog: Path) -> list[tuple[str, dict]]:
    return sorted(
        ((p.parent.name, read_json(p)) for p in catalog.glob("*/collection.json")),
        key=lambda pair: pair[0],
    )


def _child_links(collections: list[tuple[str, dict]]) -> list[dict]:
    return [
        {
            "rel": "child",
            "href": f"./{dataset_id}/collection.json",
            "type": "application/json",
            "title": doc.get("title", dataset_id),
        }
        for dataset_id, doc in collections
    ]


def _collection_row(dataset_id: str, doc: dict, *, staging: Path) -> dict:
    chips_path = staging / dataset_id / f"{dataset_id}_chips.parquet"
    counts = _chip_counts(chips_path) if chips_path.exists() else None
    return {
        "id": dataset_id,
        "title": doc.get("title", dataset_id),
        "chips": str(counts["total"]) if counts else "—",
        "splits": f"{counts['train']}/{counts['val']}/{counts['test']}" if counts else "—",
        "license": doc.get("license") or "—",
    }


def _collections_table(rows: list[dict]) -> str:
    if not rows:
        return ""
    header = "| ID | Title | Chips | Splits (train/val/test) | License | Link |\n"
    sep = "| --- | --- | --- | --- | --- | --- |\n"
    body = "".join(
        f"| {r['id']} | {r['title']} | {r['chips']} | {r['splits']} | {r['license']} "
        f"| [{r['id']}/]({r['id']}/) |\n"
        for r in rows
    )
    return header + sep + body


def _collections_list(rows: list[dict]) -> str:
    return "".join(
        f"- [{r['title']}]({r['id']}/collection.json): {r['chips']} chips "
        f"({r['splits']} train/val/test), {r['license']}\n"
        for r in rows
    )


def _replace_between_markers(path: Path, content: str) -> None:
    text = path.read_text()
    if _MARK_START not in text or _MARK_END not in text:
        raise ValueError(f"{path} is missing the {_MARK_START} / {_MARK_END} markers")
    before, _, rest = text.partition(_MARK_START)
    _, _, after = rest.partition(_MARK_END)
    middle = f"\n{content}" if content else "\n"
    path.write_text(f"{before}{_MARK_START}{middle}{_MARK_END}{after}")


def regenerate_root(manifest: dict, *, catalog: Path = CATALOG, staging: Path = STAGING) -> list[Path]:
    """Regenerate the root catalog's child links and the root docs' tables.

    Keeps every fixed link in ``catalog/catalog.json`` exactly as it is;
    rebuilds the ``child`` links, sorted by dataset id, and drops any
    ``rel: self`` link — Portolan forbids self links, and a hand-edit or an
    older ftwd is the only way one would appear here. Sets
    ``stac_extensions`` to the Portolan schema URI the pinned ftwd writes and
    ``version`` from the manifest. Fills the marker-delimited ``##
    Collections`` tables in ``catalog/README.md`` and ``catalog/AGENTS.md``,
    and the collection list in ``catalog/llms.txt``.
    """
    root_path = catalog / "catalog.json"
    doc = read_json(root_path)
    collections = _built_collections(catalog)

    doc["links"] = [
        link for link in doc["links"] if link.get("rel") not in ("child", "self")
    ] + _child_links(collections)
    doc["stac_extensions"] = [PORTOLAN_SCHEMA_URI]
    doc["version"] = manifest["catalog"]["version"]
    write_json(root_path, doc)

    rows = [_collection_row(dataset_id, coll, staging=staging) for dataset_id, coll in collections]
    table = _collections_table(rows)
    _replace_between_markers(catalog / "README.md", table)
    _replace_between_markers(catalog / "AGENTS.md", table)
    _replace_between_markers(catalog / "llms.txt", _collections_list(rows))

    return [root_path, catalog / "README.md", catalog / "AGENTS.md", catalog / "llms.txt"]


# --- the full pipeline for one dataset --------------------------------------


def catalogize(
    dataset_id: str,
    *,
    manifest: dict,
    staging: Path = STAGING,
    catalog: Path = CATALOG,
    now: datetime | None = None,
) -> list[Path]:
    """Copy ``staging/<id>``'s git-owned metadata into ``catalog/<id>``, published.

    Returns every file written under ``catalog/<id>/``. ``items.parquet`` is
    rewritten too, but stays in ``staging/<id>/`` (it is data, never
    committed), so it is not part of the returned list.
    """
    recipe = _load_recipe(dataset_id)

    rewrite_staging_items(dataset_id, staging=staging)
    rewrite_items_parquet(dataset_id, staging=staging)

    written = copy_committed(dataset_id, staging=staging, catalog=catalog)
    written += enrich_collection(
        dataset_id, catalog=catalog, staging=staging, manifest=manifest, recipe=recipe, now=now
    )
    written.append(write_llms(dataset_id, catalog=catalog))

    return list(dict.fromkeys(written))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy staging/<id>'s git-owned metadata into catalog/<id>, published.",
    )
    parser.add_argument("dataset_id", nargs="?", help="dataset id, e.g. 'lu' (see datasets.yaml)")
    parser.add_argument(
        "--root", action="store_true", help="also regenerate the root catalog and its docs"
    )
    args = parser.parse_args(argv)
    if not args.dataset_id and not args.root:
        parser.error("a dataset_id is required unless --root is given alone")

    from common import load_manifest

    manifest = load_manifest()
    written: list[Path] = []
    if args.dataset_id:
        written += catalogize(args.dataset_id, manifest=manifest)
    if args.root:
        written += regenerate_root(manifest)

    for path in written:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
