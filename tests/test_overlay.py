#!/usr/bin/env python3
"""tests/overlay.py: overlay_tree, has_staging_items, resolve_target.

Builds tiny catalog/ and staging/ trees by hand and exercises the shared
overlay helper directly -- no rashid, no stac-check, no real ftwd build.

Run: python3 tests/test_overlay.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import overlay  # noqa: E402

# Popped once, up front, so an inherited BDC_STAGING_DIR (e.g. a maintainer
# running the documented CI_LIGHT simulation from their own shell) cannot
# leak into the has_staging_items/resolve_target calls the earlier blocks in
# this file make against their own hand-built temp staging trees. Only the
# block below that actually exercises the override sets it back.
_ORIGINAL_BDC_STAGING_DIR = os.environ.pop("BDC_STAGING_DIR", None)

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc) + "\n")


def build_catalog(catalog: Path, dataset_id: str = "lu", square: str = "32UNA") -> None:
    """A minimal built collection with one committed sub-catalog."""
    write_json(catalog / dataset_id / "collection.json", {"type": "Collection", "id": dataset_id})
    write_json(
        catalog / dataset_id / "chips" / square / "catalog.json",
        {"type": "Catalog", "id": square, "links": []},
    )


# --- overlay_tree copies only *.json item files, never rasters -------------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    build_catalog(catalog)

    item_dir = staging / "lu" / "chips" / "32UNA" / "ftw-1"
    write_json(item_dir / "ftw-1.json", {"type": "Feature", "id": "ftw-1"})
    (item_dir / "ftw-1_instance.tif").write_bytes(b"not-really-a-tif")

    with overlay.overlay_tree(catalog, staging) as root:
        root = Path(root)
        dest_item_dir = root / "lu" / "chips" / "32UNA" / "ftw-1"
        check((dest_item_dir / "ftw-1.json").is_file(), "the item's own JSON is copied into the overlay")
        check(
            not (dest_item_dir / "ftw-1_instance.tif").exists(),
            "a raster asset under the item directory is never copied into the overlay",
        )
        copied = sorted(p.name for p in dest_item_dir.rglob("*") if p.is_file())
        check(copied == ["ftw-1.json"], f"only the item JSON is copied, got {copied}")


# --- overlay_tree copies nested imagery child items too ---------------------
# An imagery child item sits one directory deeper than its parent item
# (<id>/chips/<square>/<item>/<child>/<child>.json — see tools/publish.py's
# _is_item_json). Its own rel:'item' link from the parent item must resolve
# in the overlay too, so its JSON has to be copied at the same relative depth.

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    build_catalog(catalog)

    item_dir = staging / "lu" / "chips" / "32UNA" / "ftw-1"
    write_json(item_dir / "ftw-1.json", {"type": "Feature", "id": "ftw-1"})
    child_dir = item_dir / "ftw-1_20250101"
    write_json(child_dir / "ftw-1_20250101.json", {"type": "Feature", "id": "ftw-1_20250101"})
    (child_dir / "ftw-1_20250101_visual.tif").write_bytes(b"not-really-a-tif")

    with overlay.overlay_tree(catalog, staging) as root:
        root = Path(root)
        dest_item_dir = root / "lu" / "chips" / "32UNA" / "ftw-1"
        check((dest_item_dir / "ftw-1.json").is_file(), "the parent item's own JSON is copied")
        child_json = dest_item_dir / "ftw-1_20250101" / "ftw-1_20250101.json"
        check(child_json.is_file(), "a nested imagery child item's JSON is copied, at the same relative depth")
        check(
            not (dest_item_dir / "ftw-1_20250101" / "ftw-1_20250101_visual.tif").exists(),
            "a raster asset under a nested imagery child item is never copied",
        )


# --- overlay_tree's temp directory is cleaned up on context exit -----------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    build_catalog(catalog)
    write_json(staging / "lu" / "chips" / "32UNA" / "ftw-1" / "ftw-1.json", {"type": "Feature", "id": "ftw-1"})

    with overlay.overlay_tree(catalog, staging) as root:
        overlay_root = Path(root)
        check(overlay_root.is_dir(), "the overlay directory exists while the context manager is open")
    check(not overlay_root.exists(), "the overlay directory is removed once the context manager exits")


# --- has_staging_items: false on an empty staging tree ----------------------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    staging.mkdir()
    build_catalog(catalog)
    check(
        overlay.has_staging_items(catalog, staging) is False,
        "has_staging_items is false when staging/ exists but is empty",
    )

    # ... and remains false when staging/ does not exist at all.
    missing_staging = tmp / "does-not-exist"
    check(
        overlay.has_staging_items(catalog, missing_staging) is False,
        "has_staging_items is false when staging/ does not exist at all",
    )

    # Once a matching chips/ tree appears under staging/, it flips to true —
    # an empty chips/ directory is enough; has_staging_items checks for the
    # directory, not for item files inside it.
    (staging / "lu" / "chips").mkdir(parents=True)
    check(
        overlay.has_staging_items(catalog, staging) is True,
        "has_staging_items is true once the built collection's staging chips/ tree exists",
    )


# --- resolve_target: overlay when any built collection has staged items,
# catalog/ only otherwise; "any", not "all" ----------------------------------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    build_catalog(catalog)

    # No staging item tree at all: catalog/ only, and the exact catalog path
    # is yielded unchanged (not a copy).
    with overlay.resolve_target(catalog, staging) as target:
        check(target == catalog, "resolve_target yields catalog/ itself when there is no staging item tree")

    # A staging item tree exists: overlay mode, and a *different*, temporary
    # path is yielded, carrying the staged item JSON.
    write_json(staging / "lu" / "chips" / "32UNA" / "ftw-1" / "ftw-1.json", {"type": "Feature", "id": "ftw-1"})
    with overlay.resolve_target(catalog, staging) as target:
        check(target != catalog, "resolve_target yields a temp overlay, not catalog/ itself, once items exist")
        check(
            (Path(target) / "lu" / "chips" / "32UNA" / "ftw-1" / "ftw-1.json").is_file(),
            "resolve_target's overlay carries the staged item JSON",
        )

    # A second built collection with no staged items at all: has_staging_items
    # (and so resolve_target) still picks overlay mode, because ANY built
    # collection having items is enough — not all of them.
    build_catalog(catalog, dataset_id="si", square="33TUN")
    with overlay.resolve_target(catalog, staging) as target:
        check(
            target != catalog,
            "resolve_target still overlays when only one of several built collections has staged items",
        )


# --- BDC_STAGING_DIR overrides staging/, honored by both has_staging_items
# and resolve_target ---------------------------------------------------------

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    catalog = tmp / "catalog"
    staging = tmp / "staging"
    build_catalog(catalog)
    write_json(staging / "lu" / "chips" / "32UNA" / "ftw-1" / "ftw-1.json", {"type": "Feature", "id": "ftw-1"})

    try:
        check(
            overlay.has_staging_items(catalog, staging) is True,
            "sanity: has_staging_items is true against the real staging tree",
        )
        os.environ["BDC_STAGING_DIR"] = str(tmp / "does-not-exist")
        check(
            overlay.has_staging_items(catalog, staging) is False,
            "BDC_STAGING_DIR pointed at a missing directory overrides a real staging/ to 'no items'",
        )
        with overlay.resolve_target(catalog, staging) as target:
            check(
                target == catalog,
                "BDC_STAGING_DIR forces resolve_target into catalog/ only mode even though staging/ has items",
            )
    finally:
        if _ORIGINAL_BDC_STAGING_DIR is None:
            os.environ.pop("BDC_STAGING_DIR", None)
        else:
            os.environ["BDC_STAGING_DIR"] = _ORIGINAL_BDC_STAGING_DIR


if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: overlay_tree, has_staging_items, and resolve_target behave correctly")
