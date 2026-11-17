#!/usr/bin/env python3
"""Which source groups the slow gates check.

test_links.py, test_stac_valid.py and test_conformance.py read every STAC
object under catalog/. With every collection built that is hours, more than a
CI job gets. These three gates take a scope from the environment:

- Neither variable set: every group. The default, and what to run before
  publishing.
- ``BDC_SCOPE_GROUPS=at,fr``: those groups. The full CI run uses this, one
  job per group.
- ``BDC_SCOPE_BASE=<git ref>``: the groups with a change under catalog/ since
  the merge base with that ref (committed, uncommitted or untracked), plus
  SAMPLE_GROUPS. PR and push CI use this.

The root's own files (catalog.json, the docs, _assets/) are in every scope. A
group that is out of scope is not read at all: rashid gets a copy of the tree
with only the groups in scope, and a root catalog.json whose child links name
only those groups.

Each gate prints the scope it ran with, so a green run says what it read.

Run ``python3 tests/scope.py --list-json`` to print every group as a JSON list
(the full CI run's matrix).
"""
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

GROUPS_ENV = "BDC_SCOPE_GROUPS"
BASE_ENV = "BDC_SCOPE_BASE"

#: Checked in every scoped run, so a change outside catalog/ (a gate, a
#: checker version in uv.lock) still meets real collections. Small, so they
#: cost little: an ML research set and a harmonized government source.
SAMPLE_GROUPS = ("rw_rwanda_ml", "es_ib")


class ScopeError(Exception):
    """The scope the environment asks for cannot be worked out."""


@dataclass(frozen=True)
class Scope:
    """The groups in scope, out of every group in the catalog."""

    groups: frozenset[str]
    all_groups: frozenset[str]
    reason: str

    def includes(self, rel: Path) -> bool:
        """True when ``rel`` (relative to catalog/) is in scope.

        Root files and directories that are not groups (``_assets/``) always are.
        """
        if len(rel.parts) <= 1:
            return True
        top = rel.parts[0]
        return top in self.groups or top not in self.all_groups

    def describe(self) -> str:
        names = ", ".join(sorted(self.groups)) or "none"
        return (
            f"scope  {len(self.groups)} of {len(self.all_groups)} group(s) and the root"
            f" ({self.reason}): {names}"
        )


def list_groups(catalog: Path) -> list[str]:
    """Every source group: a directory under catalog/ holding a catalog.json."""
    return sorted(
        p.name for p in catalog.iterdir()
        if p.is_dir() and not p.name.startswith(("_", ".")) and (p / "catalog.json").is_file()
    )


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ScopeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def changed_groups(repo: Path, catalog: Path, base: str) -> set[str]:
    """Groups with a file under catalog/ that differs from the merge base with ``base``."""
    merge_base = _git(repo, "merge-base", base, "HEAD").strip()
    rel = str(catalog.relative_to(repo))
    paths = _git(repo, "diff", "--name-only", "--no-renames", merge_base, "--", rel).split()
    paths += _git(repo, "ls-files", "--others", "--exclude-standard", "--", rel).split()
    existing = set(list_groups(catalog))
    out = set()
    for path in paths:
        parts = Path(path).relative_to(rel).parts
        if len(parts) > 1 and parts[0] in existing:
            out.add(parts[0])
    return out


def _named(value: str, all_groups: set[str], what: str) -> set[str]:
    names = {name.strip() for name in value.split(",") if name.strip()}
    unknown = sorted(names - all_groups)
    if unknown:
        raise ScopeError(f"{what} names group(s) not in the catalog: {', '.join(unknown)}")
    return names


def resolve_scope(repo: Path, catalog: Path, env=None) -> Scope | None:
    """The scope the environment asks for, or None for every group."""
    env = os.environ if env is None else env
    all_groups = set(list_groups(catalog))
    groups_value = env.get(GROUPS_ENV, "").strip()
    base = env.get(BASE_ENV, "").strip()
    if groups_value and base:
        raise ScopeError(f"set {GROUPS_ENV} or {BASE_ENV}, not both")
    if groups_value:
        groups = _named(groups_value, all_groups, GROUPS_ENV)
        return Scope(frozenset(groups), frozenset(all_groups), f"{GROUPS_ENV}")
    if base:
        sample = _named(",".join(SAMPLE_GROUPS), all_groups, "SAMPLE_GROUPS")
        changed = changed_groups(repo, catalog, base)
        reason = f"changed since {base}, plus the sample {', '.join(SAMPLE_GROUPS)}"
        return Scope(frozenset(changed | sample), frozenset(all_groups), reason)
    return None


def describe(scope: Scope | None, catalog: Path) -> str:
    if scope is None:
        return f"scope  all {len(list_groups(catalog))} group(s) and the root"
    return scope.describe()


def _link_or_copy(src: str, dst: str) -> None:
    """A hard link where the filesystem allows one (no bytes copied), else a copy."""
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _trim_root(doc: dict, scope: Scope) -> dict:
    """The root catalog with child links to out-of-scope groups removed."""
    def keep(link: dict) -> bool:
        if link.get("rel") != "child":
            return True
        return scope.includes(Path(link.get("href", "")))
    return {**doc, "links": [link for link in doc.get("links", []) if keep(link)]}


@contextlib.contextmanager
def scoped_tree(catalog: Path, scope: Scope | None):
    """Yield catalog/ itself, or a temp copy holding only what ``scope`` includes.

    rashid validates a directory tree and refuses symlinks, so a scoped run
    gets a real tree: hard links (or copies) of the root files, ``_assets/`` and
    each group in scope, and a root catalog.json trimmed to those groups.
    """
    if scope is None:
        yield catalog
        return
    with tempfile.TemporaryDirectory(prefix="bdc-scope-") as tmp:
        root = Path(tmp)
        for entry in sorted(catalog.iterdir()):
            rel = entry.relative_to(catalog)
            if entry.is_dir():
                if scope.includes(rel / "catalog.json"):
                    shutil.copytree(entry, root / rel, copy_function=_link_or_copy)
            elif entry.name == "catalog.json":
                doc = _trim_root(json.loads(entry.read_text()), scope)
                (root / rel).write_text(json.dumps(doc, indent=2) + "\n")
            else:
                _link_or_copy(str(entry), str(root / rel))
        yield root


def gate_scope(repo: Path, catalog: Path) -> Scope | None:
    """The scope for a gate, printed; exits non-zero when it cannot be worked out."""
    try:
        scope = resolve_scope(repo, catalog)
    except ScopeError as exc:
        print(f"error  {exc}")
        raise SystemExit(1) from exc
    print(describe(scope, catalog))
    return scope


if __name__ == "__main__":
    if sys.argv[1:] != ["--list-json"]:
        raise SystemExit("usage: python3 tests/scope.py --list-json")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from common import CATALOG  # noqa: E402

    print(json.dumps(list_groups(CATALOG)))
