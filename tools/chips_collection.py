#!/usr/bin/env python3
"""Write the all-chips collection, ``catalog/chips/``: the chips table and its tiles.

    uv run python tools/chips_collection.py   # after staging a new table or tiles

``chips.parquet`` (``tools/chips_table.py``) lists every chip of every published dataset
with one column per split scheme, and ``chips.pmtiles`` (``tools/chips_tiles.py``) maps
them. They are one collection, linked from the root catalog as a child, because the
Portolan data browser maps collections only: a catalog carries no assets (PTL-AST-005).

Writes ``collection.json``, ``README.md`` and ``AGENTS.md``. The style
(``styles/split-admin2.json``) is written by hand and the thumbnail by
``chips_tiles.py --thumbnail``; this registers both as assets. The data files stay in
``staging/chips/``, uploaded by ``upload_data.py --only chips``: their ``file:size``,
``file:checksum``, ``table:columns`` and ``table:row_count``, and the table's bbox (the
spatial extent), are measured there, or carried from the committed ``collection.json``
when nothing is staged. The time span is the published collections'.
``catalogize.py --root`` runs this too.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    ALL_CHIPS,
    CATALOG,
    PORTOLAN_SCHEMA_URI,
    ROOT,
    STAGING,
    public_url,
    published_collections,
    read_json,
    write_json,
)
from ftw_dataset_tools.api.chips_table import TABLE_NAME  # noqa: E402
from ftw_dataset_tools.api.chips_tiles import OVERVIEW_LAYERS, TILES_NAME  # noqa: E402

TITLE = "All chips: every benchmark chip across the collections"
STYLE = "styles/split-admin2.json"
STYLE_KEY = "style-split-admin2"
THUMBNAIL = "thumbnail.webp"
# Every layer of the tiles, overview first: all of them are drawn by default.
TILE_LAYERS = [*OVERVIEW_LAYERS, "chips"]

FILE_URI = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
TABLE_URI = "https://stac-extensions.github.io/table/v1.2.0/schema.json"

PARQUET = "application/vnd.apache.parquet"
PMTILES = "application/vnd.pmtiles"
STYLE_TYPE = "application/vnd.mapbox.style+json"
MARKDOWN = "text/markdown"

# What each column of the table holds. Wording from README.md's "Chips collection"
# section and catalog/README.md's "Splits across collections"; the admin names are
# ftwd's stages.chips.admin_names (FAO GAUL 2024), presence-only from ftwd's docs.
COLUMNS = {
    "dataset": "The collection the chip is in (its id, such as at_2024).",
    "group": "The source group the collection is published under: the harmonized "
             "source collection it was cut from.",
    "id": "The chip's cell id on the FTW grid: the same id is the same square of ground "
          "in every collection.",
    "block": "The chip's 3x3 block of grid cells, the unit split_hash_v1 is drawn for.",
    "admin0_iso3": "ISO 3166-1 alpha-3 code of the chip's country (FAO GAUL 2024).",
    "admin0_name": "The chip's country (FAO GAUL 2024).",
    "admin1_name": "The chip's first-level administrative unit (FAO GAUL 2024).",
    "admin2_name": "The chip's second-level administrative unit (FAO GAUL 2024).",
    "license": "The collection's license, an SPDX id or other.",
    "license_url": "The collection's own license link (the SPDX page for a standard id).",
    "license_category": "The license sorted for filtering: public-domain, attribution and "
                        "share-alike allow any use, including commercial; then "
                        "non-commercial, restricted, and unknown where the terms aren't "
                        "judged yet.",
    "presence_only": "The collection's ftw:presence_only: its labels mark fields that "
                     "exist, not where fields are absent.",
    "split_legacy": "What the collection published before this table (a seeded block3x3 or "
                    "predefined split). Frozen, so chips added later are null.",
    "split_predefined": "The source's own split, for collections whose source defines one.",
    "split_hash_v1": "train, val or test from a stable hash of the chip's block, 80/10/10: "
                     "a location has the same split in every collection and year.",
    "unit_admin2_v1": "The unit split_admin2_v1 assigns: the chip's admin2 area (its admin1 "
                      "when it has no admin2 name, or its block where a country has too "
                      "few admin2 areas to balance).",
    "split_admin2_v1": "train, val or test for whole admin2 units, balanced to 80/10/10 "
                       "within each country. A unit with a presence-only chip is train.",
    "geometry": "The chip's footprint (OGC:CRS84).",
    "bbox": "The footprint's bounding box.",
}

DATA_ASSETS = {
    "chips": {
        "href": f"./{TABLE_NAME}",
        "type": PARQUET,
        "title": "Chips of every collection, with one column per split scheme",
        "roles": ["data"],
        "description": "One row per chip of every published collection, with its splits "
                       "under each scheme, its admin units and its collection's license.",
    },
    "chips_tiles": {
        "href": f"./{TILES_NAME}",
        "type": PMTILES,
        "title": "Chip locations as vector tiles, with their splits",
        "roles": ["visual"],
        "description": "Every chip location at every zoom: one polygon per location from "
                       "zoom 7, each split's chip centres clustered below it.",
    },
}

# The measured fields a data asset carries over from the committed collection.json when
# its file is not staged here.
MEASURED = ("file:size", "file:checksum", "table:columns", "table:row_count")


def _checksum(path: Path) -> str:
    """The multihash (sha2-256) ``file:checksum`` of a file, as ftwd writes it."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return "1220" + digest.hexdigest()


def table_columns(path: Path) -> tuple[list[dict], int]:
    """``table:columns`` (name, top-level DuckDB type, description) and the row count."""
    con = duckdb.connect()
    try:
        source = f"read_parquet('{str(path).replace(chr(39), chr(39) * 2)}')"
        rows = con.execute(f"DESCRIBE SELECT * FROM {source}").fetchall()
        (count,) = con.execute(f"SELECT count(*) FROM {source}").fetchone()
    finally:
        con.close()
    columns = []
    for name, dtype, *_ in rows:
        column = {"name": name, "type": str(dtype).split("(", 1)[0].strip().lower()}
        if name in COLUMNS:
            column["description"] = COLUMNS[name]
        else:
            print(f"warning  {ALL_CHIPS}: column {name} has no description in COLUMNS")
        columns.append(column)
    return columns, int(count)


def table_bbox(path: Path) -> list[float] | None:
    """The bounding box of every row's ``bbox``, or None for a table without one."""
    con = duckdb.connect()
    try:
        source = f"read_parquet('{str(path).replace(chr(39), chr(39) * 2)}')"
        names = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {source}").fetchall()}
        if "bbox" not in names:
            return None
        row = con.execute(f"SELECT min(bbox.xmin), min(bbox.ymin), max(bbox.xmax), "
                          f"max(bbox.ymax) FROM {source}").fetchone()
    finally:
        con.close()
    return None if None in row else [float(v) for v in row]


def _measure(path: Path, kind: str) -> dict:
    out: dict = {"file:size": path.stat().st_size, "file:checksum": _checksum(path)}
    if kind == PARQUET:
        out["table:columns"], out["table:row_count"] = table_columns(path)
    return out


def data_assets(staged: Path, previous: dict) -> dict:
    """The table and tiles assets, measured from ``staged`` or carried from ``previous``."""
    assets = {}
    for key, base in DATA_ASSETS.items():
        asset = dict(base)
        path = staged / base["href"].removeprefix("./")
        if path.is_file():
            asset.update(_measure(path, base["type"]))
        else:
            old = (previous.get("assets") or {}).get(key) or {}
            asset.update({k: old[k] for k in MEASURED if k in old})
            if "file:size" not in asset:
                print(f"warning  {ALL_CHIPS}: {path} is not staged and was never measured; "
                      f"its asset carries no file:size")
        assets[key] = asset
    return assets


def file_assets(folder: Path) -> dict:
    """The committed style and, once rendered, the thumbnail."""
    assets = {}
    style = folder / STYLE
    if style.is_file():
        assets[STYLE_KEY] = {
            "href": f"./{STYLE}", "type": STYLE_TYPE, "title": "Chips by admin2 split",
            "roles": ["style", "default"], "file:size": style.stat().st_size,
            "description": "MapLibre style: chip locations coloured by split_admin2_v1, "
                           "train green, val orange, test purple.",
            "file:checksum": _checksum(style),
        }
    thumbnail = folder / THUMBNAIL
    if thumbnail.is_file():
        assets["thumbnail"] = {
            "href": f"./{THUMBNAIL}", "type": "image/webp", "roles": ["thumbnail"],
            "title": "Chip locations of every collection, by admin2 split",
            "description": "Preview image of the collection rendered with its default map style.",
            "file:size": thumbnail.stat().st_size, "file:checksum": _checksum(thumbnail),
        }
    return assets


def extent(catalog: Path, staged_table: Path, previous: dict) -> dict:
    """The table's own bbox (staged, else as last measured) and the collections' time span.

    Without either measurement, the bbox is the union of the collections' bboxes.
    """
    union = union_extent(catalog)
    bbox = table_bbox(staged_table) if staged_table.is_file() else None
    if bbox:
        union["spatial"] = {"bbox": [bbox]}
    elif (previous.get("extent") or {}).get("spatial"):
        union["spatial"] = previous["extent"]["spatial"]
    return union


def union_extent(catalog: Path) -> dict:
    """The bbox and time span covering every published collection's extent."""
    boxes, starts, ends = [], [], []
    for path in published_collections(catalog).values():
        extent = read_json(path).get("extent") or {}
        boxes += (extent.get("spatial") or {}).get("bbox", [])[:1]
        for start, end in (extent.get("temporal") or {}).get("interval", [])[:1]:
            starts.append(start)
            ends.append(end)
    bbox = [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)] if boxes else [-180, -90, 180, 90]
    start = min((s for s in starts if s), default=None)
    end = None if None in ends else max(ends, default=None)
    return {"spatial": {"bbox": [bbox]}, "temporal": {"interval": [[start, end]]}}


def _links(doc_title: str, manifest: dict) -> list[dict]:
    from catalogize import human_url

    return [
        {"rel": "root", "href": "../catalog.json", "type": "application/json"},
        {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
        {"rel": "describedby", "href": "./README.md", "type": MARKDOWN,
         "title": "Collection README"},
        {"rel": "agents", "href": "./AGENTS.md", "type": MARKDOWN,
         "title": "Collection agent guide"},
        {"rel": "license", "href": "./README.md", "type": MARKDOWN,
         "title": "Each row carries its own collection's license (README, License)"},
        # PTL-PRO-001: hosted by another than its producer, it links its source, the
        # benchmark collections it is built from.
        {"rel": "via", "href": human_url(manifest), "type": "text/html",
         "title": "Source: the benchmark collections the table is built from"},
        {"rel": "pmtiles", "href": f"./{TILES_NAME}", "type": PMTILES,
         "title": doc_title, "pmtiles:layers": TILE_LAYERS},
    ]


def build_collection(catalog: Path, staging: Path, manifest: dict, updated: str) -> dict:
    """The collection.json of ``catalog/chips/``."""
    from catalogize import VERSION_EXTENSION_URI, WEB_MAP_LINKS_URI

    folder = catalog / ALL_CHIPS
    path = folder / "collection.json"
    previous = read_json(path) if path.is_file() else {}
    assets = {**data_assets(staging / ALL_CHIPS, previous), **file_assets(folder)}
    host = manifest["host"]
    return {
        "type": "Collection",
        "stac_version": "1.1.0",
        "stac_extensions": [FILE_URI, TABLE_URI, VERSION_EXTENSION_URI, PORTOLAN_SCHEMA_URI,
                            WEB_MAP_LINKS_URI],
        "id": ALL_CHIPS,
        "title": TITLE,
        "description": (
            "Every chip of every Fields of the World benchmark collection in one table, one "
            "row per collection and chip, with one column per split scheme: split_hash_v1 and "
            "split_admin2_v1 give a location the same split in every collection, so collections "
            "can be pooled without a location on both sides. The tiles map every chip location "
            "by its admin2 split. Each row carries its collection's license."
        ),
        "version": manifest["catalog"]["version"],
        "updated": updated,
        "license": "other",
        "keywords": ["field-boundaries", "benchmark", "splits"],
        "providers": [
            {"name": "Fields of the World", "roles": ["producer", "processor"],
             "url": "https://fieldsofthe.world"},
            {"name": host["name"], "roles": list(host["roles"]), "url": host["url"]},
        ],
        "extent": extent(catalog, staging / ALL_CHIPS / TABLE_NAME, previous),
        "links": _links(DATA_ASSETS["chips_tiles"]["title"], manifest),
        "assets": assets,
    }


def _browse(manifest: dict) -> str:
    from catalogize import browser_url, human_url

    tiles = public_url(f"{ALL_CHIPS}/{TILES_NAME}")
    return (
        f"[Browse in the data browser]({browser_url(f'{ALL_CHIPS}/collection.json')})"
        f" · [map in a PMTiles viewer](https://pmtiles.io/#url={tiles})"
        f" · [agent guide]({human_url(manifest, f'{ALL_CHIPS}/AGENTS.md')})"
        f" · [`{TABLE_NAME}`]({public_url(f'{ALL_CHIPS}/{TABLE_NAME}')})"
        f" · [`{TILES_NAME}`]({tiles})"
        f" · [MapLibre style]({public_url(f'{ALL_CHIPS}/{STYLE}')})"
        f" · [catalog]({human_url(manifest)})\n"
    )


def _column_list(doc: dict) -> str:
    columns = (doc["assets"]["chips"].get("table:columns")
               or [{"name": k, "description": v} for k, v in COLUMNS.items()])
    return "".join(f"- `{c['name']}`: {c.get('description', '')}\n" for c in columns)


def _count_line(doc: dict) -> str:
    rows = doc["assets"]["chips"].get("table:row_count")
    return f"**{rows:,} chips**, measured from the table's row count.\n\n" if rows else ""


_SPLITS = (
    "Each collection assigns its own train / validation / test split, so a location in "
    "several collections (other years of a country, or overlapping regions) can be test in "
    "one and train in another. This table gives every chip of every collection one column "
    "per split scheme; model code picks the column:\n\n"
    "- `split_legacy`: what each collection published before this table. Frozen, so chips "
    "added later are null.\n"
    "- `split_predefined`: the source's own split, for collections whose source defines one.\n"
    "- `split_hash_v1`: one split per location in every collection, from a stable hash of "
    "the chip's 3x3 block of grid cells (80 / 10 / 10 overall). Use it to train and test "
    "across collections without a location on both sides.\n"
    "- `split_admin2_v1`: whole admin2 areas (`unit_admin2_v1`), balanced to 80 / 10 / 10 "
    "within each country, so every country with three areas or more without presence-only "
    "chips has all three splits, and no area is on both sides. An area with any chip from a "
    "presence-only collection is train, since presence-only labels can't be scored; countries "
    "whose chips are all presence-only (India and most of Africa) are train only. Frozen once "
    "published.\n"
)

_LICENSE = (
    "## License\n\n"
    "The table mixes licenses, so the collection's license is `other`: each row carries "
    "its own collection's `license` and `license_url` (the collection's own license link, "
    "the SPDX page for a standard id), and `license_category` sorts them for filtering: "
    "`public-domain`, `attribution` and `share-alike` allow any use, including commercial; "
    "then `non-commercial`, `restricted`, and `unknown` where the terms aren't judged yet. "
    "A chip is published under the terms of the collection it is in.\n"
)


def _provenance(manifest: dict) -> str:
    from catalogize import human_url

    return (
        "## Provenance\n\n"
        "Derived from the published collections: "
        "[ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools) "
        "(`ftwd chips-table`, `ftwd chips-tiles`) reads every collection's "
        "`<id>_chips.parquet` and carries the frozen splits from the previously published "
        "table, run by `tools/chips_table.py` and `tools/chips_tiles.py` in the [source "
        "repository](https://github.com/fieldsoftheworld/benchmark-data-catalog). The "
        f"[catalog]({human_url(manifest)}) lists every collection.\n"
    )


def readme(doc: dict, manifest: dict) -> str:
    """The collection's README.md."""
    table = public_url(f"{ALL_CHIPS}/{TABLE_NAME}")
    thumbnail = (f"![Chip locations of every collection, coloured by their admin2 split: "
                 f"train green, validation orange, test purple]"
                 f"({public_url(f'{ALL_CHIPS}/{THUMBNAIL}')})\n\n"
                 if "thumbnail" in doc["assets"] else "")
    return (
        f"# {TITLE}\n\n"
        f"{doc['description']}\n\n"
        f"{_browse(manifest)}\n"
        f"{thumbnail}"
        f"{_count_line(doc)}"
        "## Splits across collections\n\n"
        f"{_SPLITS}\n"
        "Read one collection's rows with\n"
        f"`SELECT * FROM '{table}' WHERE dataset = 'at_2024'`, or the openly licensed chips "
        "with `... WHERE license_category IN ('public-domain', 'attribution', 'share-alike')`.\n"
        "Rows are sorted by group, dataset and id, so a filter on `dataset` reads few row "
        "groups.\n\n"
        "## Map\n\n"
        f"`{TILES_NAME}` maps one polygon per location from zoom 7 (layer `chips`), with its "
        "`split_admin2_v1`, `split_hash_v1`, whether any of its collections is presence-only, "
        "and whether the collections' own splits disagree there (`legacy_conflict`). Below "
        "zoom 7 its `overview_train`, `overview_val` and `overview_test` layers cluster each "
        "split's chip centres separately, each cluster counting its locations. The MapLibre "
        "style colours train green, validation orange and test purple; from zoom 7, chips are "
        "filled by `split_admin2_v1`, paler where a collection is presence-only, and outlined "
        "in red where the collections' own splits disagree.\n\n"
        "## Columns\n\n"
        f"{_column_list(doc)}\n"
        f"{_LICENSE}\n"
        f"{_provenance(manifest)}"
    )


def agents(doc: dict, manifest: dict) -> str:
    """The collection's AGENTS.md."""
    from catalogize import browser_url, human_url

    table = public_url(f"{ALL_CHIPS}/{TABLE_NAME}")
    return (
        f"# Agent guide: {TITLE}\n\n"
        "## Overview\n\n"
        f"{doc['description']} Open it in the "
        f"[data browser]({browser_url(f'{ALL_CHIPS}/collection.json')}); the "
        f"[catalog agent guide]({human_url(manifest, 'AGENTS.md')}) describes the collections "
        "themselves.\n\n"
        "## Accessing the data\n\n"
        f"- [`{TABLE_NAME}`]({table}): GeoParquet, one row per collection and chip.\n"
        f"- [`{TILES_NAME}`]({public_url(f'{ALL_CHIPS}/{TILES_NAME}')}): vector tiles, layers "
        f"{', '.join(f'`{layer}`' for layer in TILE_LAYERS)}.\n"
        f"- [MapLibre style]({public_url(f'{ALL_CHIPS}/{STYLE}')}).\n\n"
        "## Schema & field notes\n\n"
        f"{_column_list(doc)}\n"
        "## Data quality & usage notes\n\n"
        f"{_SPLITS}\n"
        "A location in several collections has one row per collection, and the same "
        "`split_hash_v1` and `split_admin2_v1` in each. Take a chip's imagery and masks from "
        "its collection (`group`/`dataset`), whose `items.parquet` lists them by `id`.\n\n"
        f"{_LICENSE}\n"
        "## Example queries\n\n"
        "```sql\n"
        "INSTALL spatial; LOAD spatial;\n"
        "SELECT split_admin2_v1, count(*)\n"
        f"FROM read_parquet('{table}')\n"
        "WHERE license_category IN ('public-domain', 'attribution', 'share-alike')\n"
        "GROUP BY 1;\n"
        "```\n\n"
        "## Related collections\n\n"
        f"The [catalog agent guide]({human_url(manifest, 'AGENTS.md')}) lists every source group "
        "and collection.\n"
    )


def write_chips_collection(
    manifest: dict, *, catalog: Path = CATALOG, staging: Path = STAGING,
    now: datetime | None = None,
) -> list[Path]:
    """Write ``catalog/chips/``'s collection.json, README.md and AGENTS.md; the paths."""
    from catalogize import _now_iso

    folder = catalog / ALL_CHIPS
    folder.mkdir(parents=True, exist_ok=True)
    doc = build_collection(catalog, staging, manifest, _now_iso(now))
    paths = [folder / "collection.json", folder / "README.md", folder / "AGENTS.md"]
    write_json(paths[0], doc)
    paths[1].write_text(readme(doc, manifest))
    paths[2].write_text(agents(doc, manifest))
    return paths


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    from common import load_manifest

    for path in write_chips_collection(load_manifest()):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
