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

# The Portolan profile version this catalog is migrated to and generates
# against (PORTO-CORE-006: every catalog and collection MUST declare the
# versioned schema URI). ftw_dataset_tools.api.stac.PORTOLAN_SCHEMA_URI tracks
# whatever version is bundled with the pinned ftwd commit (v0.1.2 as of the
# pin in pyproject.toml) — its own Portolan conformance work is still an open
# PR there (see the pyproject.toml comment on the pin), so this repo cannot
# just import its constant and get v0.3.0. Pinning the target version here,
# the way the skill's reference generators do, makes the choice explicit and
# lets catalogize.py overrule whatever older URI ftwd/an older catalogize run
# wrote. Bump this when the catalog's target spec version changes, and bump
# ftwd's pin (and drop this override) once its own PR lands.
PORTOLAN_SCHEMA_URI = "https://schemas.portolan-sdi.org/portolan/v0.3.0/schema.json"


def canonicalize_portolan_schema(doc: dict) -> bool:
    """Replace any declared Portolan schema URI in ``doc`` with ``PORTOLAN_SCHEMA_URI``.

    Only replaces an existing entry (whatever version ftwd or an older
    catalogize run stamped); never adds a declaration to an object that
    carries none. Whether a chip sub-catalog
    (``catalog/<source>/<id>/chips/<square>/catalog.json``) declares the
    Portolan extension at all varies by the ftwd version that built it
    (verified: every one of fi's lacks it, every one of wri_trazo_ml's has
    it); rashid 0.4.0 reports no finding either way (PORTO-CORE-006 says
    every catalog MUST declare it, but the validator does not check
    intermediate browsing sub-catalogs at that granularity today — see
    docs/conformance.md). Returns whether anything changed, so a caller can
    skip a rewrite.
    """
    extensions = doc.get("stac_extensions")
    if not isinstance(extensions, list):
        return False
    changed = False
    for i, entry in enumerate(extensions):
        if isinstance(entry, str) and PORTOLAN_SCHEMA_RE.fullmatch(entry) and entry != PORTOLAN_SCHEMA_URI:
            extensions[i] = PORTOLAN_SCHEMA_URI
            changed = True
    return changed

def public_url(rel: str) -> str:
    """The public URL for ``rel``, joined onto ``public_base``."""
    return _config["public_base"].rstrip("/") + "/" + rel


# --- where a dataset sits: catalog/<source>/<id>/ and <prefix>/<source>/<id>/ --

# A recipe's ``source_via``: the harmonized collection's JSON endpoint. Its
# collection id names the group folder every benchmark cut from it sits in.
SOURCE_VIA_RE = re.compile(
    r"^https://data\.source\.coop/(?P<org>[^/]+)/(?P<repo>[^/]+)/(?P<id>[^/]+)/collection\.json$"
)


class LayoutError(SystemExit):
    """A dataset whose place in the catalog cannot be worked out."""


def source_group(source_via: str | None) -> str | None:
    """The group folder for a ``source_via`` URL: the harmonized collection id, or None."""
    match = SOURCE_VIA_RE.match(source_via or "")
    return match.group("id") if match else None


def recipe_group(dataset_id: str, root: Path = ROOT) -> str:
    """The group ``datasets/<id>.yaml`` puts the dataset in, from its ``source_via``."""
    import yaml

    path = root / "datasets" / f"{dataset_id}.yaml"
    if not path.is_file():
        raise LayoutError(f"{dataset_id}: no datasets/{dataset_id}.yaml to place it by")
    group = source_group((yaml.safe_load(path.read_text()) or {}).get("source_via"))
    if not group:
        raise LayoutError(
            f"{dataset_id}: datasets/{dataset_id}.yaml has no harmonized source_via "
            "(https://data.source.coop/<org>/<repo>/<id>/collection.json) to group it under"
        )
    return group


def published_collections(catalog: Path = CATALOG) -> dict[str, Path]:
    """``{dataset id: collection.json}`` for every collection under ``catalog/<source>/``."""
    found: dict[str, Path] = {}
    for path in sorted(catalog.glob("*/*/collection.json")):
        dataset_id = path.parent.name
        if dataset_id in found:
            raise LayoutError(
                f"{dataset_id} is published twice: {found[dataset_id].parent} and {path.parent}"
            )
        found[dataset_id] = path
    return found


def dataset_relpath(dataset_id: str, *, catalog: Path = CATALOG, root: Path = ROOT) -> str:
    """``<source>/<id>``: where the dataset sits under ``catalog/`` and the bucket prefix.

    A published dataset stays where ``catalog/`` already has it; a new one goes
    under the group its recipe's ``source_via`` names. ``staging/<id>/`` stays flat.
    """
    found = sorted(catalog.glob(f"*/{dataset_id}/collection.json"))
    if len(found) > 1:
        raise LayoutError(f"{dataset_id} is published twice: {[str(p.parent) for p in found]}")
    if found:
        return f"{found[0].parent.parent.name}/{dataset_id}"
    return f"{recipe_group(dataset_id, root)}/{dataset_id}"


def dataset_dir(dataset_id: str, *, catalog: Path = CATALOG, root: Path = ROOT) -> Path:
    """``catalog/<source>/<id>``."""
    return catalog / dataset_relpath(dataset_id, catalog=catalog, root=root)


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
