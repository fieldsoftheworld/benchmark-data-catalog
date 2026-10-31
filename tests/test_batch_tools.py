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
    check(d == f"{tracking.source_stem(r)}_{r['year']}", f"{d}: id is not <source stem>_<year>")
    check(
        tracking.source_stem(r).startswith(r["harmonized_id"]),
        f"{d}: source_stem {r['source_stem']!r} is not a sub-region of {r['harmonized_id']!r}",
    )
    if r["imagery"] == "none":
        check(r["status"] != "include", f"{d}: no imagery, so it cannot be 'include'")
    if tracking.filter_file(r):
        check(r["filter"].endswith(".yaml"), f"{d}: filter {r['filter']!r} is not a yaml file")

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
check(select["imagery_mode"] == ["scenes", "mosaics"], f"both modes: {select['imagery_mode']}")
check(
    recipe["stages"]["download_images"]["mode"] == "preview",
    "both modes: ftwd previews the scenes and clips the mosaics",
)

scenes_only = yaml.safe_load(
    new_dataset.recipe_text("xx_2022", {**ROW, "imagery": "scenes", "filter": ""},
                            COLLECTION, urls, "9.9.9")
)
check(scenes_only["stages"]["select_images"]["imagery_mode"] == "scenes", "single mode")
check(scenes_only["stages"]["download_images"]["mode"] == "preview", "scenes-only previews")
check("class_filter" not in scenes_only["stages"]["masks"], "no filter, no class_filter key")
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

# --- thumbnail default follows the source's crop codes --------------------
check(new_dataset.thumbnail_spec(COLLECTION)["style"] == "dominant-crop", "crops -> dominant")
check(
    new_dataset.thumbnail_spec({"assets": {"data": {}}})["style"] == "field-coverage",
    "no crop codes -> field-coverage",
)
entry = yaml.safe_load(new_dataset.manifest_entry("xx_2022", {"style": "s", "zoom": 12, "rank": 0}))
check(entry["xx_2022"]["ftw1_name"] == "none", "new region-years have no FTW 1.0 counterpart")

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
