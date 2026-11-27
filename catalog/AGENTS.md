# Agent guide: Fields of the World Benchmark Data

Every claim in this file is quoted from a source or measured from the data.

## What this catalog is

Training and evaluation data for field boundary delineation models, one
collection per country or region. Each collection holds chip items on the FTW
grid (a fixed, MGRS-derived grid, so a cell id means the same square of ground
in every collection). Each chip item carries label masks — instance, semantic
2-class, semantic 3-class, and the DECODE boundary and distance layers, at 2.5 m
(800×800 for a 2 km chip) with boundary lines one to two pixels wide — its field
outlines (`field_boundaries`, `<item_id>_fields.parquet`: the fields cut to the
chip, in the masks' CRS), and the four Sentinel-2 quarterly cloudless mosaics
(Q1-Q4) of the collection's year, assets `q1_image` to `q4_image`, each also a
child item alongside it. Each is `stored`: a four-band GeoTIFF (red, green, blue,
NIR; 10 m, 200×200 for a 2 km chip) clipped to the masks' footprint and published
with it. Every chip has all four. Pixels a quarter's mosaic has no data for are
nodata (-32768), not filled; the chip item records each quarter's share in
`ftw:q1_nodata_pct` to `ftw:q4_nodata_pct` (0-100). Chip items also carry
`ftw:admin0_iso3`, `ftw:admin0_name`, `ftw:admin1_name` and `ftw:admin2_name`:
the country and the first- and second-level units containing the chip's centre
(or, when its centre is in none, overlapping it most), from
[FAO GAUL 2024](https://source.coop/nlebovits/gaul-l2-admin), empty where GAUL has
no name or no unit there.

Collection-level assets carry the field polygons the masks were cut from, their
boundary lines, the chips table (`<id>_chips.parquet`: footprint, field coverage,
admin names and, where the source has HCAT codes, dominant crop),
`<id>_field_embeddings.parquet` (per field, the mean and standard deviation of
each of 64 dimensions of the
[AlphaEarth Foundations](https://source.coop/tge-labs/aef) embeddings, `aef_*`,
CC-BY-4.0, and the
[OlmoEarth v1.3](https://source.coop/olmoearth/olmoearth-v1-3-embeddings)
embeddings, `olmoearth_*`, first 64 of 128 dimensions, under the
[OlmoEarth Artifact License](https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt);
join on the fields table's `id`), and `items.parquet`, a stac-geoparquet mirror
of every item.

Collections carry no train / validation / test split, except the five
`wri_trazo_ml` years, which keep their source's own (`ftw:split`, and `split` in
their chips table). The benchmark splits are in the root chips table,
[`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips.parquet):
one row per chip of every collection (`dataset`, `id` without the year suffix,
`block`, admin names, `license`, `license_url`, `license_category`,
`presence_only`, `geometry`, `bbox`) and one column per split scheme, each
`train`, `val`, `test` or null:

- `split_legacy`: the split each collection published before the table existed,
  chosen per collection, so a location can be test in one collection and train
  in another. Frozen: carried over from the previous table on every rebuild;
  null for chips added since.
- `split_predefined`: the source's own split (the `wri_trazo_ml` years); null
  elsewhere.
- `split_hash_v1`: from a stable hash of the chip's 3x3 block of grid cells,
  80 / 10 / 10, so a location has the same split in every collection and year.
- `split_admin2_v1` (unit in `unit_admin2_v1`): whole admin2 units balanced to
  80 / 10 / 10 of locations within each country; a unit with any presence-only
  chip is train. A row with no admin2 name joins its admin1's unit; a row with
  no country or admin1, and a country with fewer than three admin2 units, use
  the block as the unit. Frozen once published.

The field boundaries come from the
[harmonized field boundary catalog](https://source.coop/ftw/harmonized-field-data);
each collection's Source link below names the exact source collection.

## Accessing the data

Read `items.parquet` first. It lists every item — chips and their imagery items —
with its bbox, properties and asset hrefs, so a loader can select chips without
walking item JSON. Join it with the root `chips.parquet` for a split (an item id
is the chip id plus `_<year>`). Both are queryable in place over HTTPS:

```sql
INSTALL httpfs; LOAD httpfs;
SELECT i.id, c.split_admin2_v1 AS split, i."ftw:field_coverage_pct"
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/ee/ee_2024/items.parquet') i
JOIN read_parquet('https://data.source.coop/ftw/benchmark-data/chips.parquet') c
  ON c.dataset = 'ee_2024' AND i.id = c.id || '_2024'
WHERE c.split_admin2_v1 = 'train'
LIMIT 5;
```

Each collection's own [agent guide](https://source.coop/ftw/benchmark-data/ee/ee_2024/AGENTS.md)
(one per collection, at `https://source.coop/ftw/benchmark-data/<source>/<id>/AGENTS.md`)
documents its columns, its data quality notes and worked queries with their
results. The STAC entry point is
[catalog.json](https://data.source.coop/ftw/benchmark-data/catalog.json); the
same tree is browsable in the
[Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json).

Links in these documents are absolute: `source.coop` URLs are pages for people,
`data.source.coop` URLs are the bytes.

## Collections

<!-- collections:start -->
**180 collections · 3,082,670 chips**

| Collection | Chips | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- |
| [Cambodia/Vietnam (AI4SF) with splits — 2021](https://source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021) | 797 | 797 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ai4sf_ml](https://source.coop/ftw/harmonized-field-data/ai4sf_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021/collection.json) |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at/at_2018) | 14,493 | 14,493 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2018/collection.json) |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at/at_2019) | 14,491 | 14,491 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2019/collection.json) |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at/at_2020) | 14,496 | 14,496 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2020/collection.json) |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at/at_2021) | 14,506 | 14,506 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2021/collection.json) |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at/at_2022) | 14,473 | 14,473 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2022/collection.json) |
| [Austria — 2023](https://source.coop/ftw/benchmark-data/at/at_2023) | 14,484 | 14,484 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2023/collection.json) |
| [Austria — 2024](https://source.coop/ftw/benchmark-data/at/at_2024) | 14,497 | 14,497 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2024/collection.json) |
| [Austria — 2025](https://source.coop/ftw/benchmark-data/at/at_2025) | 14,516 | 14,516 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2025/collection.json) |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018) | 2,939 | 2,939 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018/collection.json) |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019) | 2,945 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019/collection.json) |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020) | 2,941 | 2,941 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020/collection.json) |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021) | 2,943 | 2,943 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021/collection.json) |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022) | 2,946 | 2,946 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022/collection.json) |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023) | 2,948 | 2,948 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023/collection.json) |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024) | 2,949 | 2,949 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024/collection.json) |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025) | 2,945 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025/collection.json) |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal/be_wal_2022) | 3,607 | 3,602 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/be_wal](https://source.coop/ftw/harmonized-field-data/be_wal) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal/be_wal_2022/collection.json) |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg/bg_2021) | 18,076 | 18,055 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2021/collection.json) |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg/bg_2022) | 18,123 | 18,102 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2022/collection.json) |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg/bg_2023) | 17,846 | 17,825 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2023/collection.json) |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg/bg_2024) | 18,225 | 18,204 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2024/collection.json) |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg/bg_2025) | 18,292 | 18,271 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2025/collection.json) |
| [West Bahia, Brazil — 2020](https://source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020) | 1,268 | 1,268 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/br_ba_lem](https://source.coop/ftw/harmonized-field-data/br_ba_lem) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020/collection.json) |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ag_2025) | 346 | 346 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ag_2025/collection.json) |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ai_2025) | 14 | 14 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ai_2025/collection.json) |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ar_2025) | 34 | 34 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ar_2025/collection.json) |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_be_2025) | 1,061 | 1,061 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_be_2025/collection.json) |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch/ch_bl_2025) | 142 | 142 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_bl_2025/collection.json) |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch/ch_fr_2025) | 363 | 363 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_fr_2025/collection.json) |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ge_2025) | 44 | 44 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ge_2025/collection.json) |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ju_2025) | 179 | 179 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ju_2025/collection.json) |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_lu_2025) | 354 | 354 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_lu_2025/collection.json) |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sg_2025) | 339 | 339 stored | [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sg_2025/collection.json) |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sh_2025) | 44 | 44 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sh_2025/collection.json) |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch/ch_so_2025) | 193 | 193 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_so_2025/collection.json) |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sz_2025) | 139 | 139 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sz_2025/collection.json) |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_tg_2025) | 187 | 187 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_tg_2025/collection.json) |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ur_2025) | 15 | 15 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ur_2025/collection.json) |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch/ch_vs_2025) | 145 | 145 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_vs_2025/collection.json) |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zg_2025) | 32 | 32 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_zg_2025/collection.json) |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zh_2025) | 423 | 423 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_zh_2025/collection.json) |
| [Czech — 2019](https://source.coop/ftw/benchmark-data/cz/cz_2019) | 14,444 | 14,437 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2019/collection.json) |
| [Czech — 2020](https://source.coop/ftw/benchmark-data/cz/cz_2020) | 14,576 | 14,569 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2020/collection.json) |
| [Czech — 2021](https://source.coop/ftw/benchmark-data/cz/cz_2021) | 14,572 | 14,565 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2021/collection.json) |
| [Czech — 2022](https://source.coop/ftw/benchmark-data/cz/cz_2022) | 14,604 | 14,597 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2022/collection.json) |
| [Czech — 2023](https://source.coop/ftw/benchmark-data/cz/cz_2023) | 15,060 | 15,053 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2023/collection.json) |
| [Czech — 2024](https://source.coop/ftw/benchmark-data/cz/cz_2024) | 15,064 | 15,057 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2024/collection.json) |
| [Czech — 2025](https://source.coop/ftw/benchmark-data/cz/cz_2025) | 14,836 | 14,829 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2025/collection.json) |
| [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds/de_nds_2025) | 10,891 | 10,891 stored | [DL-DE-BY-2.0](https://spdx.org/licenses/DL-DE-BY-2.0.html) | [harmonized/de_nds](https://source.coop/ftw/harmonized-field-data/de_nds) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_nds/de_nds_2025/collection.json) |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2023) | 3,452 | 3,452 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2023/collection.json) |
| [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2024) | 3,451 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2024/collection.json) |
| [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2025) | 3,451 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2025/collection.json) |
| [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk/dk_2017) | 9,688 | 9,688 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2017/collection.json) |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk/dk_2018) | 9,629 | 9,629 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2018/collection.json) |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk/dk_2019) | 9,624 | 9,624 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2019/collection.json) |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk/dk_2020) | 9,654 | 9,654 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2020/collection.json) |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk/dk_2021) | 9,647 | 9,647 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2021/collection.json) |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk/dk_2022) | 9,640 | 9,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2022/collection.json) |
| [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk/dk_2023) | 9,630 | 9,630 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2023/collection.json) |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk/dk_2024) | 9,672 | 9,672 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2024/collection.json) |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk/dk_2025) | 9,639 | 9,639 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2025/collection.json) |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021) | 13,468 | 13,468 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/ec_lt](https://source.coop/ftw/harmonized-field-data/ec_lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021/collection.json) |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee/ee_2017) | 7,745 | 7,745 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2017/collection.json) |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee/ee_2018) | 7,765 | 7,765 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2018/collection.json) |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee/ee_2019) | 7,787 | 7,787 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2019/collection.json) |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee/ee_2020) | 7,807 | 7,807 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2020/collection.json) |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee/ee_2021) | 7,853 | 7,853 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2021/collection.json) |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee/ee_2022) | 7,871 | 7,871 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2022/collection.json) |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee/ee_2023) | 7,606 | 7,606 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2023/collection.json) |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee/ee_2024) | 7,562 | 7,562 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2024/collection.json) |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_2025) | 53,145 | 53,124 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es/es_2025/collection.json) |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_po_2025) | 29,795 | 29,795 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es/es_po_2025/collection.json) |
| [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat/es_cat_2024) | 5,814 | 5,814 stored | [License](https://administraciodigital.gencat.cat/ca/dades/dades-obertes/informacio-practica/llicencies/) | [harmonized/es_cat](https://source.coop/ftw/harmonized-field-data/es_cat) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cat/es_cat_2024/collection.json) |
| [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm/es_cm_2024) | 17,833 | 17,833 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/es_cm](https://source.coop/ftw/harmonized-field-data/es_cm) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cm/es_cm_2024/collection.json) |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib/es_ib_2024) | 837 | 837 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_ib](https://source.coop/ftw/harmonized-field-data/es_ib) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_ib/es_ib_2024/collection.json) |
| [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc/es_vc_2024) | 4,926 | 4,926 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_vc](https://source.coop/ftw/harmonized-field-data/es_vc) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_vc/es_vc_2024/collection.json) |
| [Finland — 2020](https://source.coop/ftw/benchmark-data/fi/fi_2020) | 37,389 | 37,389 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2020/collection.json) |
| [Finland — 2021](https://source.coop/ftw/benchmark-data/fi/fi_2021) | 37,086 | 37,086 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2021/collection.json) |
| [Finland — 2022](https://source.coop/ftw/benchmark-data/fi/fi_2022) | 37,070 | 37,069 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2022/collection.json) |
| [Finland — 2023](https://source.coop/ftw/benchmark-data/fi/fi_2023) | 36,621 | 36,620 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2023/collection.json) |
| [Finland — 2024](https://source.coop/ftw/benchmark-data/fi/fi_2024) | 35,929 | 35,928 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2024/collection.json) |
| [Finland — 2025](https://source.coop/ftw/benchmark-data/fi/fi_2025) | 35,540 | 35,540 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2025/collection.json) |
| [France — 2017](https://source.coop/ftw/benchmark-data/fr/fr_2017) | 121,892 | 121,701 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2017/collection.json) |
| [France — 2018](https://source.coop/ftw/benchmark-data/fr/fr_2018) | 121,841 | 121,649 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2018/collection.json) |
| [France — 2019](https://source.coop/ftw/benchmark-data/fr/fr_2019) | 121,933 | 121,741 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2019/collection.json) |
| [France — 2020](https://source.coop/ftw/benchmark-data/fr/fr_2020) | 121,954 | 121,762 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2020/collection.json) |
| [France — 2021](https://source.coop/ftw/benchmark-data/fr/fr_2021) | 122,031 | 121,840 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2021/collection.json) |
| [France — 2022](https://source.coop/ftw/benchmark-data/fr/fr_2022) | 121,995 | 121,804 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2022/collection.json) |
| [France — 2023](https://source.coop/ftw/benchmark-data/fr/fr_2023) | 121,876 | 121,684 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2023/collection.json) |
| [France — 2024](https://source.coop/ftw/benchmark-data/fr/fr_2024) | 121,860 | 121,670 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2024/collection.json) |
| [GloCAB — 2017](https://source.coop/ftw/benchmark-data/glocab/glocab_2017) | 6,067 | 6,054 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2017/collection.json) |
| [GloCAB — 2018](https://source.coop/ftw/benchmark-data/glocab/glocab_2018) | 598 | 598 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2018/collection.json) |
| [GloCAB — 2019](https://source.coop/ftw/benchmark-data/glocab/glocab_2019) | 4,975 | 4,975 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2019/collection.json) |
| [GloCAB — 2020](https://source.coop/ftw/benchmark-data/glocab/glocab_2020) | 12,452 | 12,425 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2020/collection.json) |
| [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr/hr_2017) | 9,676 | 9,676 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2017/collection.json) |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr/hr_2018) | 9,704 | 9,704 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2018/collection.json) |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr/hr_2019) | 9,724 | 9,724 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2019/collection.json) |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr/hr_2020) | 9,703 | 9,703 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2020/collection.json) |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr/hr_2021) | 9,734 | 9,734 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2021/collection.json) |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr/hr_2022) | 9,715 | 9,715 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2022/collection.json) |
| [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr/hr_2023) | 9,680 | 9,680 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2023/collection.json) |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr/hr_2024) | 9,588 | 9,588 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2024/collection.json) |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie/ie_2022) | 16,734 | 16,734 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2022/collection.json) |
| [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie/ie_2023) | 16,762 | 16,762 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2023/collection.json) |
| [Ireland — 2024](https://source.coop/ftw/benchmark-data/ie/ie_2024) | 16,757 | 16,757 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2024/collection.json) |
| [India 10k with splits — 2020](https://source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020) | 2,410 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/in_10k_ml](https://source.coop/ftw/harmonized-field-data/in_10k_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020/collection.json) |
| [Italy, Tuscany — 2018](https://source.coop/ftw/benchmark-data/it_1/it_1_2018) | 4,515 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2018/collection.json) |
| [Italy, Tuscany — 2019](https://source.coop/ftw/benchmark-data/it_1/it_1_2019) | 4,713 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2019/collection.json) |
| [Italy, Tuscany — 2020](https://source.coop/ftw/benchmark-data/it_1/it_1_2020) | 4,673 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2020/collection.json) |
| [Italy, Tuscany — 2022](https://source.coop/ftw/benchmark-data/it_1/it_1_2022) | 4,679 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2022/collection.json) |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp/jp_2021) | 61,016 | 61,000 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2021/collection.json) |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp/jp_2022) | 60,961 | 60,945 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2022/collection.json) |
| [Japan — 2023](https://source.coop/ftw/benchmark-data/jp/jp_2023) | 60,957 | 60,941 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2023/collection.json) |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp/jp_2024) | 60,943 | 60,927 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2024/collection.json) |
| [Mapping Africa — 2017](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2017) | 6,972 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2017/collection.json) |
| [Mapping Africa — 2018](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2018) | 7,215 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2018/collection.json) |
| [Mapping Africa — 2019](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2019) | 7,343 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2019/collection.json) |
| [Mapping Africa — 2020](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2020) | 7,762 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2020/collection.json) |
| [Mapping Africa — 2021](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2021) | 7,141 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2021/collection.json) |
| [Mapping Africa — 2022](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2022) | 7,262 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2022/collection.json) |
| [Mapping Africa — 2023](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2023) | 6,966 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2023/collection.json) |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt/lt_2024) | 14,123 | 14,123 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt/lt_2024/collection.json) |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt/lt_2025) | 14,140 | 14,140 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt/lt_2025/collection.json) |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv/lv_2017) | 13,016 | 13,016 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2017/collection.json) |
| [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv/lv_2018) | 13,028 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2018/collection.json) |
| [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv/lv_2019) | 13,074 | 13,074 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2019/collection.json) |
| [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv/lv_2020) | 13,088 | 13,088 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2020/collection.json) |
| [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv/lv_2021) | 13,073 | 13,073 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2021/collection.json) |
| [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv/lv_2022) | 13,066 | 13,066 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2022/collection.json) |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv/lv_2023) | 13,028 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2023/collection.json) |
| [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv/lv_2024) | 13,056 | 13,056 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2024/collection.json) |
| [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv/lv_2025) | 13,061 | 13,061 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2025/collection.json) |
| [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl/nl_2017) | 7,600 | 7,594 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2017/collection.json) |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl/nl_2018) | 7,594 | 7,588 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2018/collection.json) |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl/nl_2019) | 7,582 | 7,576 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2019/collection.json) |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl/nl_2020) | 7,592 | 7,586 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2020/collection.json) |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl/nl_2021) | 7,596 | 7,590 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2021/collection.json) |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl/nl_2022) | 7,590 | 7,584 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2022/collection.json) |
| [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl/nl_2023) | 7,610 | 7,604 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2023/collection.json) |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl/nl_2024) | 7,584 | 7,578 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2024/collection.json) |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl/nl_2025) | 7,574 | 7,568 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2025/collection.json) |
| [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt/pt_2017) | 20,027 | 20,027 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2017/collection.json) |
| [Portugal — 2018](https://source.coop/ftw/benchmark-data/pt/pt_2018) | 20,085 | 20,085 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2018/collection.json) |
| [Portugal — 2019](https://source.coop/ftw/benchmark-data/pt/pt_2019) | 20,328 | 20,328 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2019/collection.json) |
| [Portugal — 2020](https://source.coop/ftw/benchmark-data/pt/pt_2020) | 20,030 | 20,030 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2020/collection.json) |
| [Portugal — 2021](https://source.coop/ftw/benchmark-data/pt/pt_2021) | 20,329 | 20,329 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2021/collection.json) |
| [Portugal — 2022](https://source.coop/ftw/benchmark-data/pt/pt_2022) | 20,361 | 20,361 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2022/collection.json) |
| [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt/pt_2023) | 20,002 | 20,002 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2023/collection.json) |
| [Portugal — 2025](https://source.coop/ftw/benchmark-data/pt/pt_2025) | 20,298 | 20,298 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2025/collection.json) |
| [Rwanda with splits — 2021](https://source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021) | 73 | 73 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/rw_rwanda_ml](https://source.coop/ftw/harmonized-field-data/rw_rwanda_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021/collection.json) |
| [Sweden — 2017](https://source.coop/ftw/benchmark-data/se/se_2017) | 32,935 | 32,935 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2017/collection.json) |
| [Sweden — 2018](https://source.coop/ftw/benchmark-data/se/se_2018) | 32,623 | 32,623 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2018/collection.json) |
| [Sweden — 2019](https://source.coop/ftw/benchmark-data/se/se_2019) | 32,880 | 32,880 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2019/collection.json) |
| [Sweden — 2020](https://source.coop/ftw/benchmark-data/se/se_2020) | 32,771 | 32,771 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2020/collection.json) |
| [Sweden — 2021](https://source.coop/ftw/benchmark-data/se/se_2021) | 32,822 | 32,822 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2021/collection.json) |
| [Sweden — 2022](https://source.coop/ftw/benchmark-data/se/se_2022) | 32,742 | 32,742 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2022/collection.json) |
| [Sweden — 2023](https://source.coop/ftw/benchmark-data/se/se_2023) | 32,640 | 32,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2023/collection.json) |
| [Sweden — 2024](https://source.coop/ftw/benchmark-data/se/se_2024) | 32,410 | 32,410 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2024/collection.json) |
| [Sweden — 2025](https://source.coop/ftw/benchmark-data/se/se_2025) | 32,552 | 32,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2025/collection.json) |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si/si_2019) | 4,300 | 4,300 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2019/collection.json) |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si/si_2020) | 4,282 | 4,282 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2020/collection.json) |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si/si_2021) | 4,286 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2021/collection.json) |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si/si_2022) | 4,286 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2022/collection.json) |
| [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si/si_2023) | 4,287 | 4,287 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2023/collection.json) |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si/si_2024) | 4,291 | 4,291 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2024/collection.json) |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk/sk_2018) | 9,806 | 9,785 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2018/collection.json) |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk/sk_2019) | 9,856 | 9,835 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2019/collection.json) |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk/sk_2020) | 9,885 | 9,864 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2020/collection.json) |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk/sk_2021) | 9,875 | 9,854 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2021/collection.json) |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk/sk_2022) | 9,866 | 9,845 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2022/collection.json) |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk/sk_2023) | 9,571 | 9,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2023/collection.json) |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk/sk_2024) | 9,986 | 9,965 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2024/collection.json) |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk/sk_2025) | 9,985 | 9,964 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2025/collection.json) |
| [Trazo with splits — 2020](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020) | 3,687 | 3,686 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020/collection.json) |
| [Trazo with splits — 2021](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021) | 498 | 498 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021/collection.json) |
| [Trazo with splits — 2022](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022) | 590 | 590 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022/collection.json) |
| [Trazo with splits — 2023](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023) | 499 | 499 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023/collection.json) |
| [Trazo with splits — 2024](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024) | 1,360 | 1,358 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/collection.json) |
| [South Africa (Fusion) with splits — 2017](https://source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017) | 239 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/za_fusion_ml](https://source.coop/ftw/harmonized-field-data/za_fusion_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Cambodia/Vietnam (AI4SF) with splits — 2021](https://source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021) | 797 | 797 stored | none |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at/at_2018) | 14,493 | 14,493 stored | 14,493 |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at/at_2019) | 14,491 | 14,491 stored | 14,491 |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at/at_2020) | 14,496 | 14,496 stored | 14,496 |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at/at_2021) | 14,506 | 14,506 stored | 14,506 |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at/at_2022) | 14,473 | 14,473 stored | 14,473 |
| [Austria — 2023](https://source.coop/ftw/benchmark-data/at/at_2023) | 14,484 | 14,484 stored | 14,484 |
| [Austria — 2024](https://source.coop/ftw/benchmark-data/at/at_2024) | 14,497 | 14,497 stored | 14,497 |
| [Austria — 2025](https://source.coop/ftw/benchmark-data/at/at_2025) | 14,516 | 14,516 stored | 14,516 |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018) | 2,939 | 2,939 stored | 2,939 |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020) | 2,941 | 2,941 stored | 2,941 |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021) | 2,943 | 2,943 stored | 2,943 |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022) | 2,946 | 2,946 stored | 2,946 |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023) | 2,948 | 2,948 stored | 2,948 |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024) | 2,949 | 2,949 stored | 2,949 |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal/be_wal_2022) | 3,607 | 3,602 stored | 3,607 |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg/bg_2021) | 18,076 | 18,055 stored | none |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg/bg_2022) | 18,123 | 18,102 stored | none |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg/bg_2023) | 17,846 | 17,825 stored | none |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg/bg_2024) | 18,225 | 18,204 stored | none |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg/bg_2025) | 18,292 | 18,271 stored | none |
| [West Bahia, Brazil — 2020](https://source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020) | 1,268 | 1,268 stored | none |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ag_2025) | 346 | 346 stored | 346 |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ai_2025) | 14 | 14 stored | 14 |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ar_2025) | 34 | 34 stored | 34 |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_be_2025) | 1,061 | 1,061 stored | 1,061 |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch/ch_bl_2025) | 142 | 142 stored | 142 |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch/ch_fr_2025) | 363 | 363 stored | 363 |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ge_2025) | 44 | 44 stored | 44 |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ju_2025) | 179 | 179 stored | 179 |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_lu_2025) | 354 | 354 stored | 354 |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sg_2025) | 339 | 339 stored | 339 |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sh_2025) | 44 | 44 stored | 44 |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch/ch_so_2025) | 193 | 193 stored | 193 |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sz_2025) | 139 | 139 stored | 139 |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_tg_2025) | 187 | 187 stored | 187 |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ur_2025) | 15 | 15 stored | 15 |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch/ch_vs_2025) | 145 | 145 stored | 145 |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zg_2025) | 32 | 32 stored | 32 |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zh_2025) | 423 | 423 stored | 423 |
| [Czech — 2019](https://source.coop/ftw/benchmark-data/cz/cz_2019) | 14,444 | 14,437 stored | 14,444 |
| [Czech — 2020](https://source.coop/ftw/benchmark-data/cz/cz_2020) | 14,576 | 14,569 stored | 14,576 |
| [Czech — 2021](https://source.coop/ftw/benchmark-data/cz/cz_2021) | 14,572 | 14,565 stored | 14,572 |
| [Czech — 2022](https://source.coop/ftw/benchmark-data/cz/cz_2022) | 14,604 | 14,597 stored | 14,604 |
| [Czech — 2023](https://source.coop/ftw/benchmark-data/cz/cz_2023) | 15,060 | 15,053 stored | 15,060 |
| [Czech — 2024](https://source.coop/ftw/benchmark-data/cz/cz_2024) | 15,064 | 15,057 stored | 15,064 |
| [Czech — 2025](https://source.coop/ftw/benchmark-data/cz/cz_2025) | 14,836 | 14,829 stored | 14,836 |
| [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds/de_nds_2025) | 10,891 | 10,891 stored | 10,891 |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2023) | 3,452 | 3,452 stored | none |
| [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2024) | 3,451 | 3,451 stored | none |
| [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2025) | 3,451 | 3,451 stored | none |
| [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk/dk_2017) | 9,688 | 9,688 stored | 9,688 |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk/dk_2018) | 9,629 | 9,629 stored | 9,629 |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk/dk_2019) | 9,624 | 9,624 stored | 9,624 |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk/dk_2020) | 9,654 | 9,654 stored | 9,654 |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk/dk_2021) | 9,647 | 9,647 stored | 9,647 |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk/dk_2022) | 9,640 | 9,640 stored | 9,640 |
| [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk/dk_2023) | 9,630 | 9,630 stored | 9,630 |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk/dk_2024) | 9,672 | 9,672 stored | 9,672 |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk/dk_2025) | 9,639 | 9,639 stored | 9,639 |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021) | 13,468 | 13,468 stored | 13,468 |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee/ee_2017) | 7,745 | 7,745 stored | 7,745 |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee/ee_2018) | 7,765 | 7,765 stored | 7,765 |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee/ee_2019) | 7,787 | 7,787 stored | 7,787 |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee/ee_2020) | 7,807 | 7,807 stored | 7,807 |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee/ee_2021) | 7,853 | 7,853 stored | 7,853 |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee/ee_2022) | 7,871 | 7,871 stored | 7,871 |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee/ee_2023) | 7,606 | 7,606 stored | 7,606 |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee/ee_2024) | 7,562 | 7,562 stored | 7,562 |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_2025) | 53,145 | 53,124 stored | 53,039 |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_po_2025) | 29,795 | 29,795 stored | 29,795 |
| [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat/es_cat_2024) | 5,814 | 5,814 stored | 5,814 |
| [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm/es_cm_2024) | 17,833 | 17,833 stored | 17,833 |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib/es_ib_2024) | 837 | 837 stored | none |
| [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc/es_vc_2024) | 4,926 | 4,926 stored | 4,926 |
| [Finland — 2020](https://source.coop/ftw/benchmark-data/fi/fi_2020) | 37,389 | 37,389 stored | 37,389 |
| [Finland — 2021](https://source.coop/ftw/benchmark-data/fi/fi_2021) | 37,086 | 37,086 stored | 37,086 |
| [Finland — 2022](https://source.coop/ftw/benchmark-data/fi/fi_2022) | 37,070 | 37,069 stored | 37,070 |
| [Finland — 2023](https://source.coop/ftw/benchmark-data/fi/fi_2023) | 36,621 | 36,620 stored | 36,621 |
| [Finland — 2024](https://source.coop/ftw/benchmark-data/fi/fi_2024) | 35,929 | 35,928 stored | 35,929 |
| [Finland — 2025](https://source.coop/ftw/benchmark-data/fi/fi_2025) | 35,540 | 35,540 stored | 35,540 |
| [France — 2017](https://source.coop/ftw/benchmark-data/fr/fr_2017) | 121,892 | 121,701 stored | 121,892 |
| [France — 2018](https://source.coop/ftw/benchmark-data/fr/fr_2018) | 121,841 | 121,649 stored | 121,841 |
| [France — 2019](https://source.coop/ftw/benchmark-data/fr/fr_2019) | 121,933 | 121,741 stored | 121,933 |
| [France — 2020](https://source.coop/ftw/benchmark-data/fr/fr_2020) | 121,954 | 121,762 stored | 121,954 |
| [France — 2021](https://source.coop/ftw/benchmark-data/fr/fr_2021) | 122,031 | 121,840 stored | 122,031 |
| [France — 2022](https://source.coop/ftw/benchmark-data/fr/fr_2022) | 121,995 | 121,804 stored | 121,995 |
| [France — 2023](https://source.coop/ftw/benchmark-data/fr/fr_2023) | 121,876 | 121,684 stored | 121,840 |
| [France — 2024](https://source.coop/ftw/benchmark-data/fr/fr_2024) | 121,860 | 121,670 stored | 121,829 |
| [GloCAB — 2017](https://source.coop/ftw/benchmark-data/glocab/glocab_2017) | 6,067 | 6,054 stored | none |
| [GloCAB — 2018](https://source.coop/ftw/benchmark-data/glocab/glocab_2018) | 598 | 598 stored | none |
| [GloCAB — 2019](https://source.coop/ftw/benchmark-data/glocab/glocab_2019) | 4,975 | 4,975 stored | none |
| [GloCAB — 2020](https://source.coop/ftw/benchmark-data/glocab/glocab_2020) | 12,452 | 12,425 stored | none |
| [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr/hr_2017) | 9,676 | 9,676 stored | 9,676 |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr/hr_2018) | 9,704 | 9,704 stored | 9,704 |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr/hr_2019) | 9,724 | 9,724 stored | 9,724 |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr/hr_2020) | 9,703 | 9,703 stored | 9,703 |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr/hr_2021) | 9,734 | 9,734 stored | 9,734 |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr/hr_2022) | 9,715 | 9,715 stored | 9,715 |
| [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr/hr_2023) | 9,680 | 9,680 stored | 9,680 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr/hr_2024) | 9,588 | 9,588 stored | 9,588 |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie/ie_2022) | 16,734 | 16,734 stored | 16,734 |
| [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie/ie_2023) | 16,762 | 16,762 stored | 16,762 |
| [Ireland — 2024](https://source.coop/ftw/benchmark-data/ie/ie_2024) | 16,757 | 16,757 stored | 16,757 |
| [India 10k with splits — 2020](https://source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020) | 2,410 | — | — |
| [Italy, Tuscany — 2018](https://source.coop/ftw/benchmark-data/it_1/it_1_2018) | 4,515 | — | — |
| [Italy, Tuscany — 2019](https://source.coop/ftw/benchmark-data/it_1/it_1_2019) | 4,713 | — | — |
| [Italy, Tuscany — 2020](https://source.coop/ftw/benchmark-data/it_1/it_1_2020) | 4,673 | — | — |
| [Italy, Tuscany — 2022](https://source.coop/ftw/benchmark-data/it_1/it_1_2022) | 4,679 | — | — |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp/jp_2021) | 61,016 | 61,000 stored | none |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp/jp_2022) | 60,961 | 60,945 stored | none |
| [Japan — 2023](https://source.coop/ftw/benchmark-data/jp/jp_2023) | 60,957 | 60,941 stored | none |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp/jp_2024) | 60,943 | 60,927 stored | none |
| [Mapping Africa — 2017](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2017) | 6,972 | — | — |
| [Mapping Africa — 2018](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2018) | 7,215 | — | — |
| [Mapping Africa — 2019](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2019) | 7,343 | — | — |
| [Mapping Africa — 2020](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2020) | 7,762 | — | — |
| [Mapping Africa — 2021](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2021) | 7,141 | — | — |
| [Mapping Africa — 2022](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2022) | 7,262 | — | — |
| [Mapping Africa — 2023](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2023) | 6,966 | — | — |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt/lt_2024) | 14,123 | 14,123 stored | 14,123 |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt/lt_2025) | 14,140 | 14,140 stored | 14,140 |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv/lv_2017) | 13,016 | 13,016 stored | 13,016 |
| [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv/lv_2018) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv/lv_2019) | 13,074 | 13,074 stored | 13,074 |
| [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv/lv_2020) | 13,088 | 13,088 stored | 13,088 |
| [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv/lv_2021) | 13,073 | 13,073 stored | 13,073 |
| [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv/lv_2022) | 13,066 | 13,066 stored | 13,066 |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv/lv_2023) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv/lv_2024) | 13,056 | 13,056 stored | 13,056 |
| [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv/lv_2025) | 13,061 | 13,061 stored | 13,061 |
| [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl/nl_2017) | 7,600 | 7,594 stored | 7,587 |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl/nl_2018) | 7,594 | 7,588 stored | 7,569 |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl/nl_2019) | 7,582 | 7,576 stored | 7,582 |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl/nl_2020) | 7,592 | 7,586 stored | 7,592 |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl/nl_2021) | 7,596 | 7,590 stored | 7,596 |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl/nl_2022) | 7,590 | 7,584 stored | 7,590 |
| [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl/nl_2023) | 7,610 | 7,604 stored | 7,610 |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl/nl_2024) | 7,584 | 7,578 stored | 7,584 |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl/nl_2025) | 7,574 | 7,568 stored | 7,574 |
| [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt/pt_2017) | 20,027 | 20,027 stored | 20,027 |
| [Portugal — 2018](https://source.coop/ftw/benchmark-data/pt/pt_2018) | 20,085 | 20,085 stored | 20,085 |
| [Portugal — 2019](https://source.coop/ftw/benchmark-data/pt/pt_2019) | 20,328 | 20,328 stored | 20,328 |
| [Portugal — 2020](https://source.coop/ftw/benchmark-data/pt/pt_2020) | 20,030 | 20,030 stored | 20,030 |
| [Portugal — 2021](https://source.coop/ftw/benchmark-data/pt/pt_2021) | 20,329 | 20,329 stored | 20,329 |
| [Portugal — 2022](https://source.coop/ftw/benchmark-data/pt/pt_2022) | 20,361 | 20,361 stored | 20,361 |
| [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt/pt_2023) | 20,002 | 20,002 stored | 20,002 |
| [Portugal — 2025](https://source.coop/ftw/benchmark-data/pt/pt_2025) | 20,298 | 20,298 stored | 20,298 |
| [Rwanda with splits — 2021](https://source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021) | 73 | 73 stored | none |
| [Sweden — 2017](https://source.coop/ftw/benchmark-data/se/se_2017) | 32,935 | 32,935 stored | 32,935 |
| [Sweden — 2018](https://source.coop/ftw/benchmark-data/se/se_2018) | 32,623 | 32,623 stored | 32,623 |
| [Sweden — 2019](https://source.coop/ftw/benchmark-data/se/se_2019) | 32,880 | 32,880 stored | 32,880 |
| [Sweden — 2020](https://source.coop/ftw/benchmark-data/se/se_2020) | 32,771 | 32,771 stored | 32,771 |
| [Sweden — 2021](https://source.coop/ftw/benchmark-data/se/se_2021) | 32,822 | 32,822 stored | 32,822 |
| [Sweden — 2022](https://source.coop/ftw/benchmark-data/se/se_2022) | 32,742 | 32,742 stored | 32,742 |
| [Sweden — 2023](https://source.coop/ftw/benchmark-data/se/se_2023) | 32,640 | 32,640 stored | 32,640 |
| [Sweden — 2024](https://source.coop/ftw/benchmark-data/se/se_2024) | 32,410 | 32,410 stored | 32,410 |
| [Sweden — 2025](https://source.coop/ftw/benchmark-data/se/se_2025) | 32,552 | 32,552 stored | 32,552 |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si/si_2019) | 4,300 | 4,300 stored | 4,300 |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si/si_2020) | 4,282 | 4,282 stored | 4,282 |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si/si_2021) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si/si_2022) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si/si_2023) | 4,287 | 4,287 stored | 4,287 |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si/si_2024) | 4,291 | 4,291 stored | 4,291 |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk/sk_2018) | 9,806 | 9,785 stored | 9,806 |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk/sk_2019) | 9,856 | 9,835 stored | 9,856 |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk/sk_2020) | 9,885 | 9,864 stored | 9,885 |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk/sk_2021) | 9,875 | 9,854 stored | 9,875 |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk/sk_2022) | 9,866 | 9,845 stored | 9,866 |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk/sk_2023) | 9,571 | 9,552 stored | 9,571 |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk/sk_2024) | 9,986 | 9,965 stored | 9,986 |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk/sk_2025) | 9,985 | 9,964 stored | 9,985 |
| [Trazo with splits — 2020](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020) | 3,687 | 3,686 stored | none |
| [Trazo with splits — 2021](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021) | 498 | 498 stored | none |
| [Trazo with splits — 2022](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022) | 590 | 590 stored | none |
| [Trazo with splits — 2023](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023) | 499 | 499 stored | none |
| [Trazo with splits — 2024](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024) | 1,360 | 1,358 stored | none |
| [South Africa (Fusion) with splits — 2017](https://source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017) | 239 | — | — |

`stored` means four-band GeoTIFFs (red, green, blue, NIR at 10 m) clipped to the chip's mask footprint and published with it: the Q1-Q4 Sentinel-2 quarterly cloudless mosaics of the collection's year (and planting/harvest scenes, where a collection has them). `linked` means the chip's imagery items point at whole Sentinel-2 scenes on the source STAC API, for a reader to window. A chip with no imagery still carries its masks (and its row in the root chips table) — pair it with imagery of your own, on the footprint in `items.parquet`.
<!-- collections:end -->

Every number above is measured, not declared: chips from each collection's
`<id>_chips.parquet`, field polygons from the `<id>_fields` table the masks were
cut from, imagery from the imagery child items, and crop labels from the
`ftw:hcat_dominant_code` property in `items.parquet`. Do not assume a collection
carries crop labels because its neighbours do — check the coverage table, or the
collection's own assets.

## Provenance and versioning

This edition is `2.0.0-alpha.1`, and while it is in alpha collections are
updated in place — the `updated` stamp in a collection's `collection.json` is
when it was last rebuilt. Every collection is rebuildable from its recipe in
the [source repository](https://github.com/fieldsoftheworld/benchmark-data-catalog)
with [ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools).
Version 1.0 of the benchmark, superseded by this one, remains at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world);
the paper is [Fields of The World (2024)](https://arxiv.org/abs/2409.16252).

## License

Each collection carries the license of the field boundary data it was cut from
(the License column above). Derived masks and imagery chips are published under
the same terms as their source. Sentinel-2 imagery is Copernicus data, free and
open.
