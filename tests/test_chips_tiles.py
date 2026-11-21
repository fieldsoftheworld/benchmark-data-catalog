#!/usr/bin/env python3
"""tools/chips_tiles.py: one feature per chip location, from a small stand-in table.

Checks the location rows (one per id, dataset count, legacy conflict, the shared hash
split), the overview points and their summed counts, the overview's tippecanoe flags,
that a table where one id has two hash splits or footprints is refused, and, when
tippecanoe is installed, that the PMTiles archive is written.

Run: python3 tests/test_chips_tiles.py
"""
import sys
import tempfile
from pathlib import Path

try:
    import duckdb
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import chips_tiles  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_table(path: Path, rows: list[tuple], size: float = 0.01) -> None:
    """rows: (dataset, id, split_legacy, split_hash_v1, x[, split_admin2_v1]) with a square of
    ``size`` degrees at x; the admin2 split defaults to the hash split."""
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial")

    def admin2(row):
        return row[3] if len(row) < 6 else row[5]

    values = ", ".join(
        f"('{r[0]}', '{r[1]}', '{r[2]}', '{r[3]}', {r[4]}, "
        f"{'NULL' if admin2(r) is None else repr(admin2(r))}, {str(r[0] == 'po').lower()})"
        for r in rows)
    con.execute(f"""
        COPY (SELECT dataset, id, id || '_b' AS block, 'Austria' AS admin0_name,
                     split_legacy, split_hash_v1, split_admin2_v1::VARCHAR AS split_admin2_v1,
                     presence_only, ST_MakeEnvelope(x, 0, x + {size}, {size}) AS geometry
              FROM (VALUES {values}) t(dataset, id, split_legacy, split_hash_v1, x,
                                       split_admin2_v1, presence_only))
        TO '{path}' (FORMAT parquet)""")
    con.close()


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    table = tmp / "chips.parquet"
    # each admin2 split differs from the hash split, so the tiles must read the right one;
    # c2 is also in a presence-only dataset ("po")
    write_table(table, [
        ("aa_2021", "c1", "train", "val", 0, "test"), ("aa_2022", "c1", "test", "val", 0, "test"),
        ("aa_2021", "c2", "train", "train", 1, "val"), ("aa_2022", "c2", "train", "train", 1, "val"),
        ("po", "c2", "train", "train", 1, "val"),
        ("bb_2020", "c3", "val", "test", 2, "train"),
    ])
    locations = tmp / "locations.parquet"
    n = chips_tiles.write_locations(str(table), locations)
    con = duckdb.connect()
    rows = {r[0]: r[1:] for r in con.execute(
        f"SELECT id, datasets, legacy_conflict, split_hash_v1, split_admin2_v1, presence_only "
        f"FROM read_parquet('{locations}')"
    ).fetchall()}
    meta = con.execute(f"SELECT decode(key) FROM parquet_kv_metadata('{locations}')").fetchall()
    con.close()
    check(n == 3 and set(rows) == {"c1", "c2", "c3"}, f"one row per chip id: {rows}")
    check(rows["c1"] == (2, True, "val", "test", False),
          f"c1 is in 2 datasets whose legacy splits differ: {rows['c1']}")
    check(rows["c2"] == (3, False, "train", "val", True),
          f"c2's legacy splits agree, and one of its datasets is presence-only: {rows['c2']}")
    check(rows["c3"] == (1, False, "test", "train", False), f"c3 is in one dataset: {rows['c3']}")
    check(("geo",) in meta, "the locations file is GeoParquet")
    con = duckdb.connect()
    columns = {r[0] for r in con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{locations}')").fetchall()}
    con.close()
    check(set(chips_tiles.ATTRIBUTES) <= columns,
          f"every tiled attribute is a column (the export drops missing ones): "
          f"{set(chips_tiles.ATTRIBUTES) - columns}")

    import json
    expected = {"train": {"chips": 1, "conflicts": 0, "datasets": 1},   # c3
                "val": {"chips": 1, "conflicts": 0, "datasets": 3},     # c2
                "test": {"chips": 1, "conflicts": 1, "datasets": 2}}    # c1
    for split in chips_tiles.SPLITS:
        seq = tmp / f"overview_{split}.geojsonseq"
        n = chips_tiles.write_overview(locations, seq, split)
        points = [json.loads(line) for line in seq.read_text().splitlines() if line.strip()]
        sums = {k: sum(p["properties"][k] for p in points) for k in chips_tiles.OVERVIEW_SUMS}
        check(n == len(points) and sums == expected[split],
              f"the {split} overview holds that split's chips with every count the clusters "
              f"sum: {sums}")
        check(all(p["geometry"]["type"] == "Point" for p in points), "overview features are points")
    cmd = chips_tiles.overview_command(seq, tmp / "o.pmtiles", "overview_test")
    check(all(f"--accumulate-attribute={k}:sum" in cmd for k in chips_tiles.OVERVIEW_SUMS)
          and "-r1" in cmd and "--cluster-densest-as-needed" in cmd
          and cmd[cmd.index("-l") + 1] == "overview_test",
          f"the overview clusters, sums every count and drops nothing by rate: {cmd}")

    for label, rows in (
        ("two hash splits", [("aa_2021", "c1", "train", "val", 0), ("aa_2022", "c1", "train", "test", 0)]),
        ("two footprints", [("aa_2021", "c1", "train", "val", 0), ("aa_2022", "c1", "train", "val", 5)]),
        ("a tiny footprint", [("aa_2021", "c1", "train", "val", 0)]),
        ("two admin2 splits", [("aa_2021", "c1", "train", "val", 0, "val"),
                               ("aa_2022", "c1", "train", "val", 0, "test")]),
        ("no admin2 split", [("aa_2021", "c1", "train", "val", 0, None)]),
    ):
        bad = tmp / "bad.parquet"
        write_table(bad, rows, size=0.001 if label == "a tiny footprint" else 0.01)
        try:
            chips_tiles.write_locations(str(bad), tmp / "x.parquet")
            errors.append(f"not refused: one chip id with {label}")
        except chips_tiles.ChipsTilesError as err:
            check("c1" in str(err), f"the refusal names the chip ({label}): {err}")

    # the thumbnail, against a stand-in chiitiler that returns a fixed PNG
    import io
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    from PIL import Image

    seen: dict = {}

    def png(blank: bool) -> bytes:
        im = Image.new("RGB", (60, 40), (244, 244, 242))
        if not blank:
            im.putpixel((5, 5), (215, 48, 31))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        return buf.getvalue()

    class Fake(BaseHTTPRequestHandler):
        body = b""

        def do_POST(self):  # noqa: N802
            seen["style"] = _json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen["path"] = self.path
            self.send_response(200)
            self.end_headers()
            self.wfile.write(Fake.body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    Fake.body = png(blank=False)
    thumb = chips_tiles.render_thumbnail(tmp / "t.webp", server=url, tiles_url="https://x/chips.pmtiles")
    source = seen["style"]["style"]["sources"]["data"]
    check(Image.open(thumb).format == "WEBP", "the thumbnail is WebP")
    check(source["tiles"] == ["pmtiles://https://x/chips.pmtiles/{z}/{x}/{y}"]
          and source["minzoom"] == chips_tiles.OVERVIEW_ZOOMS[0],
          f"chiitiler gets the tiles as a templated source from the overview's first zoom: {source}")
    Fake.body = png(blank=True)
    try:
        chips_tiles.render_thumbnail(tmp / "b.webp", server=url, tiles_url="https://x/chips.pmtiles")
        errors.append("not refused: a blank thumbnail")
    except chips_tiles.ChipsTilesError as err:
        check("blank" in str(err), f"a blank thumbnail is refused: {err}")
    server.shutdown()

    # the style reads only layers and properties the tiles have, and is usable on its own
    style = _json.loads(chips_tiles.STYLE.read_text())
    used: set[str] = set()

    def walk(expr) -> None:
        if isinstance(expr, list):
            if len(expr) == 2 and expr[0] == "get" and isinstance(expr[1], str):
                used.add(expr[1])
            for part in expr:
                walk(part)

    tiled = {"chips": set(chips_tiles.ATTRIBUTES),
             **{layer: set(chips_tiles.OVERVIEW_SUMS) for layer in chips_tiles.OVERVIEW_LAYERS}}
    by_layer = {}
    for layer in style["layers"]:
        if "source-layer" in layer:
            by_layer.setdefault(layer["source-layer"], []).append(layer)
            used.clear()
            walk(layer.get("paint"))
            walk(layer.get("filter"))
            have = tiled.get(layer["source-layer"], set())
            check(used <= have, f"style layer {layer['id']} reads only properties of its "
                                f"source layer: {used - have}")
    check(set(by_layer) == {"chips", *chips_tiles.OVERVIEW_LAYERS},
          f"the style draws every layer: {set(by_layer)}")
    check(all(l.get("maxzoom") == chips_tiles.CHIPS_ZOOMS[0]
              for layer in chips_tiles.OVERVIEW_LAYERS for l in by_layer[layer])
          and all(l.get("minzoom") == chips_tiles.CHIPS_ZOOMS[0] for l in by_layer["chips"]),
          "the overview hands over to the chips at the chips' first zoom, with no gap")
    import publish
    check(publish.content_type_for(Path(chips_tiles.STYLE.name)) == publish.STYLE_TYPE,
          "the root style is served with the style content type")
    check(style["sources"]["data"]["url"].startswith("pmtiles://https://"),
          "the published style points at the tiles by absolute URL")

    # the drop check reads tippecanoe's per-zoom strategies
    from pmtiles.tile import Compression, TileType, zxy_to_tileid
    from pmtiles.writer import Writer

    def archive(path: Path, strategies: list) -> Path:
        with path.open("wb") as f:
            w = Writer(f)
            w.write_tile(zxy_to_tileid(0, 0, 0), b"x")
            w.finalize({"tile_type": TileType.MVT, "tile_compression": Compression.NONE,
                        "min_zoom": 0, "max_zoom": 0, "min_lon_e7": 0, "min_lat_e7": 0,
                        "max_lon_e7": 0, "max_lat_e7": 0, "center_zoom": 0,
                        "center_lon_e7": 0, "center_lat_e7": 0},
                       {"strategies": _json.dumps(strategies)})
        return path

    chips_tiles.check_no_drops(archive(tmp / "ok.pmtiles", [{}, {"tiny_polygons": 3}]), "chips")
    # the strategies of a published archive (the chips and one overview layer), as tippecanoe writes them
    live = [{"coalesced_as_needed": 620167}, {"coalesced_as_needed": 754580},
            {"coalesced_as_needed": 690679}, {"coalesced_as_needed": 684300},
            {"coalesced_as_needed": 639525}, {"coalesced_as_needed": 572239},
            {"coalesced_as_needed": 419031}, {"tiny_polygons": 215}, {"tiny_polygons": 177},
            {"tiny_polygons": 236}, {"tiny_polygons": 213}, {"tiny_polygons": 258},
            {"tiny_polygons": 270}]
    chips_tiles.check_no_drops(archive(tmp / "live.pmtiles", live), "chips")
    try:
        chips_tiles.check_no_drops(archive(tmp / "livedrop.pmtiles",
                                           [*live[:6], {**live[6], "dropped_by_rate": 9}]), "overview")
        errors.append("not refused: dropped_by_rate next to clustering")
    except chips_tiles.ChipsTilesError as err:
        check("zoom 6" in str(err), f"the refusal names the zoom: {err}")
    try:
        chips_tiles.check_no_drops(archive(tmp / "drop.pmtiles", [{}, {"dropped_as_needed": 5}]), "chips")
        errors.append("not refused: an archive with dropped features")
    except chips_tiles.ChipsTilesError as err:
        check("zoom 1" in str(err), f"the refusal names the zoom: {err}")

    # an old table without the admin2 columns is refused by name, not with a traceback
    old = tmp / "old.parquet"
    con = duckdb.connect()
    con.execute(f"COPY (SELECT * EXCLUDE (split_admin2_v1, presence_only) FROM read_parquet('{table}')) "
                f"TO '{old}' (FORMAT parquet)")
    con.close()
    try:
        chips_tiles.write_locations(str(old), tmp / "x.parquet")
        errors.append("not refused: a table without split_admin2_v1")
    except chips_tiles.ChipsTilesError as err:
        check("split_admin2_v1" in str(err) and "presence_only" in str(err),
              f"the refusal names the missing columns: {err}")

    # the docs give the zooms the code tiles at
    root = chips_tiles.ROOT
    readme = " ".join((root / "README.md").read_text().split())
    catalog_readme = " ".join((root / "catalog" / "README.md").read_text().split())
    (c0, c1), (o0, o1) = chips_tiles.CHIPS_ZOOMS, chips_tiles.OVERVIEW_ZOOMS
    check(f"`chips` (zoom {c0}-{c1}" in readme and f"`overview_test` (zoom {o0}-{o1}" in readme,
          "README.md gives the layers' zooms")
    check(f"from zoom {c0}" in catalog_readme and f"Below zoom {c0}" in catalog_readme
          and f"From zoom {c0}" in catalog_readme, "catalog/README.md gives the chips' first zoom")

    from ftw_dataset_tools.api.tiles import tippecanoe_available

    if tippecanoe_available():
        out = tmp / "chips.pmtiles"
        chips_tiles.build_tiles(str(table), out)
        from pmtiles.reader import MmapSource, Reader

        with out.open("rb") as f:
            reader = Reader(MmapSource(f))
            header, meta = reader.header(), reader.metadata()
        layers = {layer["id"] for layer in meta.get("vector_layers", [])}
        check(layers == {"chips", *chips_tiles.OVERVIEW_LAYERS}
              and (header["min_zoom"], header["max_zoom"]) == (chips_tiles.OVERVIEW_ZOOMS[0],
                                                               chips_tiles.CHIPS_ZOOMS[1]),
              f"the archive has every layer at every zoom: {layers}, "
              f"{header['min_zoom']}-{header['max_zoom']}")
    else:
        print("skip   tippecanoe is not installed: the archive itself is not built")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: the chip tiles keep one feature per location with its splits")
