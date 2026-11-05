#!/usr/bin/env python3
"""The region-year batch tools: tracking.csv, new_dataset.py and run_batch.py.

Exercises the pure parts offline: tracking.csv's shape and round trip, the
recipe text new_dataset.py writes (parsed back as YAML and checked against
the same rules tests/test_manifest.py applies to a committed recipe), the
thumbnail default, and run_batch.py's queue selection. Nothing here touches
the network or runs ftwd.

Run: python3 tests/test_batch_tools.py
"""
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("skip   PyYAML is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import new_dataset  # noqa: E402
import run_batch  # noqa: E402
import tracking  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# --- tracking.csv is well-formed ------------------------------------------
rows = tracking.load()
ids = [r["dataset_id"] for r in rows]
check(len(ids) == len(set(ids)), "tracking.csv dataset_id values are unique")
for r in rows:
    d = r["dataset_id"]
    check(r["status"] in tracking.STATUSES, f"{d}: unknown status {r['status']!r}")
    check(r["imagery"] in tracking.IMAGERY, f"{d}: unknown imagery {r['imagery']!r}")
    # Derived datasets (new_dataset.DERIVED) are named for what they hold, not one source.
    check(d in new_dataset.DERIVED or d == f"{tracking.source_stem(r)}_{r['year']}",
          f"{d}: id is not <source stem>_<year>")
    check(
        tracking.source_stem(r).startswith(r["harmonized_id"]),
        f"{d}: source_stem {r['source_stem']!r} is not a sub-region of {r['harmonized_id']!r}",
    )
    if r["status"] == "include":
        check(
            any(m in new_dataset.RELEASE_IMAGERY for m in tracking.imagery_modes(r)),
            f"{d}: 'include' but none of its imagery is released; mark it blocked",
        )
    if r["status"] == "blocked":
        check(bool(r["notes"].strip()), f"{d}: blocked rows say what they wait for")
    if tracking.filter_file(r):
        check(r["filter"].endswith(".yaml"), f"{d}: filter {r['filter']!r} is not a yaml file")

# --- every committed recipe selects only released imagery ---------------
for recipe_path in sorted((ROOT / "datasets").glob("*.yaml")):
    stages = (yaml.safe_load(recipe_path.read_text()) or {}).get("stages") or {}
    select = stages.get("select_images") or {}
    if not select.get("enabled", True):
        continue
    mode = select.get("imagery_mode", "scenes")
    modes = [mode] if isinstance(mode, str) else list(mode)
    check(
        set(modes) <= set(new_dataset.RELEASE_IMAGERY),
        f"{recipe_path.name}: selects {modes}; this release builds {list(new_dataset.RELEASE_IMAGERY)}",
    )

# --- update() round-trips and refuses unknown columns ---------------------
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "tracking.csv"
    tracking.save(rows, path)
    tracking.update(ids[0], path, issues="boom")
    again = tracking.load(path)
    check(again[0]["issues"] == "boom", "update() writes the field")
    check(again[1:] == rows[1:], "update() leaves the other rows alone")
    try:
        tracking.update(ids[0], path, nope="x")
        errors.append("update() accepts an unknown column")
    except KeyError:
        pass

check(tracking.imagery_modes({"imagery": "scenes+mosaics"}) == ("scenes", "mosaics"), "modes")
check(tracking.imagery_modes({"imagery": "mosaics"}) == ("mosaics",), "mosaics-only modes")

# --- new_dataset.py writes a recipe the manifest gate accepts --------------
COLLECTION = {
    "license": "CC-BY-4.0",
    "assets": {"data": {}, "style-hcat-crops": {}},
    "providers": [
        {"name": "Agency", "roles": ["producer", "licensor"], "url": "https://agency.example"},
        {"name": "Fields of the World", "roles": ["processor", "host"]},
    ],
    "links": [{"rel": "item", "href": "./year=2022/xx-2022.json", "title": "Place — 2022"}],
}
ROW = {
    "dataset_id": "xx_2022",
    "harmonized_id": "xx",
    "year": "2022",
    "region": "Place",
    "imagery": "scenes+mosaics",
    "filter": "xx_filter.yaml",
}
urls = new_dataset.source_urls(ROW)
check(
    urls["parquet"].endswith("/xx/year=2022/xx-2022.parquet"),
    "fields_file is the year's own parquet, never latest",
)
canton = new_dataset.source_urls({**ROW, "dataset_id": "xx_ab_2022", "source_stem": "xx_ab"})
check(
    canton["parquet"].endswith("/xx/year=2022/xx_ab-2022.parquet")
    and canton["collection"].endswith("/xx/collection.json"),
    "a sub-region reads its own file from the parent collection",
)
two_items = {"links": [
    {"rel": "item", "href": "./year=2022/xx_aa-2022.json", "title": "AA — 2022"},
    {"rel": "item", "href": "./year=2022/xx_ab-2022.json", "title": "AB — 2022"},
]}
check(
    new_dataset.item_title(two_items, canton["item"], "fallback") == "AB — 2022",
    "title comes from the sub-region's own item, not the first item of that year",
)
recipe = yaml.safe_load(new_dataset.recipe_text("xx_2022", ROW, COLLECTION, urls, "9.9.9"))
check(recipe["name"] == "xx_2022" and recipe["year"] == 2022, "name and year")
check(recipe["output_dir"] == "staging/xx_2022", "output_dir is staging/<id>")
check(recipe["metadata"]["title"] == "Place — 2022", "title is the harmonized item's title")
check(recipe["metadata"]["attribution"] == "Agency", "attribution falls back to the producer")
check(recipe["metadata"]["version"] == "9.9.9", "version comes from the manifest")
names = [p["name"] for p in recipe["metadata"]["providers"]]
check(names == ["Agency", "Fields of the World"], f"FTW listed once, as processor: {names}")
check(recipe["stages"]["masks"]["class_filter"] == "filters/xx_filter.yaml", "filter path")
for mask_type in ("instance", "semantic_2_class", "semantic_3_class",
                  "decode_boundary", "decode_distance"):
    check(mask_type in recipe["stages"]["masks"]["mask_types"], f"mask type {mask_type}")
select = recipe["stages"]["select_images"]
check(select["imagery_mode"] == "mosaics", f"scenes+mosaics builds the released mosaics: {select}")
check(select["nodata_max"] == 100.0, "mosaics keep their gaps")
check(recipe["stages"]["download_images"]["mode"] == "clip", "imagery is clipped onto the mask grid")
check(recipe["fields_file"] == urls["parquet"], "an ordinary dataset reads the harmonized parquet")
check(recipe["stages"]["masks"]["presence_only"] is False, "wall-to-wall by default")

# A derived dataset reads the script's output; a Presence-only row gets presence-only masks.
es_row = {**ROW, "dataset_id": "es_po_2025", "harmonized_id": "es", "year": "2025",
          "wall_to_wall": new_dataset.PRESENCE_ONLY}
es_urls = new_dataset.source_urls(es_row)
derived = yaml.safe_load(new_dataset.recipe_text("es_po_2025", es_row, COLLECTION, es_urls, "9.9.9"))
check(derived["fields_file"] == "work/es_po_2025.parquet", f"derived input: {derived['fields_file']}")
check(derived["source_via"] == es_urls["collection"], "a derived dataset still names its collection")
check(derived["stages"]["masks"]["presence_only"] is True, "Presence-only row: presence_only true")
check(derived["stages"]["masks"]["mask_types"] == ["semantic_2_class", "semantic_3_class"],
      f"presence-only builds the semantic masks only: {derived['stages']['masks']['mask_types']}")

# Credits for a dataset drawn from several collections.
cc_open = {"license": "CC-BY-4.0", "attribution": "Nat", "providers": [
    {"name": "Nat", "roles": ["producer"]}, {"name": "Fields of the World", "roles": ["host"]}]}
cc_region = {"license": "CC-BY-4.0", "attribution": "Reg", "providers": [
    {"name": "Reg", "roles": ["producer"]}, {"name": "Fields of the World", "roles": ["host"]}]}
own_terms = {"license": "other", "attribution": "Own", "providers": [{"name": "Own", "roles": ["producer"]}],
             "links": [{"rel": "license", "href": "https://own.example/terms"}]}
same = new_dataset.combined_collection([{**cc_open, "links": COLLECTION["links"]}, cc_region])
check(same["license"] == "CC-BY-4.0", f"one shared license is kept: {same['license']}")
check(same["attribution"] == "Nat; Reg", f"attributions are joined: {same['attribution']}")
check([p["name"] for p in same["providers"]] == ["Nat", "Fields of the World", "Reg"],
      f"providers listed once each: {same['providers']}")
check(same["links"] == COLLECTION["links"], "the first collection's item links are kept")
mixed = new_dataset.combined_collection([cc_open, own_terms])
check(mixed["license"] == "other" and "TODO(attest)" in new_dataset.license_lines(mixed),
      f"differing licenses need attesting: {new_dataset.license_lines(mixed)!r}")

try:
    new_dataset.recipe_text("xx_2022", {**ROW, "imagery": "scenes"}, COLLECTION, urls, "9.9.9")
    errors.append("a scenes-only year gets a recipe though scenes are not released")
except SystemExit as stop:
    check("mark the row blocked" in str(stop), f"scenes-only says to block the row: {stop}")
unfiltered_mosaics = yaml.safe_load(
    new_dataset.recipe_text("xx_2022", {**ROW, "filter": ""}, COLLECTION, urls, "9.9.9")
)
check("class_filter" not in unfiltered_mosaics["stages"]["masks"], "no filter, no class_filter key")
unfiltered = yaml.safe_load(
    new_dataset.recipe_text("xx_2022", {**ROW, "filter": tracking.NO_FILTER}, COLLECTION, urls, "9.9.9")
)
check("class_filter" not in unfiltered["stages"]["masks"], "'none' writes no class_filter")

other = {
    **COLLECTION,
    "license": "other",
    "links": [*COLLECTION["links"], {"rel": "license", "href": "https://terms.example"}],
}
other_meta = yaml.safe_load(new_dataset.recipe_text("xx_2022", ROW, other, urls, "9.9.9"))["metadata"]
check(other_meta["license_url"] == "https://terms.example", "'other' carries the source's terms")
check("license_url" not in recipe["metadata"], "an SPDX license needs no license_url")

no_attr = {**COLLECTION, "providers": []}
check(new_dataset.attribution(no_attr) == "TODO(attest)", "missing attribution is flagged")

# --- thumbnail default: field outlines, whatever the source carries -------
check(new_dataset.thumbnail_spec() == {"style": "outline", "zoom": 13, "rank": 0}, "outline default")
spec = new_dataset.thumbnail_spec()
spec["zoom"] = 99
check(new_dataset.thumbnail_spec()["zoom"] == 13, "callers get their own copy of the default")
entry = yaml.safe_load(new_dataset.manifest_entry("xx_2022", {"style": "s", "zoom": 12, "rank": 0}))
check(entry["xx_2022"]["ftw1_name"] == "none", "new region-years have no FTW 1.0 counterpart")

# --- run_batch.py marks rows done only when the batch's gates pass --------
_saved = (run_batch.run_pass, run_batch.finish_batch, run_batch.hold_lock, tracking.update,
          tracking.load, tracking.row)
updates: dict[str, dict] = {}
run_batch.run_pass = lambda ids, **_k: {"b": "build --through stac failed"}
run_batch.hold_lock = lambda: None
tracking.update = lambda d, path=None, **kw: updates.setdefault(d, {}).update(kw)
tracking.load = lambda path=None: []
tracking.row = lambda d, rows: {}
for gate_failure, expect_built in ((None, True), ("the batch's gates failed", False)):
    updates.clear()
    run_batch.finish_batch = lambda failure=gate_failure: failure
    run_batch.main(["a", "b"])
    check(("built" in updates["a"]) == expect_built, f"a built={expect_built} when gates {gate_failure}")
    check("built" not in updates["b"], "a failed build is never marked built")
    if gate_failure:
        check(updates["a"]["issues"] == gate_failure, "a gate failure is recorded as the issue")
try:
    run_batch.main(["--next", "3", "--mark-published"])
    errors.append("--mark-published accepts --next")
except SystemExit:
    pass
(run_batch.run_pass, run_batch.finish_batch, run_batch.hold_lock, tracking.update,
 tracking.load, tracking.row) = _saved

# --- run_batch.py picks the right queue -----------------------------------
queue = [
    {"dataset_id": "a", "status": "include", "built": "", "imagery_done": ""},
    {"dataset_id": "b", "status": "exclude", "built": "", "imagery_done": ""},
    {"dataset_id": "c", "status": "include", "built": "2026-10-30", "imagery_done": ""},
    {"dataset_id": "d", "status": "include", "built": "2026-10-30", "imagery_done": "2026-10-31"},
    {"dataset_id": "e", "status": "include", "built": "", "imagery_done": "", "issues": "no source"},
]
for q in queue:
    q.setdefault("issues", "")
check(run_batch.next_ids(queue, 5, imagery=False) == ["a"], "metadata pass takes unbuilt includes")
check(run_batch.next_ids(queue, 5, imagery=True) == ["c"], "imagery pass takes built, no imagery")
argv = run_batch.tool_argv(["build.py", "{id}", "--only", "docs"], "xx_2022")
check(argv[1].endswith("tools/build.py") and argv[2:] == ["xx_2022", "--only", "docs"], "argv")


# --- a chiitiler that never starts fails the thumbnails, not the run ------
def _no_chiitiler():
    raise RuntimeError("chiitiler did not come up")


run_batch.start_chiitiler = _no_chiitiler
check(
    run_batch.thumbnails(["a", "b"]) == dict.fromkeys(["a", "b"], "chiitiler did not come up"),
    "thumbnails reports a chiitiler failure per dataset instead of exiting",
)

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("ok     batch tools")
