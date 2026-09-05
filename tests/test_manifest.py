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
import re
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

from common import PORTOLAN_SCHEMA_RE  # noqa: E402

config = load_config()
CATALOG = ROOT / config["publish_dir"]
MANIFEST = yaml.safe_load((ROOT / "datasets.yaml").read_text())
RECIPES = ROOT / "datasets"
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def check_built_collection(dataset_id: str) -> None:
    """A built collection's version, extensions and style assets agree with the manifest.

    Every check here needs the collection to actually exist on disk (it is
    built by catalogize.py, not hand-written), so this only runs for ids in
    `built`. The style checks degrade gracefully: a collection built before
    any style exists yet skips the thumbnail check with a note instead of
    failing on something tools/thumbnail.py (a later plan step) hasn't
    written.
    """
    collection = json.loads((CATALOG / dataset_id / "collection.json").read_text())

    catalog_version = (MANIFEST.get("catalog") or {}).get("version")
    if collection.get("version") != catalog_version:
        err(
            f"catalog/{dataset_id}/collection.json: version {collection.get('version')!r} != "
            f"datasets.yaml catalog.version {catalog_version!r}"
        )

    extensions = collection.get("stac_extensions") or []
    if not any(isinstance(e, str) and PORTOLAN_SCHEMA_RE.fullmatch(e) for e in extensions):
        err(f"catalog/{dataset_id}/collection.json: stac_extensions is missing a Portolan schema URI")

    assets = collection.get("assets") or {}
    styles = {key: asset for key, asset in assets.items() if key.startswith("style-")}
    if not styles:
        print(f"note: {dataset_id} has no style-* assets yet, skipping the thumbnail style check")
        return

    defaults = [key for key, asset in styles.items() if "default" in (asset.get("roles") or [])]
    if len(defaults) != 1:
        err(
            f"catalog/{dataset_id}/collection.json: expected exactly one style-* asset with role "
            f"'default', found {len(defaults)} among {sorted(styles)}"
        )

    spec = (MANIFEST.get("datasets") or {}).get(dataset_id) or {}
    thumb_style = (spec.get("thumbnail") or {}).get("style")
    if thumb_style and f"style-{thumb_style}" not in assets:
        err(
            f"catalog/{dataset_id}/collection.json: datasets.yaml thumbnail.style {thumb_style!r} "
            f"has no matching style-{thumb_style} asset"
        )


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

for dataset_id in sorted(built):
    check_built_collection(dataset_id)

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
    ftw1_name = spec.get("ftw1_name")
    if not ftw1_name:
        err(f"datasets.yaml: {dataset_id} needs ftw1_name (FTW 1.0 folder name, or 'none')")
    ftw1 = spec.get("ftw1")
    if ftw1_name == "none":
        if ftw1:
            err(f"datasets.yaml: {dataset_id} has ftw1_name: none but also carries an ftw1 block")
    elif ftw1_name:
        if not ftw1:
            err(f"datasets.yaml: {dataset_id} needs an ftw1 block (ftw1_name is {ftw1_name!r})")
        else:
            for key in ("year", "parcels", "chips", "train", "val", "test"):
                if not isinstance(ftw1.get(key), int):
                    err(f"datasets.yaml: {dataset_id}.ftw1.{key} must be an int, got {ftw1.get(key)!r}")
            license_ = ftw1.get("license")
            if not isinstance(license_, str) or not re.match(r"^[\w.\-]+$", license_ or ""):
                err(
                    f"datasets.yaml: {dataset_id}.ftw1.license must be an SPDX-looking "
                    f"string, got {license_!r}"
                )
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
