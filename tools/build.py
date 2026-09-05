#!/usr/bin/env python3
"""Thin wrapper around ``ftwd run datasets/<id>.yaml``, with a pin check.

Every recipe lives at ``datasets/<id>.yaml`` and is an ftwd config file; this
script does not interpret it, it only picks the file, checks the installed
ftwd matches the one this repo is pinned to, and streams ``ftwd run``'s
output straight through. The four invocations from spec Sec.5:

    uv run python tools/build.py at
    uv run python tools/build.py at --only masks
    uv run python tools/build.py at --from select_images
    uv run python tools/build.py at --through stac

A build made with an ftwd other than the pin in ``pyproject.toml`` is not
reproducible, and the provenance ftwd writes into the collection would
disagree with the repository, so this refuses to run on a mismatch.
``--allow-unpinned`` overrides that with a loud warning -- for local
experimentation only, never for a build meant to be committed or uploaded.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, STAGING, ftwd_pin, installed_ftwd, load_manifest, pin_matches  # noqa: E402


def command(
    dataset_id: str,
    *,
    only: str | None = None,
    from_: str | None = None,
    through: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    """The ``ftwd run`` argv for ``dataset_id``.

    ``only``, ``from_`` and ``through`` map to ftwd's own ``--only``,
    ``--from`` and ``--through`` flags, in that order; ftwd itself rejects
    ``--only`` combined with the other two, so this does not police that.
    ``dry_run`` appends ``--dry-run`` last.
    """
    argv = ["ftwd", "run", f"datasets/{dataset_id}.yaml"]
    if only is not None:
        argv += ["--only", only]
    if from_ is not None:
        argv += ["--from", from_]
    if through is not None:
        argv += ["--through", through]
    if dry_run:
        argv.append("--dry-run")
    return argv


def _check_recipe(dataset_id: str) -> dict:
    """Exit unless ``dataset_id`` names a real, published recipe.

    ``datasets/<id>.yaml`` must exist, its ``name`` field must equal
    ``dataset_id`` (ftwd stamps that name into every output it writes), and
    the id must be one this catalog actually publishes, per
    ``datasets.yaml``. Returns the parsed recipe on success.
    """
    import yaml

    recipe_path = ROOT / "datasets" / f"{dataset_id}.yaml"
    if not recipe_path.is_file():
        sys.exit(
            f"no such dataset: {dataset_id!r} (no datasets/{dataset_id}.yaml); "
            "see datasets.yaml for the published set"
        )
    recipe = yaml.safe_load(recipe_path.read_text())
    name = recipe.get("name")
    if name != dataset_id:
        sys.exit(
            f"datasets/{dataset_id}.yaml declares name: {name!r}, expected {dataset_id!r}"
        )
    if dataset_id not in load_manifest()["datasets"]:
        sys.exit(f"{dataset_id!r} is not in datasets.yaml's published set")
    return recipe


def _check_pin(*, allow_unpinned: bool) -> None:
    """Exit unless the installed ftwd matches the pin in pyproject.toml.

    ``--allow-unpinned`` downgrades a mismatch to a warning printed to
    stderr instead of exiting, so it is always visible even when the rest of
    the run's output is piped or redirected.
    """
    pin = ftwd_pin()
    installed = installed_ftwd()
    if installed is not None and pin_matches(pin, installed):
        return

    installed_desc = f"{installed.kind} {installed.value}" if installed else "not installed"
    message = f"pinned ftwd is {pin.kind} {pin.value}, installed ftwd is {installed_desc}"
    if allow_unpinned:
        print(f"WARNING: --allow-unpinned overrides a pin mismatch: {message}", file=sys.stderr)
        return
    sys.exit(f"error: {message} (use --allow-unpinned to build anyway)")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one dataset with the pinned ftwd (ftwd run datasets/<id>.yaml).",
    )
    parser.add_argument("dataset_id", help="dataset id, e.g. 'lu' (see datasets.yaml)")
    parser.add_argument("--only", default=None, help="run a single ftwd stage only")
    parser.add_argument(
        "--from", dest="from_", default=None, help="run from this ftwd stage onward"
    )
    parser.add_argument("--through", default=None, help="run through this ftwd stage, inclusive")
    parser.add_argument(
        "--dry-run", action="store_true", help="resolve the config and list stages; run nothing"
    )
    parser.add_argument(
        "--allow-unpinned",
        action="store_true",
        help="build with an unpinned ftwd anyway (loud warning; not for committed builds)",
    )
    return parser.parse_args(argv)


def subprocess_env() -> dict[str, str]:
    """The environment ftwd runs with.

    python.org and uv-managed interpreters may have no OpenSSL CA bundle
    installed, in which case every https fetch fails with
    CERTIFICATE_VERIFY_FAILED. When the caller has not configured one,
    point OpenSSL at certifi's bundle, which the environment always carries.
    """
    env = dict(os.environ)
    if not env.get("SSL_CERT_FILE") and not env.get("SSL_CERT_DIR"):
        try:
            import certifi

            env["SSL_CERT_FILE"] = certifi.where()
        except ImportError:
            pass
    return env


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    _check_recipe(args.dataset_id)
    _check_pin(allow_unpinned=args.allow_unpinned)

    result = subprocess.run(
        command(
            args.dataset_id,
            only=args.only,
            from_=args.from_,
            through=args.through,
            dry_run=args.dry_run,
        ),
        cwd=ROOT,
        env=subprocess_env(),
        check=False,
    )

    if result.returncode == 0:
        staging_dir = (STAGING / args.dataset_id).relative_to(ROOT)
        print(f"\n{staging_dir}/")
        print(f"{staging_dir / 'summary.md'}")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
