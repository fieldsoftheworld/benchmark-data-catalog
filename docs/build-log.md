# Build log

What each dataset build actually did: ftwd commit, source, counts, timing.
Attested at build time, not recomputed — if you rebuild a dataset, add a new
row rather than editing the old one, so this stays a record of what happened
rather than a claim about the current state of `catalog/`.

| Dataset | Date | ftwd commit | Source | Fields | Chips (train/val/test) | Masks | Sub-catalogs | Staging size | Wall time |
|---------|------|-------------|--------|--------|-------------------------|-------|---------------|---------------|-----------|
| lu | 2026-09-05 | [`73142362`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/73142362) (PR [#60](https://github.com/fieldsoftheworld/ftw-dataset-tools/pull/60) head) | `lu/latest/lu.parquet` | 87,997 | 775 (601 / 79 / 95) | 2,325 | 7 (MGRS) | 92 MB | ~25 min through `stac` + ~1 min `docs`, on an M-series laptop |
| si | 2026-09-05 | [`5f4a9191`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/5f4a9191) (PR [#61](https://github.com/fieldsoftheworld/ftw-dataset-tools/pull/61) head) | `si/latest/si.parquet` | 809,044 | 5,103 (4,078 / 512 / 513) | 15,309 | 7 (MGRS) | 1.5 GB | ~1 h 50 min through `stac` (batched coverage) + ~3 min `docs`; a 9 min masks rerun filled 2,298 masks lost to worker deaths (ftwd PR [#62](https://github.com/fieldsoftheworld/ftw-dataset-tools/pull/62)), on an M-series laptop |
| at | 2026-09-05 | [`5f4a9191`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/5f4a9191) build, [`74d0b341`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/74d0b341) masks rerun (PR [#62](https://github.com/fieldsoftheworld/ftw-dataset-tools/pull/62)) | `at/latest/at.parquet` | 2,944,405 (656,619 after `filters/at.yaml`) | 11,242 (9,018 / 1,153 / 1,071) | 33,726 | 24 (MGRS) | 2.2G | ~1 h 57 min through `stac` (batched coverage) + ~3 min `docs`; a 36 min masks rerun created 15,442 masks the first run lost (no instance masks: text ids; worker deaths), on an M-series laptop |

## Notes

- **lu**: the source parquet carries no `hcat:code`, so crop composition is
  skipped and the collection ships only the `split`, `field-coverage` and
  `outline` styles (no `dominant-crop`) — `datasets.yaml` picks
  `field-coverage` for its thumbnail for the same reason.
- Wall time is for `tools/build.py <id> --through stac` plus the separate
  `tools/build.py <id> --only docs` call (see `README.md`'s
  [Adding a dataset](../README.md#adding-a-dataset)); it does not include
  `catalogize.py`, thumbnail rendering, or the imagery pass.
