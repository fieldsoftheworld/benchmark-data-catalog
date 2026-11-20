#!/usr/bin/env python3
"""relayout: flat catalog/<id>/ collections into catalog/<source>/<id>/.

Builds a flat catalog in a temp git repository with two collections from one
source and one from another (real dataset ids, so the groups come from the
real recipes), runs ``relayout.apply`` and checks the result: the folders
moved with git, root links one level deeper, every published URL moved, the
group catalogs written, the root linking the groups, and a second plan finding
nothing left to move. Also checks the bucket key mapping the move is planned
from. No network, no AWS.

Run: python3 tests/test_relayout.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import relayout  # noqa: E402
from common import public_url  # noqa: E402

errors: list[str] = []
MANIFEST = {"catalog": {"version": "2.0.0-test", "human_base": "https://source.coop/ftw/benchmark-data"}}
HUMAN = "https://source.coop/ftw/benchmark-data"


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


def flat_collection(catalog: Path, dataset_id: str, source: str) -> None:
    write_json(catalog / dataset_id / "collection.json", {
        "type": "Collection", "id": dataset_id, "title": dataset_id.upper(), "license": "CC-BY-4.0",
        "ftw:config": {"config": {"year": int(dataset_id[-4:]),
                                  "source_via": f"https://data.source.coop/ftw/harmonized-field-data/{source}/collection.json"}},
        "links": [
            {"rel": "root", "href": "../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            {"rel": "child", "href": "./chips/32UNA/catalog.json", "type": "application/json"},
        ],
    })
    write_json(catalog / dataset_id / "chips" / "32UNA" / "catalog.json", {
        "type": "Catalog", "id": "32UNA",
        "links": [{"rel": "root", "href": "../../../catalog.json", "type": "application/json"}],
    })
    (catalog / dataset_id / "README.md").write_text(
        f"# {dataset_id}\n\n[browse]({relayout._url_bases(MANIFEST)[1]}/{dataset_id}/collection.json) "
        f"[items]({public_url(f'{dataset_id}/items.parquet')}) "
        f"[guide]({HUMAN}/{dataset_id}/AGENTS.md) [page]({HUMAN}/{dataset_id})\n"
    )
    write_json(catalog / dataset_id / "styles" / "default.json", {"sources": {"x": {"url": "pmtiles://../chips.pmtiles"}}})


with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    catalog = repo / "catalog"
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    for dataset_id, source in (("lv_2020", "lv"), ("lv_2021", "lv"), ("be_wal_2022", "be_wal")):
        flat_collection(catalog, dataset_id, source)
    write_json(catalog / "catalog.json", {"type": "Catalog", "id": "root", "links": [
        {"rel": "root", "href": "./catalog.json", "type": "application/json"},
        {"rel": "child", "href": "./lv_2020/collection.json", "type": "application/json"},
    ]})
    (catalog / "README.md").write_text(
        f"| [LV]({HUMAN}/lv_2020) | <img src=\"{public_url('lv_2020/thumbnail.webp')}\"> |\n"
        f"one per collection, at `{HUMAN}/<id>/AGENTS.md`; not {HUMAN}/lv_2020x\n"
        f"see <{HUMAN}/lv_2021>, [{HUMAN}/lv_2021], `{HUMAN}/lv_2021`, {HUMAN}/lv_2021, or {HUMAN}/lv_2021.\n"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)

    moves = relayout.plan(catalog)
    check(relayout.dataset_groups(catalog) == {"be_wal_2022": "be_wal", "lv_2020": "lv", "lv_2021": "lv"},
          "dataset_groups places the flat collections by recipe")
    check([(m.dataset_id, m.group) for m in moves]
          == [("be_wal_2022", "be_wal"), ("lv_2020", "lv"), ("lv_2021", "lv")],
          f"the plan groups by the recipes' source_via, got {moves}")

    # A run that stops at the second move leaves be_wal_2022 moved but not
    # rewritten and lv_2020 still flat. The rerun has to finish both.
    calls = []

    def fail_second(src: Path, dst: Path, root: Path) -> None:
        calls.append(src.name)
        if len(calls) == 2:
            raise RuntimeError("interrupted")
        relayout._git_mv(src, dst, root)

    try:
        relayout.apply(moves, manifest=MANIFEST, catalog=catalog, root=repo, move=fail_second,
                       fetch_title=lambda _u: None)
        check(False, "the injected failure stops the first run")
    except RuntimeError:
        pass
    half = json.loads((catalog / "be_wal" / "be_wal_2022" / "collection.json").read_text())
    check([l["href"] for l in half["links"] if l["rel"] == "root"] == ["../catalog.json"],
          "the interrupted run moved be_wal_2022 without rewriting it")
    rerun = relayout.plan(catalog)
    check([m.dataset_id for m in rerun] == ["lv_2020", "lv_2021"], f"the rerun plans what is left: {rerun}")
    relayout.apply(rerun, manifest=MANIFEST, catalog=catalog, root=repo, fetch_title=lambda _u: None)
    done = json.loads((catalog / "be_wal" / "be_wal_2022" / "collection.json").read_text())
    check([l["href"] for l in done["links"] if l["rel"] == "root"] == ["../../catalog.json"],
          "the rerun fixes the dataset the first run moved but did not rewrite")
    check(public_url("be_wal/be_wal_2022/items.parquet") in (catalog / "be_wal" / "be_wal_2022" / "README.md").read_text(),
          "the rerun moves that dataset's URLs too")
    again = {p: p.read_text() for p in catalog.rglob("*") if p.is_file()}
    relayout.apply([], manifest=MANIFEST, catalog=catalog, root=repo, fetch_title=lambda _u: None)
    check(again == {p: p.read_text() for p in catalog.rglob("*") if p.is_file()},
          "normalising an already relaid-out catalog changes nothing")

    check(not (catalog / "lv_2020").exists() and (catalog / "lv" / "lv_2020" / "collection.json").is_file(),
          "the collection folder moved under its source group")
    staged = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
    check("R  catalog/lv_2020/chips/32UNA/catalog.json -> catalog/lv/lv_2020/chips/32UNA/catalog.json" in staged
          or "catalog/lv/lv_2020/chips/32UNA/catalog.json" in staged,
          f"the move goes through git, got {staged[:400]}")

    coll = json.loads((catalog / "lv" / "lv_2020" / "collection.json").read_text())
    rel = {l["rel"]: l["href"] for l in coll["links"]}
    check(rel["root"] == "../../catalog.json" and rel["parent"] == "../catalog.json",
          f"collection root gains a level, parent is now the group: {rel}")
    sub = json.loads((catalog / "lv" / "lv_2020" / "chips" / "32UNA" / "catalog.json").read_text())
    check(sub["links"][0]["href"] == "../../../../catalog.json", f"sub-catalog root gains a level: {sub}")
    style = json.loads((catalog / "lv" / "lv_2020" / "styles" / "default.json").read_text())
    check(style["sources"]["x"]["url"] == "pmtiles://../chips.pmtiles", "a style's relative tile URL is left alone")

    readme = (catalog / "lv" / "lv_2020" / "README.md").read_text()
    check(public_url("lv/lv_2020/items.parquet") in readme
          and f"{HUMAN}/lv/lv_2020/AGENTS.md" in readme
          and f"{HUMAN}/lv/lv_2020)" in readme
          and "benchmark-data/lv/lv_2020/collection.json" in readme
          and "benchmark-data/lv_2020" not in readme,
          f"every published URL in the collection's docs moves: {readme}")
    root_readme = (catalog / "README.md").read_text()
    check(f"[LV]({HUMAN}/lv/lv_2020)" in root_readme
          and public_url("lv/lv_2020/thumbnail.webp") in root_readme
          and f"{HUMAN}/<source>/<id>/AGENTS.md" in root_readme
          and f"{HUMAN}/lv_2020x" in root_readme
          and root_readme.count(f"{HUMAN}/lv/lv_2021") == 5,
          f"root docs move whole dataset segments only, and the placeholder: {root_readme}")

    group = json.loads((catalog / "lv" / "catalog.json").read_text())
    check([l["href"] for l in group["links"] if l["rel"] == "child"]
          == ["./lv_2020/collection.json", "./lv_2021/collection.json"],
          f"the group catalog lists its collections in order: {group['links']}")
    check(group["title"] == "lv" and any(l["rel"] == "via" for l in group["links"]),
          "offline, the group is titled by its id and still links its source")
    check((catalog / "lv" / "README.md").is_file() and (catalog / "lv" / "AGENTS.md").is_file(),
          "the group gets a README and an agent guide")
    root_doc = json.loads((catalog / "catalog.json").read_text())
    check([l["href"] for l in root_doc["links"] if l["rel"] == "child"]
          == ["./be_wal/catalog.json", "./lv/catalog.json"],
          f"the root links the source groups: {root_doc['links']}")
    check(relayout.plan(catalog) == [], "a second plan finds nothing left to move")

# --- the bucket key mapping -----------------------------------------------------
groups = {"lv_2020": "lv"}
check(relayout.new_key("ftw/benchmark-data/lv_2020/chips/A/c/c_q1.tif", groups, "ftw/benchmark-data")
      == "ftw/benchmark-data/lv/lv_2020/chips/A/c/c_q1.tif", "a dataset key moves under its group")
check(relayout.new_key("ftw/benchmark-data/catalog.json", groups, "ftw/benchmark-data") is None,
      "a root file is not a dataset key")
check(relayout.new_key("ftw/benchmark-data/lv_2020x/a.tif", groups, "ftw/benchmark-data") is None,
      "an unknown folder is left alone")
KEYS = [
    "ftw/benchmark-data/lv_2020/collection.json",
    "ftw/benchmark-data/lv_2020/README.md",
    "ftw/benchmark-data/lv_2020/AGENTS.md",
    "ftw/benchmark-data/lv_2020/llms.txt",
    "ftw/benchmark-data/lv_2020/items.parquet",
    "ftw/benchmark-data/lv_2020/lv_2020_chips.parquet",
    "ftw/benchmark-data/lv_2020/chips.pmtiles",
    "ftw/benchmark-data/lv_2020/thumbnail.webp",
    "ftw/benchmark-data/lv_2020/chips/A/catalog.json",
    "ftw/benchmark-data/lv_2020/chips/A/README.md",
    "ftw/benchmark-data/lv_2020/chips/A/AGENTS.md",
    "ftw/benchmark-data/lv_2020/chips/A/c/c.json",
    "ftw/benchmark-data/lv_2020/chips/A/c/c_q1.tif",
    "ftw/benchmark-data/lv_2020/chips/A/c/c_q1.webp",
    "ftw/benchmark-data/README.md",
]
copy, reupload = relayout.bucket_moves(KEYS, groups, "ftw/benchmark-data")
check([old.rsplit("/", 1)[-1] for old, _ in copy]
      == ["lv_2020_chips.parquet", "chips.pmtiles", "thumbnail.webp", "c_q1.tif", "c_q1.webp"],
      f"only rasters, previews, tiles and GeoParquet are copied as they are: {copy}")
check([old.split("lv_2020/", 1)[1] for old, _ in reupload]
      == ["collection.json", "README.md", "AGENTS.md", "llms.txt", "items.parquet", "chips/A/catalog.json",
          "chips/A/README.md", "chips/A/AGENTS.md", "chips/A/c/c.json"],
      f"JSON, every dataset- and chip-level doc and the items mirror are uploaded again: {reupload}")
with tempfile.TemporaryDirectory() as tmp:
    keys_file = Path(tmp) / "keys.txt"
    keys_file.write_text("\n".join(KEYS) + "\n")
    copy_file, reupload_file = relayout.write_bucket_plan(keys_file, "ftw/benchmark-data", groups)
    copy_lines = copy_file.read_text().splitlines()
    check(len(copy_lines) == 5 and len(reupload_file.read_text().splitlines()) == 9
          and copy_lines[0] == "ftw/benchmark-data/lv_2020/lv_2020_chips.parquet\t"
                               "ftw/benchmark-data/lv/lv_2020/lv_2020_chips.parquet",
          f"the bucket plan writes old<TAB>new lists: {copy_lines[:1]}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: relayout moves collections into source groups and plans the bucket move")
