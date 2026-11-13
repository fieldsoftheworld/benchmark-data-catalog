#!/usr/bin/env python3
"""Totals over every published benchmark dataset: chips, fields, storage, countries.

    uv run python tools/catalog_stats.py                  # writes work/stats.json
    uv run python tools/catalog_stats.py --out stats.json

The published datasets are the root catalog's children (``catalog/catalog.json``,
which only ever holds published collections). Per dataset it reads, from the
public bucket, without listing it:

- chips: the rows of the chips file (``items.parquet`` also holds each chip's imagery
  child items, so it is not a chip count);
- storage: the ``file:size`` of every asset of every item in ``items.parquet`` (imagery
  and masks) plus every sized asset of ``collection.json`` (vector files, tiles);
- fields: the rows of the fields file the masks were made from
  (``fields_filtered`` when the dataset has a class filter, else ``fields``),
  read from the Parquet footer;
- countries: chips per country, from the chips file's ``admin0_iso3`` and
  ``admin0_name`` (ftwd's ``stages.chips.admin_names``, FAO GAUL 2024). For a chips
  file without them (built before ftwd had the step) the names are looked up the same
  way ftwd does, from each chip's centre.

The tracker page (hannah-rae.github.io/ftw-tracker) shows the result.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CATALOG, PUBLIC_BASE, ROOT  # noqa: E402



def published_ids(catalog_json: Path = CATALOG / "catalog.json") -> list[str]:
    """The ids the root catalog links as children: the published datasets."""
    links = json.loads(catalog_json.read_text())["links"]
    return sorted(
        link["href"].split("/")[-2] for link in links
        if link["rel"] == "child" and link["href"].endswith("/collection.json")
    )


def _read_json(url: str) -> dict:
    if "://" not in url:
        return json.loads(Path(url).read_text())
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def _href(base: str, href: str) -> str:
    return href if "://" in href else f"{base}/{href.removeprefix('./')}"


def _sql(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def items_bytes(con, items_url: str) -> int:
    """The sum of every item asset's file:size."""
    src = f"read_parquet({_sql(items_url)})"
    assets = con.execute(f"SELECT assets FROM {src} LIMIT 0").description
    # The assets struct's fields are this dataset's asset keys; sum each one's file:size.
    keys = [name for name, *_ in con.execute(
        f"SELECT unnest(struct_keys(assets)) FROM (SELECT assets FROM {src} LIMIT 1)"
    ).fetchall()] if assets else []
    sizes = " + ".join(f'coalesce(assets."{k}"."file:size", 0)' for k in keys) or "0"
    (size,) = con.execute(f"SELECT coalesce(sum({sizes}), 0) FROM {src}").fetchone()
    return int(size)


def row_count(con, parquet_url: str) -> int:
    """A Parquet file's row count, from its footer."""
    (rows,) = con.execute(
        f"SELECT sum(num_rows) FROM parquet_file_metadata({_sql(parquet_url)})"
    ).fetchone()
    return int(rows or 0)


def chips_by_country(con, chips_url: str) -> dict[str, dict]:
    """Chips per country: {iso3: {"name": ..., "chips": n}}; chips with no country left out."""
    from ftw_dataset_tools.api import admin_names

    src = f"SELECT * FROM read_parquet({_sql(chips_url)})"
    columns = [c[0] for c in con.execute(f"{src} LIMIT 0").description]
    if {"admin0_iso3", "admin0_name"} <= set(columns):
        table = f"({src})"
    else:
        admin_names.name_chips(con, src)
        table = "_named"
    rows = con.execute(
        f"SELECT admin0_iso3, any_value(admin0_name), count(*) FROM {table} "
        "WHERE admin0_iso3 IS NOT NULL GROUP BY 1"
    ).fetchall()
    return {iso: {"name": name, "chips": int(n)} for iso, name, n in rows}


def dataset_stats(dataset_id: str, base: str = PUBLIC_BASE) -> dict:
    """One published dataset's chips, fields, bytes and countries."""
    root = f"{base}/{dataset_id}"
    collection = _read_json(f"{root}/collection.json")
    assets = collection.get("assets", {})
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    try:
        chip_bytes = items_bytes(con, _href(root, assets["items"]["href"]))
        fields_key = "fields_filtered" if "fields_filtered" in assets else "fields"
        fields = row_count(con, _href(root, assets[fields_key]["href"]))
        chips_url = _href(root, assets["chips"]["href"])
        chips = row_count(con, chips_url)
        countries = chips_by_country(con, chips_url)
    finally:
        con.close()
    vector_bytes = sum(int(a.get("file:size", 0)) for a in assets.values())
    return {"id": dataset_id, "chips": chips, "fields": fields,
            "bytes": chip_bytes + vector_bytes, "countries": countries}


def totals(per_dataset: list[dict]) -> dict:
    """The catalog-wide sums, and per country the datasets that cover it."""
    countries: dict[str, dict] = {}
    for d in per_dataset:
        for iso, c in d["countries"].items():
            entry = countries.setdefault(iso, {"name": c["name"], "chips": 0, "datasets": 0})
            entry["chips"] += c["chips"]
            entry["datasets"] += 1
    return {
        "datasets": len(per_dataset),
        "chips": sum(d["chips"] for d in per_dataset),
        "fields": sum(d["fields"] for d in per_dataset),
        "bytes": sum(d["bytes"] for d in per_dataset),
        "countries": dict(sorted(countries.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "work" / "stats.json")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    ids = published_ids()
    start = time.time()
    with ThreadPoolExecutor(args.workers) as pool:
        per_dataset = list(pool.map(dataset_stats, ids))
    stats = {"generated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
             **totals(per_dataset), "per_dataset": per_dataset}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(stats, indent=1) + "\n")
    print(f"{stats['datasets']} datasets, {stats['chips']:,} chips, {stats['fields']:,} fields, "
          f"{stats['bytes'] / 1e12:.2f} TB, {len(stats['countries'])} countries "
          f"({time.time() - start:.0f}s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
