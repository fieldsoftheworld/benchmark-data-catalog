#!/usr/bin/env python3
"""The installed ftw-dataset-tools is the one pyproject.toml pins.

A build made with a different ftwd than the lock names is not reproducible, and
the provenance ftwd writes into every collection would disagree with the
repository. This gate reads the pin from pyproject.toml and the installed
distribution's PEP 610 direct_url.json (git installs) via
``tools/common.py``'s ``ftwd_pin()`` and ``installed_ftwd_commit()``, and
refuses a mismatch.

Skips with exit 0 when ftwd is not importable, so the dependency-free gates
still run in a bare interpreter; CI installs it.

Run: python3 tests/test_ftwd_pin.py
"""
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from common import ftwd_pin, installed_ftwd_commit  # noqa: E402

expected = ftwd_pin()

try:
    metadata.distribution("ftw-dataset-tools")
except metadata.PackageNotFoundError:
    print("skip   ftw-dataset-tools is not installed in this interpreter (uv sync to check the pin)")
    raise SystemExit(0) from None

actual = installed_ftwd_commit()
if actual is None:
    print(
        f"error  installed ftwd is not a git checkout of the pinned commit {expected[:12]} "
        "(PyPI or local/editable install?)"
    )
    raise SystemExit(1)
if not actual.startswith(expected):
    print(f"error  installed ftwd commit {actual[:12]} != pinned {expected[:12]}")
    raise SystemExit(1)
print(f"ok     installed ftwd is git commit {actual[:12]}")
