"""Render sample chips with the current filter's fields (yellow) and the grassland it drops (cyan).

Usage (from the repo root):
    uv run --with matplotlib python tools/review/grass_review.py <dataset_id> <filter.yaml> <imagery_year> <out_dir> [n_chips]

Grassland = classes the filter excludes whose HCAT name is a pasture, meadow, grassland or
temporary grass (leys). Other excluded classes are drawn thin grey, so the picture shows what
stays unlabelled either way. Writes <out_dir>/<dataset_id>.png and <dataset_id>.json.
"""

import json
import re
import sys

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.windows import from_bounds
from shapely import wkb
from shapely.ops import transform as shp_transform

sys.path.insert(0, "tools")
import tracking  # noqa: E402
from new_dataset import source_urls  # noqa: E402

from ftw_dataset_tools.api.config import ClassFilter  # noqa: E402
from ftw_dataset_tools.api.imagery.mosaic_search import containing_tiles  # noqa: E402

GRASS = re.compile(r"pasture|meadow|grassland|temporary_grass|grass ley|grünland|wiese|weide|pastoreo|"
                   r"pastos?\b|prado|prairie|herbe|grazing", re.I)


def filter_grass(path):
    """Excluded classes whose filter-line comment names grassland (sources without HCAT names)."""
    found, section = set(), None
    for line in open(path, encoding="utf-8"):
        if re.match(r"^[a-z_]+:", line):
            section = line.split(":")[0]
            continue
        m = re.match(r'^\s*-\s*(?:"((?:[^"\\]|\\.)*)"|([^#]+?))\s*#\s*(.*)$', line)
        if section == "exclude" and m and GRASS.search(m.group(3)):
            found.add((m.group(1) if m.group(1) is not None else m.group(2)).strip())
    return found
HALF = 1280.0  # metres: a 2.56 km chip


def connect():
    con = duckdb.connect()
    for ext in ("spatial", "httpfs"):
        con.install_extension(ext)
        con.load_extension(ext)
    return con


def class_table(con, url, col, hcat, area):
    area_sql = f'sum("{area}")' if area else "count(*)"
    hcat_sql = f'any_value(CAST("{hcat}" AS VARCHAR))' if hcat else "NULL"
    return con.execute(
        f"""SELECT CAST("{col}" AS VARCHAR), {hcat_sql}, count(*), {area_sql}
            FROM read_parquet('{url}') GROUP BY 1"""
    ).fetchall()


def source_crs(con, url):
    """The source's CRS from its GeoParquet metadata; absent means lon/lat."""
    row = con.execute(f"SELECT value FROM parquet_kv_metadata('{url}') WHERE key = 'geo'").fetchone()
    if not row:
        return "EPSG:4326"
    geo = json.loads(row[0])
    crs = geo["columns"][geo.get("primary_column", "geometry")].get("crs")
    if crs is None:
        return "EPSG:4326"
    return CRS.from_user_input(json.dumps(crs) if isinstance(crs, dict) else crs)


def chip_image(lon, lat, year):
    box = (lon - 0.02, lat - 0.02, lon + 0.02, lat + 0.02)
    for quarter in (3, 2):
        tiles = containing_tiles(box, year, quarter)
        if tiles:
            break
    else:
        return None
    item = tiles[0]
    with rasterio.open(item.assets["red"].href) as src:
        crs = src.crs
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(lon, lat)
    bounds = (x - HALF, y - HALF, x + HALF, y + HALF)
    bands = []
    for band in ("red", "green", "blue"):
        with rasterio.open(item.assets[band].href) as src:
            bands.append(src.read(1, window=from_bounds(*bounds, src.transform), boundless=True,
                                  fill_value=-32768).astype(float))
    a = np.stack(bands, axis=-1)
    a[a == -32768] = np.nan
    a = np.clip(a / np.nanpercentile(a, 98), 0, 1)
    return np.nan_to_num(a), crs, bounds, f"{year} Q{quarter}"


def main():
    dataset_id, filter_path, year, out_dir = sys.argv[1:5]
    n = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    year = int(year)
    row = tracking.row(dataset_id)
    url = source_urls(row)["parquet"]
    con = connect()
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{url}')").fetchall()]
    cf = ClassFilter.from_file(filter_path)
    col = cf.resolve_column(cols)
    hcat = next((c for c in ("hcat:name", "hcat:name_en", "ec_hcat_n") if c in cols), None)
    area = next((c for c in ("metrics:area", "area") if c in cols), None)
    include = set(cf.include)
    src = source_crs(con, url)
    src_to_ll = Transformer.from_crs(src, "EPSG:4326", always_xy=True).transform

    table = class_table(con, url, col, hcat, area)
    from_filter = filter_grass(filter_path)
    grass = {c for c, h, _, _ in table
             if c not in include and ((h and GRASS.search(h)) or c in from_filter)}
    total = sum(a or 0 for *_, a in table)
    share = lambda keep: 100 * sum(a or 0 for c, _, _, a in table if keep(c)) / total  # noqa: E731
    stats = {
        "dataset_id": dataset_id, "column": col, "hcat": hcat, "measure": area or "count",
        "include_pct": round(share(lambda c: c in include), 1),
        "grass_pct": round(share(lambda c: c in grass), 1),
        "grass_classes": sorted(
            ((c, h, round(100 * (a or 0) / total, 1)) for c, h, _, a in table if c in grass),
            key=lambda t: -t[2])[:12],
    }

    import os
    keep = grass if os.environ.get("GRASS_ONLY") else include | grass
    lits = ", ".join("'" + v.replace("'", "''") + "'" for v in keep)
    centers = con.execute(
        f"""SELECT ST_X(ST_Centroid(geometry)), ST_Y(ST_Centroid(geometry))
            FROM read_parquet('{url}') WHERE CAST("{col}" AS VARCHAR) IN ({lits})
            USING SAMPLE reservoir({n * 3} ROWS) REPEATABLE (7)"""
    ).fetchall()

    cols_n = 2
    fig, axes = plt.subplots((n + 1) // cols_n, cols_n, figsize=(13, 6.8 * ((n + 1) // cols_n)))
    axes = axes.ravel()
    done = 0
    for cx, cy in centers:
        if done == n:
            break
        lon, lat = src_to_ll(cx, cy)
        img = chip_image(lon, lat, year)
        if img is None:
            continue
        a, crs, (x0, y0, x1, y1), label = img
        to_src = Transformer.from_crs(crs, src, always_xy=True).transform
        xs, ys = zip(*(to_src(x, y) for x in (x0, x1) for y in (y0, y1)))
        w, s, e, nn = min(xs), min(ys), max(xs), max(ys)
        rows = con.execute(
            f"""SELECT CAST("{col}" AS VARCHAR), ST_AsWKB(geometry) FROM read_parquet('{url}')
                WHERE bbox.xmax >= {w} AND bbox.xmin <= {e} AND bbox.ymax >= {s} AND bbox.ymin <= {nn}"""
            if "bbox" in cols else
            f"""SELECT CAST("{col}" AS VARCHAR), ST_AsWKB(geometry) FROM read_parquet('{url}')
                WHERE ST_Intersects(geometry, ST_MakeEnvelope({w}, {s}, {e}, {nn}))"""
        ).fetchall()
        to_xy = Transformer.from_crs(src, crs, always_xy=True).transform
        ax = axes[done]
        ax.imshow(a, extent=(x0, x1, y0, y1))
        counts = {"inc": 0, "grass": 0, "other": 0}
        for cls, g in rows:
            kind = "inc" if cls in include else "grass" if cls in grass else "other"
            counts[kind] += 1
            style = {"inc": ("yellow", 0.9), "grass": ("cyan", 0.7), "other": ("#bbbbbb", 0.4)}[kind]
            geom = shp_transform(to_xy, wkb.loads(bytes(g)))
            for poly in getattr(geom, "geoms", [geom]):
                if poly.geom_type != "Polygon":
                    continue
                ax.plot(*poly.exterior.xy, color=style[0], lw=style[1])
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{lat:.3f},{lon:.3f} {label}\ncurrent {counts['inc']} · grass {counts['grass']}"
                     f" · other {counts['other']}", fontsize=10)
        done += 1
    for ax in axes[done:]:
        ax.axis("off")
    fig.suptitle(f"{dataset_id}: current filter {stats['include_pct']}% · grassland "
                 f"{stats['grass_pct']}% of {stats['measure']}  (yellow current, cyan grassland,"
                 " grey other excluded)", fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    tag = "_grass" if os.environ.get("GRASS_ONLY") else ""
    plt.savefig(f"{out_dir}/{dataset_id}{tag}.png", dpi=70)
    json.dump(stats, open(f"{out_dir}/{dataset_id}.json", "w"), indent=1)
    print(dataset_id, stats["include_pct"], stats["grass_pct"], done, "chips")


if __name__ == "__main__":
    main()
