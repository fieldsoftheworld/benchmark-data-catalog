#!/usr/bin/env python3
"""The manifest, the recipes, and the published tree agree.

datasets.yaml names what this catalog publishes. datasets/<id>.yaml is the ftwd
recipe for each. catalog/<id>/ is what was published. A dataset in one place
but not the others is a mistake: a recipe nobody builds, a collection nobody
maintains, or a child link to nothing.

Also checks that every official recipe carries the fields a publishable
collection needs (a license, a title, a source href) so a build cannot start
from an incomplete recipe. Dependency-free apart from PyYAML.

Run: python3 tests/test_manifest.py
"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("skip   PyYAML is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from publish import load_config  # noqa: E402

config = load_config()
CATALOG = ROOT / config["publish_dir"]
MANIFEST = yaml.safe_load((ROOT / "datasets.yaml").read_text())
RECIPES = ROOT / "datasets"
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


declared = set(MANIFEST.get("datasets") or {})
recipes = {p.stem for p in RECIPES.glob("*.yaml")}
built = {p.parent.name for p in CATALOG.glob("*/collection.json")}

for missing in sorted(declared - recipes):
    err(f"{missing} is in datasets.yaml but datasets/{missing}.yaml does not exist")
for extra in sorted(recipes - declared):
    err(f"datasets/{extra}.yaml exists but {extra} is not in datasets.yaml")
for missing in sorted(declared - built):
    print(f"note: {missing} is declared but not built yet (next plan: tools/build.py {missing})")
for extra in sorted(built - declared):
    err(f"catalog/{extra}/ is published but not in datasets.yaml")

root = json.loads((CATALOG / "catalog.json").read_text())
children = {Path(link["href"]).parent.name for link in root["links"] if link["rel"] == "child"}
if children != built:
    err(f"catalog.json children {sorted(children)} != built collections {sorted(built)}")

for dataset_id in sorted(declared & recipes):
    recipe = yaml.safe_load((RECIPES / f"{dataset_id}.yaml").read_text()) or {}
    if recipe.get("name") != dataset_id:
        err(f"datasets/{dataset_id}.yaml: name must be '{dataset_id}', got {recipe.get('name')!r}")
    fields_file = str(recipe.get("fields_file") or "")
    if not fields_file.startswith("https://data.source.coop/ftw/harmonized-field-data/"):
        err(f"datasets/{dataset_id}.yaml: fields_file must be a harmonized-field-data URL")
    expected_out = f"{config.get('data_dir', 'staging')}/{dataset_id}"
    out = str(recipe.get("output_dir") or "")
    if out != expected_out:
        err(f"datasets/{dataset_id}.yaml: output_dir must be {expected_out!r}, got {out!r}")
    meta = recipe.get("metadata") or {}
    for key in ("title", "license"):
        if not meta.get(key):
            err(f"datasets/{dataset_id}.yaml: metadata.{key} is required for an official dataset")
    if meta.get("license") == "other" and not meta.get("license_url"):
        err(f"datasets/{dataset_id}.yaml: metadata.license 'other' requires metadata.license_url")
    catalog_version = (MANIFEST.get("catalog") or {}).get("version")
    if meta.get("version") != catalog_version:
        err(
            f"datasets/{dataset_id}.yaml: metadata.version {meta.get('version')!r} != "
            f"datasets.yaml catalog.version {catalog_version!r}"
        )
    if "TODO(attest)" in json.dumps(recipe):
        err(f"datasets/{dataset_id}.yaml: unattested value remains (TODO(attest))")
    spec = MANIFEST["datasets"][dataset_id] or {}
    if not spec.get("ftw1_name"):
        err(f"datasets.yaml: {dataset_id} needs ftw1_name (FTW 1.0 folder name, or 'none')")
    thumb = spec.get("thumbnail") or {}
    if not thumb.get("style"):
        err(f"datasets.yaml: {dataset_id}.thumbnail needs style")
    if not isinstance(thumb.get("zoom"), int):
        err(f"datasets.yaml: {dataset_id}.thumbnail.zoom must be an int, got {thumb.get('zoom')!r}")
    if not isinstance(thumb.get("rank"), int):
        err(f"datasets.yaml: {dataset_id}.thumbnail.rank must be an int, got {thumb.get('rank')!r}")

host = MANIFEST.get("host") or {}
if host.get("name") != "Source Cooperative" or "host" not in (host.get("roles") or []):
    err("datasets.yaml: host must be Source Cooperative with role host")

catalog_meta = MANIFEST.get("catalog") or {}
for key in ("id", "title", "version", "public_base", "human_base", "repository"):
    if not catalog_meta.get(key):
        err(f"datasets.yaml: catalog.{key} is required")

processor = MANIFEST.get("processor") or {}
if not processor.get("name") or not processor.get("url"):
    err("datasets.yaml: processor needs name and url")
if "processor" not in (processor.get("roles") or []):
    err("datasets.yaml: processor must have role processor")

for e in errors:
    print(f"error  {e}")
if errors:
    raise SystemExit(1)
print(f"ok     manifest agrees with {len(recipes)} recipe(s) and {len(built)} built collection(s)")
