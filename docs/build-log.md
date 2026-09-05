# Build log

What each dataset build actually did: ftwd commit, source, counts, timing.
Attested at build time, not recomputed — if you rebuild a dataset, add a new
row rather than editing the old one, so this stays a record of what happened
rather than a claim about the current state of `catalog/`.

| Dataset | Date | ftwd commit | Source | Fields | Chips (train/val/test) | Masks | Sub-catalogs | Staging size | Wall time |
|---------|------|-------------|--------|--------|-------------------------|-------|---------------|---------------|-----------|
| lu | 2026-09-05 | [`73142362`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/73142362) (PR [#60](https://github.com/fieldsoftheworld/ftw-dataset-tools/pull/60) head) | `lu/latest/lu.parquet` | 87,997 | 775 (601 / 79 / 95) | 2,325 | 7 (MGRS) | 92 MB | ~25 min through `stac` + ~1 min `docs`, on an M-series laptop |
| si | building | | | | | | | | |
| at | building | | | | | | | | |

## Notes

- **lu**: the source parquet carries no `hcat:code`, so crop composition is
  skipped and the collection ships only the `split`, `field-coverage` and
  `outline` styles (no `dominant-crop`) — `datasets.yaml` picks
  `field-coverage` for its thumbnail for the same reason.
- Wall time is for `tools/build.py <id> --through stac` plus the separate
  `tools/build.py <id> --only docs` call (see `README.md`'s
  [Adding a dataset](../README.md#adding-a-dataset)); it does not include
  `catalogize.py`, thumbnail rendering, or the imagery pass.
