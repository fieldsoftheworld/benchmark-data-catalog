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
- ``BDC_SCOPE_DATASETS=at_2024,fr_2023``: those collections, plus every
  group's own files (catalog.json, README, AGENTS), which ``catalogize.py
  --root`` rewrites on every batch; no other collection. tools/run_batch.py
  uses this: a builder holds staging only for its own batch, so the other
  collections in a group would fail the overlay checks there.

Only one of the three may be set.

The root's own files (catalog.json, the docs, _assets/) are in every scope. A
group that is out of scope is not read at all: rashid gets a copy of the tree
with only the groups in scope, and a root catalog.json whose child links name
only those groups.

Each gate prints the scope it ran with, so a green run says what it read.

Run ``python3 tests/scope.py --groups-json`` to print the groups in scope as a
JSON list (every group when no variable is set). CI runs one job per group in
that list, so a change that touches every group does not become one long job.

Limits, by design: no run checks the untrimmed root against every group at
once. Nothing needs that today: there are no relative links between groups,
and rashid has no rule across groups. A cross-group link would show up as a
spurious PTL-LNK-006 in a scoped run, which is the cue to revisit this.
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
DATASETS_ENV = "BDC_SCOPE_DATASETS"

#: Checked in every scoped run, so a change outside catalog/ (a gate, a
#: checker version in uv.lock) still meets real collections. Small, so they
#: cost little: an ML research set and a harmonized government source.
SAMPLE_GROUPS = ("rw_rwanda_ml", "es_ib")


class ScopeError(Exception):
    """The scope the environment asks for cannot be worked out."""


@dataclass(frozen=True)
class Scope:
    """The groups in scope, out of every group in the catalog.

    ``datasets``, when set, narrows each group to those collections.
    """

    groups: frozenset[str]
    all_groups: frozenset[str]
    reason: str
    datasets: frozenset[str] | None = None

    def includes(self, rel: Path) -> bool:
        """True when ``rel`` (relative to catalog/) is in scope.

        Root files and directories that are not groups (``_assets/``) always are.
        """
        if len(rel.parts) <= 1:
            return True
        top = rel.parts[0]
        if top not in self.all_groups:
            return True
        if self.datasets is not None:
            # A group's own files are always read: catalogize --root rewrites
            # every group's, whichever datasets a batch built.
            return len(rel.parts) == 2 or (top in self.groups and rel.parts[1] in self.datasets)
        return top in self.groups

    def describe(self) -> str:
        if self.datasets is not None:
            return (
                f"scope  {len(self.datasets)} dataset(s), every group's own files and the root"
                f" ({self.reason}): {', '.join(sorted(self.datasets))}"
            )
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


def _child_groups(doc: dict) -> set[str]:
    """The first path segment of every child link in a root catalog."""
    return {
        Path(link.get("href", "")).parts[0]
        for link in doc.get("links", [])
        if link.get("rel") == "child" and Path(link.get("href", "")).parts
    }


def _root_link_changes(repo: Path, catalog: Path, merge_base: str) -> set[str]:
    """Groups whose child link the root catalog gained or lost since ``merge_base``.

    Dropping the root's link to a group is an error rashid only reports on a
    tree that holds that group, so the group has to be in scope.
    """
    rel = (catalog / "catalog.json").relative_to(repo).as_posix()
    proc = subprocess.run(
        ["git", "show", f"{merge_base}:{rel}"], cwd=repo, capture_output=True, text=True
    )
    before = _child_groups(json.loads(proc.stdout)) if proc.returncode == 0 else set()
    now_path = catalog / "catalog.json"
    now = _child_groups(json.loads(now_path.read_text())) if now_path.is_file() else set()
    return before ^ now


def changed_groups(repo: Path, catalog: Path, base: str) -> set[str]:
    """Groups that differ from the merge base with ``base``.

    A group is changed when a file under it changed (committed, uncommitted or
    untracked), or when the root catalog's child link to it was added or removed.
    """
    merge_base = _git(repo, "merge-base", base, "HEAD").strip()
    rel = catalog.relative_to(repo).as_posix()
    paths = _git(repo, "diff", "-z", "--name-only", "--no-renames", merge_base, "--", rel)
    paths += _git(repo, "ls-files", "-z", "--others", "--exclude-standard", "--", rel)
    tops = {
        Path(path).relative_to(rel).parts[0]
        for path in paths.split("\0")
        if path and len(Path(path).relative_to(rel).parts) > 1
    }
    tops |= _root_link_changes(repo, catalog, merge_base)
    return tops & set(list_groups(catalog))


def _named(value: str, all_groups: set[str], what: str) -> set[str]:
    names = {name.strip() for name in value.split(",") if name.strip()}
    unknown = sorted(names - all_groups)
    if unknown:
        raise ScopeError(f"{what} names group(s) not in the catalog: {', '.join(unknown)}")
    return names


def _dataset_scope(catalog: Path, value: str, all_groups: set[str]) -> Scope:
    """The collections ``value`` names, each in the group that holds it."""
    datasets = {name.strip() for name in value.split(",") if name.strip()}
    groups, unknown = set(), []
    for dataset_id in sorted(datasets):
        found = [p.parent.parent.name for p in catalog.glob(f"*/{dataset_id}/collection.json")]
        if len(found) != 1:
            unknown.append(dataset_id)
        groups.update(found)
    if unknown:
        raise ScopeError(
            f"{DATASETS_ENV} names dataset(s) not in the catalog once: {', '.join(unknown)}"
        )
    return Scope(frozenset(groups), frozenset(all_groups), DATASETS_ENV, frozenset(datasets))


def resolve_scope(repo: Path, catalog: Path, env=None) -> Scope | None:
    """The scope the environment asks for, or None for every group."""
    env = os.environ if env is None else env
    all_groups = set(list_groups(catalog))
    groups_value = env.get(GROUPS_ENV, "").strip()
    base = env.get(BASE_ENV, "").strip()
    datasets_value = env.get(DATASETS_ENV, "").strip()
    if sum(map(bool, (groups_value, base, datasets_value))) > 1:
        raise ScopeError(f"set one of {GROUPS_ENV}, {BASE_ENV} and {DATASETS_ENV}")
    if datasets_value:
        return _dataset_scope(catalog, datasets_value, all_groups)
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


def _trim(doc: dict, scope: Scope, here: Path) -> dict:
    """A catalog at ``here`` (relative to catalog/) without child links out of scope."""
    def keep(link: dict) -> bool:
        if link.get("rel") != "child":
            return True
        return scope.includes(here / link.get("href", ""))
    return {**doc, "links": [link for link in doc.get("links", []) if keep(link)]}


def _copy_level(src: Path, dest: Path, here: Path, scope: Scope) -> None:
    """Copy one level (the root or a group) of the tree, as ``scope`` includes it.

    Its catalog.json is trimmed; a directory below it is copied whole when in
    scope, except a group, which is copied level by level the same way.
    """
    dest.mkdir(exist_ok=True)
    for entry in sorted(src.iterdir()):
        rel = here / entry.name
        if entry.is_dir():
            if not scope.includes(rel / "catalog.json"):
                continue
            if here == Path(".") and entry.name in scope.all_groups and scope.datasets is not None:
                _copy_level(entry, dest / entry.name, rel, scope)
            else:
                shutil.copytree(entry, dest / entry.name, copy_function=_link_or_copy)
        elif entry.name == "catalog.json":
            doc = _trim(json.loads(entry.read_text()), scope, here)
            (dest / entry.name).write_text(json.dumps(doc, indent=2) + "\n")
        else:
            _link_or_copy(str(entry), str(dest / entry.name))


@contextlib.contextmanager
def scoped_tree(catalog: Path, scope: Scope | None):
    """Yield catalog/ itself, or a temp copy holding only what ``scope`` includes.

    rashid validates a directory tree and refuses symlinks, so a scoped run
    gets a real tree: hard links (or copies) of the root files, ``_assets/`` and
    what is in scope of each group, with each catalog.json's child links
    trimmed to match.
    """
    if scope is None:
        yield catalog
        return
    with tempfile.TemporaryDirectory(prefix="bdc-scope-") as tmp:
        _copy_level(catalog, Path(tmp), Path("."), scope)
        yield Path(tmp)


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
    if sys.argv[1:] != ["--groups-json"]:
        raise SystemExit("usage: python3 tests/scope.py --groups-json")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from common import CATALOG, ROOT  # noqa: E402

    try:
        chosen = resolve_scope(ROOT, CATALOG)
    except ScopeError as exc:
        raise SystemExit(f"error  {exc}") from exc
    groups = list_groups(CATALOG) if chosen is None else sorted(chosen.groups)
    print(json.dumps(groups))
