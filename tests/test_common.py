#!/usr/bin/env python3
"""Unit checks for tools/common.py's pin parsing and matching, and dataset placement.

Exercises ``parse_pin`` and ``pin_matches`` directly against literal
dependency strings, independent of what's actually installed or pinned in
this repository's pyproject.toml — so it keeps this logic honest whether the
project is pinned by git commit (today) or by an exact PyPI version (once
ftw-dataset-tools is released).

Run: python3 tests/test_common.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tempfile  # noqa: E402

from common import (  # noqa: E402
    LayoutError,
    Pin,
    dataset_relpath,
    parse_pin,
    pin_matches,
    published_collections,
    source_group,
)

errors: list[str] = []
checked = 0


def check(label: str, actual: object, expected: object) -> None:
    global checked
    checked += 1
    if actual != expected:
        errors.append(f"{label}: got {actual!r}, expected {expected!r}")


check(
    "commit pin",
    parse_pin("ftw-dataset-tools @ git+https://x/y@abc1234"),
    Pin("commit", "abc1234"),
)
check(
    "version pin",
    parse_pin("ftw-dataset-tools==0.2.0"),
    Pin("version", "0.2.0"),
)
check(
    "commit matches an installed commit it's a prefix of",
    pin_matches(Pin("commit", "abc1234"), Pin("commit", "abc1234567890")),
    True,
)
check(
    "commit does not match a different commit",
    pin_matches(Pin("commit", "abc1234"), Pin("commit", "deadbeef")),
    False,
)
check(
    "version matches the same version",
    pin_matches(Pin("version", "0.2.0"), Pin("version", "0.2.0")),
    True,
)
check(
    "version does not match a different version",
    pin_matches(Pin("version", "0.2.0"), Pin("version", "0.2.1")),
    False,
)
check(
    "a commit pin is never satisfied by a version-only install",
    pin_matches(Pin("commit", "abc1234"), Pin("version", "0.2.0")),
    False,
)

# --- where a dataset sits: catalog/<source>/<id>/ ---------------------------
check(
    "source_via names the group",
    source_group("https://data.source.coop/ftw/harmonized-field-data/lv/collection.json"),
    "lv",
)
check("a non-harmonized source_via has no group", source_group("https://example.org/x.json"), None)
check("no source_via has no group", source_group(None), None)

with tempfile.TemporaryDirectory() as tmp:
    catalog = Path(tmp) / "catalog"
    (catalog / "g" / "d1").mkdir(parents=True)
    (catalog / "g" / "d1" / "collection.json").write_text("{}")
    check("a published dataset stays where catalog/ has it",
          dataset_relpath("d1", catalog=catalog), "g/d1")
    check("an unpublished dataset is placed by its recipe's source_via",
          dataset_relpath("lv_2020", catalog=catalog), "lv/lv_2020")
    check("published_collections finds grouped collections only",
          sorted(published_collections(catalog)), ["d1"])
    try:
        dataset_relpath("d9", catalog=catalog)
        errors.append("a dataset with neither a folder nor a recipe has no place")
    except LayoutError as exc:
        check("the refusal names the recipe it looked for", "datasets/d9.yaml" in str(exc), True)
    (catalog / "h" / "d1").mkdir(parents=True)
    (catalog / "h" / "d1" / "collection.json").write_text("{}")
    try:
        published_collections(catalog)
        errors.append("a dataset published under two groups is refused")
    except LayoutError as exc:
        check("the refusal names both places", "published twice" in str(exc), True)

for e in errors:
    print(f"error  {e}")
if errors:
    raise SystemExit(1)
print(f"ok     pin parsing and matching behave correctly ({checked} checks)")
