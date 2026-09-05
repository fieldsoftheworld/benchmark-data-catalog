#!/usr/bin/env python3
"""Portolan conformance gate, via rashid.

Fails on any error-severity finding whose rule is not in ACCEPTED.

ACCEPTED ships empty, and the rule for growing it is not negotiable: every
entry needs a row in docs/conformance.md giving the rule, where it fires, why
it is accepted, and the issue tracking its removal. A known deviation with an
issue number is a debt. A silently widened allow-list is a lie about what this
catalog conforms to.

Runs with --no-data. The byte checks read every asset, which over remote hrefs
makes CI slow and dependent on a third-party host being up. Run the full check
yourself before publishing:

    rashid check catalog/

Fails when rashid is absent, or when its version is outside the required range.
A skip reports a green run for a catalog that no validator read. The failure
message gives the one command that installs a usable rashid.

A committed sub-catalog's `rel: item` links point at item JSON that lives only
in staging/ (see tests/overlay.py). Once any collection is built and its item
tree exists there, rashid runs against a temp overlay of catalog/ with that
JSON copied in, so those links resolve; otherwise (CI, and the skeleton with
no collections yet) it runs against catalog/ unchanged, as before.

## CI_LIGHT metadata-only waiver

CI runs with CI_LIGHT=1 on a checkout that has no staging/ at all, so rashid
sees the committed tree alone (catalog/ only mode, above) and reports two
findings on every built collection that are true only because of that: a
committed sub-catalog's `rel: item` links can't resolve (PTL-LNK-006, the
items are bucket-only) and the collection's item mirror has no items behind
it (PTL-COL-005). Both are artifacts of the light checkout, not real defects
— the overlay run (catalog/ + staged item JSON) sees the items and both
rules stay blocking there, as does any run without CI_LIGHT.

``CI_LIGHT_WAIVED`` is a separate mechanism from ``ACCEPTED`` on purpose:
nothing is ever added to ``ACCEPTED`` for this (that set stays reserved for
genuine, tracked deviations documented in docs/conformance.md). The waiver
fires only for these two rules, only in catalog/ only mode, only under
CI_LIGHT, and only for the exact shape each rule takes here — see
``is_ci_light_metadata_only``. Tracked at
https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1.

Set ``BDC_STAGING_DIR`` (read by ``tests/overlay.py``) to a directory that
does not exist to simulate, locally, the CI checkout that has no staging/ at
all — without touching the real staging/ tree:

    CI_LIGHT=1 BDC_STAGING_DIR=/nonexistent uv run python tests/test_conformance.py

Run: python3 tests/test_conformance.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from common import CATALOG, STAGING  # noqa: E402

from overlay import has_staging_items, resolve_target  # noqa: E402

ACCEPTED: set[str] = set()

CI_LIGHT = os.environ.get("CI_LIGHT") == "1"

# The two metadata-only findings CI_LIGHT waives in catalog/ only mode. This
# is NOT the ACCEPTED mechanism above: it only ever waives the exact shapes
# is_ci_light_metadata_only checks for, and only under CI_LIGHT + catalog/
# only mode. Tracked at
# https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1 (see
# docs/conformance.md).
CI_LIGHT_WAIVED = {"PTL-LNK-006", "PTL-COL-005"}

# A committed sub-catalog: "<id>/chips/<square>/catalog.json".
_SUBCATALOG_PATH_RE = re.compile(r"^[^/]+/chips/[^/]+/catalog\.json$")

# A dataset's own collection: "<id>/collection.json" (never a sub-catalog,
# which is named catalog.json, not collection.json).
_COLLECTION_PATH_RE = re.compile(r"^[^/]+/collection\.json$")


def is_ci_light_metadata_only(finding: dict, *, ci_light: bool, catalog_only: bool) -> bool:
    """True when ``finding`` is one of the two CI_LIGHT metadata-only findings.

    Requires both ``ci_light`` and ``catalog_only``; either shape below in
    overlay mode, or with CI_LIGHT unset, is never waived. The two shapes:

    - PTL-LNK-006 on a committed sub-catalog's own path
      (``<id>/chips/<square>/catalog.json``) whose message concerns a
      ``rel:'item'`` link.
    - PTL-COL-005 on a dataset's own collection path (``<id>/collection.json``).
    """
    if not (ci_light and catalog_only):
        return False
    rule_id = finding.get("rule_id")
    if rule_id not in CI_LIGHT_WAIVED:
        return False
    path = finding.get("path") or ""
    message = finding.get("message") or ""
    if rule_id == "PTL-LNK-006":
        return bool(_SUBCATALOG_PATH_RE.match(path)) and "rel:'item'" in message
    return bool(_COLLECTION_PATH_RE.match(path))  # PTL-COL-005


def _self_check(condition: bool, message: str) -> None:
    if not condition:
        _self_test_errors.append(f"self-test: {message}")


def _self_test_is_ci_light_metadata_only() -> None:
    """Exercise is_ci_light_metadata_only on synthetic finding dicts.

    Proves the two waived shapes, the two near-miss shapes that must not
    match, and that ci_light=False (or catalog_only=False) waives nothing —
    without needing a real rashid run.
    """
    item_link_finding = {
        "rule_id": "PTL-LNK-006",
        "severity": "error",
        "path": "lu/chips/32UNA/catalog.json",
        "message": "link rel:'item' href './ftw-1/ftw-1.json' does not resolve to any file",
    }
    mirror_finding = {
        "rule_id": "PTL-COL-005",
        "severity": "error",
        "path": "lu/collection.json",
        "message": "collection registers item mirror 'items' but publishes no items; "
        "the mirror is a derived copy and the item JSON remains the normative representation",
    }
    non_item_link_finding = {
        "rule_id": "PTL-LNK-006",
        "severity": "error",
        "path": "lu/chips/32UNA/catalog.json",
        "message": "link rel:'parent' href '../../catalog.json' must point to the containing object",
    }
    subcatalog_mirror_finding = {
        "rule_id": "PTL-COL-005",
        "severity": "error",
        "path": "lu/chips/32UNA/catalog.json",
        "message": "collection registers item mirror 'items' but publishes no items",
    }

    _self_check(
        is_ci_light_metadata_only(item_link_finding, ci_light=True, catalog_only=True),
        "a PTL-LNK-006 rel:'item' finding on a sub-catalog is waived under CI_LIGHT in catalog/ only mode",
    )
    _self_check(
        is_ci_light_metadata_only(mirror_finding, ci_light=True, catalog_only=True),
        "a PTL-COL-005 finding on the collection is waived under CI_LIGHT in catalog/ only mode",
    )
    _self_check(
        not is_ci_light_metadata_only(non_item_link_finding, ci_light=True, catalog_only=True),
        "a PTL-LNK-006 finding on a non-item link is never waived",
    )
    _self_check(
        not is_ci_light_metadata_only(subcatalog_mirror_finding, ci_light=True, catalog_only=True),
        "a PTL-COL-005 finding on a sub-catalog path is never waived",
    )
    _self_check(
        not is_ci_light_metadata_only(item_link_finding, ci_light=False, catalog_only=True),
        "nothing is waived once CI_LIGHT is unset, even in catalog/ only mode",
    )
    _self_check(
        not is_ci_light_metadata_only(mirror_finding, ci_light=False, catalog_only=True),
        "nothing is waived once CI_LIGHT is unset, even in catalog/ only mode (PTL-COL-005)",
    )
    _self_check(
        not is_ci_light_metadata_only(item_link_finding, ci_light=True, catalog_only=False),
        "nothing is waived in overlay mode, even under CI_LIGHT",
    )
    _self_check(
        not is_ci_light_metadata_only(mirror_finding, ci_light=True, catalog_only=False),
        "nothing is waived in overlay mode, even under CI_LIGHT (PTL-COL-005)",
    )


_self_test_errors: list[str] = []
_self_test_is_ci_light_metadata_only()
if _self_test_errors:
    print("\n".join(f"error  {e}" for e in _self_test_errors))
    raise SystemExit(1)
print("self-test ok  is_ci_light_metadata_only: both waived shapes, both near-misses, ci_light/catalog_only gating")

# The floor comes from portolan-cli/pyproject.toml:54. Rules PTL-LNK-007,
# PTL-LNK-008, PTL-LNK-009 and PTL-AST-006 do not exist below rashid 0.1.5.
# This gate asserts all four. A rashid below the floor reports a pass for a
# catalog that it never checked against those four rules. The upper bound stops
# an unreviewed 0.2 rule set from changing what this gate means.
MIN_VERSION = (0, 1, 5)
MAX_VERSION = (0, 2, 0)
SPEC = "rashid>=0.1.5,<0.2.0"
INSTALL = f"python -m pip install '{SPEC}'"


def fail(message: str) -> None:
    """Report the problem, name the fix, and exit non-zero."""
    print(f"error  {message}")
    print(f"       install a usable rashid with: {INSTALL}")
    raise SystemExit(1)


def rashid_version() -> tuple[int, ...]:
    """The version that rashid reports, as a tuple of integers."""
    try:
        proc = subprocess.run(
            ["rashid", "--version"], capture_output=True, text=True
        )
    except OSError as exc:
        fail(f"rashid --version did not run ({exc})")
    if proc.returncode != 0:
        fail(f"rashid --version exited {proc.returncode}")
    # rashid 0.1.6 prints "rashid, version 0.1.6". Read the first X.Y.Z in the
    # output, and fail on a string with no version in it. A gate that cannot
    # read the version must not assume the version is good.
    text = (proc.stdout + proc.stderr).strip()
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if match is None:
        fail(f"rashid --version printed no readable version: {text!r}")
    return tuple(int(part) for part in match.groups())


if shutil.which("rashid") is None:
    fail("rashid is not installed, so this gate checks nothing")

version = rashid_version()
shown = ".".join(str(part) for part in version)
if not MIN_VERSION <= version < MAX_VERSION:
    fail(f"rashid {shown} is outside the required range {SPEC}")

with resolve_target(CATALOG, STAGING) as target:
    result = subprocess.run(
        ["rashid", "check", str(target), "--no-data", "--json"],
        capture_output=True,
        text=True,
    )

# Same has_staging_items check resolve_target just made its overlay/catalog-
# only decision on (and the same BDC_STAGING_DIR override, applied inside
# it) — not: whether staging/ exists, but whether it has any item tree.
catalog_only = not has_staging_items(CATALOG, STAGING)

try:
    report = json.loads(result.stdout)
except json.JSONDecodeError:
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    raise SystemExit("rashid produced no JSON report")

findings = report.get("findings", [])
errors_ = [f for f in findings if f.get("severity") == "error"]
candidates = [f for f in errors_ if f.get("rule_id") not in ACCEPTED]
ci_light_waived = [
    f for f in candidates if is_ci_light_metadata_only(f, ci_light=CI_LIGHT, catalog_only=catalog_only)
]
# id()-keyed, not `f not in ci_light_waived`: that linear scan over unhashable
# dicts is quadratic in the finding count, which is fine at Luxembourg's
# scale but minutes of wasted CI time once Austria's ~9,700 findings land.
_waived_ids = {id(f) for f in ci_light_waived}
blocking = [f for f in candidates if id(f) not in _waived_ids]

for finding in blocking:
    where = finding.get("path", "?")
    print(f"error  {finding.get('rule_id')}  {where}: {finding.get('message')}")
    if finding.get("fix_hint"):
        print(f"       hint: {finding['fix_hint']}")

waived = [f for f in errors_ if f.get("rule_id") in ACCEPTED]
if waived:
    print(f"\n{len(waived)} accepted finding(s); see docs/conformance.md")

if ci_light_waived:
    print(
        f"waived {len(ci_light_waived)} metadata-only finding(s) under CI_LIGHT; "
        "see docs/conformance.md and "
        "https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1"
    )

if blocking:
    raise SystemExit(1)
print(
    f"OK: rashid {shown} found no blocking errors in {CATALOG.relative_to(ROOT)}/"
)
