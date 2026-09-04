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

    python3 tests/run_all.py
