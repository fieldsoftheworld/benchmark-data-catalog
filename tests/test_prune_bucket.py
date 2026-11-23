#!/usr/bin/env python3
"""The prune contract: delete only what the current build no longer publishes.

tools/prune_bucket.py compares a dataset's bucket listing with the keys the
staged data and the published catalog would write, and deletes the rest. This
gate builds a real staging and catalog tree and checks that kept files, the
catalog's own files and a sibling dataset with a shared name prefix are never
stale, and that the script refuses a dataset with no staging.

No network, no AWS, no credentials.

Run: python3 tests/test_prune_bucket.py
"""

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import catalogize  # noqa: E402
import prune_bucket  # noqa: E402
from upload_data import collect_data_uploads  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def touch(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_chips(path: Path, ids: list[str]) -> None:
    """A chips parquet with just the ``id`` column the prune guard reads."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"id": ids}), path)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = {
        "write_prefix": "s3://ftw/benchmark-data",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }
    touch(root / "staging/d1/chips/A/c1/c1_semantic_2_class.tif")
    touch(root / "staging/d1/chips/A/c1/c1.json")
    write_chips(root / "staging/d1/d1_chips.parquet", ["c1"])
    (root / "staging/d1/collection.json").write_text(json.dumps(
        {"type": "Collection", "assets": {"chips": {"href": "./d1_chips.parquet"}}}))
    touch(root / "catalog/g/d1/collection.json")
    touch(root / "catalog/g/d1/chips/A/catalog.json")
    touch(root / "catalog/g/d10/collection.json")

    keep = {
        "benchmark-data/g/d1/chips/A/c1/c1_semantic_2_class.tif",
        "benchmark-data/g/d1/chips/A/c1/c1.json",
        "benchmark-data/g/d1/collection.json",
        "benchmark-data/g/d1/chips/A/catalog.json",
    }
    drop = {
        "benchmark-data/g/d1/chips/B/c9/c9_semantic_2_class.tif",
        "benchmark-data/g/d1/chips/B/catalog.json",
    }
    others = {"benchmark-data/g/d10/collection.json", "benchmark-data/d1/collection.json"}
    remote = dict.fromkeys(keep | drop | others, (1, "e"))
    stale = set(prune_bucket.stale_keys("d1", config, remote, root))
    check(stale == drop, f"only the dropped chip's files are stale, got {sorted(stale)}")

    try:
        touch(root / "catalog/g/d2/collection.json")
        prune_bucket.stale_keys("d2", config, remote, root)
        check(False, "a dataset without staging is refused")
    except SystemExit as err:
        check("no staging" in str(err), f"the refusal says why, got {err}")

# A style the collection no longer references (v1's split.json, still staged because
# ftwd never deletes it) is neither committed, uploaded nor kept in the bucket.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    config = {
        "write_prefix": "s3://ftw/benchmark-data",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }
    staged = root / "staging/d3"
    published = root / "catalog/g/d3"
    staged.mkdir(parents=True)
    (staged / "collection.json").write_text(json.dumps(
        {"type": "Collection", "id": "d3", "assets": {"style-outline": {"href": "./styles/outline.json"}}}))
    for name in ("outline", "split"):
        touch(staged / "styles" / f"{name}.json", "{}")
        touch(published / "styles" / f"{name}.json", "{}")
    (published / "collection.json").write_text("{}")

    with redirect_stdout(io.StringIO()):
        catalogize.copy_committed("d3", staging=root / "staging", catalog=root / "catalog")
    styles = sorted(p.name for p in (published / "styles").iterdir())
    check(styles == ["outline.json"], f"catalogize leaves only the referenced style, got {styles}")

    uploads = {u.key for u in collect_data_uploads(config, root, only={"d3"})}
    check(not any("/styles/" in key for key in uploads), f"upload_data uploads no styles, got {sorted(uploads)}")

    remote = dict.fromkeys(
        ["benchmark-data/g/d3/collection.json", "benchmark-data/g/d3/styles/outline.json",
         "benchmark-data/g/d3/styles/split.json"], (1, "e"))
    stale = prune_bucket.stale_keys("d3", config, remote, root)
    check(stale == ["benchmark-data/g/d3/styles/split.json"],
          f"the bucket's split.json is stale and outline.json is kept, got {stale}")

# A staging that holds only part of the build is refused, not pruned against: the
# published files it lacks would all look stale. Dataset d: chip c1 in square A
# (directory c1_2023, an imagery child item beside it), chip c2 in square B.
CONFIG = {"write_prefix": "s3://ftw/benchmark-data", "publish_dir": "catalog", "data_dir": "staging"}
TOP = ["d_chips.parquet", "d_fields.parquet", "items.parquet", "fields.pmtiles", "styles/outline.json"]
COLLECTION = {"type": "Collection", "id": "d", "assets": {
    "chips": {"href": "./d_chips.parquet"}, "fields": {"href": "./d_fields.parquet"},
    "items": {"href": "./items.parquet"}, "fields_tiles": {"href": "./fields.pmtiles"},
    "style-outline": {"href": "./styles/outline.json", "roles": ["style", "default"]}}}
STYLE = json.dumps({"version": 8, "sources": {"data": {"type": "vector", "url": "pmtiles://../fields.pmtiles"}}})


def chip_files(square: str, chip: str) -> dict[str, str]:
    """A full chip: its item (with a mask), an imagery child item and the image."""
    at = f"chips/{square}/{chip}/{chip}"
    return {
        f"{at}.json": json.dumps({"type": "Feature", "assets": {"mask": {"href": f"./{chip}_mask.tif"}}}),
        f"{at}_mask.tif": "x",
        f"{at}_q1_s2.json": json.dumps({"type": "Feature", "assets": {"image": {"href": f"./{chip}_q1_image.tif"}}}),
        f"{at}_q1_image.tif": "x",
    }


CHIPS = {**chip_files("A", "c1_2023"), **chip_files("B", "c2_2023")}
PUBLISHED = [*TOP, *CHIPS, "collection.json", "chips/A/catalog.json", "chips/B/catalog.json"]


def prune_case(staged: dict[str, str], published=PUBLISHED, collection=COLLECTION, ids=("c1", "c2")):
    """``stale_keys`` (dataset-relative) for dataset d with these staged files, or the refusal."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "staging/d").mkdir(parents=True)
        for name, text in staged.items():
            if name == "d_chips.parquet":
                write_chips(root / "staging/d" / name, list(ids))
            else:
                touch(root / "staging/d" / name, text)
        if collection is not None:
            text = collection if isinstance(collection, str) else json.dumps(collection)
            (root / "staging/d/collection.json").write_text(text)
        for name in ("collection.json", "styles/outline.json", "chips/A/catalog.json", "chips/B/catalog.json"):
            touch(root / "catalog/g/d" / name, "{}")
        remote = dict.fromkeys((f"benchmark-data/g/d/{k}" for k in published), (1, "e"))
        try:
            return [k.removeprefix("benchmark-data/g/d/") for k in prune_bucket.stale_keys("d", CONFIG, remote, root)]
        except SystemExit as err:
            return str(err)


def refused(got, *needles: str) -> bool:
    return isinstance(got, str) and "not a full build" in got and all(n in got for n in needles)


FULL = {**{name: "x" for name in TOP}, "styles/outline.json": STYLE, **CHIPS}
STALE_STYLE = ["styles/split.json"]

# A full build: only the stale style, a v1 per-chip file nothing references any more,
# and a chip the rebuild dropped (in no parquet, not staged) go.
dropped = list(chip_files("C", "c9_2023"))
got = prune_case(FULL, published=[*PUBLISHED, *STALE_STYLE, "chips/A/c1_2023/c1_2023_overlay.webp", *dropped])
check(got == sorted(["chips/A/c1_2023/c1_2023_overlay.webp", *dropped, *STALE_STYLE]),
      f"a full staging prunes the stale style, an unreferenced chip file and a dropped chip, got {got}")

# The staged collection.json: missing, unparsable, or not a Collection with assets.
for name, collection, needle in (
    ("no staged collection.json", None, "no staged collection.json"),
    ("a parse error", "{not json", "not JSON"),
    ("an empty object", {}, "not a STAC Collection"),
    ("a list", [], "not a STAC Collection"),
    ("a Feature", {"type": "Feature", "assets": COLLECTION["assets"]}, "not a STAC Collection"),
    ("a list of assets", {"type": "Collection", "assets": []}, "has no assets"),
    ("no assets", {"type": "Collection", "assets": {}}, "has no assets"),
    ("an asset that is not an object", {"type": "Collection", "assets": {**COLLECTION["assets"], "x": "./x"}},
     "not an object"),
):
    got = prune_case(FULL, collection=collection)
    check(refused(got, needle), f"a staged collection.json that is {name} is refused, got {got}")

# Collection assets: a bare relative href and an absolute one, neither staged.
for href, needle in (("chips.pmtiles", "(chips.pmtiles) is not staged"),
                     ("https://data.source.coop/ftw/benchmark-data/g/d/chips.pmtiles", "absolute href")):
    collection = {**COLLECTION, "assets": {**COLLECTION["assets"], "chips_tiles": {"href": href}}}
    got = prune_case(FULL, collection=collection, published=[*PUBLISHED, "chips.pmtiles"])
    check(refused(got, needle), f"collection asset href {href!r} with no staged file is refused, got {got}")

# A staged style that draws from PMTiles staging lacks (a collection that lists no tiles).
collection = {**COLLECTION, "assets": {k: v for k, v in COLLECTION["assets"].items() if k != "fields_tiles"}}
got = prune_case({k: v for k, v in FULL.items() if k != "fields.pmtiles"}, collection=collection)
check(refused(got, "draws ../fields.pmtiles"), f"a style drawing unstaged PMTiles is refused, got {got}")

# What backfill.fetch leaves: item JSON and the parquets, no rasters or PMTiles.
backfill_shaped = {k: v for k, v in FULL.items() if not k.endswith((".tif", ".pmtiles"))}
got = prune_case(backfill_shaped)
check(refused(got, "fields.pmtiles", "chip A/c1_2023"), f"a backfill staging is refused, got {got}")

# A rebuild before its imagery pass: everything but the imagery, which the bucket has.
pre_imagery = {k: v for k, v in FULL.items() if "_q1_" not in k}
got = prune_case(pre_imagery)
check(refused(got, "chip A/c1_2023", "chip B/c2_2023"), f"a pre-imagery staging is refused when the bucket has imagery, got {got}")
got = prune_case(pre_imagery, published=[k for k in PUBLISHED if "_q1_" not in k])
check(got == [], f"a staging without imagery is complete when nothing published has imagery, got {got}")

# Chips the chips parquet still lists but staging lacks: all of chips/, or one square.
got = prune_case({k: v for k, v in FULL.items() if not k.startswith("chips/")})
check(refused(got, "chip A/c1_2023", "chip B/c2_2023"), f"a staging with no chips/ is refused, got {got}")
got = prune_case({k: v for k, v in FULL.items() if not k.startswith("chips/B/")})
check(refused(got, "chip B/c2_2023") and "A/c1_2023" not in got, f"a staging missing one square is refused, got {got}")
# ... and with no chips parquet, kept chips cannot be told from dropped ones.
collection = {**COLLECTION, "assets": {k: v for k, v in COLLECTION["assets"].items() if k != "chips"}}
got = prune_case({k: v for k, v in FULL.items() if not k.startswith("chips/B/")}, collection=collection)
check(refused(got, "no staged chips parquet"), f"stale chip files with no chips parquet are refused, got {got}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: prune contract holds")
