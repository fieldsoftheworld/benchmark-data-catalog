#!/usr/bin/env python3
"""The Spain 2025 union: national parcels kept, regional parcels fill only the gaps.

tools/merge_es_2025.py keeps every national parcel and adds a regional parcel only
when less than 10% of its area overlaps a national one. This gate runs the real
script on small synthetic inputs (one region in lon/lat, one in UTM metres) and
checks which parcels end up in each of the two outputs (es_2025 and the presence-only
es_po_2025), their classes and land use, that gap parcels under 0.1 ha are left out, and
that the outputs are lon/lat GeoParquet with a bbox column.

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
from pyproj import CRS, Transformer

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
    # The merge's regions are arguments; this test merges two (es_cb as a stand-in second
    # region beside es_pv) to cover border parcels. Their national parcels are in Asturias
    # (33): Atlantic, and not a presence-only province.
    gx, gy = -4.0, 43.2
    px, py = -2.5, 43.2  # País Vasco
    # The national and es_cb inputs carry real PROJJSON, so DuckDB types their geometry
    # GEOMETRY('EPSG:4258') and GEOMETRY('EPSG:4326') as it does for the published files.
    write(work / "es-2025.parquet", [
        national("n1", "1", "33", box(gx, gy)),                  # wheat
        national("n2", "62", "33", box(gx + 0.01, gy)),          # pasture, Atlantic
        national("n3", "62", "06", box(gx + 0.02, gy)),          # pasture, Badajoz
        national("n4", "63", "48", box(px, py)),                 # young pasture, Bizkaia
        national("n5", "1", "33", box(gx + 0.03, gy)),           # on a regional border
        national("n6", "1", "15", box(-8.0, 43.0)),              # Galicia: dropped
        national("n7", "62", "27", box(-7.5, 43.0)),             # Galician pasture: dropped
        national("n8", "1", "41", box(-5.9, 37.4)),              # Sevilla: presence-only
        national("n9", "1", "39", box(-4.0, 43.4)),              # Cantabria: dropped
        national("n10", "5", "47", box(-4.7, 41.6)),             # Valladolid: presence-only
    ], crs=CRS("EPSG:4258").to_json_dict())
    write(work / "es_cb-2025.parquet", [
        regional("r1", "TA", box(gx, gy)),                       # same as n1: covered
        regional("r2", "PS", box(gx + 0.95 * D, gy)),            # 5% over n1: gap
        regional("r3", "TA", box(gx + 0.05, gy)),                # alone: gap
        regional("r4", "PR", box(gx + 0.01 + D / 2, gy)),        # 50% over n2: covered
        regional("r5", "VI", box(gx + 0.03, gy, D / 2)),         # a quarter of n5
        # One id on two unrelated parcels, as es_pv does: one covered (by n1), one a gap.
        regional("dup", "TA", box(gx, gy)),
        regional("dup", "TA", box(gx + 0.07, gy)),
        # Degenerate: no area once made valid, so dropped.
        regional("flat", "TA", shapely.Polygon([(gx + 0.09, gy), (gx + 0.09 + D, gy),
                                                (gx + 0.09 + 2 * D, gy), (gx + 0.09, gy)])),
        regional("tiny", "TA", box(gx + 0.11, gy, D / 4)),      # ~560 m2: under 0.1 ha
    ], crs=CRS("EPSG:4326").to_json_dict())
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

    status = merge_es_2025.main([str(work), "--regions", "es_cb", "es_pv", "--threads", "2"])
    check(status == 0, f"merge exits 0, got {status}")
    out = work / "es_2025.parquet"
    con = duckdb.connect()
    con.load_extension("spatial")
    raw = con.execute(
        f"""SELECT id, "ftw:source", "crop:code", "landuse:code", "ftw:class",
                   ST_XMin(geometry), bbox.xmin, source_id
            FROM read_parquet('{out}')"""
    ).fetchall()
    ids = [r[0] for r in raw]
    check(len(ids) == len(set(ids)), f"output ids are unique, got {sorted(ids)}")
    dups = [r for r in raw if r[7] == "dup"]
    check(len(dups) == 1, f"of the two 'dup' parcels only the gap is added, got {len(dups)}")
    if len(dups) == 1:
        check(abs(dups[0][5] - (gx + 0.07)) < 1e-6, "the 'dup' parcel added is the free one")
    check(not any(r[7] == "flat" for r in raw), "a zero-area parcel is dropped")
    check(not any(r[7] == "tiny" for r in raw), "a gap parcel under 0.1 ha is dropped")
    check(not any(r[7] in ("n6", "n7", "n8", "n9", "n10") for r in raw),
          "national parcels in Galicia, Andalucía, Castilla y León and Cantabria stay out of es_2025")
    # Keyed by source and source id; the 'dup' pair is checked above.
    rows = {f"{r[1]}:{r[7]}": r[1:7] for r in raw if r[7] != "dup"}
    expected = {"es:n1", "es:n2", "es:n3", "es:n4", "es:n5", "es_cb:r2", "es_cb:r3", "es_pv:p2"}
    check(len(raw) == len(expected) + 1, f"national parcels plus the gaps, got {len(raw)} rows")
    check(set(rows) == expected, f"national parcels plus the gaps, got {sorted(rows)}")
    if set(rows) == expected:
        check(rows["es:n1"][2] == "TA", f"n1 takes r1's land use, got {rows['es:n1'][2]}")
        check(rows["es:n3"][2] is None, "a national parcel no region overlaps has no land use")
        check(rows["es:n5"][2] == "OV", f"a border parcel takes the larger overlap, got {rows['es:n5'][2]}")
        check(rows["es:n2"][3] == "es:62:atlantic", f"Asturian pasture, got {rows['es:n2'][3]}")
        check(rows["es:n3"][3] == "es:62", f"pasture outside the north, got {rows['es:n3'][3]}")
        check(rows["es:n4"][3] == "es:63:atlantic", f"Basque pasture, got {rows['es:n4'][3]}")
        check(rows["es:n1"][3] == "es:1", f"national class, got {rows['es:n1'][3]}")
        check(rows["es_cb:r3"][1] is None, "a gap parcel has no crop code")
        check(rows["es_cb:r3"][3] == "es_cb:TA", f"gap class, got {rows['es_cb:r3'][3]}")
        check(rows["es_pv:p2"][0] == "es_pv", "gap parcels name their source")
        x, bx = rows["es_pv:p2"][4], rows["es_pv:p2"][5]
        check(abs(x - (px + 0.05)) < 1e-6, f"UTM input comes out in lon/lat, got xmin {x}")
        check(abs(bx - x) < 1e-9, "the bbox column matches the geometry")
    geo = json.loads(pq.read_schema(out).metadata[b"geo"])
    check("covering" in geo["columns"]["geometry"], "the output declares its bbox covering")
    crs = geo["columns"]["geometry"].get("crs")
    check(crs is None, f"the output carries no CRS label (default lon/lat), got {crs}")
    po = work / "es_po_2025.parquet"
    po_rows = {r[0]: r[1:] for r in con.execute(
        f"""SELECT source_id, "ftw:source", "ftw:class", "landuse:code" FROM read_parquet('{po}')"""
    ).fetchall()}
    check(set(po_rows) == {"n8", "n10"},
          f"es_po_2025 holds Andalucía's and Castilla y León's national parcels only, "
          f"not Galicia's or Cantabria's, got {sorted(po_rows)}")
    if set(po_rows) == {"n8", "n10"}:
        check(po_rows["n8"][1] == "es:1", f"national class, got {po_rows['n8'][1]}")
        check(all(r[0] == "es" and r[2] is None for r in po_rows.values()),
              "presence-only parcels are national, with no land use")
    po_geo = json.loads(pq.read_schema(po).metadata[b"geo"])
    check("covering" in po_geo["columns"]["geometry"], "es_po_2025 declares its bbox covering")
    check(list(merge_es_2025.REGIONS) == ["es_pv"],
          f"by default only País Vasco fills gaps (es_cb is not CC-BY), got {list(merge_es_2025.REGIONS)}")
    stats = json.loads((work / "merge_stats.json").read_text())
    cb = stats["es_cb"]
    check(cb["gap_parcels"] == 3, f"three es_cb gaps, got {cb}")
    check(cb["small_gaps_dropped"] == 1, f"one small gap dropped, got {cb}")
    check(cb["zero_area_dropped"] == 1, f"one flat parcel dropped, got {cb}")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: Spain 2025 splits into es_2025 (with gaps) and presence-only es_po_2025")
