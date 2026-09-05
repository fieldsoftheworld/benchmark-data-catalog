#!/usr/bin/env python3
"""Shared helper: overlay staging item JSON onto a copy of catalog/.

A committed sub-catalog (``catalog/<id>/chips/<square>/catalog.json``) carries
``rel: item`` links like ``./<item>/<item>.json`` that point at files which
exist only under ``staging/<id>/chips/<square>/<item>/`` — ftwd writes them
there, and they are never committed (they are data, uploaded by
``tools/upload_data.py``). A validator that walks ``catalog/`` alone can
neither resolve those links nor validate the items themselves.

``overlay_tree`` builds a throwaway copy of ``catalog/`` with the matching
staging item JSON copied into place, so both problems go away. Copies, never
symlinks, so a validator that treats symlinks differently (rashid,
stac-check) sees the same bytes as a real checkout would. JSON only: rasters
and every other data file under an item directory are left out on purpose.

``test_conformance.py`` and ``test_stac_valid.py`` both need the same "should
I overlay, and what do I report" decision, so it lives here too
(``has_staging_items``, ``resolve_target``) rather than being duplicated.

Set the environment variable ``BDC_STAGING_DIR`` to a directory that does not
exist to simulate, locally, the CI checkout that has no ``staging/`` at all —
without touching the real ``staging/`` tree. Every ``staging`` argument
accepted below is resolved through this override first (``_effective_staging``),
so ``has_staging_items`` and ``resolve_target`` both honor it and a gate needs
no changes of its own to do so:

    CI_LIGHT=1 BDC_STAGING_DIR=/nonexistent uv run python tests/test_conformance.py
"""
from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path


def _effective_staging(staging: Path) -> Path:
    """``staging``, or ``BDC_STAGING_DIR`` when that environment variable is set.

    Read fresh on every call (not cached at import time) so a test can flip
    it via ``os.environ`` within one process.
    """
    override = os.environ.get("BDC_STAGING_DIR")
    return Path(override) if override else staging


def overlay_tree(catalog: Path, staging: Path) -> tempfile.TemporaryDirectory:
    """A temp copy of ``catalog/`` with staging item JSON overlaid onto it.

    For every ``catalog/<id>/chips/<square>/catalog.json``, copies every
    ``*.json`` file under the matching ``staging/<id>/chips/<square>/<item>/``
    directory into the temp tree at the same relative place
    (``<id>/chips/<square>/<item>/*.json``), recursively — an imagery child
    item sits one directory deeper still
    (``<id>/chips/<square>/<item>/<child>/<child>.json``, see
    ``tools/publish.py``'s ``_is_item_json``), and its rel:'item' link from
    the parent item must resolve too. Use as a context manager — it yields
    the temp directory's path (a ``str``) and cleans up on exit:

        with overlay_tree(catalog, staging) as root:
            check(Path(root))
    """
    tmp = tempfile.TemporaryDirectory(prefix="portolan-overlay-")
    root = Path(tmp.name)
    shutil.copytree(catalog, root, dirs_exist_ok=True)

    for sub_catalog in sorted(root.glob("*/chips/*/catalog.json")):
        square_dir = sub_catalog.parent
        dataset_id = square_dir.parent.parent.name
        square = square_dir.name
        staging_square_dir = staging / dataset_id / "chips" / square
        if not staging_square_dir.is_dir():
            continue
        for item_dir in sorted(p for p in staging_square_dir.iterdir() if p.is_dir()):
            json_files = sorted(item_dir.rglob("*.json"))
            if not json_files:
                continue
            for json_file in json_files:
                dest = square_dir / item_dir.name / json_file.relative_to(item_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(json_file, dest)

    return tmp


def has_staging_items(catalog: Path, staging: Path) -> bool:
    """True when a built collection has a staging item tree to overlay.

    False on the skeleton (no ``catalog/*/collection.json`` yet), in CI where
    ``staging/`` is not checked out at all, and wherever ``BDC_STAGING_DIR``
    is pointed at a directory that does not exist (see module docstring).
    """
    staging = _effective_staging(staging)
    for collection in catalog.glob("*/collection.json"):
        dataset_id = collection.parent.name
        if (staging / dataset_id / "chips").is_dir():
            return True
    return False


@contextlib.contextmanager
def resolve_target(catalog: Path, staging: Path):
    """Yield the tree to validate, printing which mode ran.

    An overlay (see ``overlay_tree``) when at least one built collection has
    a staging item tree — ``mode   overlay (N item JSON files)`` — otherwise
    ``catalog/`` itself, unchanged — ``mode   catalog/ only``. That is the CI
    case (staging is not checked out), the skeleton case (nothing built yet),
    and the ``BDC_STAGING_DIR`` override case (module docstring).
    """
    staging = _effective_staging(staging)
    if has_staging_items(catalog, staging):
        with overlay_tree(catalog, staging) as tmp_name:
            root = Path(tmp_name)
            n_items = sum(1 for _ in root.glob("*/chips/*/*/**/*.json"))
            print(f"mode   overlay ({n_items} item JSON files)")
            yield root
    else:
        print("mode   catalog/ only")
        yield catalog
