#!/usr/bin/env python3
"""tools/chips_tiles.py: one feature per chip location, from a small stand-in table.

Checks the location rows (one per id, dataset count, legacy conflict, the shared hash
split), that a table where one id has two hash splits is refused, and, when tippecanoe
is installed, that the PMTiles archive is written.

Run: python3 tests/test_chips_tiles.py
"""
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

import chips_tiles  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_table(path: Path, rows: list[tuple]) -> None:
    """rows: (dataset, id, split_legacy, split_hash_v1, x) with a square at x."""
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    values = ", ".join(f"('{d}', '{i}', '{l}', '{h}', {x})" for d, i, l, h, x in rows)
    con.execute(f"""
        COPY (SELECT dataset, id, id || '_b' AS block, 'Austria' AS admin0_name,
                     split_legacy, split_hash_v1, ST_MakeEnvelope(x, 0, x + 0.01, 0.01) AS geometry
              FROM (VALUES {values}) t(dataset, id, split_legacy, split_hash_v1, x))
        TO '{path}' (FORMAT parquet)""")
    con.close()


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    table = tmp / "chips.parquet"
    write_table(table, [
        ("aa_2021", "c1", "train", "val", 0), ("aa_2022", "c1", "test", "val", 0),
        ("aa_2021", "c2", "train", "train", 1), ("aa_2022", "c2", "train", "train", 1),
        ("bb_2020", "c3", "val", "test", 2),
    ])
    locations = tmp / "locations.parquet"
    n = chips_tiles.write_locations(str(table), locations)
    con = duckdb.connect()
    rows = {r[0]: r[1:] for r in con.execute(
        f"SELECT id, datasets, legacy_conflict, split_hash_v1 FROM read_parquet('{locations}')"
    ).fetchall()}
    meta = con.execute(f"SELECT decode(key) FROM parquet_kv_metadata('{locations}')").fetchall()
    con.close()
    check(n == 3 and set(rows) == {"c1", "c2", "c3"}, f"one row per chip id: {rows}")
    check(rows["c1"] == (2, True, "val"), f"c1 is in 2 datasets whose legacy splits differ: {rows['c1']}")
    check(rows["c2"] == (2, False, "train"), f"c2's legacy splits agree: {rows['c2']}")
    check(rows["c3"] == (1, False, "test"), f"c3 is in one dataset: {rows['c3']}")
    check(("geo",) in meta, "the locations file is GeoParquet")

    bad = tmp / "bad.parquet"
    write_table(bad, [("aa_2021", "c1", "train", "val", 0), ("aa_2022", "c1", "train", "test", 0)])
    try:
        chips_tiles.write_locations(str(bad), tmp / "x.parquet")
        errors.append("not refused: one chip id with two hash splits")
    except chips_tiles.ChipsTilesError as err:
        check("c1" in str(err), f"the refusal names the chip: {err}")

    from ftw_dataset_tools.api.tiles import tippecanoe_available

    if tippecanoe_available():
        out = tmp / "chips.pmtiles"
        chips_tiles.build_tiles(str(table), out)
        check(out.is_file() and out.stat().st_size > 0, "build_tiles writes the archive")
    else:
        print("skip   tippecanoe is not installed: the archive itself is not built")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the chip tiles keep one feature per location with its splits")
