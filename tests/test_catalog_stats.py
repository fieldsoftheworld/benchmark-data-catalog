#!/usr/bin/env python3
"""tools/catalog_stats.py: totals over published datasets, from local stand-ins.

Two fake published datasets on disk (no network): one whose chips already carry
ftwd's admin columns, one with a class filter (so fields_filtered is the count).
Checks the chip count comes from the chips file, not items.parquet (which also holds
imagery child items), storage sums item and collection asset sizes, and countries
add up across datasets.

Run: python3 tests/test_catalog_stats.py
"""
import json
import sys
import tempfile
from pathlib import Path

try:
    import duckdb
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import catalog_stats  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_dataset(base: Path, dataset_id: str, chips: list[tuple], fields: int,
                  items: list[tuple], filtered: bool) -> None:
    """chips: (id, iso3, name); items: (mask bytes, image bytes or None) per item."""
    root = base / dataset_id
    root.mkdir(parents=True)
    con = duckdb.connect()
    rows = ", ".join(f"('{i}', '{iso}', '{name}')" if iso else f"('{i}', NULL, NULL)"
                     for i, iso, name in chips)
    con.execute(f"COPY (SELECT * FROM (VALUES {rows}) t(id, admin0_iso3, admin0_name)) "
                f"TO '{root / 'chips.parquet'}' (FORMAT parquet)")
    fields_name = "fields_filtered.parquet" if filtered else "fields.parquet"
    con.execute(f"COPY (SELECT range AS id FROM range({fields})) TO '{root / fields_name}' "
                "(FORMAT parquet)")
    item_rows = ", ".join(
        "({'mask': {'href': 'm.tif', 'file:size': %d}, 'image': {'href': 'i.tif', 'file:size': %s}})"
        % (m, "NULL" if i is None else i) for m, i in items
    )
    con.execute(f"COPY (SELECT * FROM (VALUES {item_rows}) t(assets)) "
                f"TO '{root / 'items.parquet'}' (FORMAT parquet)")
    con.close()
    assets = {
        "chips": {"href": "./chips.parquet", "file:size": 100},
        "items": {"href": "./items.parquet", "file:size": 10},
        "thumbnail": {"href": "./thumbnail.webp"},
    }
    if filtered:
        assets["fields"] = {"href": "./fields.parquet", "file:size": 1000}
        assets["fields_filtered"] = {"href": "./fields_filtered.parquet", "file:size": 1}
    else:
        assets["fields"] = {"href": "./fields.parquet", "file:size": 1}
    (root / "collection.json").write_text(json.dumps({"id": dataset_id, "assets": assets}))


with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    # 3 chips (one with no country), 5 items: each chip item plus imagery children.
    write_dataset(base, "aa_2021", [("c1", "BRA", "Brazil"), ("c2", "BOL", "Bolivia"),
                                    ("c3", None, None)],
                  fields=7, items=[(5, 50), (5, None), (5, 50), (0, 20), (0, 20)], filtered=False)
    write_dataset(base, "bb_2022", [("d1", "BRA", "Brazil")], fields=4,
                  items=[(1, 2)], filtered=True)

    a = catalog_stats.dataset_stats("aa_2021", base=str(base))
    check(a["chips"] == 3, f"chips counted from the chips file, not items: {a['chips']}")
    check(a["fields"] == 7, f"fields from the footer: {a['fields']}")
    check(a["bytes"] == 155 + 111, f"item asset sizes plus sized collection assets: {a['bytes']}")
    check(a["countries"] == {"BRA": {"name": "Brazil", "chips": 1},
                             "BOL": {"name": "Bolivia", "chips": 1}},
          f"chips without a country are left out: {a['countries']}")

    b = catalog_stats.dataset_stats("bb_2022", base=str(base))
    check(b["fields"] == 4, f"fields_filtered is counted when there is one: {b['fields']}")

    t = catalog_stats.totals([a, b])
    check((t["datasets"], t["chips"], t["fields"]) == (2, 4, 11), f"totals: {t}")
    check(t["countries"]["BRA"] == {"name": "Brazil", "chips": 2, "datasets": 2},
          f"a country adds up across datasets: {t['countries']}")

    catalog = base / "catalog.json"
    catalog.write_text(json.dumps({"links": [
        {"rel": "root", "href": "./catalog.json"},
        {"rel": "child", "href": "./bb_2022/collection.json"},
        {"rel": "child", "href": "./aa_2021/collection.json"},
    ]}))
    ids = catalog_stats.published_ids(catalog)
    check(ids == ["aa_2021", "bb_2022"], f"published ids are the root's children: {ids}")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: catalog stats count chips, fields, storage and countries")
