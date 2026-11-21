#!/usr/bin/env python3
"""Build the root chips table: every chip of every published dataset, with its splits.

    uv run python tools/chips_table.py --bootstrap        # first build: frozen splits from the chips files
    uv run python tools/chips_table.py                    # later builds: frozen splits from the published table
    uv run python tools/chips_table.py --staged pt_2021   # read pt_2021's chips from staging/

Writes ``staging/chips.parquet`` (``--out`` to change), which ``tools/upload_data.py``
uploads to the bucket root. One row per (dataset, chip), sorted by group, dataset and
chip id, so a reader that filters on ``dataset`` skips most row groups.

Columns:

- ``dataset``, ``group`` (the harmonized source folder), ``id``, ``block`` (the chip's
  3x3 grid block), the admin names, ``geometry`` and ``bbox``.
- One column per split scheme, all ``train`` / ``val`` / ``test`` or null. Model code
  picks the column; issue #16 has the reasoning.

  - ``split_legacy``: the split each dataset published before this table existed, by
    whatever scheme its recipe used (seeded ``block3x3`` or ``predefined``). Frozen:
    ``--bootstrap`` reads it from the published chips files, every later build carries it
    over from the published table, and chips added later get null.
  - ``split_predefined``: the source's own split, for datasets whose recipe sets
    ``split_type: predefined``; null elsewhere. Read from the chips file each build.
  - ``split_hash_v1``: ftwd's ``block3x3-hash`` at 80/10/10. A block's split comes from a
    stable hash of its id, so a location has the same split in every dataset and year,
    and new chips never move existing ones.

Datasets are the collections the root catalog links (``catalog_stats.published_datasets``)
plus any ``--staged`` id that is not published yet.

The frozen columns exist nowhere else once the per-dataset files stop carrying ``split``,
so the build refuses anything that would lose them: ``--bootstrap`` when a table is
already published or a published chips file has no ``split``, a later build that leaves
out a dataset of the previous table (unless ``--drop`` names it), and a staged
predefined dataset whose chips file has no ``split``.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalog_stats import published_datasets  # noqa: E402
from common import CATALOG, PUBLIC_BASE, ROOT, STAGING, recipe_group  # noqa: E402

TABLE_NAME = "chips.parquet"
SPLITS = ("train", "val", "test")
HASH_PERCENTS = (80, 10, 10)
ADMIN_COLUMNS = ("admin0_iso3", "admin0_name", "admin1_name", "admin2_name")
SPLIT_COLUMNS = ("split_legacy", "split_predefined", "split_hash_v1")


class ChipsTableError(Exception):
    """The inputs can't make a consistent table."""


@dataclass(frozen=True)
class DatasetInput:
    """Where one dataset's chips come from and how its splits were made."""

    dataset: str
    group: str
    chips: str  # path or URL of the chips file this build reads
    published_chips: str | None  # the published chips file, for --bootstrap's frozen splits
    split_type: str | None
    km_size: float


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _chips_href(collection: dict, base: str) -> str:
    href = collection["assets"]["chips"]["href"]
    return href if "://" in href else f"{base}/{href.removeprefix('./')}"


def _recipe_split_type(dataset_id: str, root: Path) -> str | None:
    import yaml

    recipe = yaml.safe_load((root / "datasets" / f"{dataset_id}.yaml").read_text()) or {}
    return ((recipe.get("stages") or {}).get("splits") or {}).get("split_type")


def _staged_input(dataset_id: str, group: str, published: str | None, staging: Path,
                  root: Path) -> DatasetInput:
    folder = staging / dataset_id
    chips = folder / f"{dataset_id}_chips.parquet"
    if not chips.is_file():
        raise ChipsTableError(f"{dataset_id}: --staged, but {chips} does not exist")
    collection_path = folder / "collection.json"
    collection = json.loads(collection_path.read_text()) if collection_path.is_file() else {}
    return DatasetInput(dataset_id, group, str(chips), published,
                        _recipe_split_type(dataset_id, root),
                        float(collection.get("ftw:chip_size_km", 2.0)))


def resolve_inputs(staged: set[str], *, catalog: Path = CATALOG, staging: Path = STAGING,
                   base: str = PUBLIC_BASE, root: Path = ROOT) -> list[DatasetInput]:
    """One input per published dataset plus each staged one, published ones from ``base``."""
    inputs: dict[str, DatasetInput] = {}
    for relpath in published_datasets(catalog / "catalog.json"):
        group, _, dataset_id = relpath.rpartition("/")
        if dataset_id in inputs:
            raise ChipsTableError(f"{dataset_id} is published twice: in {inputs[dataset_id].group} "
                                  f"and {group}")
        collection = json.loads((catalog / relpath / "collection.json").read_text())
        published = _chips_href(collection, f"{base}/{relpath}")
        if dataset_id in staged:
            inputs[dataset_id] = _staged_input(dataset_id, group, published, staging, root)
            continue
        inputs[dataset_id] = DatasetInput(
            dataset_id, group, published, published, _recipe_split_type(dataset_id, root),
            float(collection.get("ftw:chip_size_km", 2.0)))
    for dataset_id in sorted(staged - inputs.keys()):
        inputs[dataset_id] = _staged_input(dataset_id, recipe_group(dataset_id, root), None,
                                           staging, root)
    return [inputs[k] for k in sorted(inputs)]


def _columns(con, source: str) -> set[str]:
    return {r[0] for r in con.execute(
        f"DESCRIBE SELECT * FROM read_parquet({_sql(source)})").fetchall()}


def _read_dataset(item: DatasetInput, bootstrap: bool, out: Path) -> None:
    """One dataset's rows as a parquet file in the table's column order (no hash yet)."""
    import duckdb

    try:
        _copy_dataset(item, bootstrap, out)
    except duckdb.Error as err:
        raise ChipsTableError(f"{item.dataset}: {err}") from err


def _legacy_source(con, item: DatasetInput, cols: set[str]) -> tuple[str, str]:
    """``(expression, join)`` for --bootstrap's split_legacy: the published file's ``split``."""
    if not item.published_chips:
        return "NULL::VARCHAR", ""
    published_cols = cols if item.published_chips == item.chips else _columns(
        con, item.published_chips)
    if "split" not in published_cols:
        raise ChipsTableError(f"{item.dataset}: --bootstrap, but the published chips file has no "
                              f"split column, so there is no legacy split to freeze")
    if item.published_chips == item.chips:
        return "c.split", ""
    return "p.split", (f" LEFT JOIN (SELECT id, split FROM read_parquet("
                       f"{_sql(item.published_chips)})) p USING (id)")


def _copy_dataset(item: DatasetInput, bootstrap: bool, out: Path) -> None:
    from ftw_dataset_tools.api import admin_names

    con = admin_names.connect()
    try:
        cols = _columns(con, item.chips)
        staged = item.chips != item.published_chips
        if staged and item.split_type == "predefined" and "split" not in cols:
            raise ChipsTableError(f"{item.dataset}: the recipe uses predefined splits, but "
                                  f"{item.chips} has no split column")
        admin = ", ".join(f"c.{c}" if c in cols else f"NULL::VARCHAR AS {c}"
                          for c in ADMIN_COLUMNS)
        split = "c.split" if "split" in cols else "NULL::VARCHAR"
        predefined = split if item.split_type == "predefined" else "NULL::VARCHAR"
        legacy, legacy_join = (_legacy_source(con, item, cols) if bootstrap
                               else ("NULL::VARCHAR", ""))
        con.execute(f"""
            COPY (SELECT {_sql(item.dataset)} AS dataset, {_sql(item.group)} AS "group",
                         c.id, {admin}, c.geometry, c.bbox,
                         {legacy} AS split_legacy, {predefined} AS split_predefined
                  FROM read_parquet({_sql(item.chips)}) c{legacy_join})
            TO {_sql(str(out))} (FORMAT parquet)""")
    finally:
        con.close()


def hash_splits(ids, km_size: float):
    """``(block, split_hash_v1)`` for each chip id: ftwd's block3x3-hash at HASH_PERCENTS."""
    import numpy as np
    import pandas as pd
    from ftw_dataset_tools.api.blocks import block_scores, chip_block_ids
    from ftw_dataset_tools.api.splits import SPLIT_HASH_VERSION

    blocks = chip_block_ids(pd.Series(ids), km_size)
    scores = block_scores(blocks, SPLIT_HASH_VERSION).to_numpy()
    train, val = HASH_PERCENTS[0] / 100, (HASH_PERCENTS[0] + HASH_PERCENTS[1]) / 100
    return blocks.to_numpy(), np.where(scores < train, "train",
                                       np.where(scores < val, "val", "test"))


def _hash_table(con, inputs: list[DatasetInput]) -> None:
    """Table ``hashed(id, km_size, block, split_hash_v1)`` over the chips in ``rows``."""
    import pandas as pd

    sizes = {item.dataset: item.km_size for item in inputs}
    frames = []
    for km_size in sorted(set(sizes.values())):
        names = [d for d, k in sizes.items() if k == km_size]
        ids = [r[0] for r in con.execute(
            "SELECT DISTINCT id FROM rows WHERE dataset IN (SELECT unnest(?))", [names]
        ).fetchall()]
        blocks, splits = hash_splits(ids, km_size)
        frames.append(pd.DataFrame({"id": ids, "km_size": km_size, "block": blocks,
                                    "split_hash_v1": splits}))
    hashed = pd.concat(frames) if frames else pd.DataFrame(
        columns=["id", "km_size", "block", "split_hash_v1"])
    con.register("hashed_df", hashed)
    con.execute("CREATE TABLE hashed AS SELECT * FROM hashed_df")
    con.register("sizes_df", pd.DataFrame({"dataset": list(sizes),
                                           "km_size": list(sizes.values())}))
    con.execute("CREATE TABLE sizes AS SELECT * FROM sizes_df")


def _carry_frozen(con, previous: str, inputs: list[DatasetInput], staged: set[str],
                  drop: set[str]) -> None:
    """Fill ``split_legacy`` from the previous table, and ``split_predefined`` for unstaged sets.

    Refuses when a dataset of the previous table is not an input (its frozen splits would be
    lost), unless ``drop`` names it. Reports chips a staged rebuild no longer has.
    """
    import duckdb

    try:
        con.execute(f"CREATE TABLE prev AS SELECT dataset, id, split_legacy, split_predefined "
                    f"FROM read_parquet({_sql(previous)})")
    except duckdb.Error as err:
        raise ChipsTableError(f"can't read the previous table {previous}: {err}") from err
    names = {item.dataset for item in inputs}
    missing = {r[0] for r in con.execute("SELECT DISTINCT dataset FROM prev").fetchall()} - names
    if missing - drop:
        raise ChipsTableError(
            f"the previous table has {', '.join(sorted(missing - drop))}, which this build "
            f"leaves out; their frozen splits would be lost (--drop them if that is intended)")
    for dataset, gone in con.execute("""
            SELECT dataset, count(*) FROM prev ANTI JOIN rows USING (dataset, id)
            WHERE dataset IN (SELECT unnest(?)) GROUP BY ALL ORDER BY ALL""",
            [sorted(names)]).fetchall():
        print(f"note: {dataset}: {gone:,} chips of the previous table are gone, with their "
              f"frozen splits")
    con.execute("""UPDATE rows SET split_legacy = prev.split_legacy FROM prev
                   WHERE rows.dataset = prev.dataset AND rows.id = prev.id""")
    predefined = sorted(i.dataset for i in inputs
                        if i.split_type == "predefined" and i.dataset not in staged)
    con.execute("""UPDATE rows SET split_predefined = prev.split_predefined FROM prev
                   WHERE rows.dataset = prev.dataset AND rows.id = prev.id
                     AND rows.dataset IN (SELECT unnest(?))""", [predefined])


def check_rows(con) -> None:
    """Refuse duplicate (dataset, id) rows and split values outside train/val/test."""
    dup = con.execute("SELECT dataset, id FROM rows GROUP BY ALL HAVING count(*) > 1 "
                      "LIMIT 1").fetchone()
    if dup:
        raise ChipsTableError(f"{dup[0]}: chip {dup[1]} appears more than once")
    for column in ("split_legacy", "split_predefined"):  # read from files; the hash is ours
        bad = con.execute(f"SELECT dataset, {column} FROM rows WHERE {column} IS NOT NULL "
                          f"AND {column} NOT IN {SPLITS} LIMIT 1").fetchone()
        if bad:
            raise ChipsTableError(f"{bad[0]}: {column} has the value {bad[1]!r}")


def table_exists(location: str) -> bool:
    """True when ``location`` (a path or an http(s) URL) has a file."""
    if "://" not in location:
        return Path(location).is_file()
    try:
        with urllib.request.urlopen(urllib.request.Request(location, method="HEAD"), timeout=30):
            return True
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        raise ChipsTableError(f"can't tell whether {location} exists: {err}") from err
    except urllib.error.URLError as err:
        raise ChipsTableError(f"can't tell whether {location} exists: {err}") from err


def build(inputs: list[DatasetInput], out: Path, *, bootstrap: bool,
          previous: str | None = None, staged: frozenset[str] = frozenset(),
          drop: frozenset[str] = frozenset(), workers: int = 8) -> int:
    """Write the table to ``out``; the number of rows."""
    import geoparquet_io as gpio
    from ftw_dataset_tools.api import admin_names

    if not bootstrap and previous is None:
        raise ChipsTableError("a build without --bootstrap needs the previous table")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        parts = [Path(tmp) / f"{item.dataset}.parquet" for item in inputs]
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(lambda a: _read_dataset(a[0], bootstrap, a[1]), zip(inputs, parts)))
        con = admin_names.connect()
        try:
            files = ", ".join(_sql(str(p)) for p in parts)
            con.execute(f"CREATE TABLE rows AS SELECT * FROM read_parquet([{files}])")
            if not bootstrap:
                _carry_frozen(con, previous, inputs, set(staged), set(drop))
            _hash_table(con, inputs)
            check_rows(con)
            admin = ", ".join(f"r.{c}" for c in ADMIN_COLUMNS)
            joined = Path(tmp) / "joined.parquet"
            con.execute(f"""
                COPY (SELECT r.dataset, r."group", r.id, h.block, {admin},
                             r.split_legacy, r.split_predefined, h.split_hash_v1,
                             r.geometry, r.bbox
                      FROM rows r JOIN sizes s USING (dataset)
                      JOIN hashed h ON h.id = r.id AND h.km_size = s.km_size
                      ORDER BY r."group", r.dataset, r.id)
                TO {_sql(str(joined))} (FORMAT parquet)""")
            gpio.read(str(joined)).write(str(out))
            written = con.execute(
                f"SELECT count(*) FROM read_parquet({_sql(str(out))})").fetchone()[0]
            expected = con.execute("SELECT count(*) FROM rows").fetchone()[0]
            if written != expected:
                out.unlink()
                raise ChipsTableError(f"wrote {written:,} rows from {expected:,} chips")
            return written
        finally:
            con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap", action="store_true",
                        help="read split_legacy from the published chips files (first build only)")
    parser.add_argument("--staged", nargs="*", default=[],
                        help="dataset ids to read from staging/ instead of the bucket")
    parser.add_argument("--previous", default=f"{PUBLIC_BASE}/{TABLE_NAME}",
                        help="the table to carry frozen splits from (default: the published one)")
    parser.add_argument("--drop", nargs="*", default=[],
                        help="datasets of the previous table to leave out, losing their frozen splits")
    parser.add_argument("--out", type=Path, default=STAGING / TABLE_NAME)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    staged = set(args.staged)
    try:
        if args.bootstrap and table_exists(args.previous):
            raise ChipsTableError(f"--bootstrap, but {args.previous} exists; a later build "
                                  f"carries its frozen splits instead")
        inputs = resolve_inputs(staged)
        rows = build(inputs, args.out, bootstrap=args.bootstrap,
                     previous=None if args.bootstrap else args.previous,
                     staged=frozenset(staged), drop=frozenset(args.drop),
                     workers=args.workers)
    except ChipsTableError as err:
        sys.exit(f"chips table: {err}")
    print(f"wrote {args.out}: {rows:,} chips from {len(inputs)} datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
