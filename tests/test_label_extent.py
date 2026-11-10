#!/usr/bin/env python3
"""Label extents: tools/label_extent.py builds files ftwd accepts, from the right areas.

Runs every builder on small local stand-ins for its source (no network): GloCAB
region hulls with their no_area outlines cut out, the fields' hull, the AI4SF tiles
from UTM, raster footprints from Web Mercator and lon/lat, and WRI's chips read
from their label masks, not from the chips parquet's geometry. Every file written
must pass ftwd's own ``load_label_extent``. Also checks ``reads_extent`` (what
run_batch.py asks before a build), the sha256 manifest and that the builders match
``new_dataset.LABEL_EXTENT_SOURCES``.

Run: python3 tests/test_label_extent.py
"""
import json
import sys
import tempfile
from pathlib import Path

try:
    import duckdb
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    import rasterio
    import shapely
    from pyproj import Transformer
    from rasterio.transform import from_bounds
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import label_extent  # noqa: E402
import new_dataset  # noqa: E402
from ftw_dataset_tools.api.label_extent import load_label_extent  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_fields(path: Path, rows: list[dict]) -> None:
    columns = {k: [r[k] for r in rows] for k in rows[0] if k != "geometry"}
    columns["geometry"] = [shapely.to_wkb(r["geometry"]) for r in rows]
    geo = {"version": "1.1.0", "primary_column": "geometry",
           "columns": {"geometry": {"encoding": "WKB", "geometry_types": ["Polygon"]}}}
    pq.write_table(pa.table(columns).replace_schema_metadata({b"geo": json.dumps(geo).encode()}), path)


def write_raster(path: Path, crs: str, bounds: tuple[float, float, float, float]) -> None:
    with rasterio.open(path, "w", driver="GTiff", width=8, height=8, count=1, dtype="uint8",
                       crs=crs, transform=from_bounds(*bounds, 8, 8)) as dst:
        dst.write(np.zeros((1, 8, 8), dtype="uint8"))


def read_extent(path: Path) -> dict[str, shapely.Geometry]:
    con = duckdb.connect()
    con.execute("LOAD spatial")
    rows = con.execute(f"SELECT extent_id, ST_AsWKB(geometry) FROM read_parquet('{path}')").fetchall()
    return {i: shapely.from_wkb(bytes(g)) for i, g in rows}


def build(row: dict, builder, out: Path) -> dict[str, shapely.Geometry]:
    con = label_extent._connect()
    count = label_extent.write_extent(con, builder(con, row), out)
    con.close()
    check(count > 0, f"{row['dataset_id']}: an extent was written")
    try:
        load_label_extent(out)
    except Exception as err:  # noqa: BLE001 - any refusal is the failure being tested
        errors.append(f"{row['dataset_id']}: ftwd refuses the extent: {err}")
    return read_extent(out)


check(set(label_extent.BUILDERS) == set(new_dataset.LABEL_EXTENT_SOURCES),
      "every LABEL_EXTENT_SOURCES collection has a builder, and no other")

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    fields = tmp / "fields.parquet"
    label_extent.source_urls = lambda row: {"parquet": str(fields)}

    # --- GloCAB: one hull per region, no_area outlines cut out --------------
    write_fields(fields, [
        {"region": "A", "no_area": False, "geometry": shapely.box(0, 0, 0.01, 0.01)},
        {"region": "A", "no_area": False, "geometry": shapely.box(0.09, 0.09, 0.1, 0.1)},
        {"region": "A", "no_area": True, "geometry": shapely.box(0.04, 0.04, 0.05, 0.05)},
        {"region": "B", "no_area": False, "geometry": shapely.box(1, 1, 1.01, 1.01)},
        {"region": "B", "no_area": False, "geometry": shapely.box(1.02, 1, 1.03, 1.01)},
    ])
    glocab = {"dataset_id": "glocab_2020", "harmonized_id": "glocab", "year": "2020"}
    regions = build(glocab, label_extent.glocab_regions, tmp / "glocab.parquet")
    check(set(regions) == {"A", "B"}, f"one extent per region: {sorted(regions)}")
    a = regions.get("A", shapely.Polygon())
    check(a.contains(shapely.Point(0.07, 0.07)), "a region's hull covers the gaps between its fields")
    check(not a.contains(shapely.Point(0.045, 0.045)), "a no_area outline is a hole (unknown)")
    check(not a.contains(shapely.Point(0.02, 0.07)), "the hull is convex, not the bounding box")
    check(not regions.get("B", a).intersects(shapely.Point(0.5, 0.5)), "regions stay apart")

    # --- a source in metres is refused, not written as lon/lat ---------------
    write_fields(fields, [{"region": "A", "no_area": False,
                           "geometry": shapely.box(480000, 1198000, 481000, 1199000)}])
    try:
        build({"dataset_id": "br_ba_lem_2020", "harmonized_id": "br_ba_lem", "year": "2020"},
              label_extent.fields_hull, tmp / "metres.parquet")
        errors.append("a hull in metres was written as a lon/lat extent")
    except SystemExit as stop:
        check("not lon/lat" in str(stop), f"metres refused: {stop}")
    check(not (tmp / "metres.parquet").exists(), "nothing written for a refused extent")
    write_fields(fields, [
        {"region": "A", "no_area": False, "geometry": shapely.box(0, 0, 0.01, 0.01)},
        {"region": "A", "no_area": False, "geometry": shapely.box(0.09, 0.09, 0.1, 0.1)},
        {"region": "A", "no_area": True, "geometry": shapely.box(0.04, 0.04, 0.05, 0.05)},
    ])

    # --- the fields' hull ---------------------------------------------------
    hull = build({"dataset_id": "br_ba_lem_2020", "harmonized_id": "br_ba_lem", "year": "2020"},
                 label_extent.fields_hull, tmp / "lem.parquet")
    check(list(hull) == ["br_ba_lem"], f"one hull: {list(hull)}")
    check(hull["br_ba_lem"].contains(shapely.Point(0.045, 0.045)), "the plain hull has no holes")

    # --- AI4SF: the tiles, from UTM 48N to lon/lat --------------------------
    gpkg = tmp / "sources" / "ai4sf" / "tiles_asia.gpkg"
    gpkg.parent.mkdir(parents=True)
    label_extent.SOURCES = tmp / "sources"
    con = duckdb.connect()
    con.execute("LOAD spatial")
    con.execute(f"""COPY (SELECT 3 AS id, 'cambodia' AS country, 'train' AS split,
                         ST_MakeEnvelope(479571, 1198172, 484575, 1203168) AS geom)
                    TO '{gpkg}' (FORMAT GDAL, DRIVER 'GPKG', SRS 'EPSG:32648')""")
    con.close()
    tiles = build({"dataset_id": "ai4sf_ml_2021", "harmonized_id": "ai4sf_ml", "year": "2021"},
                  label_extent.ai4sf_tiles, tmp / "ai4sf.parquet")
    to_wgs84 = Transformer.from_crs("EPSG:32648", "EPSG:4326", always_xy=True)
    lon, lat = to_wgs84.transform(482073, 1200670)
    check(list(tiles) == ["cambodia_03"], f"tile ids are <country>_<id>: {list(tiles)}")
    check(tiles.get("cambodia_03", shapely.Polygon()).contains(shapely.Point(lon, lat)),
          "the tile lands where UTM 48N puts it, in lon/lat")

    # --- raster footprints: projected outlines are transformed point by point
    merc = tmp / "merc.tif"
    write_raster(merc, "EPSG:3857", (3374000, -170000, 3375200, -168800))
    fp = label_extent.raster_footprint(str(merc))
    lon0, lat0 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform(3374000, -170000)
    check(abs(fp.bounds[0] - lon0) < 1e-9 and abs(fp.bounds[1] - lat0) < 1e-9,
          f"Web Mercator corner transformed: {fp.bounds[:2]} vs {(lon0, lat0)}")
    lonlat = tmp / "lonlat.tif"
    write_raster(lonlat, "EPSG:4326", (-61.0, -9.0, -60.98, -8.98))
    check(label_extent.raster_footprint(str(lonlat)).symmetric_difference(
              shapely.box(-61.0, -9.0, -60.98, -8.98)).area < 1e-12,
          "a lon/lat raster's footprint is its bounds")

    # --- Trazo: chips from their label masks, not the chips parquet geometry --
    trazo = tmp / "trazo"
    for region, aoi, bounds in [("acre", "tile_1", (-73.19, -7.44, -73.17, -7.42)),
                                ("acre", "tile_2", (-73.10, -7.44, -73.08, -7.42)),
                                ("pampas", "tile_9", (-56.0, -33.0, -55.98, -32.98))]:
        masks = trazo / region / "label_masks" / "semantic_3class"
        masks.mkdir(parents=True, exist_ok=True)
        write_raster(masks / f"{aoi}.tif", "EPSG:4326", bounds)
    for region, aois in [("acre", ["tile_1", "tile_2"]), ("pampas", ["tile_9"])]:
        # The geometry stands in for WRI's: a field inside the chip, not the chip.
        write_fields(trazo / region / f"chips_{region}.parquet", [
            {"aoi_id": a, "n_fields": 1, "geometry": shapely.box(-73.185, -7.435, -73.184, -7.434)}
            for a in aois])
    label_extent.TRAZO = str(trazo)
    label_extent.TRAZO_REGIONS = {"acre": 2020, "pampas": 2021}
    chips = build({"dataset_id": "wri_trazo_2020", "harmonized_id": "wri_trazo", "year": "2020"},
                  label_extent.trazo_chips, tmp / "trazo.parquet")
    check(sorted(chips) == ["acre/tile_1", "acre/tile_2"],
          f"only the year's regions (acre 2020, not pampas 2021): {sorted(chips)}")
    check(abs(chips.get("acre/tile_1", shapely.Polygon()).area - 0.02 * 0.02) < 1e-12,
          "a chip's extent is its label mask's footprint, not the fields in the parquet")

    # --- reads_extent: only a recipe that reads this script's extent file -----
    label_extent.ROOT = tmp
    (tmp / "datasets").mkdir()
    recipe = tmp / "datasets" / "rw_rwanda_ml_2021.yaml"
    check(not label_extent.reads_extent("rw_rwanda_ml_2021"), "no recipe, nothing to build")
    recipe.write_text("stages:\n  masks:\n    presence_only: false\n")
    check(not label_extent.reads_extent("rw_rwanda_ml_2021"), "a recipe without label_extent")
    recipe.write_text("stages:\n  masks:\n    label_extent: "
                      f"{new_dataset.label_extent_ref('rw_rwanda_ml_2021')}\n")
    check(label_extent.reads_extent("rw_rwanda_ml_2021"), "a recipe reading the extent file")
    recipe.write_text("stages:\n  masks:\n    label_extent: elsewhere.parquet\n")
    check(not label_extent.reads_extent("rw_rwanda_ml_2021"), "someone else's extent file")

    # --- build(): the sha256 manifest keeps a rebuilt extent byte-identical ----
    box = {"x": 1.0}
    label_extent.BUILDERS["fake"] = lambda con, row: (
        f"SELECT 'a' AS extent_id, ST_MakeEnvelope(0, 0, {box['x']}, 1) AS geometry")
    label_extent.tracking.row = lambda d, rows=None: {"dataset_id": d, "harmonized_id": "fake",
                                                      "year": "2021"}
    manifest = tmp / label_extent.SHA_MANIFEST
    out = label_extent.build("fake_2021")
    first = label_extent._sha256(out)
    check(label_extent.recorded().get("fake_2021") == first, "a new extent's sha256 is recorded")
    check(manifest.read_text() == f"{first}  work/extents/fake_2021.parquet\n",
          f"the manifest reads like sha256sum output: {manifest.read_text()!r}")
    label_extent.build("fake_2021", force=True)
    check(label_extent._sha256(out) == first, "a rebuild from the same source is byte-identical")

    def refused(call) -> str:
        try:
            call()
        except SystemExit as stop:
            return str(stop)
        return ""

    box["x"] = 2.0  # the source changed
    message = refused(lambda: label_extent.build("fake_2021", force=True))
    check("records" in message and "--accept" in message, f"a different rebuild is refused: {message}")
    check(label_extent._sha256(out) == first, "the refused rebuild leaves the recorded file in place")
    check(not list(out.parent.glob("*.new*")), "and leaves no half-written file behind")
    check(label_extent.recorded()["fake_2021"] == first, "and the manifest unchanged")
    label_extent.build("fake_2021", force=True, accept=True)
    second = label_extent._sha256(out)
    check(second != first and label_extent.recorded()["fake_2021"] == second,
          "--accept records the new file")
    out.write_bytes(b"not the recorded file")
    message = refused(lambda: label_extent.build("fake_2021"))
    check("existing" in message, f"an existing file that differs is refused: {message}")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: label extents build where the labels are complete, and ftwd accepts them")
