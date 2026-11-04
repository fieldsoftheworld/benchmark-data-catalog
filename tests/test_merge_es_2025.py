#!/usr/bin/env python3
"""The Spain 2025 union: national parcels kept, regional parcels fill only the gaps.

tools/merge_es_2025.py keeps every national parcel and adds a regional parcel only
when less than 10% of its area overlaps a national one. This gate runs the real
script on small synthetic inputs (one region in lon/lat, one in UTM metres) and
checks which parcels end up in the output, their classes, their land use and that
the output is lon/lat GeoParquet with a bbox column.

No network: the inputs sit where the script would download them.

Run: python3 tests/test_merge_es_2025.py
"""

import json
import sys
import tempfile
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
import shapely.ops
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import merge_es_2025  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write(path: Path, rows: list[dict], crs: dict | None = None) -> None:
    columns = {k: [r[k] for r in rows] for k in rows[0] if k != "geometry"}
    columns["geometry"] = [shapely.to_wkb(r["geometry"]) for r in rows]
    column = {"encoding": "WKB", "geometry_types": ["Polygon"]}
    if crs is not None:
        column["crs"] = crs
    geo = {"version": "1.1.0", "primary_column": "geometry", "columns": {"geometry": column}}
    table = pa.table(columns).replace_schema_metadata({b"geo": json.dumps(geo).encode()})
    pq.write_table(table, path)


D = 0.001  # ~80 m in lon/lat


def box(x: float, y: float, w: float = D) -> shapely.Polygon:
    return shapely.box(x, y, x + w, y + w)


def national(id_, code, prov, geom):
    return {"id": id_, "crop:code": code, "hcat:code": 1, "hcat:name_en": f"crop {code}",
            "admin_province_code": prov, "metrics:area": 1.0, "irrigation_system": None,
            "geometry": geom}


def regional(id_, code, geom):
    return {"id": id_, "crop:code": code, "crop:name_en": f"use {code}", "geometry": geom}


with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    gx, gy = -8.0, 43.0  # Galicia
    px, py = -2.5, 43.2  # País Vasco
    write(work / "es-2025.parquet", [
        national("n1", "1", "15", box(gx, gy)),                  # wheat
        national("n2", "62", "15", box(gx + 0.01, gy)),          # pasture, Atlantic
        national("n3", "62", "06", box(gx + 0.02, gy)),          # pasture, Badajoz
        national("n4", "63", "48", box(px, py)),                 # young pasture, Bizkaia
        national("n5", "1", "36", box(gx + 0.03, gy)),           # on a regional border
    ])
    write(work / "es_ga-2025.parquet", [
        regional("r1", "TA", box(gx, gy)),                       # same as n1: covered
        regional("r2", "PS", box(gx + 0.95 * D, gy)),            # 5% over n1: gap
        regional("r3", "TA", box(gx + 0.05, gy)),                # alone: gap
        regional("r4", "PR", box(gx + 0.01 + D / 2, gy)),        # 50% over n2: covered
        regional("r5", "VI", box(gx + 0.03, gy, D / 2)),         # a quarter of n5
    ])
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True).transform
    write(
        work / "es_pv-2025.parquet",
        [
            regional("p1", "PS", shapely.ops.transform(to_utm, box(px, py))),         # = n4
            regional("p2", "TA", shapely.ops.transform(to_utm, box(px + 0.05, py))),  # gap
            # The other region's parcel over n5 covers more of it than r5 does.
            regional("p3", "OV", shapely.ops.transform(to_utm, box(gx + 0.03, gy))),
        ],
        crs={"id": {"authority": "EPSG", "code": 25830}},
    )

    status = merge_es_2025.main([str(work), "--regions", "es_ga", "es_pv", "--threads", "2"])
    check(status == 0, f"merge exits 0, got {status}")
    out = work / "es_2025_merged.parquet"
    con = duckdb.connect()
    con.load_extension("spatial")
    rows = {
        r[0]: r[1:]
        for r in con.execute(
            f"""SELECT id, "ftw:source", "crop:code", "landuse:code", "ftw:class",
                       ST_XMin(geometry), bbox.xmin
                FROM read_parquet('{out}')"""
        ).fetchall()
    }
    expected = {"es:n1", "es:n2", "es:n3", "es:n4", "es:n5", "es_ga:r2", "es_ga:r3", "es_pv:p2"}
    n_rows = con.execute(f"SELECT count(*) FROM read_parquet('{out}')").fetchone()[0]
    check(n_rows == len(expected), f"no parcel appears twice, got {n_rows} rows")
    check(set(rows) == expected, f"national parcels plus the gaps, got {sorted(rows)}")
    if set(rows) == expected:
        check(rows["es:n1"][2] == "TA", f"n1 takes r1's land use, got {rows['es:n1'][2]}")
        check(rows["es:n3"][2] is None, "a national parcel no region overlaps has no land use")
        check(rows["es:n5"][2] == "OV", f"a border parcel takes the larger overlap, got {rows['es:n5'][2]}")
        check(rows["es:n2"][3] == "es:62:atlantic", f"Galician pasture, got {rows['es:n2'][3]}")
        check(rows["es:n3"][3] == "es:62", f"pasture outside the north, got {rows['es:n3'][3]}")
        check(rows["es:n4"][3] == "es:63:atlantic", f"Basque pasture, got {rows['es:n4'][3]}")
        check(rows["es:n1"][3] == "es:1", f"national class, got {rows['es:n1'][3]}")
        check(rows["es_ga:r3"][1] is None, "a gap parcel has no crop code")
        check(rows["es_ga:r3"][3] == "es_ga:TA", f"gap class, got {rows['es_ga:r3'][3]}")
        check(rows["es_pv:p2"][0] == "es_pv", "gap parcels name their source")
        x, bx = rows["es_pv:p2"][4], rows["es_pv:p2"][5]
        check(abs(x - (px + 0.05)) < 1e-6, f"UTM input comes out in lon/lat, got xmin {x}")
        check(abs(bx - x) < 1e-9, "the bbox column matches the geometry")
    geo = json.loads(pq.read_schema(out).metadata[b"geo"])
    check("covering" in geo["columns"]["geometry"], "the output declares its bbox covering")
    stats = json.loads((work / "merge_stats.json").read_text())
    check(stats["es_ga"]["gap_parcels"] == 2, f"two Galician gaps, got {stats['es_ga']}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: the Spain union keeps national parcels and fills only the gaps")
