#!/usr/bin/env python3
"""tools/chips_tiles.py and catalog/chips.style.json against ftwd's chip tiles.

The tiling itself (layers, attributes, clustering, the drop check, the thumbnail render)
is tested in ftwd. Here:

- ``main`` tiles the published table into ``work/chips.pmtiles`` by default, passes
  ``--table`` and ``--out`` through, renders ``--thumbnail`` into
  ``catalog/thumbnail.webp`` with ``catalog/chips.style.json`` over the published tiles,
  and turns an ftwd refusal into a one-line exit;
- the style reads only layers and properties ftwd tiles, draws every layer, hands the
  overview over to the chips at the chips' first zoom, points at the tiles by absolute
  URL, and is published with the style content type;
- README.md and catalog/README.md give the zooms ftwd tiles at.

Run: python3 tests/test_chips_tiles.py
"""
import contextlib
import io
import json
import sys
from pathlib import Path

try:
    from ftw_dataset_tools.api import chips_tiles as ftwd_tiles
except ImportError as missing:
    print(f"skip   {missing.name} is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import chips_tiles  # noqa: E402
import publish  # noqa: E402
from common import PUBLIC_BASE  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# main, with ftwd stubbed
seen: dict = {}


def fake_build(table, out):
    seen["build"] = (table, out)
    return 3


def fake_render(out, *, style, tiles_url, server):
    seen["render"] = (out, style, tiles_url, server)
    return out


real = chips_tiles.build_tiles, chips_tiles.render_thumbnail
chips_tiles.build_tiles, chips_tiles.render_thumbnail = fake_build, fake_render
try:
    with contextlib.redirect_stdout(io.StringIO()):
        chips_tiles.main([])
        check(seen.get("build") == (f"{PUBLIC_BASE}/chips.parquet", ROOT / "work" / "chips.pmtiles"),
              f"by default the published table is tiled into work/: {seen.get('build')}")
        chips_tiles.main(["--table", "t.parquet", "--out", "o.pmtiles"])
        check(seen["build"] == ("t.parquet", Path("o.pmtiles")),
              f"--table and --out pass through: {seen['build']}")
        chips_tiles.main(["--thumbnail"])
    check(seen.get("render") == (ROOT / "catalog" / "thumbnail.webp",
                                 ROOT / "catalog" / "chips.style.json",
                                 f"{PUBLIC_BASE}/chips.pmtiles", ftwd_tiles.DEFAULT_SERVER),
          f"--thumbnail renders the catalog's thumbnail and style over the published tiles: "
          f"{seen.get('render')}")

    def refuse(*args, **kwargs):
        raise ftwd_tiles.ChipsTilesError("the thumbnail is blank: no tiles rendered")

    chips_tiles.render_thumbnail = refuse
    try:
        chips_tiles.main(["--thumbnail"])
        errors.append("not refused: an ftwd refusal")
    except SystemExit as err:
        check(str(err.code) == "chips tiles: the thumbnail is blank: no tiles rendered",
              f"an ftwd refusal exits with one line: {err.code}")
finally:
    chips_tiles.build_tiles, chips_tiles.render_thumbnail = real

# the style reads only layers and properties the tiles have, and is usable on its own
style = json.loads(chips_tiles.STYLE.read_text())
used: set[str] = set()


def walk(expr) -> None:
    if isinstance(expr, list):
        if len(expr) == 2 and expr[0] == "get" and isinstance(expr[1], str):
            used.add(expr[1])
        for part in expr:
            walk(part)


tiled = {"chips": set(ftwd_tiles.ATTRIBUTES),
         **{layer: set(ftwd_tiles.OVERVIEW_SUMS) for layer in ftwd_tiles.OVERVIEW_LAYERS}}
by_layer: dict[str, list] = {}
for layer in style["layers"]:
    if "source-layer" in layer:
        by_layer.setdefault(layer["source-layer"], []).append(layer)
        used.clear()
        walk(layer.get("paint"))
        walk(layer.get("filter"))
        have = tiled.get(layer["source-layer"], set())
        check(used <= have, f"style layer {layer['id']} reads only properties of its "
                            f"source layer: {used - have}")
check(set(by_layer) == {"chips", *ftwd_tiles.OVERVIEW_LAYERS},
      f"the style draws every layer: {set(by_layer)}")
first_chips_zoom = ftwd_tiles.CHIPS_ZOOMS[0]
check(all(l.get("maxzoom") == first_chips_zoom
          for layer in ftwd_tiles.OVERVIEW_LAYERS for l in by_layer.get(layer, []))
      and all(l.get("minzoom") == first_chips_zoom for l in by_layer.get("chips", [])),
      "the overview hands over to the chips at the chips' first zoom, with no gap")
check(publish.content_type_for(Path(chips_tiles.STYLE.name)) == publish.STYLE_TYPE,
      "the root style is served with the style content type")
check(style["sources"]["data"]["url"].startswith("pmtiles://https://"),
      "the published style points at the tiles by absolute URL")

# the docs give the zooms ftwd tiles at
readme = " ".join((ROOT / "README.md").read_text().split())
catalog_readme = " ".join((ROOT / "catalog" / "README.md").read_text().split())
(c0, c1), (o0, o1) = ftwd_tiles.CHIPS_ZOOMS, ftwd_tiles.OVERVIEW_ZOOMS
check(f"`chips` (zoom {c0}-{c1}" in readme and f"`overview_test` (zoom {o0}-{o1}" in readme,
      "README.md gives the layers' zooms")
check(f"from zoom {c0}" in catalog_readme and f"Below zoom {c0}" in catalog_readme
      and f"From zoom {c0}" in catalog_readme, "catalog/README.md gives the chips' first zoom")

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("OK: tools/chips_tiles.py and the root style match ftwd's chip tiles")
