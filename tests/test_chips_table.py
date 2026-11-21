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
- duplicate chips, bad split values, a missing staged file, a later build without a
  previous table or with an unreadable one, a dataset published twice, and each way of
  losing frozen splits (a --bootstrap rerun over files without split or over a published
  table, a dataset left out of a later build, a staged predefined dataset without split)
  are refused; --drop leaves a dataset out on purpose.

Run: python3 tests/test_chips_table.py
"""
import contextlib
import io
import json
import shutil
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
    write_catalog(root, {"aa_2021": ("zz", "block3x3"), "bb_2022": ("bb", "predefined")})
    write_chips(base / "zz" / "aa_2021" / "aa_2021_chips.parquet", AA)
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
    order = con.execute(f'SELECT "group", dataset, id FROM read_parquet(\'{boot}\')').fetchall()
    meta = con.execute(f"SELECT decode(key) FROM parquet_kv_metadata('{boot}')").fetchall()
    con.close()
    check(order == sorted(order) and order[0][1] == "bb_2022",
          f"rows are sorted by group (bb before zz), then dataset and id: {order}")
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

    # a later build carries frozen splits from the previous table, even when the
    # published files now say something else
    write_chips(base / "bb" / "bb_2022" / "bb_2022_chips.parquet",
                [(SHARED, "train"), ("ftw-33TUN2020", "train")], admin=False)
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
    def refused(label: str, fn, match: str) -> None:
        try:
            fn()
        except chips_table.ChipsTableError as err:
            check(match in str(err), f"{label}: refused for another reason: {err}")
            return
        errors.append(f"not refused: {label}")

    refused("an unreadable previous table", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=False,
        previous=str(root / "nope.parquet"), workers=2), "can't read the previous table")
    refused("a later build without a previous table", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=False), 'needs the previous table')
    refused("a staged dataset without a chips file", lambda: chips_table.resolve_inputs(
        {"bb_2022"}, **kw), 'does not exist')

    # a dataset left out of a later build (unlinked from the catalog)
    write_catalog(root, {"aa_2021": ("zz", "block3x3")})
    refused("a later build that leaves out a dataset of the previous table",
            lambda: chips_table.build(chips_table.resolve_inputs(set(), **kw), root / "x.parquet",
                                      bootstrap=False, previous=str(boot), workers=2), 'leaves out')
    dropped = root / "dropped.parquet"
    chips_table.build(chips_table.resolve_inputs(set(), **kw), dropped, bootstrap=False,
                      previous=str(boot), drop=frozenset({"bb_2022"}), workers=2)
    check({k[0] for k in table(dropped)} == {"aa_2021"}, "--drop leaves the dataset out")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet",
                          bootstrap=False, previous=str(later), staged=frozenset({"aa_2021"}),
                          drop=frozenset({"bb_2022"}), workers=2)
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", staged_rows[:3])
    with contextlib.redirect_stdout(out):
        chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet",
                          bootstrap=False, previous=str(later), staged=frozenset({"aa_2021"}),
                          drop=frozenset({"bb_2022"}), workers=2)
    check("aa_2021: 1 chips of the previous table are gone" in out.getvalue(),
          f"a dropped chip without frozen splits is a note: {out.getvalue()!r}")
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", staged_rows[1:])
    refused("a rebuild that loses a chip with a frozen split", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=False,
        previous=str(later), staged=frozenset({"aa_2021"}), drop=frozenset({"bb_2022"}),
        workers=2), "1 chips of the previous table are gone, with their frozen splits")
    chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet",
                      bootstrap=False, previous=str(later), staged=frozenset({"aa_2021"}),
                      drop=frozenset({"bb_2022", "aa_2021"}), workers=2)

    # a carried chip whose hash split would change
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    con.execute(f"""COPY (SELECT * REPLACE (CASE WHEN split_hash_v1 = 'train' THEN 'test'
                                                 ELSE 'train' END AS split_hash_v1)
                          FROM read_parquet('{later}')) TO '{root / "moved.parquet"}'
                    (FORMAT parquet)""")
    con.close()
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", staged_rows)
    refused("a carried chip whose hash split changes", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=False,
        previous=str(root / "moved.parquet"), staged=frozenset({"aa_2021"}),
        drop=frozenset({"bb_2022"}), workers=2), "would change its block or split_hash_v1")

    # a restaged predefined dataset takes its new splits, not the previous table's
    write_catalog(root, {"aa_2021": ("zz", "block3x3"), "bb_2022": ("bb", "predefined")})
    write_chips(staging / "bb_2022" / "bb_2022_chips.parquet",
                [(SHARED, "val"), ("ftw-33TUN2020", "test")], admin=False)
    restaged = root / "restaged.parquet"
    chips_table.build(chips_table.resolve_inputs({"aa_2021", "bb_2022"}, **kw), restaged,
                      bootstrap=False, previous=str(later),
                      staged=frozenset({"aa_2021", "bb_2022"}), workers=2)
    t = table(restaged)
    check(t[("bb_2022", "ftw-33TUN2020")][1] == "test" and t[("bb_2022", SHARED)][1] == "val",
          f"a restaged predefined dataset takes its new splits: {t}")
    check(t[("bb_2022", SHARED)][0] == "test", "its legacy split stays frozen")
    shutil.rmtree(staging / "bb_2022")
    write_catalog(root, {"aa_2021": ("zz", "block3x3")})

    # a --bootstrap over a published file where a chip has no split
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    con.execute(f"""COPY (SELECT * REPLACE (CASE WHEN id = '{SHARED}' THEN NULL ELSE split END
                                            AS split)
                          FROM read_parquet('{base}/zz/aa_2021/aa_2021_chips.parquet'))
                    TO '{root / "gap.parquet"}' (FORMAT parquet)""")
    con.close()
    shutil.copy(root / "gap.parquet", base / "zz" / "aa_2021" / "aa_2021_chips.parquet")
    refused("--bootstrap over a published file with a missing split", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=True, workers=2),
        "published chips have no split")
    write_chips(base / "zz" / "aa_2021" / "aa_2021_chips.parquet", AA)

    # a --bootstrap rerun once the published files have no split
    write_chips_nosplit = root / "nosplit.parquet"
    con = duckdb.connect()
    con.execute(f"COPY (SELECT * EXCLUDE (split) FROM read_parquet('{base}/zz/aa_2021/"
                f"aa_2021_chips.parquet')) TO '{write_chips_nosplit}' (FORMAT parquet)")
    con.close()
    shutil.copy(write_chips_nosplit, base / "zz" / "aa_2021" / "aa_2021_chips.parquet")
    refused("--bootstrap over published files without split", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=True, workers=2), 'no legacy split')
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            chips_table.main(["--bootstrap", "--previous", str(boot), "--out", str(root / "x")])
        errors.append("not refused: --bootstrap over a published table")
    except SystemExit as stop:
        check("exists" in str(stop.code), f"--bootstrap names the existing table: {stop.code}")

    # a staged predefined dataset whose chips file has no split
    write_catalog(root, {"aa_2021": ("zz", "predefined"), "bb_2022": ("bb", "predefined")})
    shutil.copy(write_chips_nosplit, staging / "aa_2021" / "aa_2021_chips.parquet")
    refused("a staged predefined dataset without split", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=False,
        previous=str(later), staged=frozenset({"aa_2021"}), workers=2), 'has no split column')

    # a predefined dataset new to the table, unstaged, whose file has no split
    (root / "catalog" / "cc" / "cc_2023").mkdir(parents=True)
    (root / "catalog" / "cc" / "cc_2023" / "collection.json").write_text(json.dumps({
        "ftw:chip_size_km": 2.0, "assets": {"chips": {"href": "./cc_2023_chips.parquet"}}}))
    (root / "catalog" / "cc" / "catalog.json").write_text(json.dumps({"links": [
        {"rel": "child", "href": "./cc_2023/collection.json"}]}))
    links = json.loads((root / "catalog" / "catalog.json").read_text())
    links["links"].append({"rel": "child", "href": "./cc/catalog.json"})
    (root / "catalog" / "catalog.json").write_text(json.dumps(links))
    (root / "datasets" / "cc_2023.yaml").write_text("stages:\n  splits:\n    split_type: predefined\n")
    (base / "cc" / "cc_2023").mkdir(parents=True)
    shutil.copy(write_chips_nosplit, base / "cc" / "cc_2023" / "cc_2023_chips.parquet")
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", staged_rows)
    refused("a new unstaged predefined dataset without split", lambda: chips_table.build(
        chips_table.resolve_inputs(set(), **kw), root / "x.parquet", bootstrap=False,
        previous=str(later), workers=2), "no chip has one")
    write_catalog(root, {"aa_2021": ("zz", "predefined"), "bb_2022": ("bb", "predefined")})

    # one dataset id in two groups
    (root / "catalog" / "bb" / "aa_2021").mkdir()
    shutil.copy(root / "catalog" / "zz" / "aa_2021" / "collection.json",
                root / "catalog" / "bb" / "aa_2021" / "collection.json")
    (root / "catalog" / "bb" / "catalog.json").write_text(json.dumps({"links": [
        {"rel": "child", "href": "./bb_2022/collection.json"},
        {"rel": "child", "href": "./aa_2021/collection.json"}]}))
    refused("a dataset published twice", lambda: chips_table.resolve_inputs(set(), **kw), 'published twice')
    write_catalog(root, {"aa_2021": ("zz", "block3x3"), "bb_2022": ("bb", "predefined")})
    shutil.rmtree(root / "catalog" / "bb" / "aa_2021")

    write_chips(base / "zz" / "aa_2021" / "aa_2021_chips.parquet", AA)  # published split back
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", [(SHARED, "train"), (SHARED, "val")])
    refused("a duplicate chip", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=True,
        staged=frozenset({"aa_2021"}), workers=2), 'more than once')
    write_chips(staging / "aa_2021" / "aa_2021_chips.parquet", [(SHARED, "training")])
    write_catalog(root, {"aa_2021": ("zz", "predefined"), "bb_2022": ("bb", "predefined")})
    refused("a split value outside train/val/test", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=True,
        staged=frozenset({"aa_2021"}), workers=2), 'has the value')

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the root chips table freezes legacy splits, keeps predefined ones and hashes the rest")
