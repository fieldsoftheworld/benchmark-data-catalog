#!/usr/bin/env python3
"""tools/chips_table.py: the wrapper over ftwd's chips table.

The table itself (splits, carried columns, refusals, licenses) is tested in ftwd. Here:

- ``staged_inputs`` reads each staged id from ``staging/<id>`` and gives ftwd a group
  (from the recipe's ``source_via``) only for an id the catalog doesn't publish yet;
- ``main`` hands ftwd this catalog's root, ``PUBLIC_BASE``, the published table as
  ``--previous`` and ``work/chips.parquet`` as ``--out`` by default, passes ``--drop``,
  ``--out`` and ``--workers`` through, and turns an ftwd refusal into a one-line exit;
- ftwd's ``resolve_inputs`` accepts what ``staged_inputs`` gives it.

Run: python3 tests/test_chips_table.py
"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

try:
    import duckdb
    import ftw_dataset_tools.api.chips_table as ftwd_table
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import chips_table  # noqa: E402
from common import CATALOG, PUBLIC_BASE, STAGING  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_chips(path: Path, ids: list[str], x0: int = 0, split: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")
    rows = ", ".join(f"('{i}', {x0 + n})" for n, i in enumerate(ids))
    split_col = f"'{split}' AS split, " if split else ""
    con.execute(f"""
        COPY (SELECT id, {split_col}'AUT' AS admin0_iso3, 'Austria' AS admin0_name,
                     ST_MakeEnvelope(n, 0, n + 0.01, 0.01) AS geometry,
                     {{'xmin': n, 'ymin': 0, 'xmax': n + 0.01, 'ymax': 0.01}} AS bbox
              FROM (VALUES {rows}) t(id, n))
        TO '{path}' (FORMAT parquet)""")
    con.close()


def write_collection(folder: Path, dataset_id: str, **extra) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "collection.json").write_text(json.dumps({
        "id": dataset_id, "license": "CC-BY-4.0", "links": [],
        "assets": {"chips": {"href": f"./{dataset_id}_chips.parquet"}}, **extra}))


def stand_in(tmp: Path) -> tuple[Path, Path, Path]:
    """A catalog publishing aa/aa_2021 (data files next to it), a recipe placing bb_2022
    in bb, and staged builds of both."""
    catalog, staging, root = tmp / "catalog", tmp / "staging", tmp / "repo"
    (catalog / "catalog.json").parent.mkdir(parents=True)
    (catalog / "catalog.json").write_text(json.dumps({"links": [
        {"rel": "child", "href": "./aa/catalog.json"}]}))
    (catalog / "aa" / "catalog.json").parent.mkdir()
    (catalog / "aa" / "catalog.json").write_text(json.dumps({"links": [
        {"rel": "child", "href": "./aa_2021/collection.json"}]}))
    write_collection(catalog / "aa" / "aa_2021", "aa_2021", **{"ftw:split_type": "block3x3"})
    write_chips(catalog / "aa" / "aa_2021" / "aa_2021_chips.parquet", ["c1", "c2"],
                split="train")
    (root / "datasets").mkdir(parents=True)
    (root / "datasets" / "bb_2022.yaml").write_text(
        "source_via: https://data.source.coop/ftw/harmonized-field-data/bb/collection.json\n")
    for dataset_id, ids in (("aa_2021", ["c1", "c2", "c3"]), ("bb_2022", ["c9"])):
        write_collection(staging / dataset_id, dataset_id)  # built with the splits stage off
        write_chips(staging / dataset_id / f"{dataset_id}_chips.parquet", ids)
    return catalog, staging, root


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog, staging, root = stand_in(tmp)
    kw = {"catalog": catalog, "staging": staging, "root": root}

    local_dirs, groups = chips_table.staged_inputs(["aa_2021", "bb_2022"], **kw)
    check(local_dirs == [staging / "aa_2021", staging / "bb_2022"],
          f"staged ids are read from staging/<id>: {local_dirs}")
    check(groups == {"bb_2022": "bb"},
          f"only the unpublished id gets a group, from its recipe: {groups}")
    try:
        chips_table.staged_inputs(["cc_2023"], **kw)
        errors.append("not refused: a staged unpublished id without a recipe")
    except chips_table.LayoutError as err:
        check("cc_2023" in str(err), f"the refusal names the id: {err}")

    # ftwd accepts them: the published id keeps its catalog group, the new one gets its own
    inputs = ftwd_table.resolve_inputs(catalog / "catalog.json", None, local_dirs, groups)
    check([(i.dataset, i.group, i.local) for i in inputs]
          == [("aa_2021", "aa", True), ("bb_2022", "bb", True)],
          f"ftwd takes the staged dirs and groups: {inputs}")

    # main: the defaults and pass-through, with ftwd stubbed
    seen: dict = {}

    def fake_resolve(catalog_json, data_base_url, local_dirs, groups):
        seen["resolve"] = (catalog_json, data_base_url, list(local_dirs), dict(groups))
        return ["x"]

    def fake_build(inputs, out, previous, drop, workers):
        seen["build"] = (inputs, out, previous, list(drop), workers)
        return 7

    real = chips_table.resolve_inputs, chips_table.build_chips_table
    chips_table.resolve_inputs, chips_table.build_chips_table = fake_resolve, fake_build
    try:
        published_id = chips_table.published_datasets(CATALOG / "catalog.json")[0].rpartition("/")[2]
        with contextlib.redirect_stdout(io.StringIO()):
            chips_table.main(["--staged", published_id])
        check(seen["resolve"] == (CATALOG / "catalog.json", PUBLIC_BASE,
                                  [STAGING / published_id], {}),
              f"ftwd gets the catalog, PUBLIC_BASE and the staged dir, no group for a "
              f"published id: {seen['resolve']}")
        check(seen["build"] == (["x"], ROOT / "work" / "chips.parquet",
                                f"{PUBLIC_BASE}/chips.parquet", [], 8),
              f"the defaults: work/chips.parquet from the published table: {seen['build']}")
        with contextlib.redirect_stdout(io.StringIO()):
            chips_table.main(["--drop", "aa_2021", "bb_2022", "--out", str(tmp / "t.parquet"),
                              "--previous", "p.parquet", "--workers", "3"])
        check(seen["resolve"][2:] == ([], {}), f"nothing staged: {seen['resolve']}")
        check(seen["build"][1:] == (tmp / "t.parquet", "p.parquet", ["aa_2021", "bb_2022"], 3),
              f"--out, --previous, --drop and --workers pass through: {seen['build']}")

        def refuse(*args, **kwargs):
            raise ftwd_table.ChipsTableError("aa_2021 would lose frozen splits")

        chips_table.build_chips_table = refuse
        try:
            chips_table.main([])
            errors.append("not refused: an ftwd refusal")
        except SystemExit as err:
            check(str(err.code) == "chips table: aa_2021 would lose frozen splits",
                  f"an ftwd refusal exits with one line: {err.code}")
    finally:
        chips_table.resolve_inputs, chips_table.build_chips_table = real

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: tools/chips_table.py hands this catalog's inputs to ftwd")
