#!/usr/bin/env python3
"""Merge Spain's national 2025 declarations with the regional SIGPAC 2025 parcels.

    uv run python tools/merge_es_2025.py <work_dir>            # download, merge, write
    uv run python tools/merge_es_2025.py <work_dir> --stats    # print the overlap numbers only

The national edition (``es``, farmers' declarations, 385 crop codes) covers all of
Spain but only declared land. Five regional editions (``es_an``, ``es_cb``,
``es_cl``, ``es_ga``, ``es_pv``: SIGPAC land use, ~20 classes) cover every parcel
in their regions. The union keeps every national parcel and adds a regional parcel
only where the national edition has nothing: less than ``OVERLAP_MAX`` of the
regional parcel's area overlaps any national parcel, whatever its class. Whole
parcels are added or skipped, never cut, so no slivers appear along shared edges.

Columns of the output (``<work_dir>/es_2025_merged.parquet``):

- ``id``: the source id, prefixed with the source (``es:...``, ``es_ga:...``).
- ``ftw:source``: ``es`` or the regional collection id.
- ``crop:code``, ``hcat:code``, ``hcat:name_en``: national crop type; NULL on
  regional parcels.
- ``landuse:code``, ``landuse:name_en``: SIGPAC land use. On regional parcels, their
  own; on national parcels inside the five regions, the land use of the regional
  parcel they overlap most; NULL elsewhere.
- ``admin_province_code``, ``metrics:area``, ``irrigation_system`` where the source has
  them.
- ``ftw:class``: the value the class filter reads (``es_merged_filter.yaml`` in ftwd).
  ``es:<crop code>`` for national parcels, except permanent and young pasture
  (62, 63) in the Atlantic provinces, which is ``es:<code>:atlantic`` (field there,
  background elsewhere; see docs/grassland-review.md in ftwd). ``<region>:<land use>``
  for regional parcels.

Geometry is written in lon/lat (the national edition's ETRS89, within a metre of
WGS 84) with a ``bbox`` covering column.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import duckdb

HARMONIZED = "https://data.source.coop/ftw/harmonized-field-data"
YEAR = 2025
NATIONAL = "es"
# Regional collection -> the ftwd class filter its land-use codes follow.
REGIONS = {
    "es_an": "es_uso_filter.yaml",
    "es_cb": "es_uso_north_filter.yaml",
    "es_cl": "es_uso_filter.yaml",
    "es_ga": "es_uso_north_filter.yaml",
    "es_pv": "es_uso_north_filter.yaml",
}
# Galicia, Asturias, Cantabria, País Vasco: pasture parcels are hedge-bounded meadows.
ATLANTIC = ("15", "27", "32", "36", "33", "39", "01", "20", "48")
PASTURE = ("62", "63")
OVERLAP_MAX = 0.10
# Metric CRS for areas (UTM 30N covers mainland Spain; ratios only).
METRIC = "EPSG:25830"


def source_url(hid: str) -> str:
    return f"{HARMONIZED}/{hid}/year={YEAR}/{hid}-{YEAR}.parquet"


def download(url: str, dest: Path) -> Path:
    """Fetch ``url`` to ``dest`` once; a finished download is reused."""
    if dest.exists():
        return dest
    tmp = dest.with_suffix(".part")
    request = urllib.request.Request(url, headers={"User-Agent": "benchmark-data-catalog"})
    with urllib.request.urlopen(request, timeout=60) as resp, tmp.open("wb") as out:
        while chunk := resp.read(1 << 24):
            out.write(chunk)
    tmp.rename(dest)
    return dest


def geo_crs(con: duckdb.DuckDBPyConnection, path: Path) -> str:
    """The file's declared CRS as ``AUTH:CODE``; absent means lon/lat."""
    row = con.execute(
        "SELECT value FROM parquet_kv_metadata(?) WHERE key = 'geo'", [str(path)]
    ).fetchone()
    if not row:
        return "OGC:CRS84"
    column = json.loads(row[0])["columns"]["geometry"]
    crs = column.get("crs")
    if crs is None:
        return "OGC:CRS84"
    ident = crs.get("id", {}) if isinstance(crs, dict) else {}
    if not ident:
        raise SystemExit(f"{path}: CRS without an id; add it to merge_es_2025.geo_crs")
    return f"{ident['authority']}:{ident['code']}"


def connect(threads: int | None = None) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.install_extension("spatial")
    con.load_extension("spatial")
    if threads:
        con.execute(f"SET threads = {threads}")
    con.execute("SET preserve_insertion_order = false")
    return con


def _metric(geom: str, crs: str) -> str:
    """SQL for ``geom`` (valid) in the metric CRS."""
    valid = f"ST_MakeValid({geom})"
    if crs == METRIC:
        return valid
    src = "EPSG:4326" if crs in ("OGC:CRS84", "EPSG:4326", "EPSG:4258") else crs
    return f"ST_Transform({valid}, '{src}', '{METRIC}', always_xy := true)"


def _lonlat(geom: str, crs: str) -> str:
    """SQL for ``geom`` in lon/lat."""
    if crs in ("OGC:CRS84", "EPSG:4326", "EPSG:4258"):
        return geom
    return f"ST_Transform({geom}, '{crs}', 'EPSG:4326', always_xy := true)"


def load_national(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    crs = geo_crs(con, path)
    atlantic = ", ".join(f"'{p}'" for p in ATLANTIC)
    pasture = ", ".join(f"'{c}'" for c in PASTURE)
    con.execute(
        f"""CREATE OR REPLACE TABLE nat AS
            SELECT 'es:' || id AS id, CAST("crop:code" AS VARCHAR) AS crop_code,
                   "hcat:code" AS hcat_code, "hcat:name_en" AS hcat_name_en,
                   admin_province_code, "metrics:area" AS area, irrigation_system,
                   CASE WHEN CAST("crop:code" AS VARCHAR) IN ({pasture})
                             AND admin_province_code IN ({atlantic})
                        THEN 'es:' || CAST("crop:code" AS VARCHAR) || ':atlantic'
                        ELSE 'es:' || CAST("crop:code" AS VARCHAR) END AS ftw_class,
                   {_lonlat("geometry", crs)} AS geom,
                   {_metric("geometry", crs)} AS g
            FROM read_parquet('{path}') WHERE geometry IS NOT NULL"""
    )


def load_region(con: duckdb.DuckDBPyConnection, hid: str, path: Path) -> None:
    crs = geo_crs(con, path)
    cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall()}
    name = '"crop:name_en"' if "crop:name_en" in cols else "NULL"
    prov = "admin_province_code" if "admin_province_code" in cols else "NULL"
    area = '"metrics:area"' if "metrics:area" in cols else "NULL"
    con.execute(
        f"""CREATE OR REPLACE TABLE reg AS
            SELECT '{hid}:' || id AS id, CAST("crop:code" AS VARCHAR) AS landuse_code,
                   {name} AS landuse_name_en, CAST({prov} AS VARCHAR) AS admin_province_code,
                   CAST({area} AS FLOAT) AS area,
                   '{hid}:' || CAST("crop:code" AS VARCHAR) AS ftw_class,
                   {_lonlat("geometry", crs)} AS geom,
                   {_metric("geometry", crs)} AS g
            FROM read_parquet('{path}') WHERE geometry IS NOT NULL"""
    )


def overlap_region(con: duckdb.DuckDBPyConnection) -> None:
    """Pairs of intersecting regional/national parcels with their shared area.

    Only national parcels whose bbox meets the region's extent take part, so the
    spatial join's R-tree stays the size of one region.
    """
    xmin, ymin, xmax, ymax = con.execute(
        "SELECT min(ST_XMin(g)), min(ST_YMin(g)), max(ST_XMax(g)), max(ST_YMax(g)) FROM reg"
    ).fetchone()
    con.execute(
        f"""CREATE OR REPLACE TABLE pairs AS
            WITH n AS (SELECT id, g FROM nat
                       WHERE ST_XMax(g) >= {xmin} AND ST_XMin(g) <= {xmax}
                         AND ST_YMax(g) >= {ymin} AND ST_YMin(g) <= {ymax})
            SELECT r.id AS rid, n.id AS nid,
                   -- A GEOS failure counts as full overlap, so it can never add a duplicate.
                   coalesce(TRY(ST_Area(ST_Intersection(r.g, n.g))),
                            least(ST_Area(r.g), ST_Area(n.g))) AS shared
            FROM reg r JOIN n ON ST_Intersects(r.g, n.g)"""
    )


def classify_region(con: duckdb.DuckDBPyConnection, hid: str) -> dict[str, float]:
    """Mark the region's gap parcels and give national parcels their land use."""
    con.execute(
        f"""CREATE OR REPLACE TABLE cover AS
            SELECT r.id, coalesce(sum(p.shared), 0) / nullif(ST_Area(r.g), 0) AS covered
            FROM reg r LEFT JOIN pairs p ON p.rid = r.id GROUP BY r.id, r.g"""
    )
    con.execute(
        f"""INSERT INTO gaps
            SELECT r.id, '{hid}' AS source, r.landuse_code, r.landuse_name_en,
                   r.admin_province_code, r.area, r.ftw_class, r.geom
            FROM reg r JOIN cover c USING (id) WHERE coalesce(c.covered, 0) < {OVERLAP_MAX}"""
    )
    con.execute(
        """INSERT INTO nat_landuse
           SELECT p.nid, arg_max(r.landuse_code, p.shared), arg_max(r.landuse_name_en, p.shared),
                  max(p.shared)
           FROM pairs p JOIN reg r ON r.id = p.rid GROUP BY p.nid"""
    )
    total, gaps, gap_area, all_area = con.execute(
        f"""SELECT count(*), count(*) FILTER (WHERE coalesce(covered, 0) < {OVERLAP_MAX}),
                   sum(ST_Area(r.g)) FILTER (WHERE coalesce(covered, 0) < {OVERLAP_MAX}),
                   sum(ST_Area(r.g))
            FROM reg r JOIN cover USING (id)"""
    ).fetchone()
    return {
        "regional_parcels": total,
        "gap_parcels": gaps,
        "gap_area_pct": round(100 * (gap_area or 0) / (all_area or 1), 1),
    }


def write_merged(con: duckdb.DuckDBPyConnection, out: Path) -> int:
    """National parcels (with land use where known) plus the gap parcels, in lon/lat."""
    tmp = out.with_suffix(".tmp.parquet")
    con.execute(
        f"""COPY (
            SELECT n.id, 'es' AS "ftw:source", n.crop_code AS "crop:code",
                   n.hcat_code AS "hcat:code", n.hcat_name_en AS "hcat:name_en",
                   l.landuse_code AS "landuse:code", l.landuse_name_en AS "landuse:name_en",
                   n.admin_province_code, n.area AS "metrics:area", n.irrigation_system,
                   n.ftw_class AS "ftw:class", n.geom AS geometry
            FROM nat n LEFT JOIN (
                -- A parcel on a regional border has a row per region: keep the larger overlap.
                SELECT nid, arg_max(landuse_code, shared) AS landuse_code,
                       arg_max(landuse_name_en, shared) AS landuse_name_en
                FROM nat_landuse GROUP BY nid
            ) l ON l.nid = n.id
            UNION ALL BY NAME
            SELECT g.id, g.source AS "ftw:source", g.landuse_code AS "landuse:code",
                   g.landuse_name_en AS "landuse:name_en", g.admin_province_code,
                   g.area AS "metrics:area", g.ftw_class AS "ftw:class", g.geom AS geometry
            FROM gaps g
        ) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)"""
    )
    import geoparquet_io as gpio

    gpio.read(str(tmp)).add_bbox().write(str(out))
    tmp.unlink()
    return con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("work_dir", type=Path)
    parser.add_argument("--stats", action="store_true", help="print overlap numbers only")
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--regions", nargs="*", default=list(REGIONS))
    args = parser.parse_args(argv)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    paths = {hid: download(source_url(hid), args.work_dir / f"{hid}-{YEAR}.parquet")
             for hid in (NATIONAL, *args.regions)}
    con = connect(args.threads)
    con.execute(f"SET temp_directory = '{args.work_dir / 'duckdb_tmp'}'")
    t0 = time.time()
    load_national(con, paths[NATIONAL])
    print(f"national loaded: {con.execute('SELECT count(*) FROM nat').fetchone()[0]:,} parcels "
          f"({time.time() - t0:.0f}s)", flush=True)
    con.execute("""CREATE OR REPLACE TABLE gaps (id VARCHAR, source VARCHAR, landuse_code VARCHAR,
                   landuse_name_en VARCHAR, admin_province_code VARCHAR, area FLOAT,
                   ftw_class VARCHAR, geom GEOMETRY)""")
    con.execute("""CREATE OR REPLACE TABLE nat_landuse (nid VARCHAR, landuse_code VARCHAR,
                   landuse_name_en VARCHAR, shared DOUBLE)""")
    stats = {}
    for hid in args.regions:
        t = time.time()
        load_region(con, hid, paths[hid])
        overlap_region(con)
        stats[hid] = classify_region(con, hid)
        print(f"{hid}: {stats[hid]} ({time.time() - t:.0f}s)", flush=True)
    (args.work_dir / "merge_stats.json").write_text(json.dumps(stats, indent=1))
    if args.stats:
        return 0
    n = write_merged(con, args.work_dir / "es_2025_merged.parquet")
    print(f"wrote es_2025_merged.parquet: {n:,} parcels ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
