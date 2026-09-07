# Agent guide for benchmark-data-catalog

This repository publishes the Fields of the World benchmark dataset as a
git-backed Portolan catalog. `catalog/` is the published tree and is synced 1:1
to `s3://ftw/benchmark-data`; nothing outside it is ever uploaded. Data files
(parquet, COGs, PMTiles, item JSON) never enter git; they are built into
`staging/` by ftwd and uploaded by `tools/upload_data.py`.

Every claim in `catalog/**/README.md` and `catalog/**/AGENTS.md` is attested
(copied from a source and cited), researched and cited, or derived by a query
that is reproducible from the published data.

Recipes live in `datasets/<id>.yaml` and are ftwd config files. `datasets.yaml`
names the official set. Edit those and the tools, never the generated files
under `catalog/<id>/`.

Run the gates before every commit:

    uv run python tests/run_all.py

## Running the build and publish flow

Setup: `uv sync` (installs the pinned ftwd and validators — `tests/test_ftwd_pin.py`
refuses a build from any other ftwd) and [tippecanoe](https://github.com/felt/tippecanoe)
on `PATH` (ftwd's `docs` stage needs it for PMTiles and vector styles).

Per dataset (`README.md`'s [Adding a dataset](README.md#adding-a-dataset) has
the full walkthrough; this is the command sequence):

    uv run python tools/build.py <id> --through stac
    uv run python tools/build.py <id> --only docs      # docs runs after imagery in ftwd's order
    uv run python tools/catalogize.py <id> --root      # --root after adding/removing a dataset
    tools/chiitiler.sh &
    uv run python tools/thumbnail.py <id>
    uv run python tests/run_all.py
    git commit -am "Add <id>"
    uv run python tools/upload_data.py --confirm
    uv run python tools/upload_data.py --only lu --confirm   # one dataset while another builds
    uv run python tools/publish.py --confirm

Imagery is a second pass, once selection is ready:

    uv run python tools/build.py <id> --from select_images
    uv run python tools/build.py <id> --only docs
    uv run python tools/catalogize.py <id>
    uv run python tools/upload_data.py --confirm

`tools/build.py` runs `ftwd` from the repository root. Two environment
gotchas it works around, in case you hit them running ftwd yourself: it gives
ftwd certifi's CA bundle when the interpreter has none, and it drops any
inherited `PROJ_LIB`, `PROJ_DATA` or `GDAL_DATA` — a conda environment on
`PATH` sets those to paths rasterio and pyproj can't use, and builds fail
opaquely otherwise. `.python-version` pins uv-managed CPython 3.11 for the
same class of reason: the python.org 3.12 framework build ships without
OpenSSL certificates.

Publishing needs `source-coop login` (AWS profile `source-coop`); the
endpoint comes from `catalog.publish.yaml`.

## Never

- Never hand-edit anything under `catalog/<id>/` — it's generated. Fix the
  recipe or the tools and rerun `tools/catalogize.py <id>`.
- Never widen `ACCEPTED` in `tests/test_conformance.py`. A new entry needs a
  row in `docs/conformance.md` (rule, where it fires, why, the issue tracking
  its removal) before it's added, not after.
- Never commit `staging/` or any data file (parquet, COGs, imagery, PMTiles,
  item JSON). Those reach the bucket only through `tools/upload_data.py`.
- Never run `--confirm` on `tools/upload_data.py` or `tools/publish.py`
  without the maintainer's say-so — it's a real write to the published
  bucket, and `publish.py` never deletes, so a mistake stays live until
  someone notices and fixes it by hand.
