#!/usr/bin/env python3
"""tools/chips_collection.py: the all-chips collection, catalog/chips/.

- From a stand-in catalog: the table and tiles are measured from ``staging/chips/``
  (size, columns with descriptions, row count), or carried from the committed
  collection.json when nothing is staged; the style is the default style asset and the
  thumbnail the thumbnail asset; the ``rel: pmtiles`` link names every layer ftwd tiles;
  the license is ``other`` with a ``rel: license`` link; the extent covers every
  published collection; the docs mention the license and provenance and link absolutely.
- The committed ``catalog/chips/``: the root links it as a child, its files are what the
  tool writes (a rerun reproduces them), every column of the table is described, and its
  style draws from the published ``chips/chips.pmtiles``.

Run: python3 tests/test_chips_collection.py
"""
import json
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

try:
    import duckdb
    from ftw_dataset_tools.api import chips_tiles as ftwd_tiles
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import chips_collection  # noqa: E402
from common import CATALOG, PUBLIC_BASE, load_manifest, read_json  # noqa: E402

errors: list[str] = []
MANIFEST = load_manifest()


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_collection(path: Path, bbox: list, interval: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"type": "Collection", "extent": {
        "spatial": {"bbox": [bbox]}, "temporal": {"interval": [interval]}}}))


def relative_links(text: str) -> list[str]:
    return [href for href in re.findall(r"\]\(([^)]+)\)", text) if "://" not in href]


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog, staging = tmp / "catalog", tmp / "staging"
    write_collection(catalog / "aa" / "aa_2021" / "collection.json", [1, 2, 3, 4],
                     ["2021-01-01T00:00:00Z", "2021-12-31T23:59:59Z"])
    write_collection(catalog / "bb" / "bb_2023" / "collection.json", [-5, 0, 2, 9],
                     ["2023-01-01T00:00:00Z", "2023-12-31T23:59:59Z"])
    (staging / "chips").mkdir(parents=True)
    table = staging / "chips" / "chips.parquet"
    con = duckdb.connect()
    con.execute(f"COPY (SELECT 'aa_2021' AS dataset, 'c' || range AS id, "
                f"{{'xmin': 0.0, 'ymin': 0.0, 'xmax': 1.0, 'ymax': 1.0}} AS bbox, "
                f"1 AS extra FROM range(3)) TO '{table}' (FORMAT parquet)")
    con.close()
    (staging / "chips" / "chips.pmtiles").write_bytes(b"x" * 10)
    style = catalog / "chips" / chips_collection.STYLE
    style.parent.mkdir(parents=True)
    style.write_text("{}")
    now = datetime(2026, 1, 1, tzinfo=UTC)

    written = chips_collection.write_chips_collection(MANIFEST, catalog=catalog, staging=staging,
                                                      now=now)
    check(written == [catalog / "chips" / n for n in ("collection.json", "README.md", "AGENTS.md")],
          f"writes the collection's three files: {written}")
    doc = read_json(catalog / "chips" / "collection.json")
    assets = doc["assets"]
    check((doc["type"], doc["id"], doc["updated"]) == ("Collection", "chips", "2026-01-01T00:00:00Z"),
          f"a collection, id chips, stamped from now: {doc['type']}, {doc['id']}, {doc['updated']}")
    chips = assets["chips"]
    check(chips["file:size"] == table.stat().st_size and chips["table:row_count"] == 3
          and chips["roles"] == ["data"] and chips["type"] == "application/vnd.apache.parquet",
          f"the table is a data asset measured from staging/chips/: {chips}")
    columns = {c["name"]: c for c in chips["table:columns"]}
    check(list(columns) == ["dataset", "id", "bbox", "extra"]
          and columns["bbox"]["type"] == "struct" and columns["id"]["type"] == "varchar",
          f"columns are the table's, with top-level DuckDB types: {chips['table:columns']}")
    check(columns["dataset"]["description"] == chips_collection.COLUMNS["dataset"]
          and "description" not in columns["extra"],
          "a known column is described, an unknown one is not made up")
    tiles = assets["chips_tiles"]
    check(tiles["file:size"] == 10 and tiles["roles"] == ["visual"]
          and tiles["type"] == "application/vnd.pmtiles", f"the tiles are a visual asset: {tiles}")
    check(assets["style-split-admin2"]["roles"] == ["style", "default"]
          and assets["style-split-admin2"]["type"] == "application/vnd.mapbox.style+json"
          and assets["style-split-admin2"]["href"] == "./styles/split-admin2.json"
          and assets["style-split-admin2"]["file:checksum"].startswith("1220"),
          f"the style is the default style asset: {assets['style-split-admin2']}")
    check("thumbnail" not in assets, "no thumbnail asset before one is rendered")
    pmtiles = [l for l in doc["links"] if l["rel"] == "pmtiles"]
    check(pmtiles == [{"rel": "pmtiles", "href": "./chips.pmtiles", "type": "application/vnd.pmtiles",
                       "title": tiles["title"],
                       "pmtiles:layers": [*ftwd_tiles.OVERVIEW_LAYERS, "chips"]}],
          f"one rel: pmtiles link naming every layer ftwd tiles: {pmtiles}")
    rels = {l["rel"]: l["href"] for l in doc["links"]}
    check(doc["license"] == "other" and rels.get("license") == "./README.md",
          f"license other, with a rel: license link to the README's License section: {rels}")
    check((rels.get("root"), rels.get("parent")) == ("../catalog.json", "../catalog.json"),
          f"root and parent are the root catalog: {rels}")
    check(doc["extent"] == {"spatial": {"bbox": [[0.0, 0.0, 1.0, 1.0]]}, "temporal": {"interval": [
        ["2021-01-01T00:00:00Z", "2023-12-31T23:59:59Z"]]}},
          f"the bbox is the table's, the time span every published collection's: {doc['extent']}")
    check(tiles["file:checksum"] == chips_collection._checksum(staging / "chips" / "chips.pmtiles"),
          "the data assets carry a multihash checksum")
    check([p["roles"] for p in doc["providers"]][-1] == ["host"]
          and any("producer" in p["roles"] for p in doc["providers"]),
          f"a producer, and the host last: {doc['providers']}")
    readme = (catalog / "chips" / "README.md").read_text()
    agents = (catalog / "chips" / "AGENTS.md").read_text()
    check(readme.startswith(f"# {chips_collection.TITLE}\n") and "## License" in readme
          and "## Provenance" in readme and "**3 chips**" in readme,
          "the README has the title, the row count, a License and a Provenance section")
    check(not relative_links(readme) and not relative_links(agents),
          f"every link in the docs is absolute: {relative_links(readme) + relative_links(agents)}")
    check(f"{PUBLIC_BASE}/chips/chips.parquet" in agents and "## Schema & field notes" in agents,
          "the agent guide names the published table and documents the columns")

    # nothing staged: the measurements carry over; a rendered thumbnail is registered
    (catalog / "chips" / "thumbnail.webp").write_bytes(b"RIFF....WEBP")
    chips_collection.write_chips_collection(MANIFEST, catalog=catalog, staging=tmp / "none", now=now)
    again = read_json(catalog / "chips" / "collection.json")
    check(all(again["assets"]["chips"].get(k) == chips[k] for k in chips_collection.MEASURED)
          and again["assets"]["chips_tiles"]["file:size"] == 10
          and again["extent"] == doc["extent"],
          "with nothing staged, the measurements and the table's bbox carry over")

    # catalogize --root (no staging given) never measures, even with a different table staged
    (staging / "chips" / "chips.pmtiles").write_bytes(b"y" * 99)
    chips_collection.write_chips_collection(MANIFEST, catalog=catalog, now=now)
    carried = read_json(catalog / "chips" / "collection.json")
    check(carried["assets"]["chips_tiles"]["file:size"] == 10,
          "without staging, a different staged file changes nothing: the committed values carry")

    # never measured, nothing staged: no size, and the bbox of every collection
    fresh = tmp / "fresh"
    write_collection(fresh / "aa" / "aa_2021" / "collection.json", [1, 2, 3, 4],
                     ["2021-01-01T00:00:00Z", None])
    unmeasured = chips_collection.build_collection(fresh, tmp / "none", MANIFEST, "x")
    check("file:size" not in unmeasured["assets"]["chips"]
          and unmeasured["extent"] == {"spatial": {"bbox": [[1, 2, 3, 4]]},
                                       "temporal": {"interval": [["2021-01-01T00:00:00Z", None]]}},
          f"never measured: no file:size, the collections' bbox, an open end: {unmeasured}")
    check(again["assets"]["thumbnail"]["roles"] == ["thumbnail"]
          and again["assets"]["thumbnail"]["href"] == "./thumbnail.webp",
          f"a rendered thumbnail is the thumbnail asset: {again['assets'].get('thumbnail')}")
    check(f"{PUBLIC_BASE}/chips/thumbnail.webp" in (catalog / "chips" / "README.md").read_text(),
          "and the README shows it by absolute URL")

# the committed collection
root = read_json(CATALOG / "catalog.json")
children = [l for l in root["links"] if l["rel"] == "child"]
committed = read_json(CATALOG / "chips" / "collection.json")
check(children[0] == {"rel": "child", "href": "./chips/collection.json", "type": "application/json",
                      "title": committed["title"]},
      f"the root links the all-chips collection first, with its title: {children[0]}")
check(not any(l.get("href") in ("./chips.parquet", "./chips.pmtiles") for l in root["links"]),
      "the root no longer links the table and tiles itself")
rebuilt = chips_collection.build_collection(CATALOG, None, MANIFEST, committed["updated"])
check(rebuilt == committed, "catalog/chips/collection.json is what catalogize --root writes "
                            "(rerun tools/chips_collection.py)")
check((CATALOG / "chips" / "README.md").read_text() == chips_collection.readme(committed, MANIFEST)
      and (CATALOG / "chips" / "AGENTS.md").read_text() == chips_collection.agents(committed, MANIFEST),
      "catalog/chips/README.md and AGENTS.md are what the tool writes")
names = [c["name"] for c in committed["assets"]["chips"].get("table:columns", [])]
check(names and set(names) == set(chips_collection.COLUMNS),
      f"every column of the published table is described, and nothing else: {names}")
committed_style = read_json(CATALOG / "chips" / chips_collection.STYLE)
check(committed_style["sources"]["data"]["url"] == f"pmtiles://{PUBLIC_BASE}/chips/chips.pmtiles",
      f"the style draws from the published chips/chips.pmtiles: {committed_style['sources']}")
check("thumbnail" in committed["assets"] and (CATALOG / "chips" / "thumbnail.webp").is_file(),
      "the committed collection has its thumbnail")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the all-chips collection registers its table, tiles, style and thumbnail")
