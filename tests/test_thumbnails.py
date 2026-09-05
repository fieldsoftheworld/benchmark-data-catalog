#!/usr/bin/env python3
"""Thumbnails: file shape, collection registration, and pure-math/unit checks.

Two kinds of checks:

1. Per built collection (one with ``catalog/<id>/collection.json``): if
   ``thumbnail.webp`` doesn't exist yet, that's a *note*, not an error — the
   thumbnail is a separate, later step from building/catalogizing a dataset,
   and this gate must stay green mid-workflow. If it does exist, it must
   actually be a WebP image with a sane aspect and size, and the collection's
   ``thumbnail`` asset (and the manifest's declared style) must agree with
   what's on disk.
2. Unit tests for ``tools/thumbnail.py``'s pure functions
   (``span_for_zoom``/``window``) and its PNG-to-WebP + blank-probe pipeline
   on generated images — no chiitiler, no network.

Run: python3 tests/test_thumbnails.py
"""
import json
import math
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    print("skip   PyYAML is not installed (uv sync to run this gate)")
    raise SystemExit(0) from None

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from publish import load_config  # noqa: E402
import thumbnail  # noqa: E402

config = load_config()
CATALOG = ROOT / config["publish_dir"]
MANIFEST = yaml.safe_load((ROOT / "datasets.yaml").read_text())

MIN_ASPECT, MAX_ASPECT = 1.45, 1.55
MIN_WIDTH = 700

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# --- per built collection ---------------------------------------------------

built = sorted(p.parent.name for p in CATALOG.glob("*/collection.json"))

for dataset_id in built:
    cdir = CATALOG / dataset_id
    thumb_path = cdir / "thumbnail.webp"
    if not thumb_path.exists():
        print(f"note   {dataset_id}: no thumbnail.webp yet (run tools/thumbnail.py {dataset_id})")
        continue

    magic = thumb_path.read_bytes()[:16]
    check(
        magic[:4] == b"RIFF" and magic[8:12] == b"WEBP",
        f"catalog/{dataset_id}/thumbnail.webp: missing RIFF....WEBP magic, got {magic!r}",
    )

    with Image.open(thumb_path) as img:
        width, height = img.size
    aspect = width / height if height else 0.0
    check(
        MIN_ASPECT <= aspect <= MAX_ASPECT,
        f"catalog/{dataset_id}/thumbnail.webp: aspect {aspect:.3f} outside "
        f"[{MIN_ASPECT}, {MAX_ASPECT}] ({width}x{height})",
    )
    check(
        width >= MIN_WIDTH,
        f"catalog/{dataset_id}/thumbnail.webp: width {width} < {MIN_WIDTH}",
    )

    collection = json.loads((cdir / "collection.json").read_text())
    assets = collection.get("assets") or {}
    thumb_asset = assets.get("thumbnail")
    if thumb_asset is None:
        errors.append(f"catalog/{dataset_id}/collection.json: no 'thumbnail' asset registered")
    else:
        check(
            thumb_asset.get("href") == "./thumbnail.webp",
            f"catalog/{dataset_id}/collection.json: thumbnail asset href "
            f"{thumb_asset.get('href')!r} != './thumbnail.webp'",
        )
        check(
            thumb_asset.get("type") == "image/webp",
            f"catalog/{dataset_id}/collection.json: thumbnail asset type "
            f"{thumb_asset.get('type')!r} != 'image/webp'",
        )
        check(
            "thumbnail" in (thumb_asset.get("roles") or []),
            f"catalog/{dataset_id}/collection.json: thumbnail asset roles "
            f"{thumb_asset.get('roles')!r} missing 'thumbnail'",
        )

    spec = (MANIFEST.get("datasets") or {}).get(dataset_id) or {}
    manifest_style = (spec.get("thumbnail") or {}).get("style")
    if manifest_style:
        check(
            f"style-{manifest_style}" in assets,
            f"catalog/{dataset_id}/collection.json: datasets.yaml thumbnail.style "
            f"{manifest_style!r} has no matching style-{manifest_style} asset",
        )

# --- unit tests: pure math --------------------------------------------------

# At zoom 0 the whole 40,075,016.686 m circumference fits in 256 px (one tile).
check(
    math.isclose(thumbnail.span_for_zoom(0, 256), thumbnail.EARTH_CIRC, rel_tol=1e-9),
    "span_for_zoom(0, 256) should equal the Earth's Web Mercator circumference",
)
# Doubling zoom halves the ground distance a fixed pixel count covers.
check(
    math.isclose(
        thumbnail.span_for_zoom(10, 512), thumbnail.span_for_zoom(11, 512) * 2, rel_tol=1e-9
    ),
    "span_for_zoom should halve when zoom increases by one",
)

bbox = thumbnail.window(6.13, 49.61, 12, size_px=1024)
check(len(bbox) == 4 and bbox[0] < 6.13 < bbox[2] and bbox[1] < 49.61 < bbox[3], f"window() bbox {bbox} does not bracket its center")
width_deg = bbox[2] - bbox[0]
height_deg = bbox[3] - bbox[1]
# window() sizes a *metre* box for a 3:2 frame; near the equator that ratio
# roughly survives in degrees too, but at 49.6N the y-degree is compressed by
# cos(lat), so the degree aspect should be noticeably wider than 1.5, not
# equal to it.
check(width_deg > 0 and height_deg > 0, f"window() produced a degenerate bbox {bbox}")
check(
    (width_deg / height_deg) > thumbnail.TARGET_ASPECT,
    f"window() at 49.6N should be wider than {thumbnail.TARGET_ASPECT} in degrees "
    f"(mercator y-compression), got {width_deg / height_deg:.3f}",
)

# --- unit tests: blank probe + WebP conversion, no chiitiler ----------------

white = Image.new("RGB", (100, 60), "#ffffff")
check(
    thumbnail.blank_fraction(white) == 0.0,
    "blank_fraction of an all-background image should be 0",
)

half = Image.new("RGB", (100, 60), "#ffffff")
for y in range(30):
    for x in range(100):
        half.putpixel((x, y), (0, 100, 0))
fraction = thumbnail.blank_fraction(half)
check(
    math.isclose(fraction, 0.5, abs_tol=0.01),
    f"blank_fraction of a half-painted image should be ~0.5, got {fraction}",
)
check(
    fraction >= thumbnail.MIN_NONBLANK_FRACTION,
    "a half-painted image should clear the blank-probe threshold",
)
check(
    thumbnail.blank_fraction(white) < thumbnail.MIN_NONBLANK_FRACTION,
    "an all-background image should fail the blank-probe threshold",
)

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "out.webp"
    thumbnail.write_webp(half, out, quality=80)
    magic = out.read_bytes()[:16]
    check(
        magic[:4] == b"RIFF" and magic[8:12] == b"WEBP",
        f"write_webp did not produce a RIFF/WEBP file, got magic {magic!r}",
    )
    with Image.open(out) as roundtrip:
        check(roundtrip.size == half.size, "write_webp changed the image dimensions")

for e in errors:
    print(f"error  {e}")
if errors:
    raise SystemExit(1)
print(f"ok     thumbnails: {len(built)} built collection(s), pure-math and blank-probe unit checks pass")
