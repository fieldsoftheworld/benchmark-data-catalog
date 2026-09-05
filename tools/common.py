#!/usr/bin/env python3
"""Shared helpers: paths, the ftwd pin, and small JSON/YAML I/O.

Every tool and gate that needs the published/staging directories, the catalog
manifest, or the ftwd version pin should import them from here instead of
re-deriving them. ``ROOT``, ``CATALOG`` and ``STAGING`` are read once from
``catalog.publish.yaml`` via ``publish.load_config`` — never re-parse that file
elsewhere.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from publish import load_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
_config = load_config()
CATALOG = ROOT / _config["publish_dir"]
STAGING = ROOT / _config.get("data_dir", "staging")


def public_url(rel: str) -> str:
    """The public URL for ``rel``, joined onto ``public_base``."""
    return _config["public_base"].rstrip("/") + "/" + rel


def read_json(path: Path) -> dict:
    """Read and parse a JSON file."""
    return json.loads(Path(path).read_text())


def write_json(path: Path, doc: dict) -> None:
    """Write ``doc`` as pretty-printed JSON, newline-terminated."""
    Path(path).write_text(json.dumps(doc, indent=2) + "\n")


def load_manifest() -> dict:
    """Parse ``datasets.yaml``, the publication manifest."""
    import yaml

    return yaml.safe_load((ROOT / "datasets.yaml").read_text())


def ftwd_pin() -> str:
    """The full git commit pinned for ftw-dataset-tools in pyproject.toml.

    Exits with an error (status 1) if pyproject.toml has no
    ftw-dataset-tools dependency, or its pin is not a git commit — a version
    pin (``==X.Y.Z``) is a state this project has not reached yet.
    """
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    deps = pyproject["project"]["dependencies"]
    pin = next((d for d in deps if d.startswith("ftw-dataset-tools")), None)
    if pin is None:
        print("error  pyproject.toml does not depend on ftw-dataset-tools")
        raise SystemExit(1)
    match = re.search(r"git\+https://[^@]+@([0-9a-f]{7,40})$", pin)
    if not match:
        print(f"error  ftw-dataset-tools pin must be a git commit, got {pin!r}")
        raise SystemExit(1)
    return match.group(1)


def installed_ftwd_commit() -> str | None:
    """The git commit the installed ftw-dataset-tools distribution reports.

    None when ftw-dataset-tools is not installed, or is installed from
    somewhere other than a git checkout (PyPI, local path, editable install).
    """
    try:
        dist = metadata.distribution("ftw-dataset-tools")
    except metadata.PackageNotFoundError:
        return None
    direct = dist.read_text("direct_url.json")
    if not direct:
        return None
    vcs_info = json.loads(direct).get("vcs_info")
    if not vcs_info:
        return None
    return vcs_info.get("commit_id")
