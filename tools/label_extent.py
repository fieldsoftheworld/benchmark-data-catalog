#!/usr/bin/env python3
"""Build a dataset's label extent: the area inside which its labels are complete.

    uv run python tools/label_extent.py glocab_2020           # writes work/extents/glocab_2020.parquet
    uv run python tools/label_extent.py glocab_2020 --force   # rebuild an existing file
    uv run python tools/label_extent.py --all                 # every 'include' row that has one

Some research sets label every field, but only inside their own sample areas:
tiles, chips or mapped regions. FTW's chips sit on their own grid and straddle
those areas. ftwd's ``stages.masks.label_extent`` takes a polygon file of where
the labels are complete: inside it an unlabelled pixel is background (0),
outside it unknown (3), and chips wholly outside it are dropped.

The files are derived inputs like ``work/es_2025.parquet``: gitignored and
rebuilt from public sources by this script, in EPSG:4326 as ftwd requires.
``run_batch.py`` runs this before ftwd reads the recipe (building a missing file,
checking an existing one); run it yourself before a plain ``tools/build.py``. Each
file is checked with ftwd's own ``load_label_extent`` after it is written, and its
sha256 against the committed ``datasets/extents.sha256``: ftwd ties the chips to
the extent's sha256, so a rebuild must reproduce the recorded file exactly
(``--accept`` records a deliberate change).

The extent per harmonized collection (``BUILDERS``; the keys must match
``new_dataset.LABEL_EXTENT_SOURCES``):

- ``glocab``: per region mapped that year, the convex hull of its fields, minus
  the ``no_area`` outlines. Those outlines were drawn around several fields too
  small to digitise one by one; the class filter drops them, so without the hole
  their fields would read as background instead of unknown.
- ``ai4sf_ml``: the 62 AI4SmallFarms tiles of about 5x5 km (``tiles_asia.gpkg``
  from DANS, the file the converter takes the split from), from UTM 48N.
- ``rw_rwanda_ml``: the NASA Harvest competition's 57 train and 13 test tiles,
  read from the image headers. The harmonized set holds both splits.
- ``wri_trazo``: WRI's 256x256 Sentinel-2 chips (``chips_<region>.parquet``) of
  every region annotated that year, empty chips included.
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tracking  # noqa: E402
from common import ROOT  # noqa: E402
from new_dataset import LABEL_EXTENT_SOURCES, label_extent_file, source_urls  # noqa: E402

AI4SF_TILES = "https://phys-techsciences.datastations.nl/api/access/datafile/100418?gbrecs=true"
AI4SF_CRS = "EPSG:32648"
RWANDA_TILE = (
    "https://data.source.coop/nasa/rwanda-field-boundary-competition/source/{split}/2021_03/"
    "{index:02d}_B01.tif"
)
RWANDA_TILES = {"train": 57, "test": 13}
TRAZO = "https://data.source.coop/wri-data-lab/trazoannotations"
# The year each Trazo region was annotated, from fiboa-cli's wri_trazo converter
# (REGIONS there, which reads it from the source file names).
TRAZO_REGIONS = {
    "acre": 2020, "altoparana": 2020, "araucaria": 2023, "caatinga": 2021, "cerrado": 2021,
    "chaco": 2020, "chiquitania": 2020, "humidchaco": 2022, "lowmonte": 2023, "maparaguay": 2024,
    "matogrosso": 2020, "matogrosso_brazil_confidences": 2020, "matogrosso_brazil_lcdi": 2020,
    "matogrosso_brazil_lcdib": 2020, "matogrosso_brazil_lowconfidences": 2020, "pampas": 2021,
    "pantanal": 2023, "para": 2020, "peruvianamazon": 2022, "rondonia": 2022,
    "testchiquitania": 2020, "testmatogrosso": 2020, "testsoy": 2020, "tocantins": 2024,
    "uruguayansavannah": 2020,
}
SOURCES = ROOT / "work" / "extents" / "sources"
# The committed sha256 of every extent file; see build().
SHA_MANIFEST = "datasets/extents.sha256"


def _connect():
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs")
    con.execute("SET enable_progress_bar = false")
    return con


def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _download(url: str, path: Path, attempts: int = 4) -> Path:
    """``url`` saved at ``path``, downloaded once. DANS answers 500 now and then."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "benchmark-data-catalog"})
    tmp = path.with_suffix(path.suffix + ".part")
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=120) as resp:
                tmp.write_bytes(resp.read())
            break
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(30 * (attempt + 1))
    tmp.replace(path)
    return path


def glocab_regions(con, row: dict[str, str]) -> str:
    fields = _sql_str(source_urls(row)["parquet"])
    return f"""
        WITH f AS (SELECT region, geometry, no_area::VARCHAR = 'true' AS no_area
                   FROM read_parquet({fields})),
        hulls AS (SELECT region, ST_ConvexHull(ST_Collect(list(geometry))) AS hull
                  FROM f GROUP BY region),
        holes AS (SELECT region, ST_Union_Agg(ST_MakeValid(geometry)) AS outline
                  FROM f WHERE no_area GROUP BY region)
        SELECT h.region AS extent_id,
               CASE WHEN o.outline IS NULL THEN h.hull
                    ELSE ST_CollectionExtract(ST_Difference(h.hull, o.outline), 3) END AS geometry
        FROM hulls h LEFT JOIN holes o USING (region)"""


def ai4sf_tiles(con, row: dict[str, str]) -> str:
    path = _download(AI4SF_TILES, SOURCES / "ai4sf" / "tiles_asia.gpkg")
    return f"""
        SELECT country || '_' || lpad(id::VARCHAR, 2, '0') AS extent_id,
               ST_Transform(geom::GEOMETRY, '{AI4SF_CRS}', 'EPSG:4326', always_xy := true)
                   AS geometry
        FROM ST_Read({_sql_str(str(path))})"""


def raster_footprint(url: str):
    """A raster's footprint in EPSG:4326: its bounds, densified, then transformed.

    The chips come in lon/lat, Web Mercator and Albers; a bounding box of the
    transformed corners would overstate a projected chip, so the outline is
    transformed point by point.
    """
    import numpy as np
    import rasterio
    import shapely
    from pyproj import Transformer

    # Without this GDAL lists the whole folder (hundreds of TIFs) before every open.
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"), rasterio.open(url) as src:
        crs, bounds = src.crs, src.bounds
    outline = shapely.segmentize(shapely.box(*bounds), (bounds.right - bounds.left) / 16)
    if crs.to_epsg() == 4326:
        return outline
    to_wgs84 = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    return shapely.transform(outline, lambda xy: np.column_stack(to_wgs84.transform(xy[:, 0], xy[:, 1])))


def _footprints_query(con, table: str, sources: dict[str, str]) -> str:
    """A query over ``{extent_id: raster url}``'s footprints, read 16 at a time."""
    from concurrent.futures import ThreadPoolExecutor

    import rasterio.errors
    import shapely

    def footprint(url: str):
        try:
            return raster_footprint(url)
        except rasterio.errors.RasterioIOError as err:
            if "404" not in str(err):
                raise
            return None

    with ThreadPoolExecutor(16) as pool:
        shapes = list(pool.map(footprint, sources.values()))
    rows = []
    for (extent_id, url), shape in zip(sources.items(), shapes, strict=True):
        if shape is None:
            # One WRI chip (maparaguay chip_41133_u16) is listed but has no masks.
            print(f"skip   {extent_id}: {url} does not exist; left out, so its area is unknown")
            continue
        rows.append((extent_id, shapely.to_wkb(shape)))
    con.execute(f"CREATE OR REPLACE TEMP TABLE {table} (extent_id VARCHAR, wkb BLOB)")
    con.executemany(f"INSERT INTO {table} VALUES (?, ?)", rows)
    return f"SELECT extent_id, ST_GeomFromWKB(wkb) AS geometry FROM {table}"


def rwanda_tiles(con, row: dict[str, str]) -> str:
    sources = {
        f"{split}_{index:02d}": RWANDA_TILE.format(split=split, index=index)
        for split, count in RWANDA_TILES.items()
        for index in range(count)
    }
    return _footprints_query(con, "rwanda_tiles", sources)


def trazo_chips(con, row: dict[str, str]) -> str:
    """WRI's chips of the year's regions, from their label masks' footprints.

    ``chips_<region>.parquet`` names the chips, but its geometry is the fields, not
    the chip; WRI's README gives the TIFs' extent as the annotated area.
    """
    year = int(row["year"])
    regions = sorted(r for r, y in TRAZO_REGIONS.items() if y == year)
    if not regions:
        sys.exit(f"{row['dataset_id']}: no Trazo region was annotated in {year}")
    files = ", ".join(_sql_str(f"{TRAZO}/{r}/chips_{r}.parquet") for r in regions)
    chips = con.execute(f"""
        SELECT DISTINCT regexp_extract(filename, '/([^/]+)/chips_[^/]+$', 1) AS region, aoi_id
        FROM read_parquet([{files}], filename = true) ORDER BY ALL""").fetchall()
    sources = {
        f"{region}/{aoi}": f"{TRAZO}/{region}/label_masks/semantic_3class/{aoi}.tif"
        for region, aoi in chips
    }
    return _footprints_query(con, "trazo_chips", sources)


BUILDERS: dict[str, Callable] = {
    "ai4sf_ml": ai4sf_tiles,
    "glocab": glocab_regions,
    "rw_rwanda_ml": rwanda_tiles,
    "wri_trazo": trazo_chips,
}


def extent_path(dataset_id: str) -> Path:
    return ROOT / label_extent_file(dataset_id)


def write_extent(con, query: str, out: Path) -> int:
    """Write ``query``'s (extent_id, geometry) rows as GeoParquet; the row count."""
    import geoparquet_io as gpio

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp.parquet")
    con.execute(f"""
        COPY (SELECT extent_id, ST_Force2D(geometry) AS geometry FROM ({query})
              WHERE geometry IS NOT NULL AND NOT ST_IsEmpty(geometry) ORDER BY extent_id)
        TO {_sql_str(str(tmp))} (FORMAT parquet, COMPRESSION zstd)""")
    # The file carries no CRS, so ftwd reads it as lon/lat: refuse anything else
    # (a hull of fields stored in metres would otherwise pass every later check).
    xmin, ymin, xmax, ymax = con.execute(
        f"SELECT min(ST_XMin(geometry)), min(ST_YMin(geometry)), max(ST_XMax(geometry)), "
        f"max(ST_YMax(geometry)) FROM read_parquet({_sql_str(str(tmp))})").fetchone()
    if xmin is not None and not (-180 <= xmin <= xmax <= 180 and -90 <= ymin <= ymax <= 90):
        tmp.unlink()
        sys.exit(f"{out.name}: coordinates ({xmin}, {ymin}, {xmax}, {ymax}) are not lon/lat; "
                 f"transform the source to EPSG:4326 in its builder")
    gpio.read(str(tmp)).add_bbox().write(str(out))
    tmp.unlink()
    return con.execute(f"SELECT count(*) FROM read_parquet({_sql_str(str(out))})").fetchone()[0]


def _sha256(path: Path) -> str:
    from ftw_dataset_tools.api.label_extent import extent_fingerprint

    return extent_fingerprint(path)


def recorded(manifest: Path | None = None) -> dict[str, str]:
    """``{dataset_id: sha256}`` from the committed ``datasets/extents.sha256``."""
    manifest = manifest or ROOT / SHA_MANIFEST
    if not manifest.exists():
        return {}
    out = {}
    for line in manifest.read_text().splitlines():
        if line.strip():
            sha, rel = line.split(maxsplit=1)
            out[Path(rel).stem] = sha
    return out


def record(dataset_id: str, sha: str, manifest: Path | None = None) -> None:
    """Write ``dataset_id``'s sha256 into the manifest, in ``sha256sum -c`` form."""
    manifest = manifest or ROOT / SHA_MANIFEST
    shas = {**recorded(manifest), dataset_id: sha}
    manifest.write_text("".join(f"{s}  {label_extent_file(d)}\n" for d, s in sorted(shas.items())))


def _mismatch(dataset_id: str, expected: str, got: str, what: str) -> str:
    return (
        f"{dataset_id}: {what} has sha256 {got[:12]}, but {SHA_MANIFEST} records {expected[:12]}. "
        f"Chips built from the recorded file fail ftwd's stac stage against any other, so it is "
        f"not used. If the source or this script changed on purpose, rerun with --accept to "
        f"record the new file, commit {SHA_MANIFEST}, and rebuild the dataset from its chips."
    )


def build(dataset_id: str, *, force: bool = False, accept: bool = False) -> Path:
    """Write ``work/extents/<id>.parquet``, validate it with ftwd and check its sha256.

    The committed ``datasets/extents.sha256`` records each extent's sha256. ftwd
    stores it in the chips and refuses a later stage (``stac``, in the imagery pass)
    run against a different file, so a rebuilt extent (a fresh builder, a republished
    source, a WRI chip that went missing) must be byte-identical. An existing file is
    checked; a rebuilt one replaces it only when it matches, or with ``accept``. An
    extent with no recorded sha256 yet is recorded.
    """
    from ftw_dataset_tools.api.label_extent import load_label_extent

    row = tracking.row(dataset_id)
    builder = BUILDERS.get(row["harmonized_id"])
    if builder is None:
        sys.exit(f"{dataset_id}: {row['harmonized_id']} has no label extent (see BUILDERS)")
    out = extent_path(dataset_id)
    expected = recorded().get(dataset_id)
    if out.exists() and not force:
        got = _sha256(out)
        if expected is None:
            record(dataset_id, got)
        elif got != expected and not accept:
            sys.exit(_mismatch(dataset_id, expected, got, f"the existing {label_extent_file(dataset_id)}"))
        elif got != expected:
            record(dataset_id, got)
        return out
    new = out.with_name(f"{out.stem}.new.parquet")
    con = _connect()
    try:
        count = write_extent(con, builder(con, row), new)
    finally:
        con.close()
    if count == 0:
        new.unlink()
        sys.exit(f"{dataset_id}: the label extent came out empty")
    load_label_extent(new)
    got = _sha256(new)
    if expected is not None and got != expected and not accept:
        new.unlink()
        sys.exit(_mismatch(dataset_id, expected, got, "the rebuilt extent"))
    new.replace(out)
    if got != expected:
        record(dataset_id, got)
    return out


def reads_extent(dataset_id: str) -> bool:
    """True when the dataset's recipe reads this script's extent file."""
    import yaml

    recipe = ROOT / "datasets" / f"{dataset_id}.yaml"
    if not recipe.exists():
        return False
    masks = ((yaml.safe_load(recipe.read_text()) or {}).get("stages") or {}).get("masks") or {}
    ref = masks.get("label_extent")
    if not ref:
        return False
    return (recipe.parent / ref).resolve() == extent_path(dataset_id).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="*", help="region-year ids from tracking.csv")
    parser.add_argument("--all", action="store_true", help="every 'include' row with an extent")
    parser.add_argument("--force", action="store_true", help="rebuild existing files")
    parser.add_argument("--accept", action="store_true",
                        help=f"record a file whose sha256 differs from {SHA_MANIFEST}")
    args = parser.parse_args(argv)
    ids = list(args.dataset_ids)
    if args.all:
        ids += [r["dataset_id"] for r in tracking.load()
                if r["status"] == "include" and r["harmonized_id"] in LABEL_EXTENT_SOURCES]
    if not ids:
        parser.error("name dataset ids or pass --all")
    for dataset_id in dict.fromkeys(ids):
        existed = extent_path(dataset_id).exists() and not args.force
        path = build(dataset_id, force=args.force, accept=args.accept)
        print(f"{'ok   ' if existed else 'wrote'}  {path.relative_to(ROOT)}  {_sha256(path)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
