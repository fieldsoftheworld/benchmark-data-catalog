#!/usr/bin/env python3
"""The installed ftw-dataset-tools is the one pyproject.toml pins.

A build made with a different ftwd than the lock names is not reproducible, and
the provenance ftwd writes into every collection would disagree with the
repository. This gate reads the pin from pyproject.toml and the installed
distribution's PEP 610 direct_url.json (git installs) or version (PyPI
installs) and refuses a mismatch.

Skips with exit 0 when ftwd is not importable, so the dependency-free gates
still run in a bare interpreter; CI installs it.

Run: python3 tests/test_ftwd_pin.py
"""
import json
import re
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
deps = pyproject["project"]["dependencies"]
pin = next((d for d in deps if d.startswith("ftw-dataset-tools")), None)
if pin is None:
    print("error  pyproject.toml does not depend on ftw-dataset-tools")
    raise SystemExit(1)

try:
    dist = metadata.distribution("ftw-dataset-tools")
except metadata.PackageNotFoundError:
    print("skip   ftw-dataset-tools is not installed in this interpreter (uv sync to check the pin)")
    raise SystemExit(0)

git_pin = re.search(r"git\+https://[^@]+@([0-9a-f]{7,40})$", pin)
if git_pin:
    expected = git_pin.group(1)
    direct = dist.read_text("direct_url.json")
    if not direct:
        print(f"error  pin is git commit {expected} but the installed ftwd has no direct_url.json (PyPI install?)")
        raise SystemExit(1)
    direct_url = json.loads(direct)
    vcs_info = direct_url.get("vcs_info")
    if not vcs_info:
        print(
            f"error  installed ftwd is a local/editable install "
            f"({direct_url.get('url')}), not the pinned commit {expected[:12]}"
        )
        raise SystemExit(1)
    actual = vcs_info.get("commit_id", "")
    if not actual.startswith(expected):
        print(f"error  installed ftwd commit {actual[:12]} != pinned {expected[:12]}")
        raise SystemExit(1)
    print(f"ok     installed ftwd is git commit {actual[:12]}")
else:
    version_pin = re.search(r"==\s*([0-9][^\s,;]*)", pin)
    if version_pin is None:
        print(f"error  ftw-dataset-tools pin must be an exact version or a git commit, got {pin!r}")
        raise SystemExit(1)
    if dist.version != version_pin.group(1):
        print(f"error  installed ftwd {dist.version} != pinned {version_pin.group(1)}")
        raise SystemExit(1)
    print(f"ok     installed ftwd is version {dist.version}")
