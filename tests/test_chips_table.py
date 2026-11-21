#!/usr/bin/env python3
"""tools/chips_table.py: the root chips table, from local stand-in datasets.

Two published datasets (one seeded block3x3, one predefined) that share a chip id, and a
staged rebuild of the first with one extra chip and reshuffled splits. Checks:

- --bootstrap freezes each dataset's published split in split_legacy, fills
  split_predefined only for the predefined dataset, and gives a shared location the same
  split_hash_v1 in both datasets;
- a staged dataset under --bootstrap keeps its published splits and the new chip gets
  null legacy;
- a later build carries split_legacy (and unstaged split_predefined) from the previous
  table, not from the reshuffled chips file;
- rows are sorted by group, dataset and id, and the file is GeoParquet;
- duplicate chips, bad split values, a missing staged file and a later build without a
  previous table are refused.

Run: python3 tests/test_chips_table.py
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

import chips_table  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_chips(path: Path, chips: list[tuple[str, str]], admin: bool = True) -> None:
    """chips: (id, split); each chip a small square so the file has real geometry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    rows = ", ".join(f"('{i}', '{s}', {n})" for n, (i, s) in enumerate(chips))
    admin_cols = "'AUT' AS admin0_iso3, 'Austria' AS admin0_name, " if admin else ""
    con.execute(f"""
        COPY (SELECT id, split, {admin_cols}
                     ST_MakeEnvelope(n, 0, n + 0.01, 0.01) AS geometry,
                     {{'xmin': n, 'ymin': 0, 'xmax': n + 0.01, 'ymax': 0.01}} AS bbox
              FROM (VALUES {rows}) t(id, split, n))
        TO '{path}' (FORMAT parquet)""")
    con.close()


def write_catalog(root: Path, datasets: dict[str, tuple[str, str]]) -> None:
    """datasets: {id: (group, split_type)}; recipes and the linked catalog tree."""
    catalog = root / "catalog"
    groups: dict[str, list[str]] = {}
    for dataset_id, (group, split_type) in datasets.items():
        groups.setdefault(group, []).append(dataset_id)
        folder = catalog / group / dataset_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "collection.json").write_text(json.dumps({
            "ftw:chip_size_km": 2.0,
            "assets": {"chips": {"href": f"./{dataset_id}_chips.parquet"}}}))
        (root / "datasets").mkdir(exist_ok=True)
        (root / "datasets" / f"{dataset_id}.yaml").write_text(
            f"source_via: https://data.source.coop/ftw/harmonized-field-data/{group}/"
            f"collection.json\nstages:\n  splits:\n    split_type: {split_type}\n")
    for group, ids in groups.items():
        (catalog / group / "catalog.json").write_text(json.dumps({"links": [
            {"rel": "child", "href": f"./{d}/collection.json"} for d in ids]}))
    (catalog / "catalog.json").write_text(json.dumps({"links": [
        {"rel": "child", "href": f"./{g}/catalog.json"} for g in groups]}))


def table(path: Path) -> dict[tuple[str, str], tuple]:
    con = duckdb.connect()
    rows = con.execute(
        "SELECT dataset, id, split_legacy, split_predefined, split_hash_v1, block "
        f"FROM read_parquet('{path}')").fetchall()
    con.close()
    return {(r[0], r[1]): r[2:] for r in rows}


SHARED = "ftw-33TUN0000"
AA = [(SHARED, "train"), ("ftw-33TUN0002", "test"), ("ftw-33TUN0602", "val")]
BB = [(SHARED, "test"), ("ftw-33TUN2020", "val")]

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    base = root / "bucket"
    staging = root / "staging"
    write_catalog(root, {"aa_2021": ("aa", "block3x3"), "bb_2022": ("bb", "predefined")})
    write_chips(base / "aa" / "aa_2021" / "aa_2021_chips.parquet", AA)
    write_chips(base / "bb" / "bb_2022" / "bb_2022_chips.parquet", BB, admin=False)
    kw = {"catalog": root / "catalog", "staging": staging, "base": str(base), "root": root}

    # --bootstrap from the published files
    boot = root / "boot.parquet"
    rows = chips_table.build(chips_table.resolve_inputs(set(), **kw), boot, bootstrap=True,
                             workers=2)
    t = table(boot)
    check(rows == 5, f"bootstrap writes one row per dataset chip: {rows}")
    check(t[("aa_2021", SHARED)][0] == "train" and t[("bb_2022", SHARED)][0] == "test",
          f"split_legacy is each dataset's published split: {t}")
    check(all(v[1] is None for k, v in t.items() if k[0] == "aa_2021"),
          "split_predefined is null for a block3x3 dataset")
    check(t[("bb_2022", "ftw-33TUN2020")][1] == "val",
          "split_predefined holds a predefined dataset's split")
    check(t[("aa_2021", SHARED)][2] == t[("bb_2022", SHARED)][2],
          "a shared location has one split_hash_v1 in every dataset")
    check(all(v[2] in chips_table.SPLITS and v[3] for v in t.values()),
          "every chip has a hash split and a block")
    con = duckdb.connect()
    order = [r[0] for r in con.execute(f"SELECT dataset || id FROM read_parquet('{boot}')").fetchall()]
    meta = con.execute(f"SELECT decode(key) FROM parquet_kv_metadata('{boot}')").fetchall()
    con.close()
    check(order == sorted(order), f"rows are sorted by group, dataset and id: {order}")
    check(("geo",) in meta, f"the table is GeoParquet: {meta}")

    # a staged rebuild of aa_2021: one new chip, reshuffled splits
    staged_rows = [(SHARED, "val"), ("ftw-33TUN0002", "train"), ("ftw-33TUN0602", "val"),
                   ("ftw-33TUN4040", "train")]
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", staged_rows)
    boot2 = root / "boot2.parquet"
    chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), boot2, bootstrap=True,
                      staged=frozenset({"aa_2021"}), workers=2)
    t = table(boot2)
    check(t[("aa_2021", SHARED)][0] == "train",
          f"--bootstrap keeps a staged dataset's published split: {t[('aa_2021', SHARED)]}")
    check(t[("aa_2021", "ftw-33TUN4040")][0] is None, "a new chip has no legacy split")

    # a later build carries frozen splits from the previous table
    later = root / "later.parquet"
    chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), later, bootstrap=False,
                      previous=str(boot), staged=frozenset({"aa_2021"}), workers=2)
    t = table(later)
    check(t[("aa_2021", SHARED)][0] == "train" and t[("aa_2021", "ftw-33TUN0002")][0] == "test",
          f"split_legacy comes from the previous table: {t}")
    check(t[("aa_2021", "ftw-33TUN4040")][0] is None, "a chip added later has null legacy")
    check(t[("bb_2022", "ftw-33TUN2020")][1] == "val",
          "split_predefined of an unstaged dataset is carried over")
    check(len(t) == 6, f"the later build has the new chip: {len(t)}")

    # refusals
    def refused(label: str, fn) -> None:
        try:
            fn()
        except chips_table.ChipsTableError:
            return
        errors.append(f"not refused: {label}")

    refused("a later build without a previous table", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=False))
    refused("a staged dataset without a chips file", lambda: chips_table.resolve_inputs(
        {"bb_2022"}, **kw))
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", [(SHARED, "train"), (SHARED, "val")])
    refused("a duplicate chip", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=True,
        staged=frozenset({"aa_2021"}), workers=2))
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", [(SHARED, "training")])
    write_catalog(root, {"aa_2021": ("aa", "predefined"), "bb_2022": ("bb", "predefined")})
    refused("a split value outside train/val/test", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=True,
        staged=frozenset({"aa_2021"}), workers=2))

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the root chips table freezes legacy splits, keeps predefined ones and hashes the rest")
