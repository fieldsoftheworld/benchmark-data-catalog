#!/usr/bin/env python3
"""Copy staging metadata into the published catalog, with published links.

``tools/build.py`` writes a self-contained Portolan collection into
``staging/<id>/``. This script takes the git-owned slice of that output
(``collection.json``, ``README.md``, ``AGENTS.md``, ``styles/*.json``,
``chips/*/catalog.json``) and republishes it under ``catalog/<source>/<id>/`` with
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

    uv run python tools/catalogize.py at_2024          # one dataset
    uv run python tools/catalogize.py at_2024 --root   # + regenerate the root
    uv run python tools/catalogize.py --root           # root only (e.g. after
                                                       # removing a dataset)

Item JSON under ``staging/<id>/chips/*/*/`` is read and its ``root`` links
rewritten in place, but no item directory and no raster is ever copied into
``catalog/``; those stay bucket-only, uploaded by ``tools/upload_data.py``.
"""
from __future__ import annotations

import argparse
import hashlib
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
    PORTOLAN_SCHEMA_URI,
    PUBLIC_BASE,
    ROOT,
    STAGING,
    canonicalize_portolan_schema,
    dataset_relpath,
    public_url,
    published_collections,
    read_json,
    source_group,
    write_json,
)

# ftw_dataset_tools.api.stac.PORTOLAN_SCHEMA_URI tracks whatever version is
# bundled with the pinned ftwd commit (v0.1.2), not this catalog's migration
# target; common.PORTOLAN_SCHEMA_URI (v0.3.0, imported above) is the one this
# module writes. See the comment on that constant for why.

# The STAC version extension, required (PTL-CNF-003) whenever a document uses
# a top-level `version` property.
VERSION_EXTENSION_URI = "https://stac-extensions.github.io/version/v1.2.0/schema.json"

# The web-map-links extension, required (PTL-VIZ-003) whenever a collection
# carries a rel:'pmtiles' link.
_WEB_MAP_LINKS_PREFIX = "https://stac-extensions.github.io/web-map-links/"
WEB_MAP_LINKS_URI = f"{_WEB_MAP_LINKS_PREFIX}v1.3.0/schema.json"

# Files copied verbatim from staging/<id>/ to catalog/<source>/<id>/, plus the two glob
# patterns below (styles/*.json, chips/*/catalog.json). Everything else under
# staging/<id>/ is data: bucket-only, never committed.
COMMITTED = ("collection.json", "README.md", "AGENTS.md")

# The markers regenerate_root fills between, in catalog/README.md,
# catalog/AGENTS.md and catalog/llms.txt.
_MARK_START = "<!-- collections:start -->"
_MARK_END = "<!-- collections:end -->"

# The markers enrich_readme's "Browse" block sits between, in every
# catalog/<source>/<id>/README.md, so a rerun replaces the block instead of stacking
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
    published ``catalog/<source>/<id>/collection.json`` — staging's copy never has
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
    """Copy the git-owned metadata files from ``staging/<id>`` to ``catalog/<source>/<id>``.

    Returns the catalog-side paths written. Only ``COMMITTED`` and the two
    glob patterns (``styles/*.json``, ``chips/*/catalog.json``) are copied;
    item directories and every data file stay in staging. ``collection.json``
    is special-cased to preserve an existing thumbnail asset — see
    ``_copy_collection_preserving_thumbnail``.
    """
    src_root = staging / dataset_id
    dst_root = catalog / dataset_relpath(dataset_id, catalog=catalog)
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
    root catalog: a dataset sits at ``<source>/<id>/``, so 2 for its
    ``collection.json``, 4 for a chips sub-catalog, 5 for an item or an
    imagery child item next to it (``dataset_depth`` plus the path inside
    the dataset).
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


def dataset_depth(dataset_id: str, *, catalog: Path = CATALOG) -> int:
    """How many directories the dataset's own folder sits below the root catalog (2)."""
    return len(PurePosixPath(dataset_relpath(dataset_id, catalog=catalog)).parts)


def rewrite_staging_items(
    dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG
) -> list[Path]:
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
    above = dataset_depth(dataset_id, catalog=catalog) - 1
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
        rewrite_root_links(doc, depth=above + len(rel.parts))
        write_json(path, doc)
        touched.append(path)
    if skipped:
        print(f"note   rewrite_staging_items: skipped {skipped} non-STAC JSON file(s) under {chips_root}")
    return touched


# --- rebuilding items.parquet from the item JSON, with public URLs ---------


def _rewrite_item_links(
    relpath: str, square: str, links: list[dict], item_dir: str | None = None
) -> list[dict]:
    """Structural links go to the published root/collection/sub-catalog.

    Any other relative link (``./x.json`` — a chip's ``ftw:planting`` /
    ``ftw:harvest`` season items, a season item's ``ftw:parent_chip``) is made
    absolute against the item's directory, because a parquet row has no base
    to resolve a relative href against.
    """
    targets = {
        "root": public_url("catalog.json"),
        "collection": public_url(f"{relpath}/collection.json"),
        "parent": public_url(f"{relpath}/chips/{square}/catalog.json"),
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
            link = {**link, "href": public_url(f"{relpath}/chips/{square}/{item_dir}/{href[2:]}")}
        new_links.append(link)
    return new_links


def _rewrite_item_assets(relpath: str, item_dir: str, square: str, assets: dict) -> dict:
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
    prefix = f"{relpath}/chips/{square}/{item_dir}"
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


def _item_documents(relpath: str, chips_root: Path) -> list[dict]:
    """Every item under ``chips_root``, links and asset hrefs made public.

    ``relpath`` is the dataset's published ``<source>/<id>``. Walks
    ``chips/<square>/<chip>/*.json`` and keeps each STAC ``Feature`` —
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
            relpath, square, doc.get("links") or [], item_dir=item_dir
        )
        doc["assets"] = _rewrite_item_assets(relpath, item_dir, square, doc.get("assets") or {})
        items.append(doc)
    return items


def rewrite_items_parquet(
    dataset_id: str, *, staging: Path = STAGING, catalog: Path = CATALOG
) -> Path:
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
    items = _item_documents(
        dataset_relpath(dataset_id, catalog=catalog), staging / dataset_id / "chips"
    )
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
    """PTL-LNK-001: the collection needs a ``rel: parent`` link to its source group's catalog."""
    links = doc.setdefault("links", [])
    if any(link.get("rel") == "parent" for link in links):
        return
    links.append({"rel": "parent", "href": "../catalog.json", "type": "application/json"})


def _ensure_llms_link(doc: dict) -> None:
    """The collection needs a ``rel: llms`` link so agents can find its ``llms.txt``.

    ``write_llms`` writes ``catalog/<source>/<id>/llms.txt`` but nothing links to it
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


def _chip_counts(chips_parquet: Path) -> dict[str, int | None]:
    """Total chips and the per-split count, from a chips parquet's ``split`` column.

    A dataset built with ftwd's splits stage off (every recipe but the predefined
    ones; the root chips table holds the splits) has no ``split``: its per-split
    counts are None.
    """
    con = duckdb.connect()
    columns = {
        r[0] for r in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(chips_parquet)]).fetchall()
    }
    if "split" not in columns:
        return {"total": _row_count(chips_parquet), "train": None, "val": None, "test": None}
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


# The repository's own top-level folders that ftwd reads files from (filters,
# recipes, label extents), and the folder name a builder clones it under.
_REPO_FOLDERS = ("datasets", "work")
_REPO_NAME = "benchmark-data-catalog"


def _repo_relative(value: str, root: Path = ROOT) -> str | None:
    """A builder-local absolute path as a path inside the repository, or None.

    ftwd records the files it read (``class_filter.source``, ``label_extent``) with
    the builder's absolute path, e.g. ``/home/ubuntu/benchmark-data-catalog/...``,
    which means nothing to a reader and names the build machine's home directory.
    A path from another checkout (a worktree, another builder) is matched on the
    repository's own folders, never on this checkout's folder name.
    """
    path = Path(value)
    marker = f"/{_REPO_NAME}/"
    if path.is_relative_to(root):
        rel = path.relative_to(root).as_posix()
    elif marker in value:
        rel = value.split(marker, 1)[1]
    else:
        start = max(value.rfind(f"/{folder}/") for folder in _REPO_FOLDERS)
        rel = value[start + 1:] if start > 0 else None
    # Only a file this checkout has is a placement, not a guess (a cache or data
    # folder that happens to be called datasets/ or work/ is not the repository).
    if rel is None or ".." in Path(rel).parts or not (root / rel).is_file():
        return None
    return rel


def strip_local_paths(config, root: Path = ROOT, unresolved: list[str] | None = None):
    """``ftw:config`` with every absolute local path made repository-relative.

    A path outside any checkout keeps only its file name and is appended to
    ``unresolved``, so a caller can refuse rather than publish a guess.
    """
    if isinstance(config, dict):
        return {k: strip_local_paths(v, root, unresolved) for k, v in config.items()}
    if isinstance(config, list):
        return [strip_local_paths(v, root, unresolved) for v in config]
    if isinstance(config, str) and config.startswith("/"):
        relative = _repo_relative(config, root)
        if relative is not None:
            return relative
        if unresolved is not None:
            unresolved.append(config)
        return Path(config).name
    return config


# --- Portolan v0.3 metadata: table:columns and asset descriptions ----------
#
# PORTO-FMT-077/078/079 (SHOULD): every table:columns entry should carry a
# description, a mirror with no source descriptions should say so in its
# README, and a placeholder description should never be written.
# PORTO-CORE-088 (SHOULD): every asset should carry a title and a
# description.
#
# None of this needs staging/<id>/ — every input is already in catalog/ or
# committed to the repository (the fiboa field descriptions fetched from each
# group's harmonized source, below); they run inside ``enrich_collection``.

# tools/fiboa_field_descriptions.json: {group id: {column name: description}},
# fetched from each group's harmonized source collection
# (https://data.source.coop/ftw/harmonized-field-data/<group>/collection.json,
# the "fields"-equivalent asset's table:columns) on 2026-11-20. Those
# descriptions are the fiboa/vecorel/hcat/crop extension spec text the
# harmonized-field-data-catalog publishes (or, where a source documents no
# meaning for a column, that fact, attested "per the fiboa data survey"); this
# catalog's "fields", "fields_filtered" and "boundary_lines" assets are cut
# from that exact source with the same column semantics, so the descriptions
# apply unchanged. Re-fetch and regenerate this file if a harmonized
# collection's own field documentation improves.
_FIBOA_FIELD_DESCRIPTIONS_PATH = Path(__file__).resolve().parent / "fiboa_field_descriptions.json"
_fiboa_field_descriptions_cache: dict[str, dict[str, str]] | None = None


def _fiboa_field_descriptions(group: str) -> dict[str, str]:
    """``{column name: description}`` for ``group``'s harmonized source fields table."""
    global _fiboa_field_descriptions_cache
    if _fiboa_field_descriptions_cache is None:
        _fiboa_field_descriptions_cache = json.loads(_FIBOA_FIELD_DESCRIPTIONS_PATH.read_text())
    return _fiboa_field_descriptions_cache.get(group, {})


# Columns this catalog adds to the harmonized fields table itself, the same
# everywhere it appears (not sourced from the harmonized collection, which
# does not carry them).
_GENERIC_FIELD_COLUMNS = {
    "collection": (
        "Id of the harmonized source collection (datasets.yaml's source group, e.g. "
        "`at`) this row's field was drawn from. Differs from the group id only when a "
        "collection merges more than one harmonized source, as es_2025 and es_po_2025 do."
    ),
}

# es_2025 and es_po_2025 merge the national SIGPAC declarations with regional
# (Pais Vasco) parcels; these columns exist only on those two collections'
# "fields"/"fields_filtered"/"boundary_lines" tables and are not part of any
# harmonized source. Descriptions condensed from tools/merge_es_2025.py's own
# docstring, the first-party source for what this merge does.
_ES_MERGE_FIELD_COLUMNS = {
    "source_id": (
        "The id in the source file: the national SIGPAC id, or the regional file's row "
        "id for a regional (Pais Vasco) parcel (tools/merge_es_2025.py)."
    ),
    "ftw:source": (
        "Which SIGPAC edition this parcel came from: `es` (national declarations) or a "
        "regional collection id such as `es_pv` for Pais Vasco (tools/merge_es_2025.py)."
    ),
    "landuse:code": (
        "SIGPAC land use code. On a regional parcel, its own; on a national parcel that "
        "overlaps a Pais Vasco parcel, the land use of the regional parcel it overlaps "
        "most; null elsewhere (tools/merge_es_2025.py)."
    ),
    "landuse:name_en": (
        "SIGPAC land use name, for landuse:code, under the same rule "
        "(tools/merge_es_2025.py)."
    ),
    "ftw:class": (
        "The value the class filter reads (es_merged_filter.yaml in ftw-dataset-tools): "
        "`es:<crop code>` for national parcels (`es:<code>:atlantic` for permanent/young "
        "pasture in the Atlantic provinces), `<region>:<land use>` for regional parcels "
        "(tools/merge_es_2025.py)."
    ),
}

# The STAC-GeoParquet item mirror's own structural columns (every item carries
# all of these; the ftw:* columns next to them are this collection's own item
# properties, documented per collection in AGENTS.md's "FTW properties on
# each STAC item" section instead, since their meaning is dataset-specific).
# Same set on every collection in the catalog (verified across all 180).
_ITEM_MIRROR_STRUCTURAL_COLUMNS = {
    "type": "STAC object type; always \"Feature\" for an item.",
    "stac_version": "The STAC specification version this item conforms to.",
    "stac_extensions": "Schema URIs of the STAC extensions and the Portolan profile this item declares.",
    "id": "The STAC item identifier.",
    "links": "This item's STAC links (root, parent, collection and related items).",
    "assets": "This item's STAC assets (imagery and label masks), keyed by asset name.",
    "collection": "Id of the STAC collection this item belongs to.",
    "datetime": "The item's nominal date/time (STAC common metadata).",
    "start_datetime": "Start of the item's temporal extent, for an item spanning a range rather than an instant.",
    "end_datetime": "End of the item's temporal extent, for an item spanning a range rather than an instant.",
    "renders": "Named, ready-to-render visualizations of this item's assets (STAC render extension).",
    "bbox": "Bounding box of the item's geometry.",
    "geometry": "The item's footprint geometry (the chip square), in EPSG:4326.",
    # Present on 22 of 180 collections (all from ftwd); not documented upstream
    # or anywhere in this repository. Stated per the brief's rule for
    # genuinely unknowable semantics: say what IS known, not what it might mean.
    "portolan:render_order": (
        "Property set by the build pipeline (ftw-dataset-tools); its meaning is not "
        "documented upstream or in this repository. Present on some items, likely a "
        "draw-order hint for overlapping imagery."
    ),
}

# field_embeddings: one row per field, aef_*/olmoearth_* from AlphaEarth
# Foundations and OlmoEarth v1.3 (see each collection's own README "Field
# embeddings" section, which this reuses). Same columns on every collection.
_FIELD_EMBEDDING_COLUMNS = {
    "id": "Field id; joins onto the `fields` (or `fields_filtered`) table.",
    "pixels": "Number of 10 m pixels used for this field's embedding statistics.",
    "pixel_rule": (
        "How pixels were selected for this field: `centroid` (pixels whose centre falls "
        "inside it) or `touched` (every pixel the field touches, for a field too small to "
        "contain a pixel centre)."
    ),
    "aef_mean": (
        "Mean of each AlphaEarth Foundations Satellite Embedding dimension (64 values) "
        "over the field's pixels. AlphaEarth Foundations Satellite Embedding dataset by "
        "Google and Google DeepMind, CC-BY-4.0."
    ),
    "aef_std": (
        "Population standard deviation of each AlphaEarth Foundations Satellite Embedding "
        "dimension (64 values) over the field's pixels."
    ),
    "aef_pixels": (
        "Number of pixels the AlphaEarth Foundations product covered for this field (can "
        "differ from `pixels` where its coverage is partial)."
    ),
    "olmoearth_mean": (
        "Mean of each OlmoEarth v1.3 embedding dimension (the first 64 of 128 dimensions) "
        "over the field's pixels. OlmoEarth v1.3 embeddings by Ai2 (Allen Institute for "
        "AI); OlmoEarth Artifact License, including its Section 2 use restrictions."
    ),
    "olmoearth_std": (
        "Population standard deviation of each OlmoEarth v1.3 embedding dimension (first "
        "64 of 128) over the field's pixels."
    ),
    "olmoearth_pixels": (
        "Number of pixels the OlmoEarth v1.3 product covered for this field (can differ "
        "from `pixels` where its coverage is partial)."
    ),
}

# Every asset key this catalog's collections carry, each with the same
# meaning everywhere (verified identical title across all 180 collections).
# field_embeddings already carries its own description (enrich_collection
# writes it); it is not repeated here.
_ASSET_DESCRIPTIONS = {
    "fields": (
        "Field boundary polygons harmonized to the fiboa schema, cut for this collection "
        "from the source harmonized field boundary collection."
    ),
    "fields_filtered": (
        "The `fields` polygons that remain after the class filter that selects which "
        "classes count as a field for this collection's masks."
    ),
    "boundary_lines": "The edges of the `fields` (or `fields_filtered`) polygons, as linestrings.",
    "chips": (
        "One row per chip: its grid location, how much of it is mapped field, its "
        "dominant crop, administrative unit and the benchmark split it is assigned to."
    ),
    "items": (
        "Every chip's STAC item, mirrored into one GeoParquet file (STAC-GeoParquet) so "
        "the collection can be queried without walking the catalog tree."
    ),
    "chips_tiles": "The chip grid as PMTiles vector tiles, for fast map rendering of the chip boundaries.",
    "fields_tiles": "The field boundary polygons as PMTiles vector tiles, for fast map rendering of the fields.",
    "style-split": "MapLibre style: chips coloured by their train / validation / test split assignment.",
    "style-field-coverage": "MapLibre style: chips shaded by the share of their area covered by mapped fields.",
    "style-outline": "MapLibre style: every field in one colour, for reading the boundaries themselves.",
    "style-dominant-crop": "MapLibre style: chips coloured by the crop covering most of their field area.",
    "style-crops": "MapLibre style: fields coloured by their harmonized crop (EuroCrops HCAT).",
    "thumbnail": "Preview image of the collection rendered with its default map style.",
}

# A chips file built with ftwd's splits stage off has no ``split`` column: the root
# chips table (``chips.parquet`` at the bucket root) holds its splits.
_CHIPS_WITHOUT_SPLIT = (
    "One row per chip: its grid location, how much of it is mapped field, its "
    "dominant crop and administrative unit. Its benchmark splits are in the root chips table."
)

# AGENTS.md's "## Schema & field notes" bullet list: "- `name`: description".
# Parses the two sub-lists it documents (chips table columns, and the item's
# own ftw:* properties) without needing anything else from the file.
_AGENTS_BULLET_RE = re.compile(r"^- `([^`]+)`:\s*(.+)$")
_AGENTS_CHIPS_HEADING = "Columns in the chips table:"
_AGENTS_FTW_HEADING = "FTW properties on each STAC item:"


def _agents_bullet_section(text: str, heading: str) -> dict[str, str]:
    """``{column name: description}`` from the bullet list right after ``heading``."""
    idx = text.find(heading)
    if idx == -1:
        return {}
    columns: dict[str, str] = {}
    for line in text[idx + len(heading):].splitlines():
        line = line.strip()
        if not line:
            if columns:
                break
            continue
        match = _AGENTS_BULLET_RE.match(line)
        if not match:
            break
        columns[match.group(1)] = match.group(2)
    return columns


def _agents_column_notes(dataset_dir: Path) -> dict[str, str]:
    """``{column name: description}`` from this dataset's own AGENTS.md, both sections.

    Covers the ``chips`` asset's columns and the ``items`` mirror's ``ftw:*``
    item-property columns — dataset-specific, so sourced from the collection's
    own agent guide rather than a shared static dict.
    """
    agents_path = dataset_dir / "AGENTS.md"
    if not agents_path.is_file():
        return {}
    text = agents_path.read_text()
    return {
        **_agents_bullet_section(text, _AGENTS_CHIPS_HEADING),
        **_agents_bullet_section(text, _AGENTS_FTW_HEADING),
    }


#: Which column-description sources apply to which asset, in lookup order.
#: Scoped per asset key rather than one flat merged dict: "id" means a
#: different thing in "chips" (the chip id) than in "fields" (the field id),
#: and a flat lookup would let one clobber the other.
_FIELD_TABLE_ASSET_KEYS = ("fields", "fields_filtered", "boundary_lines")


def _column_sources_for_asset(asset_key: str, *, agents_notes: dict, fiboa_notes: dict) -> tuple[dict, ...]:
    if asset_key in _FIELD_TABLE_ASSET_KEYS:
        return (_ES_MERGE_FIELD_COLUMNS, _GENERIC_FIELD_COLUMNS, fiboa_notes)
    if asset_key == "chips":
        return (agents_notes,)
    if asset_key == "items":
        # ftw:* item properties from AGENTS.md; plain STAC fields from the
        # static dict. Order does not matter: the two never share a key
        # (every structural key is a bare STAC field name, every AGENTS.md
        # key here starts with "ftw:" or is "portolan:render_order").
        return (agents_notes, _ITEM_MIRROR_STRUCTURAL_COLUMNS)
    if asset_key == "field_embeddings":
        return (_FIELD_EMBEDDING_COLUMNS,)
    return ()


def fill_table_column_descriptions(doc: dict, *, group: str, dataset_dir: Path) -> int:
    """Fill every missing ``table:columns`` ``description`` across ``doc``'s assets.

    Looks up each column against the sources that apply to its own asset key
    (``_column_sources_for_asset``), never across asset boundaries, so e.g.
    the ``chips`` table's ``id`` (a chip id) cannot be filled from the
    ``fields`` table's ``id`` (a field id) or vice versa. Returns how many
    descriptions were filled; a column found in none of those sources is
    left exactly as it was (never a placeholder) and printed as a warning,
    so a genuinely new column surfaces instead of silently staying
    undocumented.
    """
    agents_notes = _agents_column_notes(dataset_dir)
    fiboa_notes = _fiboa_field_descriptions(group)
    filled = 0
    for asset_key, asset in (doc.get("assets") or {}).items():
        sources = _column_sources_for_asset(asset_key, agents_notes=agents_notes, fiboa_notes=fiboa_notes)
        for column in asset.get("table:columns") or []:
            if column.get("description"):
                continue
            name = column.get("name")
            description = next((s[name] for s in sources if name in s), None)
            if description is None:
                print(f"warning  {dataset_dir.name}: no description source for column "
                      f"{asset_key}.{name!r}; left undocumented")
                continue
            column["description"] = description
            filled += 1
    return filled


def fill_asset_descriptions(doc: dict) -> int:
    """Fill every missing asset-level ``description`` from ``_ASSET_DESCRIPTIONS``.

    Returns how many were filled. An asset key this dict does not cover is
    left alone and printed as a warning (never a placeholder), the same
    policy as ``fill_table_column_descriptions``.
    """
    filled = 0
    for key, asset in (doc.get("assets") or {}).items():
        if asset.get("description"):
            continue
        description = _ASSET_DESCRIPTIONS.get(key)
        columns = {c.get("name") for c in asset.get("table:columns") or []}
        if key == "chips" and columns and "split" not in columns:
            description = _CHIPS_WITHOUT_SPLIT
        if description is None:
            print(f"warning  no description source for asset {key!r}; left undocumented")
            continue
        asset["description"] = description
        filled += 1
    return filled


def _sha256_multihash(path: Path) -> str:
    """``file:checksum``: a multihash (sha2-256) of ``path``, as lowercase hex.

    ``1220`` + the 32-byte digest: multihash function code 0x12 (sha2-256),
    length byte 0x20 (32), per the STAC file extension's checksum format.
    """
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"1220{digest}"


def fill_local_checksums(doc: dict, dataset_dir: Path) -> int:
    """Set ``file:size``/``file:checksum`` for an asset whose bytes are on disk.

    Only ``thumbnail.webp`` and ``styles/*.json`` are ever committed to git
    (``COMMITTED`` plus the glob patterns ``copy_committed`` copies); every
    other asset (every ``*.parquet`` and ``*.pmtiles``) is data, uploaded by
    ``tools/upload_data.py`` and never present in a checkout of this
    repository. PORTO-CORE-028 (SHOULD) asks every asset for both fields;
    computing a checksum for the data assets needs their actual bytes, which
    means downloading each one — real data work, out of scope here (see the
    PR's "Requires data work" section). Returns how many assets changed.
    """
    changed = 0
    for asset in (doc.get("assets") or {}).values():
        href = asset.get("href", "")
        if not href.startswith("./"):
            continue
        local = dataset_dir / href[2:]
        if not local.is_file():
            continue
        size = local.stat().st_size
        checksum = _sha256_multihash(local)
        if asset.get("file:size") != size:
            asset["file:size"] = size
            changed += 1
        if asset.get("file:checksum") != checksum:
            asset["file:checksum"] = checksum
            changed += 1
    return changed


def reapply_chip_subcatalog_schema(dataset_dir: Path) -> list[Path]:
    """Canonicalize the Portolan schema URI in every ``chips/<square>/catalog.json``.

    Whether a chip sub-catalog declares the Portolan extension at all varies
    by the ftwd version that built it (verified: every one of fi's chip
    sub-catalogs declares none, while e.g. wri_trazo_ml's all do, each with
    whatever version was current then). ``canonicalize_portolan_schema`` only
    replaces an existing declaration, so a sub-catalog that has never carried
    one stays exactly as it is — see the function's own docstring for why
    that is not treated as a defect.
    """
    written = []
    for path in sorted(dataset_dir.glob("chips/*/catalog.json")):
        doc = read_json(path)
        if canonicalize_portolan_schema(doc):
            write_json(path, doc)
            written.append(path)
    return written


def enrich_collection(
    dataset_id: str,
    *,
    catalog: Path,
    staging: Path,
    manifest: dict,
    recipe: dict,
    now: datetime | None = None,
) -> list[Path]:
    """Enrich the just-copied ``catalog/<source>/<id>/collection.json`` (and README.md).

    Fixes the collection's own ``root`` link (``dataset_depth``), adds a
    ``parent`` link to its source group's catalog and a ``llms`` link to its own ``llms.txt``,
    appends the host provider once, fills in ``version`` and ``updated``,
    ensures a ``via`` link (rewritten to a browsable page, PTL-PRO-001) and
    — for an "other" license — a ``license`` link exist, registers a
    ``rel: pmtiles`` link for every PMTiles asset (PTL-VIZ-003), makes the
    absolute builder paths in ``ftw:config`` repository-relative. Also
    applies the Portolan v0.3 metadata fixups: the schema URI, every missing
    ``table:columns``/asset description, and ``file:size``/``file:checksum``
    for the committed (non-data) assets.
    """
    dataset_dir = catalog / dataset_relpath(dataset_id, catalog=catalog)
    collection_path = dataset_dir / "collection.json"
    doc = read_json(collection_path)
    rewrite_root_links(doc, depth=dataset_depth(dataset_id, catalog=catalog))
    if "ftw:config" in doc:
        unresolved: list[str] = []
        doc["ftw:config"] = strip_local_paths(doc["ftw:config"], unresolved=unresolved)
        for value in unresolved:
            print(f"warning  {dataset_id}: ftw:config path {value} is outside the repository; "
                  f"published as its file name only")
    _ensure_parent_link(doc)
    _ensure_llms_link(doc)
    _append_host_provider(doc, manifest)
    _ensure_version(doc, manifest)
    _ensure_via(doc, recipe)
    _rewrite_via_link(doc)
    _ensure_license_link(doc, recipe)
    _ensure_pmtiles_links(doc)
    _refresh_asset_sizes(doc, staging / dataset_id)
    canonicalize_portolan_schema(doc)
    fill_table_column_descriptions(doc, group=dataset_relpath(dataset_id, catalog=catalog).split("/")[0],
                                    dataset_dir=dataset_dir)
    fill_asset_descriptions(doc)
    fill_local_checksums(doc, dataset_dir)
    doc["updated"] = _now_iso(now)
    write_json(collection_path, doc)
    return [collection_path, *reapply_chip_subcatalog_schema(dataset_dir)]


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
    directory inside the catalog, e.g. ``at/at_2024``) and then published: markdown
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


def _browse_block(relpath: str, title: str, *, manifest: dict, has_thumbnail: bool) -> str:
    """The marker-delimited "Browse" block: the thumbnail, then the three ways in.

    ``relpath`` is the collection's published ``<source>/<id>``.
    """
    lines = [_BROWSE_START]
    if has_thumbnail:
        lines += [f"![{title} thumbnail]({public_url(f'{relpath}/thumbnail.webp')})", ""]
    lines.append(
        f"Open this collection in the [data browser]({browser_url(f'{relpath}/collection.json')}), "
        f"read the [agent guide]({human_url(manifest, f'{relpath}/AGENTS.md')}), or query "
        f"[items.parquet]({public_url(f'{relpath}/items.parquet')}) directly."
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
    relpath = dataset_relpath(dataset_id, catalog=catalog)
    dataset_dir = catalog / relpath
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
                relpath,
                collection_title,
                manifest=manifest,
                has_thumbnail=(dataset_dir / "thumbnail.webp").is_file(),
            ),
        )
        text = absolutize_links(text, base_rel=relpath, manifest=manifest)
        readme_path.write_text(text)
        written.append(readme_path)

    if agents_path.is_file():
        text = agents_path.read_text()
        text = _insert_after_heading(
            text,
            "## Accessing the data",
            f"Browse the collection in the [Portolan data browser]"
            f"({browser_url(f'{relpath}/collection.json')}), or read the files below straight "
            f"from [collection.json]({public_url(f'{relpath}/collection.json')}).",
        )
        text = absolutize_links(text, base_rel=relpath, manifest=manifest)
        agents_path.write_text(text)
        written.append(agents_path)

    return written


# --- llms.txt for one collection -------------------------------------------


def write_llms(dataset_id: str, *, catalog: Path = CATALOG) -> Path:
    """Write ``catalog/<source>/<id>/llms.txt``: title, blurb, and public URLs of the metadata."""
    relpath = dataset_relpath(dataset_id, catalog=catalog)
    doc = read_json(catalog / relpath / "collection.json")
    title = doc.get("title", dataset_id)
    description = (doc.get("description") or "").strip().split(". ")[0].rstrip(".") + "."

    lines = [
        f"# {title}",
        "",
        f"> {description}",
        "",
        f"- [Collection]({public_url(f'{relpath}/collection.json')})",
        f"- [README]({public_url(f'{relpath}/README.md')})",
        f"- [Agent guide]({public_url(f'{relpath}/AGENTS.md')})",
    ]
    for key, asset in sorted((doc.get("assets") or {}).items()):
        href = asset.get("href", "")
        if not href.endswith((".parquet", ".pmtiles")):
            continue
        filename = href[2:] if href.startswith("./") else href
        title_ = asset.get("title", key)
        lines.append(f"- [{title_}]({public_url(f'{relpath}/{filename}')})")

    path = catalog / relpath / "llms.txt"
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
    relpath: str, collection_title: str, square: str, n_chips: int, *, manifest: dict
) -> str:
    plural = "chip" if n_chips == 1 else "chips"
    collection_readme = human_url(manifest, f"{relpath}/README.md")
    return (
        f"# {collection_title} — MGRS square {square}\n\n"
        f"This square holds {n_chips} {plural} on the FTW grid. Each item carries the same "
        "asset types as the rest of the collection — label masks and, where imagery was "
        f"downloaded, clipped scenes — see the [collection README]({collection_readme}) for what "
        "every asset means.\n"
    )


def _subcatalog_agents(
    relpath: str, collection_title: str, square: str, *, manifest: dict
) -> str:
    """The square's agent guide, with every link and the query's path published.

    The query reads the collection's mirror by its public URL rather than a
    relative path: this file is published, and a reader who found it on the
    web has no collection directory to run it from.
    """
    items = public_url(f"{relpath}/items.parquet")
    guide = human_url(manifest, f"{relpath}/AGENTS.md")
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

    For each ``catalog/<source>/<id>/chips/<square>/catalog.json``: sets ``title`` on
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
    relpath = dataset_relpath(dataset_id, catalog=catalog)
    for sub_path in sorted((catalog / relpath / "chips").glob("*/catalog.json")):
        square = sub_path.parent.name
        doc = read_json(sub_path)
        _add_item_titles(doc)
        n_chips = len(_add_child_item_links(doc, staging / dataset_id / "chips" / square))
        _ensure_subcatalog_docs_links(doc)
        write_json(sub_path, doc)
        written.append(sub_path)

        readme_path = sub_path.parent / "README.md"
        readme_path.write_text(
            _subcatalog_readme(relpath, collection_title, square, n_chips, manifest=manifest)
        )
        written.append(readme_path)

        agents_path = sub_path.parent / "AGENTS.md"
        agents_path.write_text(
            _subcatalog_agents(relpath, collection_title, square, manifest=manifest)
        )
        written.append(agents_path)

        staged_path = staging / dataset_id / "chips" / square / "catalog.json"
        if staged_path.is_file():
            write_json(staged_path, doc)

    return written


# --- the root catalog: child links and the marker-delimited tables --------


def _built_collections(catalog: Path) -> list[tuple[str, dict]]:
    """``(dataset id, collection)`` for every published collection, sorted by id."""
    return [(dataset_id, read_json(path)) for dataset_id, path in published_collections(catalog).items()]


def _child_links(children: list[tuple[str, str]]) -> list[dict]:
    """``rel: child`` links from ``(href, title)`` pairs, in the order given."""
    return [
        {"rel": "child", "href": href, "type": "application/json", "title": title}
        for href, title in children
    ]


# --- source groups: catalog/<source>/catalog.json, README.md, AGENTS.md ----


def _collection_source_via(doc: dict) -> str | None:
    """The harmonized ``source_via`` a built collection records in its ``ftw:config``."""
    return ((doc.get("ftw:config") or {}).get("config") or {}).get("source_via")


def _collection_year(doc: dict) -> str:
    year = ((doc.get("ftw:config") or {}).get("config") or {}).get("year")
    return str(year) if year is not None else "—"


def _group_members(group: str, catalog: Path) -> list[tuple[str, dict]]:
    return [
        (dataset_id, read_json(path))
        for dataset_id, path in published_collections(catalog).items()
        if path.parent.parent.name == group
    ]


def _group_title(group: str, source_via: str | None, *, catalog: Path, fetch_title) -> str:
    """The harmonized collection's own title, kept once a group catalog carries it.

    Read from the existing ``catalog/<source>/catalog.json`` first, so a rerun
    neither needs the network nor rewrites the title when it is unreachable;
    fetched from ``source_via`` otherwise, falling back to the group id.
    """
    path = catalog / group / "catalog.json"
    if path.is_file():
        title = read_json(path).get("title")
        if title and title != group:
            return title
    return (fetch_title(source_via) if source_via else None) or group


def _group_catalog(
    group: str, title: str, source_page: str | None, members: list[tuple[str, dict]], *,
    manifest: dict, now: datetime | None = None,
) -> dict:
    links = [
        {"rel": "root", "href": "../catalog.json", "type": "application/json"},
        {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
        {"rel": "describedby", "href": "./README.md", "type": "text/markdown", "title": "README"},
        {"rel": "agents", "href": "./AGENTS.md", "type": "text/markdown", "title": "Agent guide"},
    ]
    if source_page:
        links.append({"rel": "via", "href": source_page, "type": "text/html",
                      "title": "Source field boundary collection"})
    links += _child_links(
        [(f"./{dataset_id}/collection.json", doc.get("title", dataset_id)) for dataset_id, doc in members]
    )
    return {
        "type": "Catalog",
        "stac_version": "1.1.0",
        "stac_extensions": [PORTOLAN_SCHEMA_URI, VERSION_EXTENSION_URI],
        "id": group,
        "title": title,
        "description": (
            f"Fields of the World benchmark collections cut from the harmonized field boundary "
            f"collection {title} ({group}), one per year. Train, validation and test splits for "
            f"every chip are in the root chips table (chips.parquet)."
        ),
        "version": manifest["catalog"]["version"],
        # PTL-PRO-003 / PORTO-CORE-057: a sync tool (this one) MUST stamp
        # `updated` on every mirror catalog it checks, including a group
        # whose members did not change. write_group runs on every
        # `catalogize.py --root`, so every group is "checked" each time.
        "updated": _now_iso(now),
        "links": links,
    }


def _source_line(title: str, source_page: str | None) -> str:
    return f"[{title}]({source_page})" if source_page else title


def _group_readme(
    group: str, title: str, source_page: str | None, members: list[tuple[str, dict]], *,
    manifest: dict,
) -> str:
    rows = "".join(
        f"| [{doc.get('title', dataset_id)}]({human_url(manifest, f'{group}/{dataset_id}')}) "
        f"| {_collection_year(doc)} | {_license_cell(doc)} "
        f"| [browse]({browser_url(f'{group}/{dataset_id}/collection.json')}) |\n"
        for dataset_id, doc in members
    )
    return (
        f"# {title}: benchmark collections\n\n"
        f"Fields of the World benchmark chips cut from the harmonized field boundary collection "
        f"{_source_line(title, source_page)}, one collection per year. Each collection has its own "
        f"README with what its chips, masks and imagery contain. Open this group in the "
        f"[data browser]({browser_url(f'{group}/catalog.json')}) or go back to the "
        f"[catalog]({human_url(manifest)}).\n\n"
        "| Collection | Year | License | Browse |\n"
        "| --- | --- | --- | --- |\n"
        f"{rows}"
    )


def _group_agents(
    group: str, title: str, source_page: str | None, members: list[tuple[str, dict]], *,
    manifest: dict,
) -> str:
    collections = "".join(
        f"- `{dataset_id}` ({_collection_year(doc)}): "
        f"[agent guide]({human_url(manifest, f'{group}/{dataset_id}/AGENTS.md')}), "
        f"[collection.json]({public_url(f'{group}/{dataset_id}/collection.json')}), "
        f"[items.parquet]({public_url(f'{group}/{dataset_id}/items.parquet')})\n"
        for dataset_id, doc in members
    )
    root_guide = human_url(manifest, "AGENTS.md")
    return (
        f"# {title}: benchmark collections\n\n"
        "## Overview\n\n"
        f"This group holds the Fields of the World benchmark collections cut from the harmonized "
        f"field boundary collection {_source_line(title, source_page)} (`{group}`), one per year. "
        f"See the [catalog agent guide]({root_guide}) for what every collection carries.\n\n"
        "## Accessing the data\n\n"
        f"{collections}\n"
        "## Schema & field notes\n\n"
        "Every column and asset is documented in each collection's own agent guide; the "
        "collections in this group share one schema.\n\n"
        "## Data quality & usage notes\n\n"
        "Years of the same source can overlap in space. Take splits from the root chips table "
        "(`chips.parquet`), whose `split_hash_v1` and `split_admin2_v1` give a location the same "
        "split in every year, so pooling years never puts the same field on both sides.\n\n"
        "## Example queries\n\n"
        "See each collection's agent guide for worked examples against its `items.parquet`.\n\n"
        "## Related collections\n\n"
        f"The [catalog agent guide]({root_guide}) lists every source group and collection.\n"
    )


def write_group(
    group: str, *, catalog: Path = CATALOG, manifest: dict, fetch_title=fetch_collection_title,
    now: datetime | None = None,
) -> list[Path]:
    """Write ``catalog/<group>/catalog.json``, ``README.md`` and ``AGENTS.md``.

    The group is one harmonized source collection; its children are the
    collections published under ``catalog/<group>/``, sorted by id. A group
    left with no collection has its three files deleted (and says so); returns
    [] then.
    """
    members = _group_members(group, catalog)
    if not members:
        for name in _GROUP_FILES:
            path = catalog / group / name
            if path.is_file():
                path.unlink()
                print(f"note   {group}: no collection left, deleted {path}")
        return []
    source_via = next(
        (via for _, doc in members if (via := _collection_source_via(doc))), None
    )
    source = harmonized_source({"source_via": source_via}) if source_via else None
    source_page = source[0] if source else None
    title = _group_title(group, source_via, catalog=catalog, fetch_title=fetch_title)
    args = (group, title, source_page, members)
    group_dir = catalog / group
    write_json(group_dir / "catalog.json", _group_catalog(*args, manifest=manifest, now=now))
    (group_dir / "README.md").write_text(_group_readme(*args, manifest=manifest))
    (group_dir / "AGENTS.md").write_text(_group_agents(*args, manifest=manifest))
    return [group_dir / "catalog.json", group_dir / "README.md", group_dir / "AGENTS.md"]


_GROUP_FILES = ("catalog.json", "README.md", "AGENTS.md")


def _groups(catalog: Path) -> list[str]:
    return sorted({path.parent.parent.name for path in published_collections(catalog).values()})


# An imagery child item's id suffix: a season scene or a quarterly mosaic.
_IMAGERY_CHILD = "_(planting|harvest|q[1-4])_s2$"


def _imagery_count(dataset_dir: Path) -> int | None:
    """How many chips have Sentinel-2 imagery, or None when unknowable.

    The imagery pass writes one child item per slot alongside its chip, named
    ``<chip>_<slot>_s2`` (a season scene, or a quarterly mosaic ``q1``-``q4``);
    the number of distinct chips behind those ids is the number of chips with
    imagery, whatever slots landed. The items mirror is read first (only its ``id`` column, so this
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
            f"SELECT count(DISTINCT regexp_replace(id, '{_IMAGERY_CHILD}', '')) "
            f"FROM read_parquet(?) WHERE regexp_matches(id, '{_IMAGERY_CHILD}')",
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


def _source_cell(doc: dict) -> str:
    """The Source column: the harmonized collection's human page, from the via link."""
    for link in doc.get("links") or []:
        if link.get("rel") == "via" and link.get("href"):
            name = link["href"].rstrip("/").rsplit("/", 1)[-1]
            return f"[harmonized/{name}]({link['href']})"
    return "—"


def _thumbnail_cell(relpath: str, title: str, *, rendered: bool) -> str:
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
    href = public_url(f"{relpath}/thumbnail.webp")
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
    relpath = dataset_relpath(dataset_id, catalog=catalog)
    has_thumbnail = (catalog / relpath / "thumbnail.webp").is_file()
    return {
        "id": dataset_id,
        "relpath": relpath,
        "title": title,
        "thumbnail": _thumbnail_cell(relpath, title, rendered=has_thumbnail),
        "collection": f"[{title}]({human_url(manifest, relpath)})",
        "chips": f"{counts['total']:,}" if counts else "—",
        "splits": (
            f"{counts['train']:,}/{counts['val']:,}/{counts['test']:,}"
            if counts and counts["train"] is not None
            else "—"
        ),
        "imagery": _imagery_cell(imagery, _imagery_mode(dataset_dir)),
        "imagery_n": _count_cell(imagery),
        "license": _license_cell(doc),
        "source": _source_cell(doc),
        "browse": f"[browse]({browser_url(f'{relpath}/collection.json')})",
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
        collection_url = public_url(f"{row['relpath']}/collection.json")
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
    "`stored` means four-band GeoTIFFs (red, green, blue, NIR at 10 m) clipped to the "
    "chip's mask footprint and published with it: the Q1-Q4 Sentinel-2 quarterly cloudless "
    "mosaics of the collection's year (and planting/harvest scenes, where a collection has "
    "them). `linked` means the chip's imagery items point at "
    "whole Sentinel-2 scenes on the source STAC API, for a reader to window. A chip with "
    "no imagery still carries its masks (and its row in the root chips table) — pair it "
    "with imagery of your own, on the footprint in `items.parquet`."
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


# The root's links to the chips table and its tiles, built by tools/chips_table.py and
# tools/chips_tiles.py and uploaded to the bucket root. Links, not assets: a Portolan
# catalog carries no assets (PTL-AST-005).
ROOT_DATA_LINKS = [
    {
        "rel": "related",
        "href": "./chips.parquet",
        "type": "application/vnd.apache.parquet",
        "title": "Chips of every collection, with one column per split scheme",
    },
    {
        "rel": "related",
        "href": "./chips.pmtiles",
        "type": "application/vnd.pmtiles",
        "title": "Chip locations as vector tiles, with their splits",
    },
]


def regenerate_root(
    manifest: dict,
    *,
    catalog: Path = CATALOG,
    staging: Path = STAGING,
    now: datetime | None = None,
    fetch_title=fetch_collection_title,
) -> list[Path]:
    """Regenerate the source groups, the root catalog's child links and the root docs' tables.

    Rewrites every ``catalog/<source>/`` group (``write_group``). Keeps every
    fixed link in ``catalog/catalog.json`` exactly as it is; rebuilds the
    ``child`` links, one per source group sorted by group id (after the links to
    the chips table and tiles, ``ROOT_DATA_LINKS``), and drops any
    ``rel: self`` link, so the tracked tree stays relative and validates at
    any path (git-backed-catalogs best practice). PORTO-CORE-081 (a catalog
    served from one fixed URL SHOULD carry an absolute ``self`` link) is
    satisfied at publish time instead: ``tools/publish.py`` writes it onto
    the uploaded copy from ``public_base``, never onto the tracked file — see
    ``add_root_self_link`` there. Sets ``stac_extensions`` to the Portolan
    schema URI plus the version extension (PTL-CNF-003: required wherever a
    document carries a top-level ``version``), ``version`` from the
    manifest, and stamps ``updated`` (PTL-PRO-003, and on every group too,
    via ``write_group``). Fills the marker-delimited ``## Collections``
    block in ``catalog/README.md`` and ``catalog/AGENTS.md`` — headline
    totals, the collections table, and the coverage table that says what
    each collection actually carries (``_collections_block``) — and the
    collection list in ``catalog/llms.txt``.
    """
    root_path = catalog / "catalog.json"
    doc = read_json(root_path)
    collections = _built_collections(catalog)
    written: list[Path] = []
    groups = []
    live = _groups(catalog)
    # A group folder whose last collection was removed: write_group deletes its files.
    emptied = {p.parent.name for p in catalog.glob("*/catalog.json")} - set(live)
    for group in sorted(emptied):
        write_group(group, catalog=catalog, manifest=manifest, fetch_title=fetch_title, now=now)
    for group in live:
        written += write_group(group, catalog=catalog, manifest=manifest, fetch_title=fetch_title, now=now)
        groups.append((f"./{group}/catalog.json", read_json(catalog / group / "catalog.json")["title"]))

    data_hrefs = {link["href"] for link in ROOT_DATA_LINKS}
    doc["links"] = [
        link for link in doc["links"]
        if link.get("rel") not in ("child", "self") and link.get("href") not in data_hrefs
    ] + ROOT_DATA_LINKS + _child_links(groups)
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

    return [*written, root_path, catalog / "README.md", catalog / "AGENTS.md", catalog / "llms.txt"]


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


def _check_group(dataset_id: str, recipe: dict, catalog: Path) -> None:
    """Exit when ``catalog/`` has the dataset under another group than its recipe names."""
    group = source_group(recipe.get("source_via"))
    published = dataset_relpath(dataset_id, catalog=catalog).split("/")[0]
    if group and group != published:
        sys.exit(
            f"{dataset_id}: published under catalog/{published}/ but its recipe's source_via "
            f"names {group}; move its catalog folder or fix the recipe"
        )


def catalogize(
    dataset_id: str,
    *,
    manifest: dict,
    staging: Path = STAGING,
    catalog: Path = CATALOG,
    now: datetime | None = None,
) -> list[Path]:
    """Copy ``staging/<id>``'s git-owned metadata into ``catalog/<source>/<id>``, published.

    Returns every file written under ``catalog/<source>/<id>/``. ``items.parquet`` is
    rewritten too, but stays in ``staging/<id>/`` (it is data, never
    committed), so it is not part of the returned list.
    """
    _check_staged(dataset_id, staging)
    recipe = _load_recipe(dataset_id)
    _check_group(dataset_id, recipe, catalog)

    rewrite_staging_items(dataset_id, staging=staging, catalog=catalog)
    rewrite_items_parquet(dataset_id, staging=staging, catalog=catalog)

    written = copy_committed(dataset_id, staging=staging, catalog=catalog)
    written += enrich_collection(
        dataset_id, catalog=catalog, staging=staging, manifest=manifest, recipe=recipe, now=now
    )
    written += enrich_readme(dataset_id, catalog=catalog, manifest=manifest, recipe=recipe)
    relpath = dataset_relpath(dataset_id, catalog=catalog)
    collection_title = read_json(catalog / relpath / "collection.json").get("title", dataset_id)
    written += enrich_subcatalogs(
        dataset_id,
        catalog=catalog,
        staging=staging,
        collection_title=collection_title,
        manifest=manifest,
    )
    written.append(write_llms(dataset_id, catalog=catalog))
    written += write_group(relpath.split("/")[0], catalog=catalog, manifest=manifest)

    return list(dict.fromkeys(written))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy staging/<id>'s git-owned metadata into catalog/<source>/<id>, published.",
    )
    parser.add_argument("dataset_id", nargs="?", help="dataset id, e.g. 'at_2024' (see datasets.yaml)")
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
