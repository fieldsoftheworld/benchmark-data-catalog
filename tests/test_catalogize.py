#!/usr/bin/env python3
"""catalogize: staging metadata to catalog, with published links.

Builds a temp staging tree and a temp catalog tree by hand (an items.parquet
written with pyarrow mimicking the actual shape rustac writes — struct-of-
structs assets, links without a ``title`` field, a WKB ``geometry`` column,
and NO GeoParquet ``geo`` key — plus a chips parquet with a ``split`` column
and a fields parquet), and runs ``catalogize.catalogize()`` and
``catalogize.regenerate_root()`` against them. No network, no AWS, no real
ftwd run.

The ``geometry`` column matters: rustac writes it with Parquet's own
``GEOMETRY`` logical type and no ``geo`` key, which pyarrow cannot round-trip
(confirmed against a real ``rustac``-written file — see
``tools/catalogize.py``'s ``_geoparquet_metadata`` docstring), so
``rewrite_items_parquet`` must add a ``geo`` key itself. This gate proves that
with DuckDB: ``typeof(geometry)`` must still start with ``GEOMETRY`` after the
rewrite, not fall back to ``BLOB``.

``catalogize._load_recipe()`` is not parameterized: it always reads the real
``datasets/<id>.yaml`` in this repository. So the dataset ids used here are
real ones (``lu``, ``si``) whose recipes already exist and carry the facts
this gate exercises (``lu``: license CC-BY-4.0, a ``source_via``; ``si``:
license "other" with a ``license_url``). Only ``staging/`` and ``catalog/``
are temporary.

Run: python3 tests/test_catalogize.py
"""
import json
import struct
import sys
import tempfile
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
ASSETS_TYPE = pa.struct([("instance", ASSET_TYPE), ("image_w1", ASSET_TYPE)])

GEOMETRY_FIELD = pa.field(
    "geometry", pa.binary(), metadata={"ARROW:extension:name": "geoarrow.wkb"}
)


def build_items_parquet(path: Path) -> None:
    """items.parquet with absolute build-machine link hrefs and ./file asset hrefs."""
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
                "image_w1": {"href": "./ftw-32UNA7238_2023_w1.tif", "type": "image/tiff", "file:size": 2048},
            },
            "geometry": wkb_point(6.13, 49.61),
        },
        {
            # An id that does not match the ftw-<square><4 digits> pattern: the
            # square must fall back to the parent link's directory name. Also
            # has no `image_w1` asset (None), the way a chip without imagery
            # selected would look in a real struct-of-structs column.
            "id": "oddball-item",
            "links": [
                {"href": f"{build_root}/collection.json", "rel": "root", "type": "application/json"},
                {"href": f"{build_root}/chips/99ZZZ/catalog.json", "rel": "parent", "type": "application/json"},
            ],
            "assets": {
                "instance": {"href": "./oddball-item_instance.tif", "type": "image/tiff", "file:size": 512},
                "image_w1": None,
            },
            "geometry": wkb_point(6.5, 49.7),
        },
    ]
    table = pa.table(
        {
            "id": pa.array([r["id"] for r in rows], type=pa.string()),
            "links": pa.array([r["links"] for r in rows], type=LINKS_TYPE),
            "assets": pa.array([r["assets"] for r in rows], type=ASSETS_TYPE),
            "geometry": pa.array([r["geometry"] for r in rows], type=GEOMETRY_FIELD.type),
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
                {
                    "rel": "item",
                    "href": "./ftw-32UNA7238_2023/ftw-32UNA7238_2023.json",
                    "type": "application/geo+json",
                },
            ],
        },
    )
    write_json(
        root / "chips" / "32UNA" / "ftw-32UNA7238_2023" / "ftw-32UNA7238_2023.json",
        {
            "type": "Feature",
            "id": "ftw-32UNA7238_2023",
            "links": [
                {"rel": "root", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "collection", "href": "../../../collection.json", "type": "application/json"},
                {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            ],
            "assets": {
                "instance": {"href": "./ftw-32UNA7238_2023_instance.tif"},
            },
        },
    )
    # A non-STAC JSON file under chips/: rewrite_staging_items must skip it
    # rather than crash on it or inject a bogus "links" key into it.
    write_json(root / "chips" / "32UNA" / "scratch.json", ["not", "a", "stac", "doc"])

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
    "catalog": {"id": "benchmark-data", "title": "Fields of the World Benchmark Data", "version": "2.0.0-test"},
    "host": {"name": "Source Cooperative", "url": "https://source.coop", "roles": ["host"]},
    "datasets": {
        "lu": {
            "ftw1_name": "luxembourg",
            "ftw1": {"year": 2022, "parcels": 29018, "chips": 808, "train": 643, "val": 81, "test": 84,
                      "license": "CC0-1.0"},
        },
    },
}


# --- _square_for_item: regex match and parent-link fallback ---------------

check(
    catalogize._square_for_item("ftw-32UNA7238_2023", []) == "32UNA",
    "square comes from the id when it matches the pattern",
)
check(
    catalogize._square_for_item("oddball-item", [{"rel": "parent", "href": "/x/out/chips/99ZZZ/catalog.json"}])
    == "99ZZZ",
    "square falls back to the parent link's directory name",
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

    # --- via link ensured from the real lu recipe's source_via ---
    recipe_lu = catalogize._load_recipe("lu")
    via_links = [l for l in collection["links"] if l["rel"] == "via"]
    check(
        len(via_links) == 1 and via_links[0]["href"] == recipe_lu["source_via"],
        "via link added from the recipe's source_via",
    )

    # --- sub-catalog rewritten to depth 3, in both staging and catalog ---
    sub_catalog = json.loads((lu_dir / "chips" / "32UNA" / "catalog.json").read_text())
    sub_root = [l for l in sub_catalog["links"] if l["rel"] == "root"][0]
    check(sub_root["href"] == "../../../catalog.json", "sub-catalog root link at depth 3")
    staged_sub_catalog = json.loads((staging / "lu" / "chips" / "32UNA" / "catalog.json").read_text())
    check(staged_sub_catalog == sub_catalog, "staging sub-catalog matches the copied catalog one (git-owned wins)")

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

    # --- items.parquet: public URLs, no local paths, GeoParquet typing kept, rows equal ---
    table = pq.read_table(staging / "lu" / "items.parquet")
    check(table.num_rows == 2, "items.parquet row count unchanged")

    # Existing schema metadata is kept, and a `geo` key is added (rustac
    # writes no `geo` key at all; without one, DuckDB reads `geometry` as a
    # plain BLOB after the pyarrow round trip instead of GEOMETRY).
    check(
        table.schema.metadata.get(b"stac:geoparquet_version") == b"1.0.0",
        "pre-existing schema metadata (stac:geoparquet_version) is preserved",
    )
    geo_meta = json.loads(table.schema.metadata.get(b"geo") or b"{}")
    check(geo_meta.get("primary_column") == "geometry", "geo metadata names the geometry column")
    check(
        geo_meta.get("columns", {}).get("geometry", {}).get("encoding") == "WKB",
        "geo metadata declares WKB encoding",
    )

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    items_path = staging / "lu" / "items.parquet"
    geom_type = con.execute(f"SELECT typeof(geometry) FROM read_parquet('{items_path}') LIMIT 1").fetchone()[0]
    check(geom_type.startswith("GEOMETRY"), f"DuckDB reads geometry as a GEOMETRY type, got {geom_type!r}")
    xmin = con.execute(f"SELECT ST_XMin(geometry) FROM read_parquet('{items_path}') LIMIT 1").fetchone()[0]
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

    oddball_links = {l["rel"]: l["href"] for l in rows["oddball-item"]["links"]}
    check(
        oddball_links.get("parent") == public_url("lu/chips/99ZZZ/catalog.json"),
        "the fallback-square item's parent link uses the square from its parent link",
    )
    oddball_assets = dict(rows["oddball-item"]["assets"])
    check(
        oddball_assets["instance"]["href"] == public_url("lu/chips/99ZZZ/oddball-item/oddball-item_instance.tif"),
        "the fallback-square item's asset href uses the fallback square",
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

    # --- --root: regenerate child links and the marker tables ------------
    root_manifest = dict(MANIFEST)
    written_root = catalogize.regenerate_root(root_manifest, catalog=catalog, staging=staging)
    check(len(written_root) == 4, "regenerate_root reports 4 files written")

    root_doc = json.loads((catalog / "catalog.json").read_text())
    child_links = [l for l in root_doc["links"] if l["rel"] == "child"]
    check(
        child_links == [{"rel": "child", "href": "./lu/collection.json", "type": "application/json", "title": "Luxembourg"}],
        f"root catalog gets exactly one child link for lu, got {child_links}",
    )
    check(
        root_doc["stac_extensions"] == [catalogize.PORTOLAN_SCHEMA_URI],
        "root catalog stac_extensions set to the pinned Portolan schema URI",
    )
    check(root_doc["version"] == "2.0.0-test", "root catalog version set from the manifest")
    fixed_rels = {l["rel"] for l in root_doc["links"] if l["rel"] != "child"}
    check(fixed_rels == {"root", "describedby", "agents", "llms", "vcs"}, "fixed root links are kept as they were")
    check(not any(l["rel"] == "self" for l in root_doc["links"]), "regenerate_root strips a stray self link")

    root_readme = (catalog / "README.md").read_text()
    check("| lu | Luxembourg |" in root_readme, "root README collections table lists lu")
    check("More prose." in root_readme, "root README prose outside the markers survives")

    root_agents = (catalog / "AGENTS.md").read_text()
    check("| lu | Luxembourg |" in root_agents, "root AGENTS.md collections table lists lu")

    root_llms = (catalog / "llms.txt").read_text()
    check("[Luxembourg](lu/collection.json)" in root_llms, "root llms.txt collection list mentions lu")

    # --- regenerate_root is idempotent too ---
    before = (catalog / "catalog.json").read_text()
    catalogize.regenerate_root(root_manifest, catalog=catalog, staging=staging)
    after = (catalog / "catalog.json").read_text()
    check(before == after, "regenerate_root is idempotent")


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


if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: catalogize copies staging metadata into the catalog with published links")
