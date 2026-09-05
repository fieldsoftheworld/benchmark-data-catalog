# benchmark-data-catalog

Git-backed [Portolan](https://www.portolan-sdi.org/) catalog for the Fields of
the World benchmark dataset, published at
[source.coop/ftw/benchmark-data](https://source.coop/ftw/benchmark-data).

`catalog/` is the published catalog and is synced 1:1 to the bucket. Data files
never enter git: [ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools)
(`ftwd`) builds each dataset into `staging/` from a recipe in `datasets/`, and
the uploaders carry the bytes to the bucket.

## Layout

- `datasets.yaml` names the official datasets and catalog-level facts.
- `datasets/<id>.yaml` is the ftwd recipe for one dataset. Input is always a
  collection of the [harmonized field data catalog](https://source.coop/ftw/harmonized-field-data).
- `catalog/` is published; `catalog/<id>/` holds one collection's metadata,
  docs, styles and thumbnail. Item JSON and rasters are bucket-only.
- `tools/` publishes (`publish.py`, `upload_data.py`); the build and
  catalogize tools arrive with the first dataset.
- `tests/run_all.py` runs every gate; CI runs it on every pull request.

## Working on it

    uv sync                            # installs the pinned ftwd and validators
    uv run python tests/run_all.py     # gates
    uv run python tools/publish.py     # dry run; --confirm uploads catalog/

Publishing needs `source-coop login` and the `source-coop` AWS profile.

ftwd is pinned by git commit in `pyproject.toml` while its Portolan changes are
in review; `tests/test_ftwd_pin.py` refuses a mismatch.

## Thumbnails

`tools/thumbnail.py` renders a built collection's manifest-chosen style into
`catalog/<id>/thumbnail.webp` with [chiitiler](https://github.com/Kanahiro/chiitiler),
a tile server that can rasterize a MapLibre style server-side. It needs a
running chiitiler:

    tools/chiitiler.sh &                       # clone/npm install if needed, then run
    curl -s http://localhost:13579/health      # wait for "OK"
    uv run python tools/thumbnail.py lu        # writes catalog/lu/thumbnail.webp
    pkill -f "tile-server --port 13579"        # stop it when done

`datasets.yaml` names each collection's framing under `thumbnail:` — `style`
(a `style-<id>` asset on the collection), `zoom` (the window's zoom level),
and `rank` (which densest cluster of chip or field centroids to center on;
`0` is the densest). Override any of the three on the command line
(`--style`, `--zoom`, `--rank`) to try a different frame. The result is
gated on a blank probe (at least 2% of pixels must differ from the
background) before it's written and registered as the collection's
`thumbnail` asset.

## Adding a dataset

1. Add the id under `datasets:` in `datasets.yaml`.
2. Write `datasets/<id>.yaml` with attested license and providers copied from
   the harmonized collection.
3. Build, catalogize, run the gates, commit, upload, publish (see `tools/`).

## Version

2.0.0-alpha.1, the reviewer sample. Version 1.0 lives at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world).
