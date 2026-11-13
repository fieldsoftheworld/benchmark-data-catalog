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
check(recipe["stages"]["chips"]["drop_border_chips"] is True, "wall-to-wall drops border chips")

# A derived dataset reads the script's output; a Presence-only row gets presence-only masks.
es_row = {**ROW, "dataset_id": "es_po_2025", "harmonized_id": "es", "year": "2025",
          "wall_to_wall": new_dataset.PRESENCE_ONLY}
es_urls = new_dataset.source_urls(es_row)
derived = yaml.safe_load(new_dataset.recipe_text("es_po_2025", es_row, COLLECTION, es_urls, "9.9.9"))
check(derived["fields_file"] == "work/es_po_2025.parquet", f"derived input: {derived['fields_file']}")
check(derived["source_via"] == es_urls["collection"], "a derived dataset still names its collection")
check(derived["stages"]["masks"]["presence_only"] is True, "Presence-only row: presence_only true")
check(derived["stages"]["chips"]["drop_border_chips"] is False,
      "presence-only keeps border chips: sparse samples would lose every chip")
check(derived["stages"]["masks"]["mask_types"] == ["semantic_2_class", "semantic_3_class"],
      f"presence-only builds the semantic masks only: {derived['stages']['masks']['mask_types']}")

# A collection labelled only inside its sample areas reads its label extent instead.
for hid in new_dataset.LABEL_EXTENT_SOURCES:
    ext_row = {**ROW, "dataset_id": f"{hid}_2021", "harmonized_id": hid, "year": "2021",
               "wall_to_wall": "Yes (inside labelled tiles)"}
    ext = yaml.safe_load(new_dataset.recipe_text(
        f"{hid}_2021", ext_row, COLLECTION, new_dataset.source_urls(ext_row), "9.9.9"))
    ext_masks = ext["stages"]["masks"]
    check(ext_masks.get("label_extent") == f"../work/extents/{hid}_2021.parquet",
          f"{hid}: the recipe reads work/extents/<id>.parquet, relative to datasets/: {ext_masks}")
    check(ext_masks["presence_only"] is False, f"{hid}: label_extent, so not presence-only")
    check(ext["stages"]["chips"]["drop_border_chips"] is False,
          f"{hid}: sample areas keep border chips; outside the extent is unknown anyway")
    check(ext_masks["mask_types"] == new_dataset.PRESENCE_ONLY_MASK_TYPES,
          f"{hid}: semantic masks only, the ones that mark outside the extent unknown: "
          f"{ext_masks['mask_types']}")
check("label_extent" not in recipe["stages"]["masks"], "an ordinary dataset has no label extent")
check("label_extent" not in derived["stages"]["masks"], "nor does a presence-only one")
# LEM's fields are a sample: an ordinary presence-only recipe, no extent.
lem_row = {**ROW, "dataset_id": "br_ba_lem_2020", "harmonized_id": "br_ba_lem", "year": "2020",
           "filter": "", "wall_to_wall": new_dataset.PRESENCE_ONLY}
lem = yaml.safe_load(new_dataset.recipe_text(
    "br_ba_lem_2020", lem_row, COLLECTION, new_dataset.source_urls(lem_row), "9.9.9"))
check("label_extent" not in lem["stages"]["masks"] and lem["stages"]["masks"]["presence_only"] is True
      and lem["stages"]["chips"]["drop_border_chips"] is False
      and lem["stages"]["masks"]["mask_types"] == new_dataset.PRESENCE_ONLY_MASK_TYPES,
      f"br_ba_lem_2020 is a plain presence-only recipe: {lem['stages']}")
try:
    real_row = tracking.row
    tracking.row = lambda d, rows=None: {**ROW, "dataset_id": d, "harmonized_id": "glocab",
                                         "status": "include", "wall_to_wall": new_dataset.PRESENCE_ONLY}
    new_dataset.scaffold("glocab_2021")
    errors.append("a Presence-only row of a label-extent collection is scaffolded")
except SystemExit as stop:
    check("label extent" in str(stop), f"label extent and presence-only refused together: {stop}")
finally:
    tracking.row = real_row

# The real tracking rows of the research sets scaffold the recipes decided for them
# (2026-11-10): label extents with semantic masks, and LEM plain presence-only.
from ftw_dataset_tools.api.config import DatasetConfig  # noqa: E402

EXTENT_IDS = ["ai4sf_ml_2021", "glocab_2017", "glocab_2018", "glocab_2019", "glocab_2020",
              "rw_rwanda_ml_2021", *(f"wri_trazo_ml_{y}" for y in range(2020, 2025))]
for real_id in [*EXTENT_IDS, "br_ba_lem_2020"]:
    real = tracking.row(real_id)
    check(new_dataset.row_problem(real) is None, f"{real_id}: {new_dataset.row_problem(real)}")
    check("label-extent support" not in real["issues"], f"{real_id}: obsolete issue {real['issues']!r}")
    text = new_dataset.recipe_text(real_id, real, COLLECTION, new_dataset.source_urls(real), "9.9.9")
    real_recipe = yaml.safe_load(text)
    masks, chips = real_recipe["stages"]["masks"], real_recipe["stages"]["chips"]
    check(masks["mask_types"] == new_dataset.PRESENCE_ONLY_MASK_TYPES,
          f"{real_id}: semantic masks only: {masks['mask_types']}")
    check(chips["drop_border_chips"] is False, f"{real_id}: border chips kept")
    if real_id in EXTENT_IDS:
        check(masks.get("label_extent") == f"../work/extents/{real_id}.parquet"
              and masks["presence_only"] is False, f"{real_id}: reads its label extent: {masks}")
    else:
        check("label_extent" not in masks and masks["presence_only"] is True,
              f"{real_id}: presence-only, no extent: {masks}")
    # ftwd's own validation (label_extent with presence_only, mask types); the extent file
    # itself is checked when ftwd loads the recipe from disk, not here.
    try:
        DatasetConfig.from_dict(real_recipe)
    except Exception as exc:  # noqa: BLE001 - any refusal is the failure
        errors.append(f"{real_id}: ftwd refuses the recipe: {exc}")
for year in range(2020, 2025):
    trazo = tracking.row(f"wri_trazo_ml_{year}")
    # The split column (WRI's test regions) is only in the _ml edition.
    check(trazo["harmonized_id"] == "wri_trazo_ml" and not trazo["issues"],
          f"wri_trazo_ml_{year} reads wri_trazo_ml and waits for nothing: {trazo}")

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

# A canton of a multi-source collection carries its own item's terms, not the collection's mix.
mixed = {
    **COLLECTION,
    "license": "other",
    "providers": [{"name": "Canton A", "roles": ["producer", "licensor"]},
                  {"name": "Canton B", "roles": ["producer", "licensor"]}],
    "attribution": "A; B",
    "links": [*COLLECTION["links"], {"rel": "license", "href": "https://spdx.org/licenses/CC-BY-4.0.html"},
              {"rel": "license", "href": "https://b.example/terms"}],
}
item_b = {"properties": {"license": "other", "attribution": "Canton B data",
                         "providers": [{"name": "Canton B", "roles": ["producer", "licensor"]}]},
          "links": [{"rel": "license", "href": "https://b.example/terms"}]}
own = new_dataset.item_terms(mixed, item_b)
own_meta = yaml.safe_load(new_dataset.recipe_text("xx_2022", ROW, own, urls, "9.9.9"))["metadata"]
check(own_meta["license_url"] == "https://b.example/terms", f"the canton's own terms: {own_meta.get('license_url')}")
check([p["name"] for p in own_meta["providers"]] == ["Canton B", "Fields of the World"],
      f"only the canton and FTW are credited: {own_meta['providers']}")
check(own_meta["attribution"] == "Canton B data", f"the canton's attribution: {own_meta['attribution']}")
cc0 = new_dataset.item_terms(mixed, {"properties": {"license": "CC0-1.0"}, "links": []})
check(cc0["license"] == "CC0-1.0", "an SPDX item license replaces the collection's 'other'")
check(new_dataset.item_terms(COLLECTION, {"properties": {}}) is COLLECTION, "an item without terms keeps the collection's")

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

# --- run_batch.py checks the label extent before ftwd reads the recipe -----
_saved_steps = (run_batch._run, run_batch.reads_extent, run_batch.LOGS)
with tempfile.TemporaryDirectory() as tmp:
    run_batch.LOGS = Path(tmp)
    calls: list[str] = []
    exit_codes: dict[str, int] = {}

    def fake_run(argv, log):
        script = Path(argv[1]).name
        calls.append(script)
        return exit_codes.get(script, 0)

    run_batch._run = fake_run
    steps = run_batch.IMAGERY_STEPS
    run_batch.reads_extent = lambda d: d == "ext_2021"
    check(run_batch.run_dataset("ext_2021", steps, scaffold=False) is None, "extent ok, steps run")
    check(calls[:1] == ["label_extent.py"] and calls.count("build.py") == 2,
          f"the extent is checked first, then the build: {calls}")
    calls.clear()
    check(run_batch.run_dataset("plain_2021", steps, scaffold=False) is None, "no extent, steps run")
    check("label_extent.py" not in calls, f"a recipe without an extent skips the step: {calls}")
    calls.clear()
    exit_codes["label_extent.py"] = 1
    check(run_batch.run_dataset("ext_2021", steps, scaffold=False) == "label_extent",
          "a failed extent (missing source, sha256 mismatch) names the step")
    check(calls == ["label_extent.py"], f"and nothing is built from the wrong extent: {calls}")
run_batch._run, run_batch.reads_extent, run_batch.LOGS = _saved_steps

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
