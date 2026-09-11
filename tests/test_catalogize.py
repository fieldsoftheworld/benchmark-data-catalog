#!/usr/bin/env python3
"""catalogize: staging metadata to catalog, with published links.

Builds a temp staging tree and a temp catalog tree by hand — chip item JSON
with two imagery child items alongside one chip and none alongside the other,
a stale pre-imagery items.parquet, a chips parquet with a ``split`` column and
a fields parquet — and runs ``catalogize.catalogize()`` and
``catalogize.regenerate_root()`` against them. No network, no AWS, no real
ftwd run.

Two things the fixture is shaped to prove. First, PTL-LNK-002: the sub-catalog
must list every Feature under its own directory, so the chip with children
gains a ``rel: item`` link per child and the chip without children gains none.
Second, ``items.parquet`` is *rebuilt* from the item JSON on disk rather than
patched: the fixture's mirror is the pre-imagery snapshot ftwd's ``stac``
stage writes (one row, stale assets), and the rebuilt file must carry every
chip and child item instead.

The ``geometry`` column matters too. rustac writes a GeoParquet ``geo`` key of
its own, and DuckDB reads the column as ``GEOMETRY('OGC:CRS84')`` from it;
this gate proves that with DuckDB — ``typeof(geometry)`` must start with
``GEOMETRY`` after the rebuild, not fall back to ``BLOB``.

``catalogize._load_recipe()`` is not parameterized: it always reads the real
``datasets/<id>.yaml`` in this repository. So the dataset ids used here are
real ones (``lu``, ``si``) whose recipes already exist and carry the facts
this gate exercises (``lu``: license CC-BY-4.0, a ``source_via``; ``si``:
license "other" with a ``license_url``). Only ``staging/`` and ``catalog/``
are temporary.

Run: python3 tests/test_catalogize.py
"""
import io
import json
import struct
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import catalogize  # noqa: E402
from common import public_url  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


def wkb_point(x: float, y: float) -> bytes:
    """A minimal little-endian WKB Point, the same encoding rustac writes."""
    return struct.pack("<BIdd", 1, 1, x, y)


def collect_hrefs(obj) -> list[str]:
    """Every string found under an ``href`` key, anywhere in ``obj``."""
    hrefs: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "href" and isinstance(value, str):
                hrefs.append(value)
            else:
                hrefs.extend(collect_hrefs(value))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            hrefs.extend(collect_hrefs(item))
    return hrefs


# links: a list<struct<href, rel, type>> — no `title`, matching real rustac output.
LINK_TYPE = pa.struct([("href", pa.string()), ("rel", pa.string()), ("type", pa.string())])
LINKS_TYPE = pa.list_(LINK_TYPE)

# assets: a struct-of-structs with a FIXED set of keys shared by every row
# (real rustac output: instance_mask, semantic_2class_mask, ...), each
# nullable for a row that doesn't have that asset. `file:size` mirrors a real
# field name that would false-positive a naive `"file:" in json.dumps(...)`
# scan for local paths, which is why the no-local-path check below only
# scans href values.
ASSET_TYPE = pa.struct([("href", pa.string()), ("type", pa.string()), ("file:size", pa.int64())])
ASSETS_TYPE = pa.struct([("instance", ASSET_TYPE), ("stale_only", ASSET_TYPE)])

GEOMETRY_FIELD = pa.field(
    "geometry", pa.binary(), metadata={"ARROW:extension:name": "geoarrow.wkb"}
)

# bbox: a struct-of-floats column, the shape ftwd actually writes alongside
# `geometry`. Its presence is what tells rewrite_items_parquet to add a
# GeoParquet 1.1 `covering` entry.
BBOX_TYPE = pa.struct(
    [("xmin", pa.float64()), ("ymin", pa.float64()), ("xmax", pa.float64()), ("ymax", pa.float64())]
)


def build_items_parquet(path: Path) -> None:
    """The stale, pre-imagery mirror ftwd's ``stac`` stage leaves behind.

    One row for the first chip only — no second chip, no child items — with
    absolute build-machine link hrefs, a ``stale_only`` asset key that exists
    nowhere in the item JSON on disk, and no ``geo`` key. Every one of those
    is a marker: none of them may survive a rebuild that reads the item JSON
    instead of patching this file.
    """
    build_root = "/private/tmp/ftwd-build-xyz/out"
    rows = [
        {
            "id": "ftw-32UNA7238_2023",
            "links": [
                {"href": f"{build_root}/collection.json", "rel": "root", "type": "application/json"},
                {"href": f"{build_root}/collection.json", "rel": "collection", "type": "application/json"},
                {"href": f"{build_root}/chips/32UNA/catalog.json", "rel": "parent", "type": "application/json"},
                {
                    "href": f"{build_root}/chips/32UNA/ftw-32UNA7238_2023/ftw-32UNA7238_2023.json",
                    "rel": "self",
                    "type": "application/geo+json",
                },
            ],
            "assets": {
                "instance": {"href": "./ftw-32UNA7238_2023_instance.tif", "type": "image/tiff", "file:size": 1024},
                "stale_only": {"href": "./ftw-32UNA7238_2023_stale.tif", "type": "image/tiff", "file:size": 2048},
            },
            "geometry": wkb_point(6.13, 49.61),
            "bbox": {"xmin": 6.12, "ymin": 49.60, "xmax": 6.14, "ymax": 49.62},
        },
    ]
    table = pa.table(
        {
            "id": pa.array([r["id"] for r in rows], type=pa.string()),
            "links": pa.array([r["links"] for r in rows], type=LINKS_TYPE),
            "assets": pa.array([r["assets"] for r in rows], type=ASSETS_TYPE),
            "geometry": pa.array([r["geometry"] for r in rows], type=GEOMETRY_FIELD.type),
            "bbox": pa.array([r["bbox"] for r in rows], type=BBOX_TYPE),
        }
    )
    schema = table.schema.set(table.schema.get_field_index("geometry"), GEOMETRY_FIELD)
    table = table.cast(schema)
    # Real rustac output carries other schema metadata (e.g.
    # stac:geoparquet_version) but no `geo` key — rewrite_items_parquet must
    # add one without dropping what was already there.
    table = table.replace_schema_metadata({b"stac:geoparquet_version": b"1.0.0"})
    pq.write_table(table, str(path))


def build_chips_parquet(path: Path) -> None:
    ids = ["ftw-32UNA7238_2023", "c2", "c3", "c4"]
    splits = ["train", "train", "val", "test"]
    coverage = [0.9, 0.8, 0.7, 0.6]
    table = pa.table({"id": ids, "split": splits, "field_coverage_pct": coverage})
    pq.write_table(table, str(path))


def build_fields_parquet(path: Path) -> None:
    table = pa.table({"id": list(range(10))})
    pq.write_table(table, str(path))


def build_staging_lu(staging: Path) -> None:
    root = staging / "lu"
    write_json(
        root / "collection.json",
        {
            "type": "Collection",
            "id": "lu",
            "title": "Luxembourg",
            "description": "Benchmark chips for Luxembourg. See the recipe for details.",
            "license": "CC-BY-4.0",
            "links": [
                {"rel": "root", "href": "./collection.json", "type": "application/json"},
                {"rel": "child", "href": "./chips/32UNA/catalog.json", "type": "application/json"},
                {"rel": "describedby", "href": "./README.md", "type": "text/markdown"},
                {"rel": "agents", "href": "./AGENTS.md", "type": "text/markdown"},
                # deliberately no `via` link: enrich_collection must add one
                # from the recipe's source_via.
            ],
            "providers": [{"name": "Fields of the World", "roles": ["processor"], "url": "https://fieldsofthe.world"}],
            "assets": {
                "fields": {"href": "./lu_fields.parquet", "type": "application/vnd.apache.parquet", "title": "Fields"},
                "boundary_lines": {
                    "href": "./lu_boundary_lines.parquet",
                    "type": "application/vnd.apache.parquet",
                    "title": "Boundary lines",
                },
                "chips": {"href": "./lu_chips.parquet", "type": "application/vnd.apache.parquet", "title": "Chips"},
                "items": {"href": "./items.parquet", "type": "application/vnd.apache.parquet", "title": "Items"},
                "chips_tiles": {"href": "./chips.pmtiles", "type": "application/vnd.pmtiles", "title": "Chip tiles"},
                "style-default": {"href": "./styles/default.json", "roles": ["style", "default"]},
            },
        },
    )
    (root / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# Luxembourg\n\nSome facts about Luxembourg.\n")
    (root / "AGENTS.md").write_text("# Agent guide: Luxembourg\n")
    write_json(root / "styles" / "default.json", {"version": 8, "sources": {}, "layers": []})
    write_json(
        root / "chips" / "32UNA" / "catalog.json",
        {
            "type": "Catalog",
            "id": "32UNA",
            "links": [
                {"rel": "root", "href": "../../collection.json", "type": "application/json"},
                # ftwd lists the chip items and only those; the season child
                # items alongside them go unlisted (PTL-LNK-002).
                {
                    "rel": "item",
                    "href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023.json",
                    "type": "application/geo+json",
                },
                {
                    "rel": "item",
                    "href": "./ftw-32UNA7240_2023/ftw-32UNA7240_2023.json",
                    "type": "application/geo+json",
                },
            ],
        },
    )
    # The first chip: two imagery child items alongside it. The second chip
    # (below) has none — the two cases enrich_subcatalogs has to tell apart.
    write_json(
        root / "chips" / "32UNA" / "ftw-32UNA7238_2023" / "ftw-32UNA7238_2023.json",
        {
            "type": "Feature",
            "id": "ftw-32UNA7238_2023",
            "geometry": {"type": "Point", "coordinates": [6.13, 49.61]},
            "bbox": [6.12, 49.60, 6.14, 49.62],
            "properties": {"datetime": "2023-06-01T00:00:00Z"},
            "links": [
                {"rel": "root", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "collection", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
                {
                    "rel": "ftw:planting",
                    "href": "./ftw-32UNA7238_2023_planting_s2.json",
                    "type": "application/json",
                },
            ],
            "assets": {
                "instance": {"href": "./ftw-32UNA7238_2023_instance.tif"},
                "planting_image": {"href": "./ftw-32UNA7238_2023_planting_image_s2.tif"},
            },
        },
    )
    for season in ("planting", "harvest"):
        write_json(
            root / "chips" / "32UNA" / "ftw-32UNA7238_2023" / f"ftw-32UNA7238_2023_{season}_s2.json",
            {
                "type": "Feature",
                "id": f"ftw-32UNA7238_2023_{season}_s2",
                "geometry": {"type": "Point", "coordinates": [6.13, 49.61]},
                "bbox": [6.12, 49.60, 6.14, 49.62],
                "properties": {"ftw:season": season, "datetime": "2023-06-01T00:00:00Z"},
                "links": [
                    {"rel": "root", "href": "../../../collection.json", "type": "application/json"},
                    {"rel": "collection", "href": "../../../collection.json", "type": "application/json"},
                    {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
                    {
                        "rel": "ftw:parent_chip",
                        "href": "./ftw-32UNA7238_2023.json",
                        "type": "application/json",
                    },
                    # An absolute href on a link must survive untouched.
                    {
                        "rel": "via",
                        "href": "https://earth-search.aws.element84.com/v1/collections/x/items/y",
                        "type": "application/json",
                    },
                ],
                "assets": {
                    # A relative href resolves against the CHIP's directory,
                    # not a directory named after this child's own id.
                    "image": {"href": f"./ftw-32UNA7238_2023_{season}_image_s2.tif"},
                    # An absolute scene href must survive untouched.
                    "visual": {"href": "https://e84-earth-search-sentinel-data.s3.example/TCI.tif"},
                },
            },
        )
    write_json(
        root / "chips" / "32UNA" / "ftw-32UNA7240_2023" / "ftw-32UNA7240_2023.json",
        {
            "type": "Feature",
            "id": "ftw-32UNA7240_2023",
            "geometry": {"type": "Point", "coordinates": [6.15, 49.63]},
            "bbox": [6.14, 49.62, 6.16, 49.64],
            "properties": {"datetime": "2023-06-01T00:00:00Z"},
            "links": [
                {"rel": "root", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "collection", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
                {
                    "rel": "self",
                    "href": "/private/tmp/ftwd-build-xyz/out/chips/32UNA/"
                    "ftw-32UNA7240_2023/ftw-32UNA7240_2023.json",
                    "type": "application/geo+json",
                },
            ],
            "assets": {"instance": {"href": "./ftw-32UNA7240_2023_instance.tif"}},
        },
    )
    # A non-STAC JSON file under chips/: rewrite_staging_items must skip it
    # rather than crash on it or inject a bogus "links" key into it, and the
    # mirror rebuild must not try to make an item out of it.
    write_json(root / "chips" / "32UNA" / "scratch.json", ["not", "a", "stac", "doc"])
    # A JSON file inside an item directory that is not a Feature: neither a
    # child item link nor a mirror row may come out of it.
    write_json(
        root / "chips" / "32UNA" / "ftw-32UNA7238_2023" / "notes.json",
        {"type": "NotAFeature", "id": "notes"},
    )

    build_items_parquet(root / "items.parquet")
    build_chips_parquet(root / "lu_chips.parquet")
    build_fields_parquet(root / "lu_fields.parquet")


def build_catalog_root(catalog: Path) -> None:
    write_json(
        catalog / "catalog.json",
        {
            "type": "Catalog",
            "id": "benchmark-data",
            "title": "Fields of the World Benchmark Data",
            "stac_extensions": ["https://schemas.portolan-sdi.org/portolan/v0.1.1/schema.json"],
            "links": [
                {"rel": "root", "href": "./catalog.json", "type": "application/json"},
                {"rel": "describedby", "href": "./README.md", "type": "text/markdown"},
                {"rel": "agents", "href": "./AGENTS.md", "type": "text/markdown"},
                {"rel": "llms", "href": "./llms.txt", "type": "text/plain"},
                {"rel": "vcs", "href": "https://example.invalid/repo"},
                # a stray self link: regenerate_root must strip it.
                {"rel": "self", "href": "https://example.invalid/catalog.json"},
            ],
        },
    )
    (catalog / "README.md").write_text(
        "# Fields of the World Benchmark Data\n\n"
        "## Collections\n\n<!-- collections:start -->\n<!-- collections:end -->\n\nMore prose.\n"
    )
    (catalog / "AGENTS.md").write_text(
        "# Agent guide\n\n## Collections\n\n<!-- collections:start -->\n<!-- collections:end -->\n"
    )
    (catalog / "llms.txt").write_text(
        "# Fields of the World Benchmark Data\n\n"
        "## Collections\n\n<!-- collections:start -->\n<!-- collections:end -->\n"
    )


MANIFEST = {
    "catalog": {
        "id": "benchmark-data",
        "title": "Fields of the World Benchmark Data",
        "version": "2.0.0-test",
        # The base every link for a *person* is built from. Never hard-coded
        # in the tools: pages live on source.coop, bytes on data.source.coop.
        "human_base": "https://source.coop/ftw/benchmark-data",
    },
    "host": {"name": "Source Cooperative", "url": "https://source.coop", "roles": ["host"]},
    "datasets": {
        "lu": {
            "ftw1_name": "luxembourg",
            "ftw1": {"year": 2022, "parcels": 29018, "chips": 808, "train": 643, "val": 81, "test": 84,
                      "license": "CC0-1.0"},
        },
    },
}


# --- _is_chip_item_link: a chip item's file is named after its directory ---

check(
    catalogize._is_chip_item_link({"href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023.json"}),
    "./<chip>/<chip>.json is a chip item link",
)
check(
    not catalogize._is_chip_item_link({"href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023_planting_s2.json"}),
    "a child item's link, whose file is not named after its directory, is not a chip item link",
)


# --- rewrite_root_links: depth and self-removal ----------------------------

doc = {
    "links": [
        {"rel": "root", "href": "./collection.json"},
        {"rel": "self", "href": "/abs/collection.json"},
        {"rel": "child", "href": "./chips/32UNA/catalog.json"},
    ]
}
catalogize.rewrite_root_links(doc, depth=3)
check(
    any(l["href"] == "../../../catalog.json" and l["type"] == "application/json" for l in doc["links"] if l["rel"] == "root"),
    "root link rewritten to the correct depth with type application/json",
)
check(not any(l["rel"] == "self" for l in doc["links"]), "self link removed")
check(any(l["rel"] == "child" for l in doc["links"]), "other links are untouched")

# A root link carrying a stray `title` (ftwd emits the root link as a
# self-reference titled with the collection's own title) must lose it: a
# naive {**link, ...} merge would carry it onto every document in the tree.
doc = {"links": [{"rel": "root", "href": "./collection.json", "title": "Luxembourg"}]}
catalogize.rewrite_root_links(doc, depth=1)
check(
    doc["links"][0] == {"rel": "root", "href": "../catalog.json", "type": "application/json"},
    f"a stray title on the root link is dropped, got {doc['links'][0]}",
)


# --- _ensure_version: sets the version extension only when it sets version -

doc = {}
catalogize._ensure_version(doc, {"catalog": {"version": "2.0.0-test"}})
check(doc["version"] == "2.0.0-test", "_ensure_version sets version from the manifest")
check(
    doc.get("stac_extensions") == [catalogize.VERSION_EXTENSION_URI],
    f"_ensure_version declares the version extension when it sets version, got {doc.get('stac_extensions')}",
)

# Idempotent: a doc that already has a version (and the extension) is untouched.
doc = {"version": "1.0.0", "stac_extensions": [catalogize.VERSION_EXTENSION_URI]}
catalogize._ensure_version(doc, {"catalog": {"version": "2.0.0-test"}})
check(doc["version"] == "1.0.0", "_ensure_version leaves an existing version alone")
check(
    doc["stac_extensions"] == [catalogize.VERSION_EXTENSION_URI],
    "_ensure_version does not duplicate the extension when version was already set",
)

# _add_stac_extension itself is idempotent.
doc = {"stac_extensions": [catalogize.VERSION_EXTENSION_URI]}
catalogize._add_stac_extension(doc, catalogize.VERSION_EXTENSION_URI)
check(
    doc["stac_extensions"] == [catalogize.VERSION_EXTENSION_URI],
    "_add_stac_extension does not add a duplicate entry",
)


# --- _ensure_llms_link: idempotent, next to the parent link -----------------

doc = {"links": []}
catalogize._ensure_llms_link(doc)
catalogize._ensure_llms_link(doc)
check(
    [l for l in doc["links"] if l["rel"] == "llms"]
    == [{"rel": "llms", "href": "./llms.txt", "type": "text/plain", "title": "llms.txt"}],
    f"a llms link is added exactly once, even after two calls, got {doc['links']}",
)


# --- _geoparquet_metadata: a covering entry only when has_bbox is True ------

geo_no_bbox = json.loads(catalogize._geoparquet_metadata(None)[b"geo"])
check(
    "covering" not in geo_no_bbox["columns"]["geometry"],
    "no covering key in geo metadata when has_bbox is False",
)
geo_with_bbox = json.loads(catalogize._geoparquet_metadata(None, has_bbox=True)[b"geo"])
check(
    geo_with_bbox["columns"]["geometry"].get("covering")
    == {
        "bbox": {
            "xmin": ["bbox", "xmin"],
            "ymin": ["bbox", "ymin"],
            "xmax": ["bbox", "xmax"],
            "ymax": ["bbox", "ymax"],
        }
    },
    f"a bbox covering entry is added when has_bbox is True, got {geo_with_bbox}",
)


# --- _rewrite_via_link: PTL-PRO-001, both branches -------------------------

doc = {
    "links": [
        {
            "rel": "via",
            "href": "https://data.source.coop/ftw/harmonized-field-data/lu/collection.json",
            "type": "application/json",
            "title": "Source collection",
        }
    ]
}
catalogize._rewrite_via_link(doc)
check(
    doc["links"][0]
    == {
        "rel": "via",
        "href": "https://source.coop/ftw/harmonized-field-data/lu",
        "type": "text/html",
        "title": "Source field boundary collection",
    },
    f"a data.source.coop via href is rewritten to the human page, got {doc['links'][0]}",
)

doc = {"links": [{"rel": "via", "href": "https://example.com/some/other/page", "type": "application/json"}]}
catalogize._rewrite_via_link(doc)
check(
    doc["links"][0] == {"rel": "via", "href": "https://example.com/some/other/page", "type": "text/html"},
    f"a non-matching via href only gets its type changed, got {doc['links'][0]}",
)

# idempotent: rewriting the already-rewritten human page a second time is a no-op
before_via = dict(doc["links"][0])
catalogize._rewrite_via_link(doc)
check(doc["links"][0] == before_via, "_rewrite_via_link is idempotent on a non-matching href")


# --- _ensure_pmtiles_links: idempotent by (rel, href) -----------------------

doc = {
    "assets": {
        "chips_tiles": {"href": "./chips.pmtiles", "type": "application/vnd.pmtiles", "title": "Chip tiles"},
        "fields": {"href": "./x.parquet", "type": "application/vnd.apache.parquet"},
    },
    "links": [],
}
catalogize._ensure_pmtiles_links(doc)
catalogize._ensure_pmtiles_links(doc)
check(
    [l for l in doc["links"] if l["rel"] == "pmtiles"]
    == [
        {
            "rel": "pmtiles",
            "href": "./chips.pmtiles",
            "type": "application/vnd.pmtiles",
            "title": "Chip tiles",
            "pmtiles:layers": ["chips"],
        }
    ],
    "a pmtiles link (with pmtiles:layers derived from the asset key) is added exactly once, even after two calls",
)
check(
    catalogize.WEB_MAP_LINKS_URI in doc["stac_extensions"]
    and doc["stac_extensions"].count(catalogize.WEB_MAP_LINKS_URI) == 1,
    "the web-map-links extension is declared exactly once when a pmtiles link exists",
)


# --- full pipeline: catalogize("lu", ...) ----------------------------------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"
    build_staging_lu(staging)
    build_catalog_root(catalog)

    now1 = datetime(2026, 1, 1, tzinfo=UTC)
    written1 = catalogize.catalogize("lu", manifest=MANIFEST, staging=staging, catalog=catalog, now=now1)

    # --- files copied, and only those ---
    lu_dir = catalog / "lu"
    all_files = {p.relative_to(lu_dir) for p in lu_dir.rglob("*") if p.is_file()}
    expected = {
        Path("collection.json"),
        Path("README.md"),
        Path("AGENTS.md"),
        Path("llms.txt"),
        Path("styles/default.json"),
        Path("chips/32UNA/catalog.json"),
        Path("chips/32UNA/README.md"),
        Path("chips/32UNA/AGENTS.md"),
    }
    check(all_files == expected, f"exactly the committed files are written, got {sorted(all_files)}")
    check(not (lu_dir / "chips" / "32UNA" / "ftw-32UNA7238_2023").exists(), "item directories are never copied")
    check(
        set(written1) == {lu_dir / p for p in expected},
        f"catalogize() returns exactly the files it wrote, got {sorted(written1)}",
    )

    collection = json.loads((lu_dir / "collection.json").read_text())

    # --- root link at depth 1, no self ---
    root_links = [l for l in collection["links"] if l["rel"] == "root"]
    check(len(root_links) == 1 and root_links[0]["href"] == "../catalog.json", "collection root link at depth 1")
    check(not any(l["rel"] == "self" for l in collection["links"]), "collection has no self link")

    # --- host provider appended once ---
    host_providers = [p for p in collection["providers"] if "host" in p.get("roles", [])]
    check(len(host_providers) == 1 and host_providers[0]["name"] == "Source Cooperative", "host provider appended")

    # --- version and updated stamped ---
    check(collection.get("version") == "2.0.0-test", "version set from the manifest")
    check(collection.get("updated") == "2026-01-01T00:00:00Z", "updated stamped from `now`")

    # --- via link ensured from the real lu recipe's source_via, then
    # rewritten to a browsable page (PTL-PRO-001): lu's source_via matches
    # the data.source.coop/<org>/<repo>/<id>/collection.json shape ---
    recipe_lu = catalogize._load_recipe("lu")
    via_links = [l for l in collection["links"] if l["rel"] == "via"]
    check(
        len(via_links) == 1 and via_links[0]["href"] == "https://source.coop/ftw/harmonized-field-data/lu",
        f"via link rewritten to the source.coop page, got {via_links}",
    )
    check(via_links[0]["type"] == "text/html", "via link type is text/html")
    check(via_links[0]["title"] == "Source field boundary collection", "via link title set")

    # --- parent link to the root catalog (PTL-LNK-001) ---
    parent_links = [l for l in collection["links"] if l["rel"] == "parent"]
    check(
        len(parent_links) == 1 and parent_links[0]["href"] == "../catalog.json",
        f"collection has exactly one parent link to the root catalog, got {parent_links}",
    )

    # --- llms link to the collection's own llms.txt ---
    llms_links = [l for l in collection["links"] if l["rel"] == "llms"]
    check(
        llms_links == [{"rel": "llms", "href": "./llms.txt", "type": "text/plain", "title": "llms.txt"}],
        f"collection has exactly one llms link to its own llms.txt, got {llms_links}",
    )

    # --- pmtiles asset gets a matching rel: pmtiles link (PTL-VIZ-003) ---
    pmtiles_links = [l for l in collection["links"] if l["rel"] == "pmtiles"]
    check(
        pmtiles_links
        == [
            {
                "rel": "pmtiles",
                "href": "./chips.pmtiles",
                "type": "application/vnd.pmtiles",
                "title": "Chip tiles",
                "pmtiles:layers": ["chips"],
            }
        ],
        f"chips_tiles asset gets a matching pmtiles link, got {pmtiles_links}",
    )
    check(
        catalogize.WEB_MAP_LINKS_URI in collection.get("stac_extensions", []),
        "web-map-links extension declared when a pmtiles link exists",
    )

    # --- sub-catalog rewritten to depth 3, in both staging and catalog ---
    sub_catalog = json.loads((lu_dir / "chips" / "32UNA" / "catalog.json").read_text())
    sub_root = [l for l in sub_catalog["links"] if l["rel"] == "root"][0]
    check(sub_root["href"] == "../../../catalog.json", "sub-catalog root link at depth 3")
    staged_sub_catalog = json.loads((staging / "lu" / "chips" / "32UNA" / "catalog.json").read_text())
    check(staged_sub_catalog == sub_catalog, "staging sub-catalog matches the copied catalog one (git-owned wins)")

    # --- rel: item links get a title (PTL-TTL-003), and every Feature under
    # the square's directories is listed: the two chips first, then the child
    # items of the chip that has them, sorted (PTL-LNK-002). The second chip
    # has no children and contributes none. `notes.json` is not a Feature and
    # must not be listed at all. ---
    item_links = [l for l in sub_catalog["links"] if l["rel"] == "item"]
    check(
        item_links == [
            {
                "rel": "item",
                "href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023.json",
                "type": "application/geo+json",
                "title": "ftw-32UNA7238_2023",
            },
            {
                "rel": "item",
                "href": "./ftw-32UNA7240_2023/ftw-32UNA7240_2023.json",
                "type": "application/geo+json",
                "title": "ftw-32UNA7240_2023",
            },
            {
                "rel": "item",
                "href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023_harvest_s2.json",
                "type": "application/geo+json",
                "title": "ftw-32UNA7238_2023_harvest_s2",
            },
            {
                "rel": "item",
                "href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023_planting_s2.json",
                "type": "application/geo+json",
                "title": "ftw-32UNA7238_2023_planting_s2",
            },
        ],
        f"chip item links first with title = the item id, then the child items sorted, got {item_links}",
    )

    # --- describedby/agents links to the square's own docs (PTL-FIL-001/002) ---
    sub_describedby = [l for l in sub_catalog["links"] if l["rel"] == "describedby"]
    sub_agents = [l for l in sub_catalog["links"] if l["rel"] == "agents"]
    check(
        len(sub_describedby) == 1 and sub_describedby[0]["href"] == "./README.md",
        f"sub-catalog has one describedby link to its own README, got {sub_describedby}",
    )
    check(
        len(sub_agents) == 1 and sub_agents[0]["href"] == "./AGENTS.md",
        f"sub-catalog has one agents link to its own AGENTS.md, got {sub_agents}",
    )

    # --- the square's own README.md and AGENTS.md (PTL-FIL-001/002/003) ---
    square_readme = (lu_dir / "chips" / "32UNA" / "README.md").read_text()
    check(
        square_readme.startswith("# Luxembourg — MGRS square 32UNA"),
        f"square README titled with the collection title and square, got {square_readme[:60]!r}",
    )
    # The count is chips, not items: the two child items listed above must
    # not inflate it.
    check("2 chips" in square_readme, "square README states the chip count for this square (2 chips, not 4 items)")
    check(
        "[collection README](https://source.coop/ftw/benchmark-data/lu/README.md)" in square_readme,
        f"square README links back to the collection README by its published URL, got {square_readme}",
    )

    square_agents = (lu_dir / "chips" / "32UNA" / "AGENTS.md").read_text()
    for heading in (
        "## Overview",
        "## Accessing the data",
        "## Schema & field notes",
        "## Data quality & usage notes",
        "## Example queries",
        "## Related collections",
    ):
        check(heading in square_agents, f"square AGENTS.md has the {heading!r} heading")
    check(
        "[collection agent guide](https://source.coop/ftw/benchmark-data/lu/AGENTS.md)" in square_agents,
        f"square AGENTS.md links the collection agent guide by its published URL, got {square_agents}",
    )
    check(
        "WHERE id LIKE 'ftw-32UNA%'" in square_agents,
        "square AGENTS.md gives a DuckDB query filtered on this square",
    )
    check(
        public_url("lu/items.parquet") in square_agents,
        "square AGENTS.md query reads the collection's items.parquet by its public URL, so it "
        "runs for a reader who found this file on the web",
    )
    check(
        "../.." not in square_agents and "../.." not in square_readme,
        "no relative link survives in a square's docs",
    )

    # --- staging item JSON rewritten to depth 4, no self ---
    item_doc = json.loads(
        (staging / "lu" / "chips" / "32UNA" / "ftw-32UNA7238_2023" / "ftw-32UNA7238_2023.json").read_text()
    )
    item_root = [l for l in item_doc["links"] if l["rel"] == "root"][0]
    check(item_root["href"] == "../../../../catalog.json", "staging item root link at depth 4")
    check(not any(l["rel"] == "self" for l in item_doc["links"]), "staging item has no self link")

    # --- non-STAC JSON under chips/ is skipped, not rewritten or crashed on ---
    scratch = json.loads((staging / "lu" / "chips" / "32UNA" / "scratch.json").read_text())
    check(scratch == ["not", "a", "stac", "doc"], "a non-STAC JSON array under chips/ is left untouched")

    # --- README carries the FTW 1.0 section with computed numbers ---
    readme = (lu_dir / "README.md").read_text()
    check("## Compared with Fields of the World 1.0" in readme, "FTW 1.0 section present")
    check("`4` chips" in readme, "computed chip count (4) appears in the FTW 1.0 section")
    check("`2`/`1`/`1`" in readme, "computed split counts (2/1/1) appear in the FTW 1.0 section")
    check("`10` fields" in readme, "computed field count (10) appears in the FTW 1.0 section")
    check("`808` chips" in readme, "the FTW 1.0 chip count (808) appears verbatim from the manifest")

    agents_text1 = (lu_dir / "AGENTS.md").read_text()

    # --- llms.txt written with public URLs ---
    llms = (lu_dir / "llms.txt").read_text()
    check(public_url("lu/collection.json") in llms, "llms.txt links the collection")
    check(public_url("lu/items.parquet") in llms, "llms.txt links items.parquet")
    check(public_url("lu/lu_chips.parquet") in llms, "llms.txt links the chips parquet")
    check(public_url("lu/chips.pmtiles") in llms, "llms.txt links the pmtiles")

    # --- items.parquet: rebuilt from disk, public URLs, no local paths, GeoParquet typing ---
    items_path = staging / "lu" / "items.parquet"
    table = pq.read_table(items_path)
    # 2 chip items + 2 child items. The stale mirror had 1 row and knew
    # nothing of the children, so anything but 4 means it was patched rather
    # than rebuilt.
    check(table.num_rows == 4, f"items.parquet is rebuilt from the item JSON: 4 rows, got {table.num_rows}")
    check(
        sorted(table.column("id").to_pylist())
        == [
            "ftw-32UNA7238_2023",
            "ftw-32UNA7238_2023_harvest_s2",
            "ftw-32UNA7238_2023_planting_s2",
            "ftw-32UNA7240_2023",
        ],
        f"every chip and child item is a row, got {sorted(table.column('id').to_pylist())}",
    )

    # The `geo` key lives in the Parquet file's own key/value metadata, not in
    # `table.schema.metadata` — a file carrying an `ARROW:schema` key (rustac's
    # do) has its schema rebuilt from that, and `geo` never surfaces there.
    file_meta = pq.ParquetFile(items_path).metadata.metadata or {}
    geo_meta = json.loads(file_meta.get(b"geo") or b"{}")
    check(geo_meta.get("primary_column") == "geometry", f"geo metadata names the geometry column, got {geo_meta}")
    check(
        geo_meta.get("columns", {}).get("geometry", {}).get("encoding") == "WKB",
        "geo metadata declares WKB encoding",
    )
    # A `bbox` struct column is written alongside `geometry`, so the geo
    # metadata must carry a GeoParquet 1.1 covering entry pointing at it,
    # letting a reader prune row groups without decoding geometry.
    check(
        geo_meta.get("columns", {}).get("geometry", {}).get("covering")
        == {
            "bbox": {
                "xmin": ["bbox", "xmin"],
                "ymin": ["bbox", "ymin"],
                "xmax": ["bbox", "xmax"],
                "ymax": ["bbox", "ymax"],
            }
        },
        f"geo metadata declares a bbox covering entry, got {geo_meta}",
    )

    # The rebuild writes to a temp file and os.replace()s it into place; no
    # leftover .tmp file should remain once it's done.
    check(
        not (staging / "lu" / "items.parquet.tmp").exists(),
        "no leftover items.parquet.tmp after the rebuild",
    )

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    geom_type = con.execute(
        "SELECT typeof(geometry) FROM read_parquet(?) LIMIT 1", [str(items_path)]
    ).fetchone()[0]
    check(geom_type.startswith("GEOMETRY"), f"DuckDB reads geometry as a GEOMETRY type, got {geom_type!r}")
    xmin = con.execute(
        "SELECT ST_XMin(geometry) FROM read_parquet(?) LIMIT 1", [str(items_path)]
    ).fetchone()[0]
    check(isinstance(xmin, float), f"ST_XMin(geometry) returns a number, got {xmin!r}")

    # The no-local-path check scans href VALUES only: a struct field literally
    # named `file:size` would false-positive a naive "file:" substring search
    # over the whole dumped structure.
    href_values = collect_hrefs(table.column("links").to_pylist()) + collect_hrefs(
        table.column("assets").to_pylist()
    )
    check(all("/private/" not in h for h in href_values), "no /private/ path survives in any href")
    check(all("/Users/" not in h for h in href_values), "no /Users/ path survives in any href")
    check(all("/tmp/" not in h for h in href_values), "no /tmp/ path survives in any href")
    check(all("file:" not in h for h in href_values), "no file: URL survives in any href")
    check(
        all("_stale.tif" not in h for h in href_values),
        "the stale mirror's asset href does not survive the rebuild",
    )

    rows = {r["id"]: r for r in [dict(id=i, links=l, assets=a) for i, l, a in zip(
        table.column("id").to_pylist(), table.column("links").to_pylist(), table.column("assets").to_pylist()
    )]}
    matched_links = {l["rel"]: l["href"] for l in rows["ftw-32UNA7238_2023"]["links"]}
    check(
        matched_links.get("root") == public_url("catalog.json"),
        "matched item's root link is the public root catalog URL",
    )
    check(
        matched_links.get("collection") == public_url("lu/collection.json"),
        "matched item's collection link is the public collection URL",
    )
    check(
        matched_links.get("parent") == public_url("lu/chips/32UNA/catalog.json"),
        "matched item's parent link is the public sub-catalog URL",
    )
    check("self" not in matched_links, "self link dropped from items.parquet")
    matched_assets = dict(rows["ftw-32UNA7238_2023"]["assets"])
    check(
        matched_assets["instance"]["href"]
        == public_url("lu/chips/32UNA/ftw-32UNA7238_2023/ftw-32UNA7238_2023_instance.tif"),
        "asset href rewritten to public_url('<id>/chips/<square>/<item>/<file>')",
    )

    # --- a child item's own row: its relative asset href resolves against
    # its CHIP's directory, not one named after its own id, and an absolute
    # scene href is left exactly as it was ---
    child_assets = dict(rows["ftw-32UNA7238_2023_planting_s2"]["assets"])
    check(
        child_assets["image"]["href"]
        == public_url("lu/chips/32UNA/ftw-32UNA7238_2023/ftw-32UNA7238_2023_planting_image_s2.tif"),
        f"a child item's image asset is a public URL under its chip's directory, "
        f"got {child_assets['image']['href']!r}",
    )
    check(
        child_assets["visual"]["href"] == "https://e84-earth-search-sentinel-data.s3.example/TCI.tif",
        f"a child item's absolute scene href is untouched, got {child_assets['visual']['href']!r}",
    )
    child_links = {l["rel"]: l["href"] for l in rows["ftw-32UNA7238_2023_planting_s2"]["links"]}
    check(
        child_links.get("parent") == public_url("lu/chips/32UNA/catalog.json"),
        f"a child item's parent link is its square's public sub-catalog URL, got {child_links}",
    )
    check(
        child_links.get("via") == "https://earth-search.aws.element84.com/v1/collections/x/items/y",
        "a child item's absolute via link is untouched",
    )

    # --- second run: idempotent apart from `updated` ---
    now2 = datetime(2026, 1, 2, tzinfo=UTC)
    catalogize.catalogize("lu", manifest=MANIFEST, staging=staging, catalog=catalog, now=now2)

    collection2 = json.loads((lu_dir / "collection.json").read_text())
    check(collection2.get("updated") == "2026-01-02T00:00:00Z", "updated advances on rerun")
    collection_sans_updated = {k: v for k, v in collection.items() if k != "updated"}
    collection2_sans_updated = {k: v for k, v in collection2.items() if k != "updated"}
    check(collection_sans_updated == collection2_sans_updated, "collection.json is otherwise identical on rerun")

    host_providers2 = [p for p in collection2["providers"] if "host" in p.get("roles", [])]
    check(len(host_providers2) == 1, "host provider still appears exactly once after a second run")

    readme2 = (lu_dir / "README.md").read_text()
    check(readme2 == readme, "README.md is byte-identical on rerun (no duplicated FTW 1.0 section)")

    check((lu_dir / "AGENTS.md").read_text() == agents_text1, "AGENTS.md stable on rerun")
    check((lu_dir / "llms.txt").read_text() == llms, "llms.txt stable on rerun")

    for rel in ("chips/32UNA/catalog.json",):
        check(
            (catalog / "lu" / rel).read_text() == (staging / "lu" / rel).read_text(),
            f"{rel} stays git-owned-wins consistent after a second run",
        )

    # --- sub-catalog README.md/AGENTS.md are regenerated byte-identically on
    # rerun, not appended to (_subcatalog_readme/_subcatalog_agents write_text
    # the whole file every time; a regression to append-mode would double up
    # the headings and prose checked above) ---
    square_readme2 = (lu_dir / "chips" / "32UNA" / "README.md").read_text()
    check(
        square_readme2 == square_readme,
        "sub-catalog README.md is regenerated byte-identically on rerun, not appended to",
    )
    square_agents2 = (lu_dir / "chips" / "32UNA" / "AGENTS.md").read_text()
    check(
        square_agents2 == square_agents,
        "sub-catalog AGENTS.md is regenerated byte-identically on rerun, not appended to",
    )

    # --- --root: regenerate child links and the marker tables ------------
    root_manifest = dict(MANIFEST)
    root_now = datetime(2026, 1, 3, tzinfo=UTC)
    written_root = catalogize.regenerate_root(root_manifest, catalog=catalog, staging=staging, now=root_now)
    check(len(written_root) == 4, "regenerate_root reports 4 files written")

    root_doc = json.loads((catalog / "catalog.json").read_text())
    child_links = [l for l in root_doc["links"] if l["rel"] == "child"]
    check(
        child_links == [{"rel": "child", "href": "./lu/collection.json", "type": "application/json", "title": "Luxembourg"}],
        f"root catalog gets exactly one child link for lu, got {child_links}",
    )
    check(
        set(root_doc["stac_extensions"]) == {catalogize.PORTOLAN_SCHEMA_URI, catalogize.VERSION_EXTENSION_URI}
        and len(root_doc["stac_extensions"]) == 2,
        f"root catalog stac_extensions carries the Portolan and version URIs with no duplicates, "
        f"got {root_doc['stac_extensions']}",
    )
    check(root_doc["version"] == "2.0.0-test", "root catalog version set from the manifest")
    check(root_doc.get("updated") == "2026-01-03T00:00:00Z", "root catalog updated stamped from `now`")
    fixed_rels = {l["rel"] for l in root_doc["links"] if l["rel"] != "child"}
    check(fixed_rels == {"root", "describedby", "agents", "llms", "vcs"}, "fixed root links are kept as they were")
    check(not any(l["rel"] == "self" for l in root_doc["links"]), "regenerate_root strips a stray self link")

    root_readme = (catalog / "README.md").read_text()
    check(
        "| [Luxembourg](https://source.coop/ftw/benchmark-data/lu) |" in root_readme,
        f"root README collections table links lu's human page, got {root_readme}",
    )
    check("| Thumbnail | Collection |" in root_readme, "root README table leads with Thumbnail")
    check("More prose." in root_readme, "root README prose outside the markers survives")

    root_agents = (catalog / "AGENTS.md").read_text()
    check(
        "| [Luxembourg](https://source.coop/ftw/benchmark-data/lu) |" in root_agents,
        "root AGENTS.md collections table lists lu",
    )
    check(
        "Thumbnail" not in root_agents and "![" not in root_agents,
        "root AGENTS.md carries the same facts without the thumbnail image",
    )

    root_llms = (catalog / "llms.txt").read_text()
    check(
        f"[Luxembourg]({public_url('lu/collection.json')})" in root_llms,
        "root llms.txt collection list links lu's collection.json by public URL",
    )

    # --- regenerate_root is idempotent too (same `now`, so `updated` doesn't move) ---
    before = (catalog / "catalog.json").read_text()
    catalogize.regenerate_root(root_manifest, catalog=catalog, staging=staging, now=root_now)
    after = (catalog / "catalog.json").read_text()
    check(before == after, "regenerate_root is idempotent")

    # --- a thumbnail asset added directly to the catalog copy survives a rerun ---
    # tools/thumbnail.py (a concurrent task) adds a role: thumbnail asset
    # straight to the published collection.json; staging's copy never has
    # one. copy_committed must carry it forward rather than clobber it.
    thumb_collection = json.loads((lu_dir / "collection.json").read_text())
    thumb_collection["assets"]["thumbnail"] = {
        "href": "./thumbnail.webp",
        "type": "image/webp",
        "roles": ["thumbnail"],
        "title": "Thumbnail",
    }
    (lu_dir / "collection.json").write_text(json.dumps(thumb_collection, indent=2) + "\n")

    now3 = datetime(2026, 1, 4, tzinfo=UTC)
    catalogize.catalogize("lu", manifest=MANIFEST, staging=staging, catalog=catalog, now=now3)

    collection3 = json.loads((lu_dir / "collection.json").read_text())
    check(
        collection3.get("assets", {}).get("thumbnail")
        == {"href": "./thumbnail.webp", "type": "image/webp", "roles": ["thumbnail"], "title": "Thumbnail"},
        f"a thumbnail asset added to the catalog copy survives catalogize() rerunning, "
        f"got {collection3.get('assets', {}).get('thumbnail')}",
    )
    check(
        not (staging / "lu" / "collection.json").read_text().count('"thumbnail"'),
        "the staging copy is never given a thumbnail asset (only the catalog copy is)",
    )


# --- regenerate_root: a warning names a dataset whose chips parquet is gone

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"
    build_catalog_root(catalog)

    # "lu" has a real staged chips parquet; "si" is built (a collection.json
    # exists) but its staging tree has been pruned, the state _collection_row
    # falls back to "—" for.
    write_json(catalog / "lu" / "collection.json", {"type": "Collection", "id": "lu", "title": "Luxembourg"})
    write_json(catalog / "si" / "collection.json", {"type": "Collection", "id": "si", "title": "Slovenia"})
    (staging / "lu").mkdir(parents=True, exist_ok=True)
    build_chips_parquet(staging / "lu" / "lu_chips.parquet")

    two_manifest = {"catalog": {"version": "2.0.0-test"}}
    out = io.StringIO()
    with redirect_stdout(out):
        catalogize.regenerate_root(two_manifest, catalog=catalog, staging=staging, now=datetime(2026, 1, 1, tzinfo=UTC))
    printed = out.getvalue()
    check(
        "warning" in printed and "si" in printed and str(staging / "si" / "si_chips.parquet") in printed,
        f"a warning names the dataset (si) and the missing chips parquet path, got {printed!r}",
    )
    check(printed.count("warning") == 1, f"exactly one warning is printed, for si only (lu's parquet exists): {printed!r}")

    root_readme = (catalog / "README.md").read_text()
    check(
        "| — | [Slovenia](" in root_readme and "| — | — | — |" in root_readme,
        f"si's row falls back to '—' for thumbnail, chips, splits and imagery, got {root_readme}",
    )


# --- catalogize(): a missing items.parquet or collection.json exits with a
# clear message naming the file and tools/build.py <id>, instead of an
# opaque traceback from pq.read_table/read_text on a file that isn't there.

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"
    build_catalog_root(catalog)
    # A real recipe (lu) but a staging tree that never reached the stac stage:
    # no items.parquet, no collection.json.
    (staging / "lu").mkdir(parents=True)

    try:
        catalogize.catalogize("lu", manifest=MANIFEST, staging=staging, catalog=catalog)
        check(False, "catalogize() should exit when items.parquet is missing")
    except SystemExit as exc:
        message = str(exc)
        check(
            "items.parquet" in message and "tools/build.py lu" in message,
            f"the exit message names the missing file and the fix, got {message!r}",
        )


# --- catalogize.py main(): an unknown dataset id exits with a clear message,
# not a traceback from _load_recipe's own read_text() ------------------------

out = io.StringIO()
try:
    with redirect_stdout(out):
        catalogize.main(["no-such-dataset-xyz"])
    check(False, "main() should exit for an unknown dataset id")
except SystemExit as exc:
    message = str(exc)
    check(
        "no-such-dataset-xyz" in message and "datasets.yaml" in message,
        f"main() names the bad id and points at datasets.yaml, got {message!r}",
    )


# --- enrich_collection: license 'other' gets a license link from the recipe

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"
    si_dir = catalog / "si"
    write_json(
        si_dir / "collection.json",
        {
            "type": "Collection",
            "id": "si",
            "title": "Slovenia",
            "description": "Benchmark chips for Slovenia.",
            "license": "other",
            "links": [{"rel": "root", "href": "./collection.json", "type": "application/json"}],
            "providers": [],
        },
    )
    si_manifest = {
        "catalog": MANIFEST["catalog"],
        "host": MANIFEST["host"],
        "datasets": {"si": {"ftw1_name": "slovenia"}},  # no ftw1 block: README section must be skipped
    }
    recipe_si = catalogize._load_recipe("si")
    written = catalogize.enrich_collection(
        "si", catalog=catalog, staging=staging, manifest=si_manifest, recipe=recipe_si, now=datetime(2026, 1, 1)
    )
    check(len(written) == 1, "no README written when the manifest carries no ftw1 block for this dataset")
    si_collection = json.loads((si_dir / "collection.json").read_text())
    license_links = [l for l in si_collection["links"] if l["rel"] == "license"]
    check(
        len(license_links) == 1 and license_links[0]["href"] == recipe_si["metadata"]["license_url"],
        "a license link is added from the recipe's license_url when license is 'other'",
    )

    # idempotent: running again does not duplicate the license link
    catalogize.enrich_collection(
        "si", catalog=catalog, staging=staging, manifest=si_manifest, recipe=recipe_si, now=datetime(2026, 1, 1)
    )
    si_collection2 = json.loads((si_dir / "collection.json").read_text())
    check(
        len([l for l in si_collection2["links"] if l["rel"] == "license"]) == 1,
        "license link is added only once",
    )


# --- copy_committed: staging's own thumbnail asset wins over a stale one
# already sitting in the catalog copy. _copy_collection_preserving_thumbnail
# only carries a catalog-side thumbnail *forward* when staging's fresh copy
# has none of its own (see the earlier "thumbnail added directly to the
# catalog copy survives a rerun" case) -- once staging's build produces its
# own thumbnail asset, that fresh one must replace the stale catalog one, not
# be shadowed by it.

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"

    write_json(
        staging / "lu" / "collection.json",
        {
            "type": "Collection",
            "id": "lu",
            "assets": {
                "thumbnail": {
                    "href": "./thumbnail-new.webp",
                    "type": "image/webp",
                    "roles": ["thumbnail"],
                    "title": "New thumbnail",
                },
            },
        },
    )
    write_json(
        catalog / "lu" / "collection.json",
        {
            "type": "Collection",
            "id": "lu",
            "assets": {
                "thumbnail": {
                    "href": "./thumbnail-old.webp",
                    "type": "image/webp",
                    "roles": ["thumbnail"],
                    "title": "Stale thumbnail",
                },
            },
        },
    )

    catalogize.copy_committed("lu", staging=staging, catalog=catalog)
    thumb_result = json.loads((catalog / "lu" / "collection.json").read_text())
    check(
        thumb_result["assets"]["thumbnail"]["href"] == "./thumbnail-new.webp",
        f"staging's own thumbnail asset wins over a stale catalog one, "
        f"got {thumb_result['assets'].get('thumbnail')}",
    )


# --- a failed mirror write leaves no temp file and keeps the original ---------
with tempfile.TemporaryDirectory() as tmp:
    staging = Path(tmp) / "staging"
    build_staging_lu(staging)
    before = (staging / "lu" / "items.parquet").read_bytes()
    real_write = catalogize.rustac.write_sync

    def _boom(*_a, **_k):
        raise OSError("disk full")

    catalogize.rustac.write_sync = _boom
    try:
        raised = False
        try:
            catalogize.rewrite_items_parquet("lu", staging=staging)
        except OSError:
            raised = True
    finally:
        catalogize.rustac.write_sync = real_write
    check(raised, "a failing mirror write propagates the error")
    check(not (staging / "lu" / "items.parquet.tmp").exists(), "no stray items.parquet.tmp after a failed write")
    check((staging / "lu" / "items.parquet").read_bytes() == before, "the original mirror is untouched after a failed write")


# --- rewrite_items_parquet: an empty item tree exits with a clear message -----
with tempfile.TemporaryDirectory() as tmp:
    staging = Path(tmp) / "staging"
    (staging / "lu" / "chips").mkdir(parents=True)
    try:
        catalogize.rewrite_items_parquet("lu", staging=staging)
        check(False, "rewrite_items_parquet should exit when there is no item JSON to rebuild from")
    except SystemExit as exc:
        check(
            "no item JSON" in str(exc) and "tools/build.py lu" in str(exc),
            f"the exit message names the empty tree and the fix, got {str(exc)!r}",
        )

# --- the FTW 1.0 comparison counts the class-filtered fields when present ------
with tempfile.TemporaryDirectory() as tmp:
    staging = Path(tmp) / "staging"; (staging / "lu").mkdir(parents=True)
    con = duckdb.connect()
    con.execute(f"COPY (SELECT range AS id FROM range(10)) TO '{staging / 'lu' / 'lu_fields.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT range AS id FROM range(3)) TO '{staging / 'lu' / 'lu_fields_filtered.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY (SELECT 'ftw-1' AS id, 'train' AS split) TO '{staging / 'lu' / 'lu_chips.parquet'}' (FORMAT PARQUET)")
    con.close()
    spec = {"ftw1_name": "luxembourg", "ftw1": {"year": 2022, "parcels": 29018, "chips": 808, "train": 643, "val": 81, "test": 84, "license": "CC0-1.0"}}
    section = catalogize.ftw1_section("lu", spec, staging=staging, recipe={"metadata": {"description": "edition 2026"}})
    check("`3` fields" in section, "the comparison counts the class-filtered fields, not the full set")

# --- sibling links in the mirror are absolute too -----------------------------
_links = catalogize._rewrite_item_links(
    "lu", "31UFR",
    [{"rel": "ftw:parent_chip", "href": "./ftw-1.json"}, {"rel": "via", "href": "https://x/y"}],
    item_dir="ftw-1",
)
check(_links[0]["href"] == catalogize.public_url("lu/chips/31UFR/ftw-1/ftw-1.json"), "a ./ sibling link becomes a public URL in the mirror")
check(_links[1]["href"] == "https://x/y", "an absolute via link is untouched")

# --- collection asset sizes follow the staged files ----------------------------
with tempfile.TemporaryDirectory() as tmp:
    sd = Path(tmp) / "staging" / "lu"; sd.mkdir(parents=True)
    (sd / "items.parquet").write_bytes(b"x" * 1234)
    doc = {"assets": {"items": {"href": "./items.parquet", "file:size": 1}, "remote": {"href": "https://x/y", "file:size": 7}, "missing": {"href": "./nope.parquet", "file:size": 9}}}
    n = catalogize._refresh_asset_sizes(doc, sd)
    check(n == 1 and doc["assets"]["items"]["file:size"] == 1234, "file:size is re-read from the staged file")
    check(doc["assets"]["remote"]["file:size"] == 7 and doc["assets"]["missing"]["file:size"] == 9, "remote and missing assets keep their size")

# --- the root table's columns: thumbnail, imagery, and the two license forms --
#
# Every cell is a link or a measured number, and the same facts (minus the
# image) go into catalog/AGENTS.md and catalog/llms.txt. The fixture pairs a
# collection with everything (a rendered thumbnail, a chips table, an items
# mirror carrying season child items, an SPDX license, a via link) against one
# with none of it and an 'other' license, which is the pair the row builder has
# to tell apart.

def build_mirror_ids(path: Path, ids: list[str]) -> None:
    """A minimal items mirror: only the `id` column _imagery_count reads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"id": ids}), str(path))


def build_counted_chips_parquet(path: Path, *, train: int, val: int, test: int) -> None:
    """A chips table whose totals are big enough to prove thousands separators."""
    splits = ["train"] * train + ["val"] * val + ["test"] * test
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table({"id": [f"c{i}" for i in range(len(splits))], "split": splits}), str(path)
    )


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    staging = tmp / "staging"
    catalog = tmp / "catalog"

    write_json(
        catalog / "lu" / "collection.json",
        {
            "type": "Collection",
            "id": "lu",
            "title": "Luxembourg",
            "license": "CC-BY-4.0",
            "links": [
                {
                    "rel": "via",
                    "href": "https://source.coop/ftw/harmonized-field-data/lu",
                    "type": "text/html",
                }
            ],
        },
    )
    (catalog / "lu" / "thumbnail.webp").write_bytes(b"RIFF-not-really-a-webp")
    build_counted_chips_parquet(staging / "lu" / "lu_chips.parquet", train=1200, val=20, test=14)
    # Two chips, one of which has both season child items: one chip with imagery.
    build_mirror_ids(
        staging / "lu" / "items.parquet",
        [
            "ftw-32UNA7238_2023",
            "ftw-32UNA7238_2023_planting_s2",
            "ftw-32UNA7238_2023_harvest_s2",
            "ftw-32UNA7240_2023",
        ],
    )

    write_json(
        catalog / "si" / "collection.json",
        {
            "type": "Collection",
            "id": "si",
            "title": "Slovenia",
            "license": "other",
            "links": [
                {"rel": "license", "href": "https://example.invalid/terms", "title": "Ministry terms"}
            ],
        },
    )

    lu_row = catalogize._collection_row(
        "lu",
        json.loads((catalog / "lu" / "collection.json").read_text()),
        staging=staging,
        catalog=catalog,
        manifest=MANIFEST,
    )
    si_row = catalogize._collection_row(
        "si",
        json.loads((catalog / "si" / "collection.json").read_text()),
        staging=staging,
        catalog=catalog,
        manifest=MANIFEST,
    )

    check(
        lu_row["thumbnail"]
        == f'<img src="{public_url("lu/thumbnail.webp")}" alt="Luxembourg" '
        f'width="{catalogize.THUMBNAIL_WIDTH_PX}">',
        f"a rendered thumbnail becomes a width-constrained <img> in the row — markdown image "
        f"syntax carries no size and renders at native resolution, got {lu_row['thumbnail']!r}",
    )
    check(
        si_row["thumbnail"] == "—",
        f"a collection with no thumbnail.webp gets '—', got {si_row['thumbnail']!r}",
    )
    check(
        lu_row["collection"] == "[Luxembourg](https://source.coop/ftw/benchmark-data/lu)",
        f"the Collection cell links the human page from the manifest, got {lu_row['collection']!r}",
    )
    check(lu_row["chips"] == "1,234", f"chips carry thousands separators, got {lu_row['chips']!r}")
    check(
        lu_row["splits"] == "1,200/20/14", f"splits are measured per split, got {lu_row['splits']!r}"
    )
    check(
        lu_row["imagery"] == "1",
        f"imagery counts the chips with season scenes, not the season items, got {lu_row['imagery']!r}",
    )
    check(
        si_row["imagery"] == "—",
        f"a collection with no items mirror shows '—' for imagery, got {si_row['imagery']!r}",
    )
    check(
        lu_row["license"] == "[CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)",
        f"an SPDX license id links its spdx.org page, got {lu_row['license']!r}",
    )
    check(
        si_row["license"] == "[Ministry terms](https://example.invalid/terms)",
        f"an 'other' license shows its license link's title, got {si_row['license']!r}",
    )
    check(
        lu_row["source"] == "[harmonized/lu](https://source.coop/ftw/harmonized-field-data/lu)",
        f"the Source cell links the harmonized human page from the via link, got {lu_row['source']!r}",
    )
    check(si_row["source"] == "—", f"no via link means no source cell, got {si_row['source']!r}")
    check(
        lu_row["browse"] == f"[browse]({catalogize.browser_url('lu/collection.json')})",
        f"the Browse cell links the data browser, got {lu_row['browse']!r}",
    )

    table = catalogize._collections_table([lu_row, si_row])
    header = table.splitlines()[0]
    check(
        header == "| Thumbnail | Collection | Chips | Splits (train/val/test) | Imagery | License "
        "| Source | Browse |",
        f"the README table's header names every column, got {header!r}",
    )
    check(table.count("\n") == 4, f"header, separator and one row per collection, got {table!r}")

    agents_table = catalogize._collections_table([lu_row, si_row], thumbnails=False)
    check(
        agents_table.splitlines()[0].startswith("| Collection |") and "![" not in agents_table,
        f"the AGENTS.md table drops the image column and keeps the rest, got {agents_table!r}",
    )
    check(
        all(cell in agents_table for cell in (lu_row["chips"], lu_row["imagery"], lu_row["source"])),
        "the AGENTS.md table carries the same facts as the README one",
    )

    listed = catalogize._collections_list([lu_row, si_row])
    check(
        f"[Luxembourg]({public_url('lu/collection.json')}): 1,234 chips" in listed,
        f"llms.txt lists each collection by public URL with its chip count, got {listed!r}",
    )
    check("1 with imagery" in listed, f"llms.txt carries the imagery count, got {listed!r}")
    check("![" not in listed, "llms.txt carries no image")


# --- enrich_readme: source line, Browse block, absolute links, idempotence ----
#
# ftwd writes these two files for a tree on a build machine. Everything here is
# what publication needs on top: a source line naming a page a person can read,
# a Browse block under the description, and no relative link anywhere — a
# relative link resolves against the wrong base on source.coop and 404s.

FTWD_README = """# Luxembourg

Benchmark chips for Luxembourg cut from the harmonized field boundary collection.

## Provenance

- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Derived from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/lu/collection.json)
- Masks rasterized at 10 m per pixel

## Access

See [AGENTS.md](AGENTS.md) for the schema, and [the styles](styles/default.json).
"""

FTWD_AGENTS = """# Luxembourg

## Overview

Benchmark chips for Luxembourg.

## Accessing the data

Query `items.parquet` with DuckDB; see the [collection README](README.md).
"""


def build_collection_docs(catalog: Path, *, thumbnail: bool = False) -> Path:
    lu_dir = catalog / "lu"
    write_json(lu_dir / "collection.json", {"type": "Collection", "id": "lu", "title": "Luxembourg"})
    (lu_dir / "README.md").write_text(FTWD_README)
    (lu_dir / "AGENTS.md").write_text(FTWD_AGENTS)
    if thumbnail:
        (lu_dir / "thumbnail.webp").write_bytes(b"RIFF-not-really-a-webp")
    return lu_dir


recipe_lu = catalogize._load_recipe("lu")
SOURCE_STAC = recipe_lu["source_via"]
SOURCE_PAGE = "https://source.coop/ftw/harmonized-field-data/lu"

with tempfile.TemporaryDirectory() as tmp:
    catalog = Path(tmp) / "catalog"
    lu_dir = build_collection_docs(catalog)

    fetched: list[str] = []

    def offline_fetch(url: str, **_kwargs) -> None:
        """The offline case: the harmonized collection.json cannot be read."""
        fetched.append(url)
        return None

    written = catalogize.enrich_readme(
        "lu", catalog=catalog, manifest=MANIFEST, recipe=recipe_lu, fetch_title=offline_fetch
    )
    check(
        written == [lu_dir / "README.md", lu_dir / "AGENTS.md"],
        f"enrich_readme reports both documents it rewrote, got {written}",
    )
    check(
        fetched == [SOURCE_STAC],
        f"the source title is read from the harmonized collection.json exactly once, got {fetched}",
    )

    readme = (lu_dir / "README.md").read_text()
    check("Derived from" not in readme, "ftwd's 'Derived from' line is replaced, not kept alongside")
    check(
        f"- Source data: [Harmonized field boundaries for Luxembourg]({SOURCE_PAGE}) "
        f"(harmonized field boundaries; STAC [collection.json]({SOURCE_STAC}))" in readme,
        f"offline, the source line falls back to a derived title and still links both, got {readme}",
    )

    # --- the Browse block: once, under the description, above the first
    # section, with no image when no thumbnail has been rendered ---
    check(
        readme.count(catalogize._BROWSE_START) == 1 and readme.count(catalogize._BROWSE_END) == 1,
        "the Browse block is inserted exactly once",
    )
    check(
        readme.index("Benchmark chips for Luxembourg")
        < readme.index(catalogize._BROWSE_START)
        < readme.index("## Provenance"),
        "the Browse block sits between the description paragraph and the first section",
    )
    check(
        f"Open this collection in the [data browser]({catalogize.browser_url('lu/collection.json')}), "
        f"read the [agent guide](https://source.coop/ftw/benchmark-data/lu/AGENTS.md), or query "
        f"[items.parquet]({public_url('lu/items.parquet')}) directly." in readme,
        f"the Browse paragraph offers the browser, the agent guide and the mirror, got {readme}",
    )
    check("![" not in readme, "no thumbnail image when no thumbnail.webp has been rendered")

    # --- every relative link is absolute: markdown to the human page, data
    # files to the bucket ---
    check(
        "[AGENTS.md](https://source.coop/ftw/benchmark-data/lu/AGENTS.md)" in readme,
        f"a relative markdown link becomes a source.coop page URL, got {readme}",
    )
    check(
        f"[the styles]({public_url('lu/styles/default.json')})" in readme,
        f"a relative non-markdown link becomes a data.source.coop URL, got {readme}",
    )
    check(
        "](AGENTS.md)" not in readme and "](styles/" not in readme,
        "no relative link survives in the README",
    )
    check(
        "[CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)" in readme,
        "an already-absolute link is left exactly as it was",
    )

    agents = (lu_dir / "AGENTS.md").read_text()
    check(
        catalogize.browser_url("lu/collection.json") in agents,
        f"AGENTS.md gains a data browser pointer, got {agents}",
    )
    check(
        agents.index("## Accessing the data")
        < agents.index("Browse the collection")
        < agents.index("Query `items.parquet`"),
        f"the pointer is the first paragraph under '## Accessing the data', got {agents}",
    )
    check(
        "[collection README](https://source.coop/ftw/benchmark-data/lu/README.md)" in agents,
        f"AGENTS.md's relative links are absolute too, got {agents}",
    )

    # --- rerunning in place changes nothing (markers, and an absolute link
    # stays absolute) ---
    catalogize.enrich_readme(
        "lu", catalog=catalog, manifest=MANIFEST, recipe=recipe_lu, fetch_title=offline_fetch
    )
    check((lu_dir / "README.md").read_text() == readme, "enrich_readme is idempotent on the README")
    check((lu_dir / "AGENTS.md").read_text() == agents, "enrich_readme is idempotent on AGENTS.md")


# --- enrich_readme with a reachable source and a rendered thumbnail ----------

with tempfile.TemporaryDirectory() as tmp:
    catalog = Path(tmp) / "catalog"
    lu_dir = build_collection_docs(catalog, thumbnail=True)

    catalogize.enrich_readme(
        "lu",
        catalog=catalog,
        manifest=MANIFEST,
        recipe=recipe_lu,
        fetch_title=lambda url, **_kwargs: "Luxembourg field boundaries",
    )
    readme = (lu_dir / "README.md").read_text()
    check(
        f"- Source data: [Luxembourg field boundaries]({SOURCE_PAGE})" in readme,
        f"the source collection's own title is used when it can be read, got {readme}",
    )
    check(
        readme.count(f"![Luxembourg thumbnail]({public_url('lu/thumbnail.webp')})") == 1,
        f"the thumbnail image appears once in the Browse block, got {readme}",
    )
    check(
        readme.index("![Luxembourg thumbnail") < readme.index("Open this collection"),
        "the image comes before the Browse paragraph",
    )


if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: catalogize copies staging metadata into the catalog with published links")
