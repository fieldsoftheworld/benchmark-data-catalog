#!/usr/bin/env python3
"""The data upload contract: two gates, and no reimplementation.

tools/upload_data.py walks a staging directory that sits outside the published
catalog. It admits a file only when both gates pass. The path gate admits only
files under data_dir. The extension gate admits only the suffixes in
PUBLISHABLE_SUFFIXES.

This gate also checks that the script refuses an unedited config and that it
exits with a message when data_dir is absent.

No network, no AWS, no credentials.

Run: python3 tests/test_upload_data.py
"""
import io
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import upload_data  # noqa: E402
from upload_data import (  # noqa: E402
    PUBLISHABLE_SUFFIXES,
    collect_data_uploads,
    data_root,
    git_owned,
    is_data_publishable,
    unedited_sentinels,
)

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def exit_message(call) -> str:
    """Run a call that must exit, and return the message it exits with."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            call()
    except SystemExit as exc:
        return str(exc.code)
    return ""


# --- the extension allow-list ------------------------------------------
check(".parquet" in PUBLISHABLE_SUFFIXES, "parquet is publishable")
check(".pmtiles" in PUBLISHABLE_SUFFIXES, "pmtiles is publishable")
check(".json" in PUBLISHABLE_SUFFIXES, "item JSON trees are publishable")
check(".geojson" not in PUBLISHABLE_SUFFIXES, "geojson scratch never uploads")
check(".yaml" not in PUBLISHABLE_SUFFIXES, "yaml is barred")
check(".md" not in PUBLISHABLE_SUFFIXES, "markdown is barred")
check(".geojsonseq" not in PUBLISHABLE_SUFFIXES, "geojsonseq is barred")
check(".txt" not in PUBLISHABLE_SUFFIXES, "txt is barred")
check(is_data_publishable(Path("a/roads.parquet")), "parquet passes")
check(is_data_publishable(Path("a/roads.PARQUET")), "suffix case is ignored")
check(is_data_publishable(Path("a/tiles.pmtiles")), "pmtiles passes")
check(not is_data_publishable(Path("a/scratch.geojson")), "geojson is barred")
check(not is_data_publishable(Path("a/notes.md")), "markdown is barred")
check(not is_data_publishable(Path("a/roads.parquet.tmp")), "tmp is barred")
check(not is_data_publishable(Path("a/.hidden/x.parquet")), "dotdir is barred")
check(
    is_data_publishable(Path("lu/chips/32UNA/ftw-1/ftw-1.json")),
    "an item JSON tree is publishable",
)
check(
    not is_data_publishable(Path("lu/ftwd-config.resolved.yaml")),
    "a resolved ftwd config is not publishable",
)
check(
    not is_data_publishable(Path("lu/summary.md")),
    "a summary markdown file is not publishable",
)

# --- the path gate and the walk ----------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # Staged data. Both gates pass for the first two.
    write(root / "staging/roads/part-0.parquet")
    write(root / "staging/roads/part-1.parquet")
    write(root / "staging/tiles/roads.pmtiles")
    write(root / "staging/dem/tile.tif")

    # Staged scratch. The extension gate bars it.
    write(root / "staging/scratch/roads.geojson")
    write(root / "staging/scratch/notes.md")
    write(root / "staging/.work/tmp.parquet")

    # Outside the staging tree. The path gate bars it.
    write(root / "catalog/catalog.json")
    write(root / "elsewhere/stray.parquet")
    write(root / "stray-at-root.pmtiles")

    config = {
        "write_prefix": "s3://a-bucket/a/prefix",
        "public_base": "https://data.example.org/a/prefix",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }
    uploads = collect_data_uploads(config, root)
    keys = {u.key for u in uploads}

    expected = {
        "a/prefix/roads/part-0.parquet",
        "a/prefix/roads/part-1.parquet",
        "a/prefix/tiles/roads.pmtiles",
        "a/prefix/dem/tile.tif",
    }
    check(keys == expected, f"upload set wrong.\n  extra:   {keys - expected}"
                            f"\n  missing: {expected - keys}")

    # Content types come from publish.py, not from a second table.
    types = {u.key: u.content_type for u in uploads}
    check(
        types["a/prefix/roads/part-0.parquet"]
        == "application/vnd.apache.parquet",
        "parquet content type comes from publish.py",
    )
    check(
        types["a/prefix/tiles/roads.pmtiles"] == "application/vnd.pmtiles",
        "pmtiles content type comes from publish.py",
    )

    # --only restricts the walk to named dataset directories.
    write(root / "staging/lu/items.parquet")
    only_keys = {u.key for u in collect_data_uploads(config, root, only={"lu"})}
    check(only_keys == {"a/prefix/lu/items.parquet"}, f"--only lu uploads only lu: {only_keys}")
    check(
        {u.key for u in collect_data_uploads(config, root, only={"roads", "lu"})}
        == {"a/prefix/roads/part-0.parquet", "a/prefix/roads/part-1.parquet", "a/prefix/lu/items.parquet"},
        "--only accepts several datasets",
    )
    expected = expected | {"a/prefix/lu/items.parquet"}

    # The bare-prefix case: no prefix at all.
    flat = dict(config, write_prefix="s3://a-bucket")
    check(
        {u.key for u in collect_data_uploads(flat, root)}
        == {k.removeprefix("a/prefix/") for k in expected},
        "keys are wrong when write_prefix names no prefix",
    )

    # An absolute data_dir works too.
    absolute = dict(config, data_dir=str(root / "staging"))
    check(
        {u.key for u in collect_data_uploads(absolute, root)} == expected,
        "an absolute data_dir walks the same tree",
    )

    # --- an absent or wrong data_dir exits with a message ---------------
    message = exit_message(lambda: data_root(dict(config, data_dir=""), root))
    check("data_dir" in message, f"an empty data_dir names the key: {message}")
    check("\n" in message, "the empty data_dir message says what to do")

    no_key = {k: v for k, v in config.items() if k != "data_dir"}
    check(
        "data_dir" in exit_message(lambda: data_root(no_key, root)),
        "an absent data_dir names the key",
    )

    missing = dict(config, data_dir="no-such-directory")
    check(
        "does not exist" in exit_message(lambda: data_root(missing, root)),
        "a data_dir that does not exist says so",
    )

# --- catalog/ owns it: git-owned staged files are skipped ---------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # In both staging/ and catalog/: git owns it, never uploaded.
    write(root / "staging/lu/collection.json")
    write(root / "catalog/lu/collection.json")
    write(root / "staging/lu/chips/32UNA/catalog.json")
    write(root / "catalog/lu/chips/32UNA/catalog.json")

    # Only in staging/: uploaded, with the item-JSON content type.
    write(root / "staging/lu/chips/32UNA/ftw-1/ftw-1.json")
    write(root / "staging/lu/items.parquet")

    owned_config = {
        "write_prefix": "s3://a-bucket/a/prefix",
        "public_base": "https://data.example.org/a/prefix",
        "publish_dir": "catalog",
        "data_dir": "staging",
    }

    check(
        git_owned(Path("lu/collection.json"), root, owned_config),
        "a path that exists under publish_dir is git-owned",
    )
    check(
        not git_owned(
            Path("lu/chips/32UNA/ftw-1/ftw-1.json"), root, owned_config
        ),
        "a path that exists only in staging is not git-owned",
    )

    skipped: list[Path] = []
    owned_uploads = collect_data_uploads(owned_config, root, skipped=skipped)
    owned_keys = {u.key for u in owned_uploads}

    owned_expected = {
        "a/prefix/lu/chips/32UNA/ftw-1/ftw-1.json",
        "a/prefix/lu/items.parquet",
    }
    check(
        owned_keys == owned_expected,
        f"upload set wrong.\n  extra:   {owned_keys - owned_expected}"
        f"\n  missing: {owned_expected - owned_keys}",
    )
    check(
        {p.as_posix() for p in skipped}
        == {"lu/collection.json", "lu/chips/32UNA/catalog.json"},
        f"the skipped list names the git-owned paths, got {skipped}",
    )

    owned_types = {u.key: u.content_type for u in owned_uploads}
    check(
        owned_types["a/prefix/lu/chips/32UNA/ftw-1/ftw-1.json"]
        == "application/geo+json",
        "an uploaded item JSON gets geo+json via rel",
    )

    # collect_data_uploads without a skipped list still works: skipping is
    # silent unless the caller asks to see it.
    check(
        {u.key for u in collect_data_uploads(owned_config, root)}
        == owned_expected,
        "collect_data_uploads skips git-owned files with no skipped list too",
    )

    # The dry-run report names how many staged files catalog/ owns. main()
    # calls collect_data_uploads(config) with the default root (the real
    # ROOT), so both data_dir and publish_dir are made absolute here — an
    # absolute right-hand path in a Path "/" join replaces the left side
    # entirely, so this stays independent of ROOT.
    abs_config = dict(
        owned_config,
        data_dir=str(root / "staging"),
        publish_dir=str(root / "catalog"),
    )
    argv = sys.argv
    sys.argv = ["upload_data.py"]
    real_load = upload_data.load_config
    upload_data.load_config = lambda *a, **k: abs_config
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            code = upload_data.main()
    finally:
        upload_data.load_config = real_load
        sys.argv = argv
    check(code == 0, f"the dry run exits cleanly, got {code}")
    check(
        "2 staged file(s) skipped because catalog/ owns them" in out.getvalue(),
        f"the dry run reports the skip count:\n{out.getvalue()}",
    )

# --- a config with no data_dir exits cleanly ----------------------------
# main() must report the missing key via data_root's message instead of
# falling through to remote_index and a live S3 listing. This does not read
# the repository's own catalog.publish.yaml (which sets data_dir), so the
# gate stays true even once staging/ exists.
no_data_dir_config = {
    "write_prefix": "s3://a-bucket/a/prefix",
    "public_base": "https://data.example.org/a/prefix",
    "publish_dir": "catalog",
}
argv = sys.argv
sys.argv = ["upload_data.py"]
real_load = upload_data.load_config
upload_data.load_config = lambda *a, **k: no_data_dir_config
try:
    message = exit_message(upload_data.main)
finally:
    upload_data.load_config = real_load
    sys.argv = argv
check("data_dir" in message, f"a config without data_dir exits on data_dir: {message!r}")

# --- the sentinel guard ------------------------------------------------
check(
    unedited_sentinels({
        "write_prefix": "s3://EXAMPLE-BUCKET/EXAMPLE-PREFIX",
        "public_base": "https://example.invalid/EXAMPLE-PREFIX",
    }) != [],
    "an unedited config is refused",
)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root / "staging/roads/part-0.parquet")
    sentinel_config = {
        "write_prefix": "s3://EXAMPLE-BUCKET/EXAMPLE-PREFIX",
        "public_base": "https://example.invalid/EXAMPLE-PREFIX",
        "publish_dir": "catalog",
        "data_dir": str(root / "staging"),
    }
    out = io.StringIO()
    argv = sys.argv
    sys.argv = ["upload_data.py", "--confirm"]
    real_load = upload_data.load_config
    upload_data.load_config = lambda *a, **k: sentinel_config
    try:
        with redirect_stdout(out):
            code = upload_data.main()
    finally:
        upload_data.load_config = real_load
        sys.argv = argv
    check(code == 1, f"the sentinel guard refuses to upload, got {code}")
    check(
        "EXAMPLE-BUCKET" in out.getvalue(),
        "the guard names the sentinel it found",
    )

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: data upload contract holds")
