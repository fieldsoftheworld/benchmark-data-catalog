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
    collection = path.parent / "collection.json"  # a staged build writes one too
    if not collection.exists():
        collection.write_text(json.dumps({"ftw:chip_size_km": 2.0, "license": "CC-BY-4.0",
                                          "ftw:presence_only": False}))


PRESENCE_ONLY = {"bb_2022"}


def write_catalog(root: Path, datasets: dict[str, tuple[str, str]]) -> None:
    """datasets: {id: (group, split_type)}; recipes and the linked catalog tree."""
    catalog = root / "catalog"
    groups: dict[str, list[str]] = {}
    for dataset_id, (group, split_type) in datasets.items():
        groups.setdefault(group, []).append(dataset_id)
        folder = catalog / group / dataset_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "collection.json").write_text(json.dumps({
            "ftw:chip_size_km": 2.0, "license": "other",
            "links": [{"rel": "license", "href": "https://data.source.coop/olmoearth/"
                                                 "olmoearth-v1-3-embeddings/LICENSE.txt"},
                      {"rel": "license", "href": "https://go.planet.com/nicfi-pla-2024"}],
            "ftw:presence_only": dataset_id in PRESENCE_ONLY,
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
    con = duckdb.connect()
    extra = {r[0]: r[1:] for r in con.execute(f"""
        SELECT dataset || ' ' || id, license, license_url, license_category, presence_only,
               unit_admin2_v1, split_admin2_v1 FROM read_parquet('{boot}')""").fetchall()}
    con.close()
    check(extra[f"bb_2022 {SHARED}"][:4] == ("other", "https://go.planet.com/nicfi-pla-2024",
                                             "non-commercial", True),
          f"license, its own link (not the embeddings'), its category and presence_only come "
          f"from the collection: "
          f"{extra[f'bb_2022 {SHARED}']}")
    check(extra[f"aa_2021 {SHARED}"][4:] == extra[f"bb_2022 {SHARED}"][4:]
          and extra[f"aa_2021 {SHARED}"][5] == "train",
          f"a location in a presence-only dataset is train in every dataset: {extra}")
    check(all(v[5] in chips_table.SPLITS and v[4] for v in extra.values()),
          "every chip has an admin2 unit and split")

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

    # the first build that adds split_admin2_v1 reads a previous table without it
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    con.execute(f"""COPY (SELECT * EXCLUDE (unit_admin2_v1, split_admin2_v1, license, license_url,
                                            license_category, presence_only)
                          FROM read_parquet('{boot}')) TO '{root / "old.parquet"}' (FORMAT parquet)""")
    con.close()
    try:
        chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet",
                          bootstrap=False, previous=str(root / "old.parquet"),
                          staged=frozenset({"aa_2021"}), workers=2)
        errors.append("not refused: a previous table without split_admin2_v1")
    except chips_table.ChipsTableError as err:
        check("--start-admin2-split" in str(err), f"the refusal names the flag: {err}")
    started = root / "started.parquet"
    chips_table.build(chips_table.resolve_inputs({"aa_2021"}, **kw), started, bootstrap=False,
                      previous=str(root / "old.parquet"), staged=frozenset({"aa_2021"}),
                      workers=2, start_admin2=True)
    t2 = table(started)
    check(all(t2[k][:3] == t[k][:3] for k in t), "starting the admin2 split keeps the other splits")

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
    (staging / "aa_2021" / "collection.json").rename(staging / "aa_2021" / "c.json")
    refused("a staged dataset without a collection", lambda: chips_table.resolve_inputs(
        {"aa_2021"}, **kw), 'needs its license')
    (staging / "aa_2021" / "c.json").rename(staging / "aa_2021" / "collection.json")

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

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    con.execute(f"""COPY (SELECT * REPLACE (block || '_x' AS block) FROM read_parquet('{later}'))
                    TO '{root / "reblocked.parquet"}' (FORMAT parquet)""")
    con.close()
    refused("a carried chip whose block changes", lambda: chips_table.build(
        chips_table.resolve_inputs({"aa_2021"}, **kw), root / "x.parquet", bootstrap=False,
        previous=str(root / "reblocked.parquet"), staged=frozenset({"aa_2021"}),
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

# license categories
cat = chips_table.license_category
check(cat("CC-BY-4.0", None) == "attribution" and cat("CC0-1.0", None) == "public-domain"
      and cat("CC-BY-SA-4.0", None) == "share-alike", "SPDX licenses map to their category")
check(cat("other", "https://go.planet.com/nicfi-pla-2024") == "non-commercial",
      "an other license is judged by its link")
check(cat("other", "https://example.com/terms") == "unknown" and cat(None, None) == "unknown"
      and cat("MIT-ish", None) == "unknown", "an unjudged license is unknown")
check(set(chips_table.LICENSES.values()) <= set(chips_table.LICENSE_CATEGORIES),
      "every judged license has a known category")

# admin2 splits, on stand-in locations
import pandas as pd  # noqa: E402


def locs(rows):
    """rows: (id, country, admin1, admin2, presence_only); block = id's first 4 chars."""
    return pd.DataFrame([{"id": i, "country": c, "admin1": a1, "admin2": a2,
                          "block": i[:4], "presence_only": po} for i, c, a1, a2, po in rows])


def splits(out):
    return dict(zip(out["id"], out["split"]))


big = [(f"a{u:02d}{k:03d}", "AAA", "r", f"u{u}", False) for u in range(20) for k in range(5 + u)]
out = chips_table.admin2_splits(locs(big))
by_unit = out.groupby("unit")["split"].nunique()
check((by_unit == 1).all(), "a unit has one split")
share = out["split"].value_counts(normalize=True)
check(set(share.index) == set(chips_table.SPLITS) and abs(share["train"] - 0.8) < 0.08,
      f"a country with many units is balanced near 80/10/10: {share.to_dict()}")
check(splits(chips_table.admin2_splits(locs(big[::-1]))) == splits(out),
      "the result does not depend on row order")

po = big + [("p0001", "AAA", "r", "u0", True), ("q0001", "AAA", "r", "pq", True),
            ("q0002", "AAA", "r", "pq", False)]
out = splits(chips_table.admin2_splits(locs(po)))
check(all(out[i] == "train" for i in ("p0001", "q0001", "q0002"))
      and all(out[r[0]] == "train" for r in big if r[3] == "u0"),
      "a unit with a presence-only chip is train, all of it")

few = [("b1x01", "BBB", "r", "u1", False), ("b2x01", "BBB", "r", "u2", False),
       ("b3x01", "BBB", "r", "u2", False), ("zzzz1", None, None, None, False),
       ("yyyy1", "CCC", None, None, False)]
out = chips_table.admin2_splits(locs(few)).set_index("id")["unit"]
check(out["b1x01"] == "BBB|block:b1x0" and out["zzzz1"] == "|block:zzzz"
      and out["yyyy1"] == "CCC|block:yyyy",
      f"blocks are units without a country or admin1, or with under three admin2 units: {out.to_dict()}")

lopsided = [(f"k{u}{k:04d}", "KKK", "r", f"u{u}", False)
            for u, n in ((0, 300), (1, 5), (2, 3)) for k in range(n)]
out = chips_table.admin2_splits(locs(lopsided))
per = out.assign(u=out["unit"]).groupby("u")["split"].first().to_dict()
check(per["KKK|r|u0"] == "train" and {per["KKK|r|u1"], per["KKK|r|u2"]} == {"val", "test"},
      f"three units give all three splits, the biggest in train: {per}")

# a country keeps its kind of unit once published
xx = [(f"x{u}{k:03d}", "XXX", "r", f"u{u}", False) for u in range(3) for k in range(10)]
first_xx = chips_table.admin2_splits(locs(xx))
per = dict(zip(first_xx["unit"], first_xx["split"]))
train_unit = next(u for u, s in per.items() if s == "train").split("|")[2]
val_unit = next(u for u, s in per.items() if s == "val").split("|")[2]
later_xx = xx + [("pzzz1", "XXX", "r", train_unit, True), ("nnnn1", "XXX", "r", val_unit, False)]
out = chips_table.admin2_splits(locs(later_xx), first_xx).set_index("id")
check(out.loc["nnnn1", "split"] == "val" and "|block:" not in out.loc["nnnn1", "unit"],
      f"a country stays on admin2 units when presence-only chips leave it under three: "
      f"{out.loc['nnnn1'].to_dict()}")
yy = [("y1aa1", "YYY", "r", "a", False), ("y2bb1", "YYY", "r", "b", False),
      ("y3cc1", "YYY", "r", "b", False)]
first_yy = chips_table.admin2_splits(locs(yy))
later_yy = yy + [("y3cc2", "YYY", "r", "c", False), ("y4dd1", "YYY", "r", "d", False)]
out = chips_table.admin2_splits(locs(later_yy), first_yy).set_index("id")
check(out.loc["y3cc2", "unit"] == "YYY|block:y3cc"
      and out.loc["y3cc2", "split"] == dict(zip(first_yy["id"], first_yy["split"]))["y3cc1"],
      f"a country stays on blocks when it gains a third admin2 unit: {out.to_dict()}")
mixed = few + [("zzzz2", None, None, None, True)]
out = splits(chips_table.admin2_splits(locs(mixed)))
check(out["zzzz1"] == out["zzzz2"] == "train", "a block unit with a presence-only chip is train")

# a carried country with only train gets val and test from its new units
only_train = pd.DataFrame({"id": [r[0] for r in big], "unit": [f"AAA|r|{r[3]}" for r in big],
                           "split": "train"})
grown = big + [(f"m{u}{k:03d}", "AAA", "r", f"more{u}", False) for u in range(4) for k in range(3)]
out = chips_table.admin2_splits(locs(grown), only_train)
new_splits = set(out[out["id"].str.startswith("m")]["split"])
check({"val", "test"} <= new_splits, f"new units fill the missing splits: {new_splits}")

# license links: the dataset's own, not the embeddings'; the SPDX page for a standard id
fields = chips_table._license_fields({"license": "CC-BY-4.0", "links": [
    {"rel": "license", "href": "https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt"}]})
check(fields["license_url"] == "https://spdx.org/licenses/CC-BY-4.0.html",
      f"a standard id without its own link points at SPDX: {fields}")
check(chips_table._license_fields({"license": "other", "links": []})["license_url"] is None,
      "an other license without a link has no url")

# carried: a known unit keeps its split, new units fill in, nothing moves
first = chips_table.admin2_splits(locs(big))
grown = big + [("a00999", "AAA", "r", "u0", False)] + [
    (f"n{u}{k:03d}", "AAA", "r", f"new{u}", False) for u in range(6) for k in range(8)]
second = chips_table.admin2_splits(locs(grown), first)
s1, s2 = splits(first), splits(second)
check(all(s2[i] == s1[i] for i in s1), "a later build moves no carried chip")
check(s2["a00999"] == s1["a00000"], "a new chip of a known unit takes that unit's split")
check(all(s2[i] in chips_table.SPLITS for i in s2), "new units get a split")
renamed = first.copy()
renamed.loc[renamed["id"] == "a00000", "unit"] = "AAA|r|old-name"
check(dict(zip(*chips_table.admin2_splits(locs(big), renamed)[["id", "unit"]].T.values))["a00000"]
      == "AAA|r|old-name", "a carried chip keeps its unit even if its admin names change")
frozen = first[first["split"] == "val"]["unit"].iloc[0]
name = frozen.split("|")[2]
try:
    chips_table.admin2_splits(locs(big + [("x0001", "AAA", "r", name, True)]), first)
    errors.append("not refused: a frozen val unit that gains a presence-only chip")
except chips_table.ChipsTableError as err:
    check(frozen in str(err), f"the refusal names the unit: {err}")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the root chips table freezes legacy splits, keeps predefined ones and hashes the rest")
