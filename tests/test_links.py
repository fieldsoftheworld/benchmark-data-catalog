#!/usr/bin/env python3
"""Every relative link and asset href resolves to a file that exists.

This catches the most common hand-edit mistake: adding a child link before the
directory it points at exists. Dependency-free and offline, so it runs in
milliseconds on a clean checkout.

Resolution order for a relative href found in ``catalog/<rel_dir>/<doc>``:

1. ``catalog/<rel_dir>/<href>`` — the normal case.
2. ``staging/<rel_dir>/<href>`` — a committed sub-catalog's ``rel: item`` link
   (``./<item>/<item>.json``) and a collection's data-suffixed asset href
   (``./chips.pmtiles``, ``./items.parquet``, ...) point at files ftwd wrote
   into ``staging/<id>/``, never committed. Checked only when ``staging/``
   exists at all — locally, where the bytes are on disk.

CI clones the metadata and not the bytes, because .gitignore keeps data out of
git and staging/ is never checked out. Set CI_LIGHT=1 there: a href still
missing after step 1 is *skipped* (counted, not checked against staging) when
it is a ``rel: item`` link or a data-suffixed href (an asset, or a link such
as ``rel: pmtiles``) — exactly the hrefs
step 2 exists for. Every other missing href is still an error; CI_LIGHT never
widens what structural links must resolve.

Run: python3 tests/test_links.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from publish import load_config  # noqa: E402

config = load_config()
BASE = ROOT / config["publish_dir"]
STAGING = ROOT / config.get("data_dir", "staging")

errors: list[str] = []
skipped = 0

CI_LIGHT = os.environ.get("CI_LIGHT") == "1"
# The exemption reads the suffix and nothing else. A directory rule or a path
# prefix rule widens on its own as the catalog grows. This tuple does not.
DATA_SUFFIXES = (
    ".parquet", ".pmtiles", ".tif", ".tiff", ".copc.laz", ".laz", ".gpkg",
    ".zarr", ".geojsonl", ".shp", ".zip",
)


def is_remote(href: str) -> bool:
    return "://" in href or href.startswith(("#", "mailto:"))


def is_data_href(href: str) -> bool:
    return href.lower().endswith(DATA_SUFFIXES)


def resolve_href_status(
    path: Path, href: str, *, is_item: bool, is_data: bool,
    base: Path, staging: Path, ci_light: bool,
) -> str:
    """Where ``href`` (found in the document at ``path``) resolves.

    Returns ``"ok"`` when it exists under ``base`` (or, failing that and
    ``ci_light`` is false, under the matching directory in ``staging``);
    ``"skip"`` when it is missing under ``base``, ``ci_light`` is set, and it
    is a ``rel: item`` link or a data-suffixed asset href — the two kinds of
    href step 2 exists to check, which CI_LIGHT cannot do because the bytes
    are not on disk; ``"missing"`` otherwise, which the caller must treat as
    an error.
    """
    if (path.parent / href).resolve().exists():
        return "ok"
    if ci_light:
        return "skip" if (is_item or is_data) else "missing"
    if staging.exists():
        rel_dir = path.parent.relative_to(base)
        if (staging / rel_dir / href).resolve().exists():
            return "ok"
    return "missing"


def _self_check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(f"self-test: {message}")


def _self_test() -> None:
    """Exercise resolve_href_status's three outcomes against a temp tree.

    Proves the resolution order and the CI_LIGHT skip/error split without
    needing a built collection, so this gate's own rules are tested even on
    the skeleton, before the repo scan below runs.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        base = tmp_path / "catalog"
        staging = tmp_path / "staging"
        doc_dir = base / "lu" / "chips" / "32UNA"
        doc_dir.mkdir(parents=True)
        doc_path = doc_dir / "catalog.json"
        doc_path.write_text("{}")

        # Outcome 1: resolves directly under catalog/ (step 1).
        (doc_dir / "sibling.json").write_text("{}")
        _self_check(
            resolve_href_status(
                doc_path, "./sibling.json", is_item=False, is_data=False,
                base=base, staging=staging, ci_light=False,
            ) == "ok",
            "an href present under catalog/ resolves there",
        )

        # Outcome 2: missing under catalog/, resolves under staging/<rel_dir>/
        # (step 2), without CI_LIGHT.
        staging_item_dir = staging / "lu" / "chips" / "32UNA" / "ftw-1"
        staging_item_dir.mkdir(parents=True)
        (staging_item_dir / "ftw-1.json").write_text("{}")
        _self_check(
            resolve_href_status(
                doc_path, "./ftw-1/ftw-1.json", is_item=True, is_data=False,
                base=base, staging=staging, ci_light=False,
            ) == "ok",
            "a rel:item href missing under catalog/ resolves under staging/",
        )
        _self_check(
            resolve_href_status(
                doc_path, "./chips.pmtiles", is_item=False, is_data=True,
                base=base, staging=staging, ci_light=False,
            ) == "missing",
            "staging fallback follows the document's own rel_dir, not just any match",
        )

        # Outcome 3: missing everywhere. CI_LIGHT skips item/data hrefs and
        # still errors on everything else; without CI_LIGHT, anything missing
        # after staging is an error, exemption or not.
        _self_check(
            resolve_href_status(
                doc_path, "./missing/missing.json", is_item=True, is_data=False,
                base=base, staging=staging, ci_light=True,
            ) == "skip",
            "CI_LIGHT skips a missing rel:item href",
        )
        _self_check(
            resolve_href_status(
                doc_path, "./chips.pmtiles", is_item=False, is_data=True,
                base=base, staging=staging, ci_light=True,
            ) == "skip",
            "CI_LIGHT skips a missing data-suffixed asset href",
        )
        _self_check(
            resolve_href_status(
                doc_path, "./missing.json", is_item=False, is_data=False,
                base=base, staging=staging, ci_light=True,
            ) == "missing",
            "CI_LIGHT still errors on an ordinary missing href",
        )
        _self_check(
            resolve_href_status(
                doc_path, "./gone/gone.json", is_item=True, is_data=False,
                base=base, staging=staging, ci_light=False,
            ) == "missing",
            "without CI_LIGHT, a rel:item href missing from both trees is still an error",
        )


_errors_before_self_test = len(errors)
_self_test()
if len(errors) == _errors_before_self_test:
    print("self-test ok  resolve_href_status: catalog hit, staging fallback, CI_LIGHT skip/error")


def stac_documents() -> list[Path]:
    """Every STAC object under the published directory."""
    out = []
    for path in sorted(BASE.rglob("*.json")):
        if any(part.startswith(".") for part in path.relative_to(BASE).parts):
            continue
        if path.name.endswith(".style.json") or "styles" in path.parts:
            continue
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
            continue
        if isinstance(doc, dict) and doc.get("type") in {
            "Catalog", "Collection", "Feature"
        }:
            out.append(path)
    return out


documents = stac_documents()
checked = 0

for path in documents:
    doc = json.loads(path.read_text())
    rel_path = path.relative_to(ROOT)

    for link in doc.get("links", []):
        href = link.get("href", "")
        if not href or is_remote(href):
            continue
        status = resolve_href_status(
            path, href, is_item=link.get("rel") == "item", is_data=is_data_href(href),
            base=BASE, staging=STAGING, ci_light=CI_LIGHT,
        )
        if status == "skip":
            skipped += 1
            continue
        checked += 1
        if status == "missing":
            errors.append(f"{rel_path}: rel:{link.get('rel')} -> {href} does not exist")

    for key, asset in (doc.get("assets") or {}).items():
        href = asset.get("href", "")
        if not href or is_remote(href):
            continue
        status = resolve_href_status(
            path, href, is_item=False, is_data=is_data_href(href),
            base=BASE, staging=STAGING, ci_light=CI_LIGHT,
        )
        if status == "skip":
            skipped += 1
            continue
        checked += 1
        if status == "missing":
            errors.append(f"{rel_path}: asset {key} -> {href} does not exist")

if skipped:
    print(
        f"note   {skipped} item/data href(s) not checked: CI_LIGHT is set and "
        "they live in\n       object storage, not git. Run without CI_LIGHT "
        "locally to check them."
    )

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)

print(f"OK: {checked} relative href(s) across {len(documents)} object(s)")
