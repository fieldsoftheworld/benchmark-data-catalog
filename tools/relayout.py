#!/usr/bin/env python3
"""Move flat ``catalog/<id>/`` collections into source groups, ``catalog/<source>/<id>/``.

One-off migration for the grouping decided on 2026-11-14: one folder per
harmonized source collection (its ``source_via`` id), with a group catalog,
README.md and AGENTS.md in each. For every dataset still at ``catalog/<id>/``:

1. ``git mv catalog/<id> catalog/<source>/<id>``.

Then, for every grouped dataset (so a run that stopped half way is finished by
the next one):

2. every ``root`` link in its committed JSON is set from the file's own depth
   below ``catalog/`` (the collection's ``parent`` stays ``../catalog.json``,
   now the group);
3. every published URL naming ``<base>/<id>`` in its committed files, and in
   the root README.md, AGENTS.md and llms.txt, becomes ``<base>/<source>/<id>``.

Then each group's catalog and docs are written (``catalogize.write_group``) and
the root catalog's child links point at the groups. Nothing is re-measured, so
the root tables keep their numbers on a machine without staging. Nothing is
uploaded: ``--bucket-plan`` splits a bucket listing into the keys to copy
server-side and the keys to upload again, and executes nothing.

    uv run python tools/relayout.py            # dry run: what would move
    uv run python tools/relayout.py --confirm  # move, rewrite, regenerate the groups
    uv run python tools/relayout.py --bucket-plan keys.txt   # copy / re-upload lists
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    CATALOG,
    PUBLIC_BASE,
    ROOT,
    published_collections,
    read_json,
    recipe_group,
    write_json,
)

# Committed text files whose published URLs name the dataset's folder.
_TEXT_SUFFIXES = {".json", ".md", ".txt"}
# Root files that link every collection by URL.
_ROOT_DOCS = ("README.md", "AGENTS.md", "llms.txt")
# Bucket objects the move leaves byte for byte as they are, so a server-side copy
# suffices: rasters, previews, tiles and GeoParquet. Everything else (JSON, docs,
# llms.txt, the items mirror whose links are public URLs) changes with the move
# and is uploaded again from the relaid-out catalog/ and a re-catalogized staging.
_COPY_SUFFIXES = (".tif", ".tiff", ".pmtiles", ".webp", ".jpg", ".jpeg", ".laz", ".parquet")
_REWRITTEN_NAMES = ("items.parquet",)


@dataclass(frozen=True)
class Move:
    dataset_id: str
    group: str

    @property
    def new_rel(self) -> str:
        return f"{self.group}/{self.dataset_id}"


def flat_datasets(catalog: Path = CATALOG) -> list[str]:
    """Datasets still at ``catalog/<id>/collection.json``."""
    return sorted(p.parent.name for p in catalog.glob("*/collection.json"))


def plan(catalog: Path = CATALOG, root: Path = ROOT) -> list[Move]:
    """One Move per flat dataset, grouped by its recipe's ``source_via``.

    Refuses a group name that is also a dataset id, so a group folder can never
    land on top of a collection.
    """
    moves = [Move(dataset_id, recipe_group(dataset_id, root)) for dataset_id in flat_datasets(catalog)]
    clash = sorted({m.group for m in moves} & {m.dataset_id for m in moves})
    if clash:
        sys.exit(f"source group name(s) {clash} are also dataset ids")
    return moves


def _url_bases(manifest: dict) -> list[str]:
    """Every base a published URL to a dataset folder starts with."""
    from catalogize import BROWSER_BASE

    human = ((manifest.get("catalog") or {}).get("human_base") or "").rstrip("/")
    public = PUBLIC_BASE.rstrip("/")
    bases = [public, BROWSER_BASE + public.split("://", 1)[-1]]
    return [*bases, human] if human else bases


def rewrite_urls(text: str, moves: list[Move], bases: list[str]) -> str:
    """``<base>/<id>`` becomes ``<base>/<source>/<id>`` for every moved dataset.

    Matches the dataset id as a whole path segment only (followed by ``/``,
    ``)``, ``]``, ``>``, a quote, a backtick, ``#``, ``,``, ``.``, whitespace or
    the end), so ``lv_2020`` never matches inside ``lv_2020x`` and an
    already-moved URL is not moved again.
    """
    targets = {m.dataset_id: m.new_rel for m in moves}
    if not targets:
        return text
    for base in bases:
        pattern = re.compile(
            re.escape(base + "/") + "(" + "|".join(map(re.escape, targets)) + r")(?=[/)\]>\"'`#,.\s]|$)"
        )
        text = pattern.sub(lambda match, b=base: f"{b}/{targets[match.group(1)]}", text)
    return text


def _set_root_links(doc: dict, depth: int) -> None:
    """Every ``root`` link points ``depth`` folders up, at ``catalog/catalog.json``."""
    for link in doc.get("links", []):
        if link.get("rel") == "root":
            link["href"] = "../" * depth + "catalog.json"


def rewrite_dataset(
    dataset_dir: Path, moves: list[Move], bases: list[str], catalog: Path = CATALOG
) -> list[Path]:
    """Root links from each file's depth, and moved URLs, in one dataset's committed files.

    Idempotent, and independent of the state a previous run left: the root
    link depth comes from where the file sits, not from what it said before.
    Returns the files that changed.
    """
    written = []
    for path in sorted(p for p in dataset_dir.rglob("*") if p.suffix in _TEXT_SUFFIXES):
        text = path.read_text()
        new = text
        if path.suffix == ".json" and "styles" not in path.relative_to(dataset_dir).parts:
            doc = read_json(path)
            if isinstance(doc, dict) and doc.get("type") in {"Catalog", "Collection"}:
                _set_root_links(doc, len(path.relative_to(catalog).parts) - 1)
                new = json.dumps(doc, indent=2) + "\n"
        new = rewrite_urls(new, moves, bases)
        if new != text:
            path.write_text(new)
            written.append(path)
    return written


def _git_mv(src: Path, dst: Path, root: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "mv", str(src), str(dst)], cwd=root, check=True)


def _root_child_links(catalog: Path, groups: list[str]) -> None:
    from catalogize import _child_links

    path = catalog / "catalog.json"
    doc = read_json(path)
    children = [
        (f"./{group}/catalog.json", read_json(catalog / group / "catalog.json")["title"])
        for group in groups
    ]
    doc["links"] = [link for link in doc["links"] if link.get("rel") != "child"] + _child_links(children)
    write_json(path, doc)


def apply(
    moves: list[Move], *, manifest: dict, catalog: Path = CATALOG, root: Path = ROOT,
    move=_git_mv, fetch_title=None,
) -> list[Path]:
    """Move, rewrite and regroup. Returns the files written (moves excluded).

    Dataset files and root docs count only when they changed; the group files
    and the root catalog are always rewritten (byte-identical on a rerun).
    """
    from catalogize import fetch_collection_title, write_group

    bases = _url_bases(manifest)
    written: list[Path] = []
    for m in moves:
        move(catalog / m.dataset_id, catalog / m.new_rel, root)
    # Every grouped dataset, not just this run's: a run that stopped after a move
    # left that dataset unrewritten, and this finishes it.
    grouped = [
        Move(dataset_id, path.parent.parent.name)
        for dataset_id, path in published_collections(catalog).items()
    ]
    for m in grouped:
        written += rewrite_dataset(catalog / m.new_rel, grouped, bases, catalog)
    for name in _ROOT_DOCS:
        path = catalog / name
        if path.is_file():
            before = path.read_text()
            text = rewrite_urls(before, grouped, bases)
            for base in bases:  # the hand-written "<base>/<id>/AGENTS.md" placeholders
                text = text.replace(f"{base}/<id>/", f"{base}/<source>/<id>/")
            if text != before:
                path.write_text(text)
                written.append(path)
    groups = sorted({p.parent.parent.name for p in catalog.glob("*/*/collection.json")})
    for group in groups:
        written += write_group(
            group, catalog=catalog, manifest=manifest,
            fetch_title=fetch_title or fetch_collection_title,
        )
    _root_child_links(catalog, groups)
    written.append(catalog / "catalog.json")
    return written


# --- the bucket: old flat keys to new grouped keys (planning only) ------------


def new_key(key: str, groups: dict[str, str], prefix: str) -> str | None:
    """``<prefix>/<id>/rest`` as ``<prefix>/<source>/<id>/rest``; None for a key outside a dataset."""
    head = f"{prefix.rstrip('/')}/" if prefix else ""
    if not key.startswith(head):
        return None
    dataset_id, sep, rest = key[len(head):].partition("/")
    if not sep or dataset_id not in groups:
        return None
    return f"{head}{groups[dataset_id]}/{dataset_id}/{rest}"


def bucket_moves(keys, groups: dict[str, str], prefix: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """``(copy, reupload)`` pairs of (old key, new key) for every key inside a moved dataset.

    ``copy`` holds only the objects the move leaves byte-identical (rasters,
    previews, PMTiles, GeoParquet other than the items mirror), for a
    server-side CopyObject. ``reupload`` holds everything else (item JSON,
    sub-catalogs, every README/AGENTS/llms.txt, the items mirror): upload those
    from the relaid-out catalog/ and a re-catalogized staging. Keys outside a
    moved dataset are left out of both.
    """
    copy: list[tuple[str, str]] = []
    reupload: list[tuple[str, str]] = []
    for key in keys:
        target = new_key(key, groups, prefix)
        if target is None:
            continue
        name = key.rsplit("/", 1)[-1]
        unchanged = name.lower().endswith(_COPY_SUFFIXES) and name not in _REWRITTEN_NAMES
        (copy if unchanged else reupload).append((key, target))
    return copy, reupload


def dataset_groups(catalog: Path = CATALOG, root: Path = ROOT) -> dict[str, str]:
    """``{dataset id: source group}`` for every collection, flat or already grouped."""
    groups = {m.dataset_id: m.group for m in plan(catalog, root)}
    groups.update({p.parent.name: p.parent.parent.name for p in catalog.glob("*/*/collection.json")})
    return groups


def write_bucket_plan(keys_file: Path, prefix: str, groups: dict[str, str]) -> tuple[Path, Path]:
    """Split a listing (one key per line) into ``<keys_file>.copy.tsv`` and ``.reupload.tsv``.

    Each line is ``old key<TAB>new key``. Planning only: nothing is read from or
    written to the bucket.
    """
    keys = [line.strip() for line in keys_file.read_text().splitlines() if line.strip()]
    copy, reupload = bucket_moves(keys, groups, prefix)
    outputs = []
    for name, pairs in (("copy", copy), ("reupload", reupload)):
        out = keys_file.with_name(f"{keys_file.name}.{name}.tsv")
        out.write_text("".join(f"{old}\t{new}\n" for old, new in pairs))
        outputs.append(out)
    print(f"{len(keys):,} key(s): {len(copy):,} to copy server-side, {len(reupload):,} to upload "
          f"again, {len(keys) - len(copy) - len(reupload):,} outside any dataset")
    for out in outputs:
        print(f"  wrote {out}")
    return outputs[0], outputs[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--confirm", action="store_true", help="move and rewrite (default: dry run)")
    parser.add_argument(
        "--prefix", metavar="PREFIX",
        help="the prefix the listed keys start with (default: write_prefix's, e.g. "
             "benchmark-data; ftw/benchmark-data for a listing of the anonymous read bucket)",
    )
    parser.add_argument(
        "--bucket-plan", type=Path, metavar="KEYS_FILE",
        help="split a bucket listing (one key per line) into copy and re-upload lists; "
             "executes nothing",
    )
    args = parser.parse_args(argv)

    from common import load_manifest
    from publish import load_config, split_s3_uri

    if args.bucket_plan:
        prefix = args.prefix or split_s3_uri(load_config()["write_prefix"])[1]
        write_bucket_plan(args.bucket_plan, prefix, dataset_groups())
        return 0
    moves = plan()
    if not moves:
        print("nothing to move: every collection is already under a source group")
        if args.confirm:
            written = apply([], manifest=load_manifest())
            print(f"normalised the grouped collections; {len(written)} file(s) written")
        return 0
    groups: dict[str, list[str]] = {}
    for m in moves:
        groups.setdefault(m.group, []).append(m.dataset_id)
    for group, ids in sorted(groups.items()):
        print(f"{group}/  <- {', '.join(ids)}")
    print(f"{len(moves)} collection(s) into {len(groups)} source group(s)")
    if not args.confirm:
        print("\ndry run. re-run with --confirm to move.")
        return 0
    written = apply(moves, manifest=load_manifest())
    print(f"moved {len(moves)} collection(s); {len(written)} file(s) rewritten or written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
