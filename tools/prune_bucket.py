#!/usr/bin/env python3
"""Delete a dataset's objects that its current build no longer publishes.

A rebuilt dataset can drop chips (a new class filter or chip rule changes the
chip set). ``upload_data.py`` and ``publish.py`` never delete, so the dropped
chips' files would stay in the bucket, unlinked from the catalog. This lists
``<write_prefix>/<source>/<id>/`` and deletes every key that neither the staged data
(``upload_data.collect_data_uploads``) nor the published catalog
(``publish.collect_uploads``) would write, and that ``catalog/<source>/<id>/`` does
not reference (``catalog_refs``).

    uv run python tools/prune_bucket.py at_2018 at_2019            # dry run
    uv run python tools/prune_bucket.py at_2018 at_2019 --confirm  # delete

Run it after the dataset's last pass (imagery, if any) is uploaded and its catalog
published. It refuses a staging that is not a full build (``staging_gaps``): a
backfill staging, a rebuild before its imagery pass, or one whose chips parquet does
not list exactly its staged chip directories lacks published files that pruning
against it would delete. A chip's files are pruned only when staging has no
directory for it, the chips parquet does not list it and catalog/ does not link it.
Source Cooperative's proxy has no DeleteObjects, so keys go one at a time.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import dataset_relpath  # noqa: E402
from publish import (  # noqa: E402
    ROOT,
    aws_session,
    collect_uploads,
    load_config,
    remote_index,
    s3_client,
    split_s3_uri,
)
from upload_data import collect_data_uploads, data_root  # noqa: E402


def stale_keys(
    dataset_id: str, config: dict[str, str], remote: dict, root: Path = ROOT
) -> list[str]:
    """Keys under the dataset's ``<source>/<id>/`` prefix that the current build does not publish."""
    _, prefix = split_s3_uri(config["write_prefix"])
    rel = dataset_relpath(dataset_id, catalog=root / config["publish_dir"], root=root)
    under = f"{prefix}/{rel}/" if prefix else f"{rel}/"
    if not (data_root(config, root) / dataset_id).is_dir():
        sys.exit(f"{dataset_id}: no staging to compare against; refusing to prune")
    wanted = {u.key for u in collect_data_uploads(config, root, only={dataset_id})}
    wanted |= {u.key for u in collect_uploads(config, root, only={dataset_id}) if u.key.startswith(under)}
    if not any(k.endswith("/collection.json") for k in wanted):
        sys.exit(
            f"{dataset_id}: the build publishes no collection.json; refusing to prune"
        )
    published = root / config["publish_dir"] / rel
    files, chips = catalog_refs(published)
    stale = sorted(
        k for k in remote
        if k.startswith(under) and k not in wanted and not _referenced(k[len(under):], files, chips)
    )
    staged = data_root(config, root) / dataset_id
    gaps = staging_gaps(staged, [k[len(under):] for k in stale], published)
    if gaps:
        shown = ", ".join(gaps[:5]) + (f" and {len(gaps) - 5:,} more" if len(gaps) > 5 else "")
        sys.exit(
            f"{dataset_id}: staging is not a full build ({shown}); refusing to prune. "
            "A backfill staging or a rebuild before its imagery pass holds only part of "
            "what is published, and pruning against it would delete the rest."
        )
    return stale


def _referenced(rel: str, files: set[str], chips: set[tuple[str, str]]) -> bool:
    """Whether the catalog still references ``rel``: a file it names, or anything in a chip it links."""
    parts = PurePosixPath(rel).parts
    return rel in files or (len(parts) >= 4 and parts[0] == "chips" and (parts[1], parts[2]) in chips)


def staging_gaps(staged: Path, stale: list[str], published: Path | None = None) -> list[str]:
    """Why ``staged`` is not a full build to prune against; empty when it is.

    ``stale`` holds the dataset-relative paths prune would delete, ``published`` the
    dataset's ``catalog/`` folder (a collection asset it holds, the thumbnail, is not
    staged). A full build shows none of these:

    - a staged ``collection.json`` that is missing or is not a Collection with a
      non-empty ``assets`` object of objects;
    - a collection asset whose file is not on disk (a backfill fetches no PMTiles),
      or whose href is absolute, which cannot be checked, or a staged style that
      draws from PMTiles that are not staged;
    - a stale key in the directory of a chip the build still has (``chip_gaps``).

    A chip the rebuild dropped is in neither the staged chips parquet nor staging, so
    its files are prunable.
    """
    doc, gaps = _staged_collection(staged)
    if doc is None:
        return gaps
    for key, asset in sorted(doc["assets"].items()):
        href = asset.get("href") or ""
        if urlsplit(href).scheme or href.startswith("/"):
            gaps.append(f"collection asset {key} has an absolute href ({href}) that cannot be checked")
        elif not _on_disk(href, staged, published):
            gaps.append(f"collection asset {key} ({href}) is not staged")
        elif "style" in (asset.get("roles") or []) or key.startswith("style-"):
            gaps += _style_gaps(key, staged / href.removeprefix("./"))
    return gaps + chip_gaps(staged, stale, doc["assets"].get("chips"))


def _staged_collection(staged: Path) -> tuple[dict | None, list[str]]:
    """The staged ``collection.json`` if it is a Collection with assets, else why not."""
    path = staged / "collection.json"
    if not path.is_file():
        return None, ["no staged collection.json"]
    try:
        doc = json.loads(path.read_text())
    except ValueError:
        return None, ["the staged collection.json is not JSON"]
    assets = doc.get("assets") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("type") != "Collection":
        return None, ["the staged collection.json is not a STAC Collection"]
    if not isinstance(assets, dict) or not assets:
        return None, ["the staged collection.json has no assets"]
    if not all(isinstance(asset, dict) for asset in assets.values()):
        return None, ["the staged collection.json has an asset that is not an object"]
    return doc, []


def _style_gaps(key: str, style: Path) -> list[str]:
    """The PMTiles a staged style draws from that are not staged next to it."""
    try:
        sources = json.loads(style.read_text()).get("sources") or {}
    except (ValueError, AttributeError):
        return [f"collection asset {key} is not a style document"]
    gaps = []
    for source in sources.values():
        url = (source.get("url") or "") if isinstance(source, dict) else ""
        tiles = url.removeprefix("pmtiles://")
        if url.startswith("pmtiles://") and not urlsplit(tiles).scheme and not (style.parent / tiles).is_file():
            gaps.append(f"collection asset {key} draws {tiles}, which is not staged")
    return gaps


def _on_disk(href: str, base: Path, published: Path | None) -> bool:
    """Whether a relative ``href`` names a file in ``base`` or in ``published``."""
    rel = href[2:] if href.startswith("./") else href
    return bool(rel) and ((base / rel).is_file() or (published is not None and (published / rel).is_file()))


def chip_gaps(staged: Path, stale: list[str], chips_asset: dict | None) -> list[str]:
    """Stale keys of chips the build still has, unless staging holds that chip whole.

    A chip is kept when staging has its directory, ``chips/<square>/<id>[_<year>]/``.
    The staged chips parquet (the collection's ``chips`` asset) must list exactly
    those chips: an empty parquet, one without an ``id`` column, a staged directory
    it does not list or an id with no staged directory means staging and parquet are
    not the same build, and nothing can be told dropped. A kept chip's stale key is
    a gap when staging has no item JSON for it, when the key is JSON (an imagery
    child item before the imagery pass), or when a staged JSON in that directory
    names an asset that is not on disk (a backfill's masks). What is left — a file
    the whole staged chip no longer references (a v1 overlay), or any file of a chip
    with no staged directory, which the rebuild dropped — is prunable.
    """
    by_chip: dict[tuple[str, str], list[str]] = {}
    for rel in stale:
        parts = PurePosixPath(rel).parts
        if len(parts) >= 4 and parts[0] == "chips":
            by_chip.setdefault((parts[1], parts[2]), []).append(rel)
    chip_dirs = {(d.parent.name, d.name) for d in staged.glob("chips/*/*") if d.is_dir()}
    if not by_chip and not chip_dirs:
        return []
    gaps = _parquet_gaps(staged, chips_asset, {name for _, name in chip_dirs})
    if gaps:
        return gaps
    for (square, chip), rels in sorted(by_chip.items()):
        if (square, chip) not in chip_dirs:
            continue
        chip_dir = staged / "chips" / square / chip
        if not (chip_dir / f"{chip}.json").is_file():
            gaps.append(f"chip {square}/{chip} is staged without its item JSON")
        elif any(rel.endswith(".json") for rel in rels) or _missing_assets(chip_dir):
            gaps.append(f"chip {square}/{chip} is not staged whole ({rels[0]} would be deleted)")
    return gaps


def _parquet_gaps(staged: Path, chips_asset: dict | None, dir_names: set[str]) -> list[str]:
    """Why the staged chips parquet and the staged chip directories are not one build."""
    href = (chips_asset or {}).get("href") or ""
    if not href or urlsplit(href).scheme or not _on_disk(href, staged, None):
        return ["no staged chips parquet (the collection's chips asset) to tell kept chips from dropped"]
    path = staged / href.removeprefix("./")
    if "id" not in pq.read_schema(path).names:
        return [f"the staged chips parquet {path.name} has no id column"]
    ids = set(pq.read_table(path, columns=["id"]).column("id").to_pylist())
    if not ids:
        return [f"the staged chips parquet {path.name} lists no chips"]
    matched = {_chip_id(name, ids) for name in dir_names}
    unlisted = sorted(name for name in dir_names if _chip_id(name, ids) is None)
    unstaged = sorted(map(str, ids - matched))
    gaps = [f"chip directory {name} is not in the chips parquet" for name in unlisted[:3]]
    gaps += [f"chips parquet id {chip} has no staged directory" for chip in unstaged[:3]]
    if len(unlisted) + len(unstaged) > len(gaps):
        gaps.append(f"{len(unlisted):,} staged chip(s) unlisted, {len(unstaged):,} listed chip(s) unstaged in all")
    return gaps


def _chip_id(dir_name: str, ids: set) -> str | None:
    """The chips parquet id a chip directory ``<id>`` or ``<id>_<year>`` belongs to."""
    if dir_name in ids:
        return dir_name
    base, _, year = dir_name.rpartition("_")
    return base if year.isdigit() and base in ids else None


def _missing_assets(chip_dir: Path) -> bool:
    """Whether any STAC JSON in ``chip_dir`` is unreadable or names an asset that is not on disk."""
    for path in chip_dir.glob("*.json"):
        try:
            assets = json.loads(path.read_text()).get("assets") or {}
        except (ValueError, AttributeError):
            return True
        if not isinstance(assets, dict):
            return True
        for asset in assets.values():
            href = (asset.get("href") or "") if isinstance(asset, dict) else ""
            if href and not urlsplit(href).scheme and not _on_disk(href, chip_dir, None):
                return True
    return False


def catalog_refs(published: Path) -> tuple[set[str], set[tuple[str, str]]]:
    """What ``catalog/<source>/<id>/`` still references, so prune keeps it.

    Returns the dataset-relative files (the collection's assets and the PMTiles its
    styles draw from) and the ``(square, chip directory)`` pairs its chip
    sub-catalogs link. Prune then stays safe when run before catalogize or publish.
    """
    files: set[str] = set()
    chips: set[tuple[str, str]] = set()
    files |= _hrefs(published / "collection.json", "assets")
    for style in published.glob("styles/*.json"):
        for source in (_read(style).get("sources") or {}).values():
            url = (source.get("url") or "") if isinstance(source, dict) else ""
            if url.startswith("pmtiles://") and not urlsplit(url.removeprefix("pmtiles://")).scheme:
                files.add(posixpath.normpath(posixpath.join("styles", url.removeprefix("pmtiles://"))))
    for sub in published.glob("chips/*/catalog.json"):
        for link in _read(sub).get("links") or []:
            href = (link.get("href") or "") if isinstance(link, dict) else ""
            parts = PurePosixPath(posixpath.normpath(href)).parts
            if link.get("rel") == "item" and not urlsplit(href).scheme and len(parts) == 2:
                chips.add((sub.parent.name, parts[0]))
    return files, chips


def _read(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _hrefs(path: Path, key: str) -> set[str]:
    """The relative hrefs of a document's ``key`` objects, normalized and dataset-relative."""
    values = _read(path).get(key)
    out = set()
    for value in values.values() if isinstance(values, dict) else []:
        href = (value.get("href") or "") if isinstance(value, dict) else ""
        if href and not urlsplit(href).scheme and not href.startswith("/"):
            out.add(posixpath.normpath(href))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="+")
    parser.add_argument("--confirm", action="store_true", help="actually delete")
    args = parser.parse_args()

    config = load_config()
    bucket, prefix = split_s3_uri(config["write_prefix"])
    client = s3_client(aws_session(config), config.get("endpoint_url"))
    status = 0
    for dataset_id in args.dataset_ids:
        remote = remote_index(bucket, prefix, config, only={dataset_id})
        stale = stale_keys(dataset_id, config, remote)
        print(
            f"{dataset_id}: {len(remote)} object(s) in the bucket, {len(stale)} stale"
        )
        for key in stale[:5]:
            print(f"  {key}")
        if not args.confirm or not stale:
            continue

        def delete(key: str) -> str | None:
            try:
                client.delete_object(Bucket=bucket, Key=key)
            except Exception as err:  # report and carry on
                return f"{key}: {err}"
            return None

        with ThreadPoolExecutor(32) as pool:
            errors = [e for e in pool.map(delete, stale) if e]
        print(f"  deleted {len(stale) - len(errors)}, {len(errors)} error(s)")
        for e in errors[:5]:
            print(f"  {e}")
        status |= bool(errors)
    if not args.confirm:
        print("\ndry run. re-run with --confirm to delete.")
    return status


if __name__ == "__main__":
    sys.exit(main())
