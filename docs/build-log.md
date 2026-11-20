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

| be_wal_2022 (pilot, not published) | 2026-10-31 | [`3968be0f`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/3968be0f) | `be_wal/year=2022/be_wal-2022.parquet` | 341,968 (122,200 after filter) | 3,929 (3,189 / 358 / 382) | 19,645 | 13 (MGRS) | 378 MB | ~16 min first run (died at `stac` on the crop calendar 403) + 2 min 14 s rerun with masks reused + 68 s `docs`, r7i.4xlarge |
| de_sl_2026 (pilot, not published) | 2026-10-31 | [`3968be0f`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/3968be0f) | `de_sl/year=2026/de_sl-2026.parquet` | 54,038 (16,317 after filter) | 600 (464 / 65 / 71) | 3,000 | 1 (MGRS) | 67 MB | ~2 min first run (same 403) + 37 s rerun + 18 s `docs`, r7i.4xlarge |
| hr_2024 (pilot, not published) | 2026-10-31 | [`3968be0f`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/3968be0f) | `hr/year=2024/hr-2024.parquet` | 1,284,769 (929,854 after filter) | 11,611 (9,328 / 1,147 / 1,136) | 58,055 | 24 (MGRS) | 1.3 GB | 3 h 39 min through `stac`, mostly chip coverage over 85,867 grid cells + 2 min `docs`, r7i.4xlarge |
| ee_2024 (pilot, not published) | 2026-10-31 | [`3968be0f`](https://github.com/fieldsoftheworld/ftw-dataset-tools/commit/3968be0f) | `ee/year=2024/ee-2024.parquet` | 166,500 (86,826 after filter) | 7,882 (6,294 / 750 / 838) | 39,410 | 13 (MGRS) | 916 MB | 59 min through `stac` + 84 s `docs`, r7i.4xlarge |

## Notes

- **lu**: the source parquet carries no `hcat:code`, so crop composition is
  skipped and the collection ships only the `split`, `field-coverage` and
  `outline` styles (no `dominant-crop`) — `datasets.yaml` picks
  `field-coverage` for its thumbnail for the same reason.
- Wall time is for `tools/build.py <id> --through stac` plus the separate
  `tools/build.py <id> --only docs` call (see `README.md`'s
  [Adding a dataset](../README.md#adding-a-dataset)); it does not include
  `catalogize.py`, thumbnail rendering, or the imagery pass.
- **Region-year pilot (2026-10-31)**: be_wal_2022, de_sl_2026, hr_2024
  and ee_2024 were built on the AWS builder and reviewed, then **not uploaded**.
  The instance was terminated and the pilot will be rebuilt after mask
  changes in ftwd. Findings from the review:
  - Masks are rasterized in EPSG:4326 with 10 m converted to degrees on both
    axes, so pixels are 10 m north-south but 5.3 m (ee) to 7.1 m (hr)
    east-west, and chip widths vary (277-376 px against ~200 px). The
    per-chip UTM grid exists only for PlanetScope on ftwd's unmerged
    `feat/planetscope-source`. lu, si and at shipped with the same 4326
    masks.
  - The conformance gate fails PTL-AST-001 on every pilot collection: ftwd's
    `item_assets.thumbnail` declares no media type (dropped in ftwd 2a5264c).
  - `min_coverage: 0.01` (percent) keeps near-empty chips: under 5% coverage
    for 48% of hr chips, 25-30% for the others.
  - Grass-legume leys count as field (ee: 11% of field area; de_sl
    Ackerfutter: 26%) while permanent grass is excluded. This goes with the
    deferred pasture decision.
  - `dominant-crop` thumbnails at zoom 12 show chip squares, and hr's is a
    single colour (92% of its field area is code 200 "Arable land").
  - Masks agree with recorded coverage (r >= 0.998 on 600 random chips per
    dataset), every class is covered by its filter, and splits are about
    80/10/10 in 3x3 blocks.
