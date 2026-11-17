#!/usr/bin/env python3
"""tests/scope.py: which groups the slow gates read, and the tree rashid gets.

Builds a tiny catalog in a throwaway git repo and exercises the scope helper
directly -- no rashid, no stac-check.

Run: python3 tests/test_scope.py
"""
import json
import subprocess
import tempfile
from pathlib import Path

import scope as sc

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc) + "\n")


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo, check=True, capture_output=True,
    )


def build(repo: Path) -> Path:
    """A repo whose catalog/ has groups a, b and the two sample groups."""
    catalog = repo / "catalog"
    groups = ["a", "b", *sc.SAMPLE_GROUPS]
    write_json(catalog / "catalog.json", {
        "type": "Catalog", "id": "root",
        "links": [{"rel": "root", "href": "./catalog.json"}]
        + [{"rel": "child", "href": f"./{g}/catalog.json"} for g in groups],
    })
    (catalog / "README.md").write_text("root\n")
    write_json(catalog / "_assets" / "logo.json", {})
    for g in groups:
        write_json(catalog / g / "catalog.json", {"type": "Catalog", "id": g, "links": []})
        write_json(catalog / g / f"{g}_2024" / "collection.json", {"type": "Collection"})
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "init")
    return catalog


with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    catalog = build(repo)
    everything = set(sc.list_groups(catalog))

    check(everything == {"a", "b", *sc.SAMPLE_GROUPS}, "_assets/ is not a group")
    check(sc.resolve_scope(repo, catalog, env={}) is None, "no variable set means every group")

    named = sc.resolve_scope(repo, catalog, env={sc.GROUPS_ENV: "a, b"})
    check(named.groups == {"a", "b"}, "BDC_SCOPE_GROUPS names the groups")
    check(named.includes(Path("catalog.json")), "the root catalog is in every scope")
    check(named.includes(Path("_assets/logo.json")), "_assets/ is in every scope")
    check(named.includes(Path("a/a_2024/collection.json")), "a file in a named group is in scope")
    check(not named.includes(Path(f"{sc.SAMPLE_GROUPS[0]}/catalog.json")),
          "a group not named is out of scope")

    for env, what in [
        ({sc.GROUPS_ENV: "a,zz"}, "an unknown group"),
        ({sc.GROUPS_ENV: "a", sc.BASE_ENV: "main"}, "both variables"),
        ({sc.BASE_ENV: "no-such-ref"}, "a base ref git cannot find"),
    ]:
        try:
            sc.resolve_scope(repo, catalog, env=env)
            errors.append(f"{what} is refused")
        except sc.ScopeError:
            pass

    unchanged = sc.resolve_scope(repo, catalog, env={sc.BASE_ENV: "main"})
    check(unchanged.groups == set(sc.SAMPLE_GROUPS), "no change means the sample alone")

    git(repo, "checkout", "-q", "-b", "pr")
    write_json(catalog / "a" / "a_2024" / "collection.json", {"type": "Collection", "x": 1})
    git(repo, "commit", "-qam", "change a")
    (catalog / "README.md").write_text("root changed\n")
    write_json(catalog / "b" / "b_2025" / "collection.json", {"type": "Collection"})
    changed = sc.resolve_scope(repo, catalog, env={sc.BASE_ENV: "main"})
    check(changed.groups == {"a", "b", *sc.SAMPLE_GROUPS},
          "committed, uncommitted and untracked changes all count; a root file adds no group")

    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "more")
    git(repo, "checkout", "-q", "-b", "drop-link", "main")
    root_doc = json.loads((catalog / "catalog.json").read_text())
    root_doc["links"] = [l for l in root_doc["links"] if l["href"] != "./b/catalog.json"]
    write_json(catalog / "catalog.json", root_doc)
    dropped = sc.resolve_scope(repo, catalog, env={sc.BASE_ENV: "main"})
    check(dropped.groups == {"b", *sc.SAMPLE_GROUPS},
          "a group whose root child link was removed is in scope")
    git(repo, "checkout", "-q", "--", ".")

    write_json(catalog / "a" / "a 2026" / "collection.json", {"type": "Collection"})
    spaced = sc.resolve_scope(repo, catalog, env={sc.BASE_ENV: "main"})
    check(spaced.groups == {"a", *sc.SAMPLE_GROUPS}, "a path with a space is read whole")

    with sc.scoped_tree(catalog, named) as root:
        check(sorted(p.name for p in root.iterdir())
              == ["README.md", "_assets", "a", "b", "catalog.json"],
              "the scoped tree holds the root files, _assets/ and the named groups only")
        children = [l["href"] for l in json.loads((root / "catalog.json").read_text())["links"]
                    if l["rel"] == "child"]
        check(children == ["./a/catalog.json", "./b/catalog.json"],
              "the root's child links are trimmed to the groups in scope")
        check(any(l["rel"] == "root" for l in json.loads((root / "catalog.json").read_text())["links"]),
              "links other than child are kept")
        check((root / "a" / "a_2024" / "collection.json").read_text()
              == (catalog / "a" / "a_2024" / "collection.json").read_text(),
              "group files are copied unchanged")
        scoped_root = root
    check(not scoped_root.exists(), "the scoped tree is removed afterwards")
    check(json.loads((catalog / "catalog.json").read_text())["links"][-1]["rel"] == "child",
          "the real root catalog is not touched")

    with sc.scoped_tree(catalog, None) as root:
        check(root == catalog, "no scope means catalog/ itself")

    check("2 of 4" in sc.describe(named, catalog), "the scope line counts the groups")
    check("all 4" in sc.describe(None, catalog), "the full scope says so")

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: scope picks named or changed groups plus the sample, and trims the tree rashid reads")
