#!/usr/bin/env python3
"""tools/backfill.py: fetch selection, change detection, item updates and the docs input.

No network: the bucket is a stand-in client over a dict, and the dataset is a few
files on disk. The ftwd side (collection edits, docs) is tested in ftwd itself.

Run: python3 tests/test_backfill.py
"""
import hashlib
import importlib
import json
import sys
import tempfile
from pathlib import Path

try:
    import duckdb  # noqa: F401
    importlib.import_module("ftw_dataset_tools.api.backfill")
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import backfill  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# --- which published files the backfill reads ---------------------------------
top = {"ds_chips.parquet", "ds_fields.parquet"}
check(backfill.wanted("chips/33UXP/c_2024/c_2024.json", top), "chip item JSON is read")
check(backfill.wanted("chips/33UXP/c_2024/c_2024_q1_s2.json", top), "child item JSON is read")
check(backfill.wanted("chips/33UXP/catalog.json", top), "sub-catalog is read")
check(not backfill.wanted("chips/33UXP/c_2024/c_2024_q1_image_s2.tif", top), "rasters are not")
check(not backfill.wanted("chips/33UXP/README.md", top), "sub-catalog docs are not")
check(backfill.wanted("ds_chips.parquet", top), "the chips file is read")
check(not backfill.wanted("ds_boundary_lines.parquet", top), "boundary lines are not")
check(not backfill.wanted("fields.pmtiles", top), "tiles are not")
check(not backfill.wanted("styles/ds_chips.parquet", top), "only top-level files match by name")

# --- change detection against the listing -------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "a.json"
    path.write_text("{}")
    md5 = hashlib.md5(b"{}").hexdigest()
    check(backfill.is_current(path, backfill.Remote("k", 2, md5)), "same size and MD5: current")
    check(not backfill.is_current(path, backfill.Remote("k", 2, "0" * 32)), "other MD5: stale")
    check(not backfill.is_current(path, backfill.Remote("k", 3, md5)), "other size: stale")
    check(backfill.is_current(path, backfill.Remote("k", 2, "abc-4")),
          "multipart ETag: compared on size alone")
    check(not backfill.is_current(Path(tmp) / "missing", backfill.Remote("k", 2, md5)),
          "missing file: stale")

# --- fetch: only the stale files it reads, and the git collection ---------------


class FakeClient:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects
        self.downloaded: list[str] = []

    def get_paginator(self, _name):
        objects = self.objects

        class Paginator:
            def paginate(self, Bucket, Prefix):  # noqa: N803 - boto3's names
                yield {"Contents": [
                    {"Key": k, "Size": len(v), "ETag": f'"{hashlib.md5(v).hexdigest()}"'}
                    for k, v in sorted(objects.items()) if k.startswith(Prefix)
                ]}

        return Paginator()

    def download_file(self, _bucket, key, dest):
        self.downloaded.append(key)
        Path(dest).write_bytes(self.objects[key])

    def get_object(self, Bucket, Key):  # noqa: N803 - boto3's names
        import io

        self.downloaded.append(Key)
        return {"Body": io.BytesIO(self.objects[Key])}


with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    catalog, staging = base / "catalog", base / "staging"
    collection = {"id": "ds", "assets": {
        "chips": {"href": "./ds_chips.parquet"}, "fields": {"href": "./ds_fields.parquet"},
    }}
    (catalog / "g" / "ds").mkdir(parents=True)
    (catalog / "g" / "ds" / "collection.json").write_text(json.dumps(collection))
    pre = f"{backfill.READ_PREFIX}/g/ds/"
    objects = {
        pre + "ds_chips.parquet": b"chips",
        pre + "ds_fields.parquet": b"fields",
        pre + "ds_boundary_lines.parquet": b"lines",
        pre + "chips/S/c/c.json": b'{"type": "Feature"}',
        pre + "chips/S/c/c_image.tif": b"tif",
        f"{backfill.READ_PREFIX}/g/ds_other/ds_chips.parquet": b"other dataset",
        f"{backfill.READ_PREFIX}/ds/chips/S/c/c.json": b"the old flat copy",
        f"{backfill.READ_PREFIX}/ds/ds_chips.parquet": b"chips",
        f"{backfill.READ_PREFIX}/ds/ds_fields.parquet": b"fields",
    }
    (staging / "ds").mkdir(parents=True)
    (staging / "ds" / "ds_fields.parquet").write_bytes(b"fields")  # already as published
    client = FakeClient(objects)
    backfill._client = lambda: client
    fetched = backfill.fetch("ds", staging=staging, catalog=catalog)
    check(sorted(client.downloaded) == [pre + "chips/S/c/c.json", pre + "ds_chips.parquet"],
          f"fetch downloads the stale files it reads, got {client.downloaded}")
    check(fetched == 2, f"fetch reports two files, got {fetched}")
    check(json.loads((staging / "ds" / "collection.json").read_text()) == collection,
          "fetch takes collection.json from catalog/<source>/<id>/")
    client.downloaded.clear()
    (staging / "ds" / "chips/S/c/c.json").unlink()
    backfill.fetch("ds", staging=staging, catalog=catalog, read_flat=True)
    check(client.downloaded == [f"{backfill.READ_PREFIX}/ds/chips/S/c/c.json"],
          f"read_flat reads the old flat <id>/ folder, got {client.downloaded}")
    (staging / "ds" / "chips/S/c/c.json").unlink()
    backfill.fetch("ds", staging=staging, catalog=catalog)
    del objects[pre + "ds_fields.parquet"]
    try:
        backfill.fetch("ds", staging=staging, catalog=catalog)
        check(False, "a collection asset missing from the bucket stops the fetch")
    except SystemExit as stop:
        check("ds_fields.parquet" in str(stop), f"names the missing file, got {stop}")

# --- the collection the docs see -------------------------------------------------
published = {
    "assets": {"chips": {"href": "./c.parquet"}, "thumbnail": {"href": "./thumbnail.webp"}},
    "links": [{"rel": "via", "href": "https://source.coop/ftw/h/x", "type": "text/html"}],
    "ftw:config": {"config": {"source_via": "https://data.source.coop/ftw/h/x/collection.json"}},
}
staged = backfill.staged_collection(published)
check("thumbnail" not in staged["assets"], "the docs do not see the thumbnail")
check(staged["links"][0] == {"rel": "via", "type": "application/json",
                             "href": "https://data.source.coop/ftw/h/x/collection.json"},
      f"via points back at the harmonized JSON, got {staged['links'][0]}")
check("thumbnail" in published["assets"] and published["links"][0]["type"] == "text/html",
      "the published collection is left as it was")
no_via = backfill.staged_collection({"links": [{"rel": "via", "href": "h"}], "assets": {}})
check(no_via["links"] == [{"rel": "via", "href": "h"}], "no source_via: via left alone")

# --- admin names onto the chip items ------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "ds"
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    chips = root / "ds_chips.parquet"
    root.mkdir()
    con.execute(f"""COPY (SELECT * FROM (VALUES
        ('ftw-33UXP0410', 'AUT', 'Austria', 'Wien', NULL, ST_GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))')),
        ('ftw-33UXP0411', NULL, NULL, NULL, NULL, ST_GeomFromText('POLYGON((1 0,2 0,2 1,1 1,1 0))'))
        ) t(id, admin0_iso3, admin0_name, admin1_name, admin2_name, geometry))
        TO '{chips}' (FORMAT parquet)""")

    def item(item_id: str, props: dict) -> Path:
        path = root / "chips" / "33UXP" / item_id / f"{item_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"type": "Feature", "id": item_id, "properties": props}))
        return path

    a = item("ftw-33UXP0410_2024", {"ftw:split": "train"})
    b = item("ftw-33UXP0411_2024", {"ftw:admin0_name": "stale"})
    child = root / "chips" / "33UXP" / "ftw-33UXP0410_2024" / "ftw-33UXP0410_2024_q1_s2.json"
    child.write_text(json.dumps({"type": "Feature", "id": "q1", "properties": {}}))
    changed, seen = backfill.update_items(root, chips, 2024)
    check((changed, seen) == (2, 2), f"both chip items change, got {(changed, seen)}")
    props = json.loads(a.read_text())["properties"]
    check(props == {"ftw:split": "train", "ftw:admin0_iso3": "AUT", "ftw:admin0_name": "Austria",
                    "ftw:admin1_name": "Wien"}, f"names set, empty ones left out, got {props}")
    check(json.loads(b.read_text())["properties"] == {}, "a chip in no unit loses stale names")
    check(json.loads(child.read_text())["properties"] == {}, "child items are left alone")
    check(backfill.update_items(root, chips, 2024) == (0, 2), "a second run changes nothing")
    b.unlink()
    try:
        backfill.update_items(root, chips, 2024)
        check(False, "a chip without its item stops the run")
    except SystemExit as stop:
        check("1 chip items for 2 chips" in str(stop), f"says how many are missing, got {stop}")

# --- a staging tree with unpublished data is refused --------------------------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "staging" / "ds"
    catalog_dir = Path(tmp) / "catalog" / "ds"
    (catalog_dir / "chips" / "S").mkdir(parents=True)
    (catalog_dir / "chips" / "S" / "catalog.json").write_text("{}")
    def put(rel: str, body: bytes = b"x") -> None:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(body)
    listing = {r: backfill.Remote(r, 1, hashlib.md5(b"x").hexdigest()) for r in (
        "ds_chips.parquet", "chips/S/c/c.json", "chips/S/c/c_mask.tif", "items.parquet")}
    top = {"ds_chips.parquet"}
    check_ok = lambda: backfill.check_staging(root, listing, catalog_dir=catalog_dir, top_level=top)  # noqa: E731
    check_ok()  # nothing there yet
    put("ds_chips.parquet", b"rewritten with admin columns")  # read, so refetched
    put("chips/S/c/c.json", b'{"edited": true}')
    put("chips/S/c/c_mask.tif")
    put("chips/S/catalog.json", b"git owns it")
    put("items.parquet", b"the backfill writes it")
    put("ds_field_embeddings.parquet", b"the backfill writes it")
    put("ds_field_embeddings.parquet.partial/part-000000.parquet")
    put("ftwd-config.resolved.yaml")
    put("chips/S/c/c_overlay.md")
    check_ok()
    for rel, body, why in (("chips/S/c/c_mask.tif", b"rebuilt mask", "a raster that differs"),
                           ("chips/S/d/d.json", b"{}", "an item the bucket lacks"),
                           ("chips/S/d/d_mask.tif", b"x", "a raster the bucket lacks")):
        saved = (root / rel).read_bytes() if (root / rel).exists() else None
        put(rel, body)
        try:
            check_ok()
            check(False, f"{why} is refused")
        except SystemExit as stop:
            check(rel in str(stop) and "move staging/ds aside" in str(stop), f"{why}: {stop}")
        if saved is None:
            (root / rel).unlink()
        else:
            put(rel, saved)

# --- the fetch keeps a published embeddings file ----------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    (base / "catalog" / "g" / "ds").mkdir(parents=True)
    (base / "catalog" / "g" / "ds" / "collection.json").write_text(json.dumps({"id": "ds", "assets": {
        "chips": {"href": "./c.parquet"}, "fields": {"href": "./f.parquet"},
        "field_embeddings": {"href": "./ds_field_embeddings.parquet"}}}))
    pre = f"{backfill.READ_PREFIX}/g/ds/"
    client = FakeClient({pre + "c.parquet": b"c", pre + "f.parquet": b"f",
                         pre + "ds_field_embeddings.parquet": b"e"})
    backfill._client = lambda: client
    backfill.fetch("ds", staging=base / "staging", catalog=base / "catalog")
    check(pre + "ds_field_embeddings.parquet" in client.downloaded,
          "a published embeddings file is fetched, so a rerun can keep it")
    del client.objects[pre + "ds_field_embeddings.parquet"]
    (base / "staging" / "ds" / "ds_field_embeddings.parquet").unlink()
    backfill.fetch("ds", staging=base / "staging", catalog=base / "catalog")  # not required

# --- the host provider is left to catalogize -----------------------------------------------
host = {"name": "Source Cooperative", "roles": ["host"], "url": "https://source.coop"}
doc = {"assets": {}, "links": [], "providers": [
    {"name": "NASA", "roles": ["producer"]}, dict(host)]}
check(backfill.staged_collection(doc, host)["providers"] == [{"name": "NASA", "roles": ["producer"]}],
      "the docs do not see the host provider")
check(len(doc["providers"]) == 2, "the published providers are left as they were")

# --- the recipe keeps both steps on ----------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    recipe = Path(tmp) / "ds.yaml"
    recipe.write_text("name: ds\nstages:\n  chips:\n    min_coverage: 0.01\n"
                      "    # keep\n    admin_names: false\n  splits:\n    random_seed: 42\n")
    check(backfill.enable_recipe_steps(recipe), "the recipe is edited")
    text = recipe.read_text()
    check(text == "name: ds\nstages:\n  chips:\n    min_coverage: 0.01\n    # keep\n"
                  "    admin_names: true\n    field_embeddings: true\n  splits:\n"
                  "    random_seed: 42\n", f"flags set inside chips, comments kept, got {text!r}")
    check(not backfill.enable_recipe_steps(recipe), "a second run leaves it alone")
    import yaml
    check(yaml.safe_load(text)["stages"]["chips"]["field_embeddings"] is True, "still valid YAML")
    recipe.write_text("name: ds\n")
    try:
        backfill.enable_recipe_steps(recipe)
        check(False, "a recipe without a chips block is refused")
    except SystemExit:
        pass

# --- where the crop names come from ---------------------------------------------
import tracking  # noqa: E402

_saved_row = tracking.row
tracking.row = lambda d, rows=None: {
    "pt_2025": {"harmonized_id": "pt", "year": "2025", "source_stem": ""},
    "ch_ag_2025": {"harmonized_id": "ch", "year": "2025", "source_stem": "ch_ag"},
}[d]
hstage = Path("/h/staging")
check(backfill.harmonized_edition("pt_2025", hstage)
      == hstage / "pt" / "year=2025" / "pt-2025.parquet", "the edition is <id>/year=<y>/<id>-<y>")
check(backfill.harmonized_edition("ch_ag_2025", hstage)
      == hstage / "ch" / "year=2025" / "ch_ag-2025.parquet", "a sub-region uses its source stem")
tracking.row = _saved_row

# --- how the crop names are joined -----------------------------------------------
import types  # noqa: E402

calls = []
fake = types.SimpleNamespace(add_crop_names=lambda path, source, by="id": calls.append((
    path.name, by)) or types.SimpleNamespace(columns=("crop:name",), named=1, rows=1, changed=True))
_saved_module = sys.modules.get("ftw_dataset_tools.api.crop_names")
sys.modules["ftw_dataset_tools.api.crop_names"] = fake
import ftw_dataset_tools.api as _api  # noqa: E402

_saved_attr = getattr(_api, "crop_names", None)
_api.crop_names = fake
try:
    doc = {"assets": {"fields": {"href": "./f.parquet"}, "fields_filtered": {"href": "./ff.parquet"}}}
    files = backfill.field_files(doc, Path("/d"))
    check(files == {"fields": Path("/d/f.parquet"), "fields_filtered": Path("/d/ff.parquet")},
          f"both field files are staged by asset key: {files}")
    check(backfill.field_files({"assets": {"fields": {"href": "f.parquet"}}}, Path("/d"))
          == {"fields": Path("/d/f.parquet")}, "a dataset without fields_filtered has one file")
    backfill.add_crop_names("fr_2024", files, Path("/s.parquet"), "code")
    check(calls == [("f.parquet", "code"), ("ff.parquet", "code")],
          f"both field files are joined by the given key: {calls}")
    calls.clear()
    backfill.add_crop_names("fr_2022", {"fields": Path("/d/f.parquet")}, Path("/s.parquet"))
    check(calls == [("f.parquet", "id")], "the join is by id unless told otherwise")
finally:
    if _saved_module is None:
        sys.modules.pop("ftw_dataset_tools.api.crop_names", None)
    else:
        sys.modules["ftw_dataset_tools.api.crop_names"] = _saved_module
    if _saved_attr is None:
        delattr(_api, "crop_names")
    else:
        _api.crop_names = _saved_attr

# --- which flag combinations are refused, and refusals skip one dataset -------------
import contextlib  # noqa: E402
import io  # noqa: E402

for argv, why in (
    (["fr_2024", "--crop-names-by", "code"], "--crop-names-by without --crop-names-from"),
    (["fr_2024", "fr_2022", "--crop-names-from", "/h", "--crop-names-by", "code"],
     "--crop-names-by code with two datasets"),
):
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            backfill.main(argv)
        check(False, f"{why} is refused")
    except SystemExit as stop:
        check(stop.code == 2, f"{why} is a usage error")

import build  # noqa: E402
import common  # noqa: E402
from ftw_dataset_tools.api.crop_names import CropNameError  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    published = Path(tmp)
    (published / "collection.json").write_text("{}")
    ran = []

    def _fake_backfill(dataset_id, **kwargs):
        ran.append((dataset_id, kwargs["crop_names_by"]))
        if dataset_id == "bad":
            raise CropNameError(Path("/f"), "3 field(s) not in the edition")

    saved = (backfill.dataset_dir, backfill.backfill_dataset, backfill.enable_recipe_steps,
             build._check_recipe, common.load_manifest)
    backfill.dataset_dir = lambda dataset_id: published
    backfill.backfill_dataset = _fake_backfill
    backfill.enable_recipe_steps = lambda recipe: ran.append(("recipe", recipe.stem)) and False
    build._check_recipe = lambda dataset_id: None
    common.load_manifest = lambda: {}
    try:
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = backfill.main(["bad", "good", "--allow-uncommitted-ftwd"])
        check(code == 1, "a run with a refused dataset exits 1")
        check(ran == [("bad", "id"), ("good", "id"), ("recipe", "good")],
              f"the refused dataset is skipped and the next one still runs: {ran}")
        check("bad: crop names refused" in err.getvalue(), "the refusal is reported briefly")
    finally:
        (backfill.dataset_dir, backfill.backfill_dataset, backfill.enable_recipe_steps,
         build._check_recipe, common.load_manifest) = saved

if errors:
    for message in errors:
        print(f"FAIL   {message}")
    raise SystemExit(1)
print("OK: backfill fetches, detects changes and updates items as intended")
