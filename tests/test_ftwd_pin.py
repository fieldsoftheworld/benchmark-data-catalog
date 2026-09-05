#!/usr/bin/env python3
"""The installed ftw-dataset-tools is the one pyproject.toml pins.

A build made with a different ftwd than the lock names is not reproducible, and
the provenance ftwd writes into every collection would disagree with the
repository. This gate reads the pin from pyproject.toml and the installed
distribution's PEP 610 direct_url.json (git installs) or version (PyPI
installs), via ``tools/common.py``'s ``ftwd_pin()`` / ``installed_ftwd()`` /
``pin_matches()``, and refuses a mismatch.

Skips with exit 0 when ftwd is not importable, so the dependency-free gates
still run in a bare interpreter; CI installs it.

Run: python3 tests/test_ftwd_pin.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from common import ftwd_pin, installed_ftwd, pin_matches  # noqa: E402

expected = ftwd_pin()
installed = installed_ftwd()

if installed is None:
    print("skip   ftw-dataset-tools is not installed in this interpreter (uv sync to check the pin)")
    raise SystemExit(0)

if pin_matches(expected, installed):
    if expected.kind == "commit":
        print(f"ok     installed ftwd is git commit {installed.value[:12]}")
    else:
        print(f"ok     installed ftwd is version {installed.value}")
    raise SystemExit(0)

if expected.kind == "commit" and installed.kind != "commit":
    print(
        f"error  pin is git commit {expected.value} but the installed ftwd "
        f"is not a git checkout (installed version {installed.value}; PyPI or editable install?)"
    )
    raise SystemExit(1)
if expected.kind == "commit":
    print(f"error  installed ftwd commit {installed.value[:12]} != pinned {expected.value[:12]}")
    raise SystemExit(1)
print(f"error  installed ftwd {installed.value} != pinned {expected.value}")
raise SystemExit(1)
