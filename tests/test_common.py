#!/usr/bin/env python3
"""Unit checks for tools/common.py's pin parsing and matching.

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
from common import Pin, parse_pin, pin_matches  # noqa: E402

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

for e in errors:
    print(f"error  {e}")
if errors:
    raise SystemExit(1)
print(f"ok     pin parsing and matching behave correctly ({checked} checks)")
