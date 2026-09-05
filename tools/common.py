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
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))

from publish import load_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
_config = load_config()
CATALOG = ROOT / _config["publish_dir"]
STAGING = ROOT / _config.get("data_dir", "staging")
PUBLIC_BASE = _config["public_base"]

# Any Portolan profile schema version. A vX.Y.Z bump must not silently turn a
# schema-URI check (tests/test_manifest.py) or a stac-check dialect-crash
# exemption (tests/test_stac_valid.py) into a false failure. Deliberately
# unanchored: match with ``.fullmatch()`` when comparing a whole string,
# ``.search()`` when scanning for it inside a larger message.
PORTOLAN_SCHEMA_RE = re.compile(
    r"https://schemas\.portolan-sdi\.org/portolan/v\d+\.\d+\.\d+/schema\.json"
)


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


@dataclass(frozen=True)
class Pin:
    """A dependency pin: either a git commit or an exact version.

    ``kind`` says which; ``value`` is the commit (full or abbreviated) or the
    version string. Two Pins of different kinds are never equal via
    ``pin_matches`` even if their values happen to coincide.
    """

    kind: Literal["commit", "version"]
    value: str


_GIT_PIN = re.compile(r"git\+https://[^@]+@([0-9a-f]{7,40})$")
_VERSION_PIN = re.compile(r"==\s*([0-9][^\s,;]*)")


def parse_pin(dep: str) -> Pin:
    """Parse one dependency line into a Pin.

    ``... @ git+https://...@<hash>`` is a commit pin. ``name==X.Y.Z`` is a
    version pin — the state this project moves to once ftwd is on PyPI.
    Anything else exits with an error: the pin must be exact one way or the
    other, or the lock and the pin gate can silently drift.
    """
    git_pin = _GIT_PIN.search(dep)
    if git_pin:
        return Pin("commit", git_pin.group(1))
    version_pin = _VERSION_PIN.search(dep)
    if version_pin:
        return Pin("version", version_pin.group(1))
    print(f"error  ftw-dataset-tools pin must be an exact version or a git commit, got {dep!r}")
    raise SystemExit(1)


def ftwd_pin() -> Pin:
    """The pin for ftw-dataset-tools declared in pyproject.toml."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    deps = pyproject["project"]["dependencies"]
    dep = next((d for d in deps if d.startswith("ftw-dataset-tools")), None)
    if dep is None:
        print("error  pyproject.toml does not depend on ftw-dataset-tools")
        raise SystemExit(1)
    return parse_pin(dep)


def installed_ftwd() -> Pin | None:
    """The Pin the installed ftw-dataset-tools distribution reports.

    A commit Pin when it's a git checkout (PEP 610 direct_url.json carries
    vcs_info with a commit_id); otherwise a version Pin from the
    distribution's version (covers PyPI installs and local/editable installs
    alike). None when ftw-dataset-tools is not installed at all.
    """
    try:
        dist = metadata.distribution("ftw-dataset-tools")
    except metadata.PackageNotFoundError:
        return None
    direct = dist.read_text("direct_url.json")
    if direct:
        vcs_info = json.loads(direct).get("vcs_info") or {}
        commit_id = vcs_info.get("commit_id")
        if commit_id:
            return Pin("commit", commit_id)
    return Pin("version", dist.version)


def pin_matches(pin: Pin, installed: Pin) -> bool:
    """True when the installed Pin satisfies the declared one.

    A commit pin matches when the installed commit starts with the pinned
    one (the pin may be abbreviated). A version pin matches on exact
    equality. The kinds must agree — a commit pin is never satisfied by a
    version-only install, and vice versa.
    """
    if pin.kind != installed.kind:
        return False
    if pin.kind == "commit":
        return installed.value.startswith(pin.value)
    return installed.value == pin.value
