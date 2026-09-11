#!/usr/bin/env python3
"""Copy staging metadata into the published catalog, with published links.

``tools/build.py`` writes a self-contained Portolan collection into
``staging/<id>/``. This script takes the git-owned slice of that output
(``collection.json``, ``README.md``, ``AGENTS.md``, ``styles/*.json``,
``chips/*/catalog.json``) and republishes it under ``catalog/<id>/`` with
every ``root`` link pointed at the published root catalog instead of the
staging copy of ``collection.json``. It also rebuilds ``items.parquet`` (which
stays in staging; it is data, uploaded by ``upload_data.py``, never
committed) from the item JSON on disk, so that it covers the imagery child
items too and its links and asset hrefs are public URLs instead of
build-machine paths, enriches the collection with the host provider, a
version, an ``updated`` stamp, and the FTW 1.0 comparison, post-processes the
collection's ``README.md`` and ``AGENTS.md`` for publication (``enrich_readme``:
a named source link, a "Browse" block, and every relative link made absolute —
source.coop renders these files where a relative link cannot resolve), and —
with ``--root`` — regenerates the root catalog's child links and the ``##
Collections`` tables in the root docs.

    uv run python tools/catalogize.py lu            # one dataset
    uv run python tools/catalogize.py lu --root      # + regenerate the root
    uv run python tools/catalogize.py --root         # root only (e.g. after
                                                      # removing a dataset)

Item JSON under ``staging/<id>/chips/*/*/`` is read and its ``root`` links
rewritten in place, but no item directory and no raster is ever copied into
``catalog/``; those stay bucket-only, uploaded by ``tools/upload_data.py``.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen

import duckdb
import pyarrow.parquet as pq
import rustac

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build import _check_recipe as _check_dataset_recipe  # noqa: E402
from common import (  # noqa: E402
    CATALOG,
    PUBLIC_BASE,
    ROOT,
    STAGING,
    public_url,
    read_json,
    write_json,
)

from ftw_dataset_tools.api.stac import PORTOLAN_SCHEMA_URI  # noqa: E402

# The STAC version extension, required (PTL-CNF-003) whenever a document uses
# a top-level `version` property.
VERSION_EXTENSION_URI = "https://stac-extensions.github.io/version/v1.2.0/schema.json"

# The web-map-links extension, required (PTL-VIZ-003) whenever a collection
# carries a rel:'pmtiles' link.
_WEB_MAP_LINKS_PREFIX = "https://stac-extensions.github.io/web-map-links/"
WEB_MAP_LINKS_URI = f"{_WEB_MAP_LINKS_PREFIX}v1.3.0/schema.json"

# Files copied verbatim from staging/<id>/ to catalog/<id>/, plus the two glob
# patterns below (styles/*.json, chips/*/catalog.json). Everything else under
# staging/<id>/ is data: bucket-only, never committed.
COMMITTED = ("collection.json", "README.md", "AGENTS.md")

# The markers regenerate_root fills between, in catalog/README.md,
# catalog/AGENTS.md and catalog/llms.txt.
_MARK_START = "<!-- collections:start -->"
_MARK_END = "<!-- collections:end -->"

# The markers enrich_readme's "Browse" block sits between, in every
# catalog/<id>/README.md, so a rerun replaces the block instead of stacking
# another copy of it under the description.
_BROWSE_START = "<!-- browse:start -->"
_BROWSE_END = "<!-- browse:end -->"

# The Portolan data browser renders any publicly readable STAC document; the
# path it takes is that document's public URL with the scheme stripped.
BROWSER_BASE = "https://browser.portolan-sdi.org/#/external/"

# Where an SPDX license id is documented, for the root table's License column.
SPDX_BASE = "https://spdx.org/licenses/"

# How wide the root table's thumbnails render, in CSS pixels. Markdown image
# syntax carries no size, so a renderer draws the file at its native 1024x683
# and one row fills a screen. source.coop renders inline HTML in a README —
# verified against planet/eu-field-boundaries, whose README's
# `<img ... width="100%"/>` reaches the page as a real <img> element with its
# width attribute intact — so the cell is written as an <img> tag instead.
# 120 px keeps the 3:2 thumbnail 80 px tall, one scannable table row.
THUMBNAIL_WIDTH_PX = 120

# Sent when reading a source collection's title over HTTPS: an anonymous
# request with no User-Agent is refused by some CDNs.
_USER_AGENT = "benchmark-data-catalog (+https://github.com/fieldsoftheworld/benchmark-data-catalog)"

# How long enrich_readme waits on the harmonized collection.json before
# falling back to the offline title. A build must not hang on a slow host.
_FETCH_TIMEOUT = 10.0

# The only document types rewrite_staging_items touches. Anything else under
# staging/<id>/chips/ is not ftwd's own output and is left alone.
_STAC_TYPES = {"Feature", "Catalog", "Collection"}

# A `source_via` pointing at a harmonized-collection JSON endpoint on
# data.source.coop, matched so PTL-PRO-001's via link can be rewritten to the
# human-readable page at the equivalent source.coop path.
_DATA_SOURCE_COOP_RE = re.compile(
    r"^https://data\.source\.coop/(?P<org>[^/]+)/(?P<repo>[^/]+)/(?P<id>[^/]+)/collection\.json$"
)


# --- published URLs: raw files, human pages, the data browser -------------


def browser_url(rel: str) -> str:
    """The Portolan data browser URL for the published document at ``rel``.

    The browser's ``#/external/`` route takes a host-plus-path, so this is
    ``public_url(rel)`` with its scheme stripped. Never hard-codes the host:
    the path comes from ``catalog.publish.yaml`` like every other public URL.
    """
    return BROWSER_BASE + public_url(rel).split("://", 1)[-1]


def human_url(manifest: dict, rel: str = "") -> str:
    """The human-readable catalog page for ``rel``, from ``catalog.human_base``.

    ``data.source.coop`` serves bytes; ``source.coop`` serves the pages a
    person reads. Docs link people at the second and raw files at the first.
    Falls back to the public base only when a manifest carries no
    ``human_base`` (``tests/test_manifest.py`` requires one in the real
    manifest, so that is a fixture-only path).
    """
    base = ((manifest.get("catalog") or {}).get("human_base") or PUBLIC_BASE).rstrip("/")
    return f"{base}/{rel}" if rel else base


def harmonized_source(recipe: dict) -> tuple[str, str] | None:
    """``(human page, collection.json)`` for the recipe's harmonized source.

    ``source_via`` names the harmonized collection's JSON endpoint on
    data.source.coop; the human page is the same org/repo/id path on
    source.coop. None when the recipe points somewhere else entirely, in
    which case the README's provenance line is left as ftwd wrote it.
    """
    source_via = recipe.get("source_via") or ""
    match = _DATA_SOURCE_COOP_RE.match(source_via)
    if not match:
        return None
    return "https://source.coop/{org}/{repo}/{id}".format(**match.groupdict()), source_via


def fetch_collection_title(url: str, *, timeout: float = _FETCH_TIMEOUT) -> str | None:
    """The ``title`` of the STAC collection served at ``url``, or None.

    Any failure — offline, DNS, a 404, a timeout, JSON that is not a
    collection — returns None with a note printed, so a build without network
    access still produces a README (with the caller's offline fallback title)
    instead of dying on a documentation link.
    """
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 (https, from the recipe)
            doc = json.loads(response.read().decode())
    except Exception as exc:
        print(f"note   could not read {url} ({exc}); using the offline source title")
        return None
    title = doc.get("title") if isinstance(doc, dict) else None
    return title or None


# --- copying the git-owned slice of staging into the catalog --------------


def _committed_relpaths(dataset_root: Path) -> list[Path]:
    """Relative paths under ``dataset_root`` that catalogize copies."""
    rels = [Path(name) for name in COMMITTED if (dataset_root / name).is_file()]
    rels += [p.relative_to(dataset_root) for p in sorted(dataset_root.glob("styles/*.json"))]
    rels += [p.relative_to(dataset_root) for p in sorted(dataset_root.glob("chips/*/catalog.json"))]
    return rels


def _thumbnail_asset(doc: dict) -> tuple[str, dict] | None:
    """The ``(key, asset)`` pair with role ``thumbnail``, if any."""
    for key, asset in (doc.get("assets") or {}).items():
        if "thumbnail" in (asset.get("roles") or []):
            return key, asset
    return None


def _copy_collection_preserving_thumbnail(src: Path, dst: Path) -> None:
    """Copy ``collection.json``, carrying over an existing thumbnail asset.

    ``tools/thumbnail.py`` adds a ``role: thumbnail`` asset straight to the
    published ``catalog/<id>/collection.json`` — staging's copy never has
    one. A plain overwrite here would silently drop that asset on every
    ``catalogize`` rerun, so when the catalog copy already carries a
    thumbnail and the fresh staging copy does not, it is carried forward.
    """
    doc = read_json(src)
    if dst.is_file():
        existing_thumbnail = _thumbnail_asset(read_json(dst))
        if existing_thumbnail and not _thumbnail_asset(doc):
            key, asset = existing_thumbnail
            doc.setdefault("assets", {})[key] = asset
    write_json(dst, doc)


def copy_committed(dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG) -> list[Path]:
    """Copy the git-owned metadata files from ``staging/<id>`` to ``catalog/<id>``.

    Returns the catalog-side paths written. Only ``COMMITTED`` and the two
    glob patterns (``styles/*.json``, ``chips/*/catalog.json``) are copied;
    item directories and every data file stay in staging. ``collection.json``
    is special-cased to preserve an existing thumbnail asset — see
    ``_copy_collection_preserving_thumbnail``.
    """
    src_root = staging / dataset_id
    dst_root = catalog / dataset_id
    written = []
    for rel in _committed_relpaths(src_root):
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel == Path("collection.json"):
            _copy_collection_preserving_thumbnail(src_root / rel, dst)
        else:
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

    The replacement root link is built explicitly with only ``rel``, ``href``
    and ``type`` — ftwd writes the root link as a self-reference carrying the
    collection's own ``title``, and a naive ``{**link, ...}`` merge would
    carry that title forward onto every document in the tree, mislabeling
    the root catalog with e.g. the collection's title in any client that
    renders link titles.
    """
    href = "../" * depth + "catalog.json"
    links = []
    for link in doc.get("links", []):
        if link.get("rel") == "self":
            continue
        if link.get("rel") == "root":
            link = {"rel": "root", "href": href, "type": "application/json"}
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


# --- rebuilding items.parquet from the item JSON, with public URLs ---------


def _rewrite_item_links(
    dataset_id: str, square: str, links: list[dict], item_dir: str | None = None
) -> list[dict]:
    """Structural links go to the published root/collection/sub-catalog.

    Any other relative link (``./x.json`` — a chip's ``ftw:planting`` /
    ``ftw:harvest`` season items, a season item's ``ftw:parent_chip``) is made
    absolute against the item's directory, because a parquet row has no base
    to resolve a relative href against.
    """
    targets = {
        "root": public_url("catalog.json"),
        "collection": public_url(f"{dataset_id}/collection.json"),
        "parent": public_url(f"{dataset_id}/chips/{square}/catalog.json"),
    }
    new_links = []
    for link in links:
        rel = link.get("rel")
        href = link.get("href", "")
        if rel == "self":
            continue
        if rel in targets:
            link = {**link, "href": targets[rel]}
        elif item_dir and href.startswith("./"):
            link = {**link, "href": public_url(f"{dataset_id}/chips/{square}/{item_dir}/{href[2:]}")}
        new_links.append(link)
    return new_links


def _rewrite_item_assets(dataset_id: str, item_dir: str, square: str, assets: dict) -> dict:
    """Rewrite every ``./file`` asset href to its public URL.

    ``item_dir`` is the *directory* the item's JSON sits in, not the item id:
    an imagery child item (``<chip>_planting_s2``) lives inside its chip's
    directory (``<chip>/``) and its ``./file`` assets resolve against that,
    so keying the prefix on the id would point every child asset at a
    directory that does not exist.

    A ``None`` asset is passed through unchanged, so this is also safe on the
    struct-of-structs shape a stac-geoparquet reader hands back (a fixed set
    of asset keys shared by every row, ``None`` where a row has no such
    asset).
    """
    prefix = f"{dataset_id}/chips/{square}/{item_dir}"
    new_assets = {}
    for key, asset in assets.items():
        href = (asset or {}).get("href", "")
        if href.startswith("./"):
            asset = {**asset, "href": public_url(f"{prefix}/{href[2:]}")}
        new_assets[key] = asset
    return new_assets


def _geoparquet_metadata(
    existing: dict | None, *, geometry_column: str = "geometry", has_bbox: bool = False
) -> dict:
    """Schema metadata with a GeoParquet 1.1 ``geo`` key added, everything else kept.

    The fallback for a writer that leaves no ``geo`` key of its own — see
    ``_ensure_geoparquet_metadata``, which only calls this when the file
    needs it. Any GeoParquet-aware reader, DuckDB included, recognizes the
    column as geometry from that key. No ``crs`` entry means OGC:CRS84,
    which is what ftwd writes.

    ``has_bbox`` adds a GeoParquet 1.1 ``covering`` entry pointing at the
    table's own ``bbox`` struct column, so a reader can prune row groups from
    that column instead of decoding ``geometry``. Only set when the table
    actually carries a ``bbox`` struct column with ``xmin``/``ymin``/``xmax``/
    ``ymax`` fields (ftwd's own shape).
    """
    column_meta: dict = {"encoding": "WKB", "geometry_types": []}
    if has_bbox:
        column_meta["covering"] = {
            "bbox": {
                "xmin": ["bbox", "xmin"],
                "ymin": ["bbox", "ymin"],
                "xmax": ["bbox", "xmax"],
                "ymax": ["bbox", "ymax"],
            }
        }
    meta = dict(existing or {})
    meta[b"geo"] = json.dumps(
        {
            "version": "1.1.0",
            "primary_column": geometry_column,
            "columns": {geometry_column: column_meta},
        }
    ).encode()
    return meta


def _ensure_geoparquet_metadata(path: Path) -> bool:
    """Guarantee ``path``'s ``geometry`` column reads back as GEOMETRY, not BLOB.

    rustac writes a GeoParquet 1.1 ``geo`` key of its own (with a ``covering``
    entry for the ``bbox`` struct column), and DuckDB reads the column as
    ``GEOMETRY('OGC:CRS84')`` on the strength of it — so the normal case here
    is to verify and keep what the writer produced, rewriting nothing.

    Only when a file has a ``geometry`` column and *no* ``geo`` key is it
    rewritten through pyarrow with one added (``_geoparquet_metadata``);
    without that key a GeoParquet-unaware reader sees a plain binary blob.
    Note that the check reads the Parquet file's own key/value metadata
    rather than ``table.schema.metadata``: when a file carries an
    ``ARROW:schema`` key — rustac's do — pyarrow rebuilds the schema from it
    and the ``geo`` key never surfaces as schema metadata at all.

    Returns True when the file was rewritten.
    """
    if b"geo" in (pq.ParquetFile(path).metadata.metadata or {}):
        return False
    table = pq.read_table(path)
    if "geometry" not in table.schema.names:
        return False
    table = table.replace_schema_metadata(
        _geoparquet_metadata(table.schema.metadata, has_bbox="bbox" in table.schema.names)
    )
    pq.write_table(table, str(path))
    return True


def _item_documents(dataset_id: str, chips_root: Path) -> list[dict]:
    """Every item under ``chips_root``, links and asset hrefs made public.

    Walks ``chips/<square>/<chip>/*.json`` and keeps each STAC ``Feature`` —
    the chip items and the imagery child items alongside them — in a
    deterministic order: by square, then chip id, then file name, which is
    exactly sorted path order. Sub-catalogs and any non-STAC JSON are
    skipped.

    Each document's ``root``/``collection``/``parent`` links and its
    relative asset hrefs become absolute public URLs; ``self`` is dropped and
    an already-absolute href (a child item's ``via`` link, or the Earth
    Search scene assets it points at) is left alone. The square and the chip
    directory both come from the path, so a child item's assets resolve
    against its chip's directory rather than its own id.
    """
    items = []
    for path in sorted(chips_root.rglob("*.json")):
        doc = read_json(path)
        if not isinstance(doc, dict) or doc.get("type") != "Feature":
            continue
        rel = path.relative_to(chips_root)
        if len(rel.parts) < 3:
            continue
        square, item_dir = rel.parts[0], rel.parts[1]
        doc["links"] = _rewrite_item_links(
            dataset_id, square, doc.get("links") or [], item_dir=item_dir
        )
        doc["assets"] = _rewrite_item_assets(dataset_id, item_dir, square, doc.get("assets") or {})
        items.append(doc)
    return items


def rewrite_items_parquet(dataset_id: str, *, staging: Path = STAGING) -> Path:
    """Rebuild ``staging/<id>/items.parquet`` from the item JSON on disk.

    The mirror ftwd's ``stac`` stage writes is a snapshot of the chip items
    as they stood *before* the imagery pass: it has none of the season child
    items, and the chip items in it carry their pre-imagery assets. Patching
    that file could never add the missing rows, so the mirror is rebuilt from
    scratch out of every ``Feature`` JSON under ``staging/<id>/chips/``
    (``_item_documents``) and written back as stac-geoparquet with
    ``rustac``, the same writer ftwd itself uses.

    Writes to a temporary file in the same directory and ``os.replace``s it
    over ``items.parquet`` at the end, so a process killed mid-write leaves
    the original file intact instead of a truncated, corrupt one. The
    temporary name has no ``.parquet`` extension for rustac to infer a format
    from, hence the explicit ``format``.
    """
    path = staging / dataset_id / "items.parquet"
    items = _item_documents(dataset_id, staging / dataset_id / "chips")
    if not items:
        sys.exit(
            f"no item JSON found under {staging / dataset_id / 'chips'}; run: "
            f"uv run python tools/build.py {dataset_id} --through stac"
        )

    tmp_path = path.with_name(path.name + ".tmp")
    try:
        rustac.write_sync(str(tmp_path), items, format="parquet")
        _ensure_geoparquet_metadata(tmp_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    os.replace(tmp_path, path)
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


def _add_stac_extension(doc: dict, uri: str) -> None:
    """Append ``uri`` to ``stac_extensions`` idempotently."""
    extensions = doc.setdefault("stac_extensions", [])
    if uri not in extensions:
        extensions.append(uri)


def _ensure_version(doc: dict, manifest: dict) -> None:
    """Set ``version`` from the manifest when absent, declaring the version extension too.

    PTL-CNF-003 requires the version extension URI in ``stac_extensions``
    wherever a document carries a top-level ``version`` — the same constant
    ``regenerate_root`` declares for the root catalog.
    """
    if not doc.get("version"):
        doc["version"] = manifest["catalog"]["version"]
        _add_stac_extension(doc, VERSION_EXTENSION_URI)


def _ensure_via(doc: dict, recipe: dict) -> None:
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "via" for link in links):
        return
    source_via = recipe.get("source_via")
    if source_via:
        links.append({"rel": "via", "href": source_via, "type": "application/json", "title": "Source collection"})


def _rewrite_via_link(doc: dict) -> None:
    """PTL-PRO-001: a ``via`` link must have type ``text/html``, a browsable page.

    Recipes point ``source_via`` at the harmonized collection's JSON endpoint
    on data.source.coop, not a page. When the href matches that exact shape,
    it is rewritten to the human-readable page at the equivalent
    ``source.coop/<org>/<repo>/<id>`` path; any other via href is left as is
    apart from the type. Idempotent: a href already rewritten to the
    source.coop page no longer matches the data.source.coop pattern, so a
    second run only re-confirms the type.
    """
    links = doc.get("links", [])
    for i, link in enumerate(links):
        if link.get("rel") != "via":
            continue
        match = _DATA_SOURCE_COOP_RE.match(link.get("href", ""))
        if match:
            links[i] = {
                **link,
                "href": "https://source.coop/{org}/{repo}/{id}".format(**match.groupdict()),
                "type": "text/html",
                "title": "Source field boundary collection",
            }
        else:
            links[i] = {**link, "type": "text/html"}


def _ensure_parent_link(doc: dict) -> None:
    """PTL-LNK-001: the collection needs a ``rel: parent`` link to the root catalog."""
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "parent" for link in links):
        return
    links.append({"rel": "parent", "href": "../catalog.json", "type": "application/json"})


def _ensure_llms_link(doc: dict) -> None:
    """The collection needs a ``rel: llms`` link so agents can find its ``llms.txt``.

    ``write_llms`` writes ``catalog/<id>/llms.txt`` but nothing links to it
    from the collection, so an agent walking the catalog by link traversal
    alone never finds it. Idempotent by ``rel``.
    """
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "llms" for link in links):
        return
    links.append({"rel": "llms", "href": "./llms.txt", "type": "text/plain", "title": "llms.txt"})


def _ensure_pmtiles_links(doc: dict) -> None:
    """PTL-VIZ-003: every PMTiles asset also needs a matching ``rel: pmtiles`` link.

    The link also needs a ``pmtiles:layers`` array of the default-visible
    vector tile layers. ftwd names a PMTiles asset ``<layer>_tiles`` (e.g.
    ``chips_tiles`` for the ``chips`` layer, confirmed against the
    ``source-layer`` a real style file references), so the layer name is
    derived from the asset key. Once any ``rel: pmtiles`` link exists, the
    web-map-links extension it requires is declared in ``stac_extensions``.
    Idempotent by ``(rel, href)``: rerunning never adds a second link for the
    same PMTiles asset, nor a duplicate extension entry.
    """
    links = doc.setdefault("links", [])
    existing = {(link.get("rel"), link.get("href")) for link in links}
    for key, asset in (doc.get("assets") or {}).items():
        if asset.get("type") != "application/vnd.pmtiles":
            continue
        href = asset.get("href")
        if ("pmtiles", href) in existing:
            continue
        layer = key[: -len("_tiles")] if key.endswith("_tiles") else key
        links.append(
            {
                "rel": "pmtiles",
                "href": href,
                "type": "application/vnd.pmtiles",
                "title": asset.get("title"),
                "pmtiles:layers": [layer],
            }
        )
        existing.add(("pmtiles", href))

    if any(link.get("rel") == "pmtiles" for link in links):
        extensions = doc.setdefault("stac_extensions", [])
        if not any(isinstance(ext, str) and ext.startswith(_WEB_MAP_LINKS_PREFIX) for ext in extensions):
            extensions.append(WEB_MAP_LINKS_URI)


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


def _fields_parquet(dataset_dir: Path) -> Path | None:
    """The field polygons the chips and masks were actually cut from.

    The class-filtered set when a ``class_filter`` was configured (ftwd writes
    ``<id>_fields_filtered.parquet`` then), otherwise the full reprojected
    set. None when neither is on disk — a CI checkout, or a staging tree
    pruned after publication.
    """
    dataset_id = dataset_dir.name
    for name in (f"{dataset_id}_fields_filtered.parquet", f"{dataset_id}_fields.parquet"):
        path = dataset_dir / name
        if path.exists():
            return path
    return None


def _field_count(dataset_dir: Path) -> int | None:
    """How many field polygons this collection was cut from, or None."""
    path = _fields_parquet(dataset_dir)
    return _row_count(path) if path else None


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
    n_fields = _row_count(_fields_parquet(staging / dataset_id))
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


def _refresh_asset_sizes(doc: dict, staging_dir: Path) -> int:
    """Re-read ``file:size`` for every relative asset that exists in staging.

    ftwd stamps ``file:size`` when it writes the collection, but catalogize
    rebuilds ``items.parquet`` afterwards (parents plus imagery children), so
    the mirror's declared size went stale and a live check compared it
    against the served Content-Length. Returns how many sizes changed.
    """
    changed = 0
    for asset in (doc.get("assets") or {}).values():
        href = asset.get("href", "")
        if not href.startswith("./"):
            continue
        local = staging_dir / href[2:]
        if not local.is_file():
            continue
        size = local.stat().st_size
        if asset.get("file:size") != size:
            asset["file:size"] = size
            changed += 1
    return changed


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

    Fixes the collection's own ``root`` link (depth 1), adds a ``parent``
    link to the root catalog and a ``llms`` link to its own ``llms.txt``,
    appends the host provider once, fills in ``version`` and ``updated``,
    ensures a ``via`` link (rewritten to a browsable page, PTL-PRO-001) and
    — for an "other" license — a ``license`` link exist, registers a
    ``rel: pmtiles`` link for every PMTiles asset (PTL-VIZ-003), and, when
    the manifest carries an ``ftw1`` block for this dataset, appends the FTW
    1.0 comparison to README.md.
    """
    collection_path = catalog / dataset_id / "collection.json"
    doc = read_json(collection_path)
    rewrite_root_links(doc, depth=1)
    _ensure_parent_link(doc)
    _ensure_llms_link(doc)
    _append_host_provider(doc, manifest)
    _ensure_version(doc, manifest)
    _ensure_via(doc, recipe)
    _rewrite_via_link(doc)
    _ensure_license_link(doc, recipe)
    _ensure_pmtiles_links(doc)
    _refresh_asset_sizes(doc, staging / dataset_id)
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


# --- post-processing the collection's README.md and AGENTS.md --------------

# The provenance line ftwd writes, pointing at the harmonized collection's
# JSON endpoint. enrich_readme replaces it with a line that names the source
# collection and links the page a person can actually read.
_DERIVED_FROM_RE = re.compile(
    r"^- Derived from \[[^\]]*\]\((?P<href>https://data\.source\.coop/\S+/collection\.json)\)[ \t]*$",
    re.MULTILINE,
)

# A markdown link or image. The target must be whitespace-free, which is
# every link ftwd writes; a `[x](url "title")` form is left alone rather than
# half-rewritten.
_MD_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")


def _absolute_target(target: str, *, base_rel: str, manifest: dict) -> str:
    """One markdown link target, made absolute against the published catalog.

    A relative target is resolved against ``base_rel`` (the document's own
    directory inside the catalog, e.g. ``lu``) and then published: markdown
    goes to the human page on source.coop, everything else to the raw file on
    data.source.coop. Already-absolute targets, fragments and ``mailto:``
    are returned untouched.
    """
    if "://" in target or target.startswith(("#", "mailto:")):
        return target
    path, sep, fragment = target.partition("#")
    if not path:
        return target
    rel = posixpath.normpath(posixpath.join(base_rel, path))
    url = human_url(manifest, rel) if rel.endswith(".md") else public_url(rel)
    return url + sep + fragment


def absolutize_links(text: str, *, base_rel: str, manifest: dict) -> str:
    """Rewrite every relative markdown link in ``text`` to a published URL.

    source.coop renders a README at a path that is not the file's own
    directory, so a relative link (``[AGENTS.md](AGENTS.md)``, ``[at/](at/)``)
    resolves against the wrong base and 404s. Every link in a published
    document is therefore absolute. Idempotent: an absolute target is left
    exactly as it is.
    """

    def replace(match: re.Match) -> str:
        bang, label, target = match.groups()
        return f"{bang}[{label}]({_absolute_target(target, base_rel=base_rel, manifest=manifest)})"

    return _MD_LINK_RE.sub(replace, text)


def _source_data_line(title: str, human: str, stac: str) -> str:
    return (
        f"- Source data: [{title}]({human}) (harmonized field boundaries; "
        f"STAC [collection.json]({stac}))"
    )


def _replace_derived_from(text: str, *, recipe: dict, collection_title: str, fetch_title) -> str:
    """Replace ftwd's "Derived from <json endpoint>" line with a readable one.

    Names the harmonized collection (its own ``title``, read over HTTPS) and
    links the human page, keeping the JSON endpoint as a secondary link for
    machines. Offline, the title falls back to "Harmonized field boundaries
    for <collection title>" so the line is still accurate and the build still
    finishes. A README already carrying the replacement no longer matches, so
    a rerun changes nothing.
    """
    if not _DERIVED_FROM_RE.search(text):
        return text
    source = harmonized_source(recipe)
    if not source:
        return text
    human, stac = source
    title = fetch_title(stac) or f"Harmonized field boundaries for {collection_title}"
    return _DERIVED_FROM_RE.sub(lambda _m: _source_data_line(title, human, stac), text, count=1)


def _browse_block(dataset_id: str, title: str, *, manifest: dict, has_thumbnail: bool) -> str:
    """The marker-delimited "Browse" block: the thumbnail, then the three ways in."""
    lines = [_BROWSE_START]
    if has_thumbnail:
        lines += [f"![{title} thumbnail]({public_url(f'{dataset_id}/thumbnail.webp')})", ""]
    lines.append(
        f"Open this collection in the [data browser]({browser_url(f'{dataset_id}/collection.json')}), "
        f"read the [agent guide]({human_url(manifest, f'{dataset_id}/AGENTS.md')}), or query "
        f"[items.parquet]({public_url(f'{dataset_id}/items.parquet')}) directly."
    )
    lines.append(_BROWSE_END)
    return "\n".join(lines)


def _description_end(lines: list[str]) -> int:
    """Index of the line just past the H1 and the description paragraph under it.

    0 when the document has no H1 at all, which puts the block at the very
    top rather than dropping it.
    """
    start = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if start is None:
        return 0
    index = start + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    while index < len(lines) and lines[index].strip() and not lines[index].startswith("#"):
        index += 1
    return index


def _insert_browse_block(text: str, block: str) -> str:
    """Put ``block`` right after the H1's description paragraph, exactly once.

    Idempotent by the ``browse`` markers: once a README carries them, the
    block between them is replaced in place, wherever it sits.
    """
    if _BROWSE_START in text and _BROWSE_END in text:
        before, _, rest = text.partition(_BROWSE_START)
        _, _, after = rest.partition(_BROWSE_END)
        return before + block + after
    lines = text.split("\n")
    index = _description_end(lines)
    return "\n".join(lines[:index] + ["", block] + lines[index:])


def _insert_after_heading(text: str, heading: str, line: str) -> str:
    """Insert ``line`` as the first paragraph under ``heading``, once.

    A no-op when the line is already there (so a rerun adds nothing) or when
    the heading is absent (so a differently shaped document is left alone).
    """
    if line in text:
        return text
    lines = text.split("\n")
    for i, current in enumerate(lines):
        if current.strip() == heading:
            return "\n".join(lines[: i + 1] + ["", line] + lines[i + 1 :])
    return text


def enrich_readme(
    dataset_id: str,
    *,
    catalog: Path = CATALOG,
    manifest: dict,
    recipe: dict,
    fetch_title=fetch_collection_title,
) -> list[Path]:
    """Post-process the docs ftwd wrote for one collection, for publication.

    ftwd writes ``README.md`` and ``AGENTS.md`` for a collection sitting on a
    build machine; this makes them publishable:

    - the provenance line naming the source becomes a link to the harmonized
      collection's own page (``_replace_derived_from``),
    - a "Browse" block goes under the description: the thumbnail when one has
      been rendered, and the data browser / agent guide / ``items.parquet``
      links,
    - every remaining relative link becomes an absolute published URL
      (``absolutize_links``), because source.coop renders these files at a
      path their relative links cannot resolve against,
    - ``AGENTS.md`` gains the same absolute links and a one-line pointer at
      the data browser under "## Accessing the data".

    Runs after ``copy_committed``, on the catalog's copy only — staging's
    copy is ftwd's own output and is left alone. Idempotent: rerunning
    produces byte-identical files (a fresh copy each run, and marker-guarded
    insertion when a README is processed twice in place).
    """
    dataset_dir = catalog / dataset_id
    readme_path = dataset_dir / "README.md"
    agents_path = dataset_dir / "AGENTS.md"
    collection_title = read_json(dataset_dir / "collection.json").get("title", dataset_id)
    written: list[Path] = []

    if readme_path.is_file():
        text = readme_path.read_text()
        text = _replace_derived_from(
            text, recipe=recipe, collection_title=collection_title, fetch_title=fetch_title
        )
        text = _insert_browse_block(
            text,
            _browse_block(
                dataset_id,
                collection_title,
                manifest=manifest,
                has_thumbnail=(dataset_dir / "thumbnail.webp").is_file(),
            ),
        )
        text = absolutize_links(text, base_rel=dataset_id, manifest=manifest)
        readme_path.write_text(text)
        written.append(readme_path)

    if agents_path.is_file():
        text = agents_path.read_text()
        text = _insert_after_heading(
            text,
            "## Accessing the data",
            f"Browse the collection in the [Portolan data browser]"
            f"({browser_url(f'{dataset_id}/collection.json')}), or read the files below straight "
            f"from [collection.json]({public_url(f'{dataset_id}/collection.json')}).",
        )
        text = absolutize_links(text, base_rel=dataset_id, manifest=manifest)
        agents_path.write_text(text)
        written.append(agents_path)

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


# --- enriching sub-catalogs: item titles, docs, describedby/agents links --


def _add_item_titles(doc: dict) -> None:
    """PTL-TTL-003: every ``rel: item`` link needs a ``title`` — the item id."""
    for link in doc.get("links", []):
        if link.get("rel") == "item":
            link["title"] = Path(link["href"]).stem


def _is_chip_item_link(link: dict) -> bool:
    """True for a ``rel: item`` link naming a chip item, ``./<chip>/<chip>.json``.

    A chip item's file is named after the directory it sits in; every other
    Feature in that directory (the imagery child items) is not, which is what
    separates the two without hard-coding any season suffix.
    """
    href = PurePosixPath(link.get("href", ""))
    return href.stem == href.parent.name


def _child_item_links(square_dir: Path, chip_links: list[dict]) -> list[dict]:
    """``rel: item`` links for every non-chip Feature in this square's item directories.

    PTL-LNK-002: a catalog must carry a ``rel: item`` link for every Feature
    under its own directory, and ftwd's sub-catalog lists only the chip
    items — the season child items the imagery pass writes alongside them go
    unlisted. ``square_dir`` is the *staging* square directory, since that is
    where the item directories live (they are data, never committed).

    A file is a child when it parses as a STAC ``Feature`` and is not the
    chip item's own JSON; the title is its ``id``. Sorted by href, so the
    order is stable across reruns.
    """
    links = []
    for chip_link in chip_links:
        href = PurePosixPath(chip_link.get("href", ""))
        item_dir = square_dir / href.parent.name
        if not item_dir.is_dir():
            continue
        for path in sorted(item_dir.glob("*.json")):
            if path.name == href.name:
                continue
            doc = read_json(path)
            if not isinstance(doc, dict) or doc.get("type") != "Feature":
                continue
            links.append(
                {
                    "rel": "item",
                    "href": f"./{href.parent.name}/{path.name}",
                    "type": "application/geo+json",
                    "title": doc.get("id", path.stem),
                }
            )
    return sorted(links, key=lambda link: link["href"])


def _add_child_item_links(doc: dict, square_dir: Path) -> list[dict]:
    """List every child Feature in ``doc``'s item directories, after the chip links.

    Returns the chip item links, so the caller can count chips without
    counting the children just added. Idempotent: any child link already
    present is dropped and recomputed, and the ones kept go immediately after
    the last chip link, leaving every other link where it was.
    """
    links = [
        link
        for link in doc.get("links", [])
        if link.get("rel") != "item" or _is_chip_item_link(link)
    ]
    chip_links = [link for link in links if link.get("rel") == "item"]
    children = _child_item_links(square_dir, chip_links)
    if children:
        last = max(i for i, link in enumerate(links) if link.get("rel") == "item")
        links = links[: last + 1] + children + links[last + 1 :]
    doc["links"] = links
    return chip_links


def _ensure_subcatalog_docs_links(doc: dict) -> None:
    """PTL-FIL-001/002: the sub-catalog needs ``describedby``/``agents`` links."""
    links = doc.setdefault("links", [])
    existing_rels = {link.get("rel") for link in links}
    if "describedby" not in existing_rels:
        links.append(
            {"rel": "describedby", "href": "./README.md", "type": "text/markdown", "title": "Square README"}
        )
    if "agents" not in existing_rels:
        links.append(
            {"rel": "agents", "href": "./AGENTS.md", "type": "text/markdown", "title": "Square agent guide"}
        )


def _subcatalog_readme(
    dataset_id: str, collection_title: str, square: str, n_chips: int, *, manifest: dict
) -> str:
    plural = "chip" if n_chips == 1 else "chips"
    collection_readme = human_url(manifest, f"{dataset_id}/README.md")
    return (
        f"# {collection_title} — MGRS square {square}\n\n"
        f"This square holds {n_chips} {plural} on the FTW grid. Each item carries the same "
        "asset types as the rest of the collection — label masks and, where imagery was "
        f"downloaded, clipped scenes — see the [collection README]({collection_readme}) for what "
        "every asset means.\n"
    )


def _subcatalog_agents(
    dataset_id: str, collection_title: str, square: str, *, manifest: dict
) -> str:
    """The square's agent guide, with every link and the query's path published.

    The query reads the collection's mirror by its public URL rather than a
    relative path: this file is published, and a reader who found it on the
    web has no collection directory to run it from.
    """
    items = public_url(f"{dataset_id}/items.parquet")
    guide = human_url(manifest, f"{dataset_id}/AGENTS.md")
    query = f"SELECT * FROM read_parquet('{items}') WHERE id LIKE 'ftw-{square}%';"
    return (
        f"# {collection_title} — MGRS square {square}\n\n"
        "## Overview\n\n"
        f"This is a sub-catalog of chips in MGRS 100 km square {square}. See the "
        f"[collection agent guide]({guide}) for the full collection.\n\n"
        "## Accessing the data\n\n"
        "Query this square's items out of the collection's `items.parquet`, filtered on the "
        "square prefix of the item id:\n\n"
        f"```sql\n{query}\n```\n\n"
        "## Schema & field notes\n\n"
        "Every column and property is documented in the "
        f"[collection agent guide]({guide}); nothing here is specific to this square.\n\n"
        "## Data quality & usage notes\n\n"
        f"Every data quality note in the [collection agent guide]({guide}) applies "
        "equally to this square.\n\n"
        "## Example queries\n\n"
        f"See the [collection agent guide]({guide}) for worked examples against the "
        "full collection; the query above scopes any of them to this square.\n\n"
        "## Related collections\n\n"
        f"See the [collection agent guide]({guide}) for related collections and the "
        "source field boundary data.\n"
    )


def enrich_subcatalogs(
    dataset_id: str,
    *,
    catalog: Path = CATALOG,
    staging: Path = STAGING,
    collection_title: str,
    manifest: dict,
) -> list[Path]:
    """Give every committed sub-catalog a title on each item link, its children, and its own docs.

    For each ``catalog/<id>/chips/<square>/catalog.json``: sets ``title`` on
    every item link (PTL-TTL-003), adds a ``rel: item`` link for every
    imagery child item sitting in one of its chip directories (PTL-LNK-002,
    see ``_add_child_item_links``), adds ``describedby``/``agents`` links
    (PTL-FIL-001/002), and writes ``README.md``/``AGENTS.md`` alongside it
    (PTL-FIL-001/002/003). The same link edits are applied to the staging
    copy too, so the two stay identical — the git-owned-wins rule in
    ``upload_data.py`` then skips the staged copy rather than uploading a
    differing one.

    The README's chip count counts chips, not items: it comes from the chip
    links ``_add_child_item_links`` hands back, so the season child items it
    just listed do not inflate it.
    """
    written = []
    for sub_path in sorted((catalog / dataset_id / "chips").glob("*/catalog.json")):
        square = sub_path.parent.name
        doc = read_json(sub_path)
        _add_item_titles(doc)
        n_chips = len(_add_child_item_links(doc, staging / dataset_id / "chips" / square))
        _ensure_subcatalog_docs_links(doc)
        write_json(sub_path, doc)
        written.append(sub_path)

        readme_path = sub_path.parent / "README.md"
        readme_path.write_text(
            _subcatalog_readme(dataset_id, collection_title, square, n_chips, manifest=manifest)
        )
        written.append(readme_path)

        agents_path = sub_path.parent / "AGENTS.md"
        agents_path.write_text(
            _subcatalog_agents(dataset_id, collection_title, square, manifest=manifest)
        )
        written.append(agents_path)

        staged_path = staging / dataset_id / "chips" / square / "catalog.json"
        if staged_path.is_file():
            write_json(staged_path, doc)

    return written


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


def _imagery_count(dataset_dir: Path) -> int | None:
    """How many chips have Sentinel-2 season scenes, or None when unknowable.

    The imagery pass writes one child item per season alongside its chip,
    named ``<chip>_<season>_s2``; the number of distinct chips behind those
    ids is the number of chips with imagery, whether one season or both
    landed. The items mirror is read first (only its ``id`` column, so this
    works on a mirror written before the season properties existed).

    A mirror that reports none is not trusted on its own: ftwd's ``stac``
    stage writes ``items.parquet`` *before* the imagery pass runs, and
    ``rewrite_items_parquet`` only rebuilds it when ``catalogize <id>`` is run
    for that dataset. Running ``--root`` alone against a tree whose imagery
    landed after the last ``stac`` stage would otherwise report a real
    collection as having no imagery at all. So when the mirror shows none, the
    season item JSON on disk — which is the ground truth the mirror is rebuilt
    from — is counted instead.

    None only when there is neither a mirror nor a ``chips/`` tree to count:
    a CI checkout, or a staging tree pruned after publication. Zero means
    measured and genuinely none, and the two are shown differently.
    """
    count: int | None = None
    items_parquet = dataset_dir / "items.parquet"
    if items_parquet.exists():
        con = duckdb.connect()
        (count,) = con.execute(
            "SELECT count(DISTINCT regexp_replace(id, '_(planting|harvest)_s2$', '')) "
            "FROM read_parquet(?) WHERE regexp_matches(id, '_(planting|harvest)_s2$')",
            [str(items_parquet)],
        ).fetchone()
    chips_root = dataset_dir / "chips"
    if not count and chips_root.is_dir():
        chips = {path.parent.name for path in chips_root.glob("*/*/*_s2.json")}
        count = len(chips)
    return count


def _imagery_mode(dataset_dir: Path) -> str | None:
    """``"stored"``, ``"linked"``, or None — how this collection carries imagery.

    Two shapes are in use and they are not interchangeable for a data loader.
    With ``download_images`` enabled ftwd clips each selected scene to the
    chip and stores a four-band GeoTIFF beside it (``stored``); with it
    disabled the season item is written anyway but its bands stay the whole
    Sentinel-2 scene COG on the source STAC API, to be windowed by the reader
    (``linked``).

    Read from the collection's own resolved recipe, which ftwd writes into
    the staging tree, so it says what this build actually did rather than what
    the recipe in git says today. None when that file is absent or does not
    declare the stage.
    """
    import yaml

    resolved = dataset_dir / "ftwd-config.resolved.yaml"
    if not resolved.is_file():
        return None
    doc = yaml.safe_load(resolved.read_text()) or {}
    stages = ((doc.get("config") or doc).get("stages") or {})
    enabled = (stages.get("download_images") or {}).get("enabled")
    if enabled is None:
        return None
    return "stored" if enabled else "linked"


def _crop_label_count(items_parquet: Path) -> int | None:
    """How many chip items carry an HCAT crop label, or None without a mirror.

    ``ftw:hcat_dominant_code`` is written only when the harmonized source
    carries HCAT crop codes, so the column is absent entirely for a collection
    whose source has none — which is a zero, not a missing measurement.
    """
    if not items_parquet.exists():
        return None
    con = duckdb.connect()
    columns = {
        d[0] for d in con.execute("SELECT * FROM read_parquet(?) LIMIT 0", [str(items_parquet)]).description
    }
    if "ftw:hcat_dominant_code" not in columns:
        return 0
    (count,) = con.execute(
        'SELECT count(*) FROM read_parquet(?) WHERE "ftw:hcat_dominant_code" IS NOT NULL',
        [str(items_parquet)],
    ).fetchone()
    return count


def _license_cell(doc: dict) -> str:
    """The License column: an SPDX id linked to spdx.org, or the license link.

    A collection whose license is ``other`` carries a ``rel: license`` link
    naming the terms it is published under (ftwd copies it from the recipe);
    that link's own title is what the table shows, since there is no SPDX
    page to point at.
    """
    license_id = doc.get("license") or "—"
    if license_id not in ("other", "—"):
        return f"[{license_id}]({SPDX_BASE}{license_id}.html)"
    for link in doc.get("links") or []:
        if link.get("rel") == "license" and link.get("href"):
            return f"[{link.get('title') or 'License terms'}]({link['href']})"
    return license_id


def _source_cell(dataset_id: str, doc: dict) -> str:
    """The Source column: the harmonized collection's human page, from the via link."""
    for link in doc.get("links") or []:
        if link.get("rel") == "via" and link.get("href"):
            return f"[harmonized/{dataset_id}]({link['href']})"
    return "—"


def _thumbnail_cell(dataset_id: str, title: str, *, rendered: bool) -> str:
    """The Thumbnail column: a width-constrained ``<img>``, or ``—``.

    Deliberately not ``![title](href)``. Markdown image syntax carries no size,
    so the renderer draws the 1024x683 thumbnail at native resolution and a
    single table row fills the viewport. An inline ``<img>`` with an explicit
    ``width`` is the only way to say "small" in a markdown document, and
    source.coop passes inline HTML through to the page (see
    ``THUMBNAIL_WIDTH_PX``).

    If a renderer ever did sanitize the tag away, the fix is to stop rendering
    this column rather than to go back to a full-bleed image: pass
    ``thumbnails=False`` to ``_collections_block`` for the README too, as
    ``catalog/AGENTS.md`` already does, and let the Browse column and the data
    browser's own card grid carry the pictures.
    """
    if not rendered:
        return "—"
    href = public_url(f"{dataset_id}/thumbnail.webp")
    return f'<img src="{href}" alt="{title}" width="{THUMBNAIL_WIDTH_PX}">'


def _imagery_cell(imagery: int | None, mode: str | None) -> str:
    """The Imagery column: how many chips have scenes, and in which shape.

    Three distinguishable answers, because the collections here genuinely
    differ and a single number would imply they do not: ``—`` for not
    measurable, ``none`` for measured and zero (a labels-only collection,
    whose chips still carry masks and a split), and a count qualified by
    ``stored`` or ``linked`` (see ``_imagery_mode``) where scenes exist. An
    unqualified count is the fallback when the resolved recipe is not on disk
    to say which shape was built.
    """
    if imagery is None:
        return "—"
    if not imagery:
        return "none"
    return f"{imagery:,} {mode}" if mode else f"{imagery:,}"


def _collection_row(
    dataset_id: str, doc: dict, *, staging: Path, catalog: Path, manifest: dict
) -> dict:
    """One row of facts about a published collection, every cell already a link.

    Chips and splits are measured from the staged chips parquet, fields from
    the field polygons the chips were cut from, imagery and crop labels from
    the collection's own item JSON and items mirror; the thumbnail cell is a
    markdown image only when the thumbnail has actually been rendered into the
    catalog. Every URL is built from the manifest's bases, never hard-coded.

    The measured integers are kept alongside the rendered cells (``n_chips``,
    ``n_imagery``, ``n_crops``, ``n_fields``) so the coverage table and the
    summary line can do arithmetic on them without re-measuring or reparsing a
    formatted string. ``None`` means "not measurable here"; ``0`` means
    "measured, and there are none" — the two render differently, because a
    collection that genuinely has no imagery is a fact about the data and a
    missing staging tree is a fact about this machine.
    """
    title = doc.get("title", dataset_id)
    dataset_dir = staging / dataset_id
    chips_path = dataset_dir / f"{dataset_id}_chips.parquet"
    counts = _chip_counts(chips_path) if chips_path.exists() else None
    if counts is None:
        print(
            f"warning  {dataset_id}: {chips_path} is missing; root tables will show "
            "'—' for its chips/splits instead of the real counts"
        )
    imagery = _imagery_count(dataset_dir)
    crops = _crop_label_count(dataset_dir / "items.parquet")
    fields = _field_count(dataset_dir)
    has_thumbnail = (catalog / dataset_id / "thumbnail.webp").is_file()
    return {
        "id": dataset_id,
        "title": title,
        "thumbnail": _thumbnail_cell(dataset_id, title, rendered=has_thumbnail),
        "collection": f"[{title}]({human_url(manifest, dataset_id)})",
        "chips": f"{counts['total']:,}" if counts else "—",
        "splits": (
            f"{counts['train']:,}/{counts['val']:,}/{counts['test']:,}" if counts else "—"
        ),
        "imagery": _imagery_cell(imagery, _imagery_mode(dataset_dir)),
        "imagery_n": _count_cell(imagery),
        "license": _license_cell(doc),
        "source": _source_cell(dataset_id, doc),
        "browse": f"[browse]({browser_url(f'{dataset_id}/collection.json')})",
        "n_chips": counts["total"] if counts else None,
        "n_imagery": imagery,
        "n_crops": crops,
        "n_fields": fields,
    }


# The root table's columns, as (heading, row key). catalog/AGENTS.md gets the
# same facts without the image — an agent reading markdown gains nothing from
# a thumbnail it cannot see.
_TABLE_COLUMNS = (
    ("Thumbnail", "thumbnail"),
    ("Collection", "collection"),
    ("Chips", "chips"),
    ("Splits (train/val/test)", "splits"),
    ("Imagery", "imagery"),
    ("License", "license"),
    ("Source", "source"),
    ("Browse", "browse"),
)


def _collections_table(rows: list[dict], *, thumbnails: bool = True) -> str:
    if not rows:
        return ""
    columns = [c for c in _TABLE_COLUMNS if thumbnails or c[1] != "thumbnail"]
    header = "| " + " | ".join(heading for heading, _ in columns) + " |\n"
    sep = "| " + " | ".join("---" for _ in columns) + " |\n"
    body = "".join(
        "| " + " | ".join(row[key] for _, key in columns) + " |\n" for row in rows
    )
    return header + sep + body


def _collections_list(rows: list[dict]) -> str:
    """The same facts as the table, as a list, for llms.txt."""
    lines = []
    for row in rows:
        collection_url = public_url(f"{row['id']}/collection.json")
        lines.append(
            f"- [{row['title']}]({collection_url}): {row['chips']} chips "
            f"({row['splits']} train/val/test), {row['imagery_n']} with imagery, "
            f"license {row['license']}, source {row['source']}, {row['browse']}\n"
        )
    return "".join(lines)


# --- the generated Collections block: totals, the table, and coverage ------

# The columns of the coverage table, which says what each collection actually
# carries rather than what the catalog carries on average. Every cell is a
# count of *chips*, so the columns are comparable with each other and with the
# Chips column of the main table.
_COVERAGE_COLUMNS = ("Collection", "Label masks", "Sentinel-2 imagery", "HCAT crop labels")

_COVERAGE_NOTE = (
    "`stored` means a four-band GeoTIFF clipped to the chip and published with it; "
    "`linked` means the chip's season item points at the whole Sentinel-2 scene on the "
    "source STAC API, for a reader to window. A chip with no scene still carries its "
    "masks and its split — pair it with imagery of your own, on the footprint in "
    "`items.parquet`."
)


def _count_cell(value: int | None, *, zero: str = "none") -> str:
    """A measured count as a table cell: ``—`` unknown, ``zero`` for 0, else the number."""
    if value is None:
        return "—"
    return zero if not value else f"{value:,}"


def _summary_line(rows: list[dict]) -> str:
    """The headline numbers, above the table: collections, chips, field polygons.

    Every number is summed from the rows, which measured them; a quantity no
    row could measure is left out of the line rather than shown as a wrong
    total. Bold, and on its own line, because this is the first thing a reader
    landing on the catalog sees after the opening paragraph.
    """
    parts = [f"{len(rows)} collection" + ("s" if len(rows) != 1 else "")]
    for key, noun in (("n_chips", "chips"), ("n_fields", "field polygons")):
        measured = [row[key] for row in rows if row.get(key) is not None]
        if len(measured) == len(rows) and rows:
            parts.append(f"{sum(measured):,} {noun}")
    return "**" + " · ".join(parts) + "**\n"


def _coverage_table(rows: list[dict]) -> str:
    """Which components each collection actually carries, in chips.

    The main table has one Imagery number per collection, which is easy to
    read as a detail. This one puts the components side by side so that an
    uneven catalog reads as uneven: a labels-only collection shows ``none``
    next to its neighbours' counts instead of being a footnote.
    """
    header = "| " + " | ".join(_COVERAGE_COLUMNS) + " |\n"
    sep = "| " + " | ".join("---" for _ in _COVERAGE_COLUMNS) + " |\n"
    body = ""
    for row in rows:
        body += (
            f"| {row['collection']} | {_count_cell(row.get('n_chips'))} "
            f"| {row['imagery']} | {_count_cell(row.get('n_crops'))} |\n"
        )
    return header + sep + body


def _collections_block(rows: list[dict], *, thumbnails: bool = True) -> str:
    """Everything between the ``collections`` markers: totals, table, coverage.

    One marker pair rather than three, so a document only has to carry the
    pair it already has. Empty for an empty catalog, which is what
    ``_replace_between_markers`` renders as a blank block.
    """
    if not rows:
        return ""
    return (
        f"{_summary_line(rows)}\n"
        f"{_collections_table(rows, thumbnails=thumbnails)}\n"
        "### What each collection carries\n\n"
        f"{_coverage_table(rows)}\n"
        f"{_COVERAGE_NOTE}\n"
    )


def _replace_between_markers(path: Path, content: str) -> None:
    text = path.read_text()
    if _MARK_START not in text or _MARK_END not in text:
        raise ValueError(f"{path} is missing the {_MARK_START} / {_MARK_END} markers")
    before, _, rest = text.partition(_MARK_START)
    _, _, after = rest.partition(_MARK_END)
    middle = f"\n{content}" if content else "\n"
    path.write_text(f"{before}{_MARK_START}{middle}{_MARK_END}{after}")


def regenerate_root(
    manifest: dict, *, catalog: Path = CATALOG, staging: Path = STAGING, now: datetime | None = None
) -> list[Path]:
    """Regenerate the root catalog's child links and the root docs' tables.

    Keeps every fixed link in ``catalog/catalog.json`` exactly as it is;
    rebuilds the ``child`` links, sorted by dataset id, and drops any
    ``rel: self`` link — Portolan forbids self links, and a hand-edit or an
    older ftwd is the only way one would appear here. Sets
    ``stac_extensions`` to the Portolan schema URI plus the version extension
    (PTL-CNF-003: required wherever a document carries a top-level
    ``version``), ``version`` from the manifest, and stamps ``updated``
    (PTL-PRO-003). Fills the marker-delimited ``## Collections`` block in
    ``catalog/README.md`` and ``catalog/AGENTS.md`` — headline totals, the
    collections table, and the coverage table that says what each collection
    actually carries (``_collections_block``) — and the collection list in
    ``catalog/llms.txt``.
    """
    root_path = catalog / "catalog.json"
    doc = read_json(root_path)
    collections = _built_collections(catalog)

    doc["links"] = [
        link for link in doc["links"] if link.get("rel") not in ("child", "self")
    ] + _child_links(collections)
    doc["stac_extensions"] = [PORTOLAN_SCHEMA_URI, VERSION_EXTENSION_URI]
    doc["version"] = manifest["catalog"]["version"]
    doc["updated"] = _now_iso(now)
    write_json(root_path, doc)

    rows = [
        _collection_row(dataset_id, coll, staging=staging, catalog=catalog, manifest=manifest)
        for dataset_id, coll in collections
    ]
    _replace_between_markers(catalog / "README.md", _collections_block(rows))
    _replace_between_markers(catalog / "AGENTS.md", _collections_block(rows, thumbnails=False))
    _replace_between_markers(catalog / "llms.txt", _collections_list(rows))

    return [root_path, catalog / "README.md", catalog / "AGENTS.md", catalog / "llms.txt"]


# --- the full pipeline for one dataset --------------------------------------


def _check_staged(dataset_id: str, staging: Path) -> None:
    """Exit with a clear message naming the missing file when a build hasn't reached ``stac`` yet.

    ``rewrite_items_parquet`` needs ``items.parquet`` and ``copy_committed``
    needs ``collection.json``; both are written by ftwd's ``stac`` stage. A
    build stopped earlier (``--through select_images``, say) leaves neither,
    and reading them straight off would raise an opaque traceback instead of
    naming the fix.
    """
    for name in ("items.parquet", "collection.json"):
        path = staging / dataset_id / name
        if not path.is_file():
            sys.exit(f"{path} not found; run: uv run python tools/build.py {dataset_id} --through stac")


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
    _check_staged(dataset_id, staging)
    recipe = _load_recipe(dataset_id)

    rewrite_staging_items(dataset_id, staging=staging)
    rewrite_items_parquet(dataset_id, staging=staging)

    written = copy_committed(dataset_id, staging=staging, catalog=catalog)
    written += enrich_collection(
        dataset_id, catalog=catalog, staging=staging, manifest=manifest, recipe=recipe, now=now
    )
    written += enrich_readme(dataset_id, catalog=catalog, manifest=manifest, recipe=recipe)
    collection_title = read_json(catalog / dataset_id / "collection.json").get("title", dataset_id)
    written += enrich_subcatalogs(
        dataset_id,
        catalog=catalog,
        staging=staging,
        collection_title=collection_title,
        manifest=manifest,
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
        _check_dataset_recipe(args.dataset_id)
        written += catalogize(args.dataset_id, manifest=manifest)
    if args.root:
        written += regenerate_root(manifest)

    for path in written:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
