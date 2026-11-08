# Agent guide: Fields of the World Benchmark Data

Every claim in this file is quoted from a source or measured from the data.

## What this catalog is

Training and evaluation data for field boundary delineation models, one
collection per country or region. Each collection holds chip items on the FTW
grid (a fixed, MGRS-derived grid, so a cell id means the same square of ground
in every collection). Each chip item carries label masks — instance, semantic
2-class, semantic 3-class, and the DECODE boundary and distance layers — and,
where the collection has imagery, the four Sentinel-2 quarterly cloudless
mosaics (Q1-Q4) of the collection's year as child items alongside it, assets
`q1_image` to `q4_image`. Each is `stored`: a four-band GeoTIFF (red, green,
blue, NIR; 10 m) clipped to the chip's mask grid and published with it. Pixels
a quarter's mosaic has no data for are nodata (-32768), not filled. Imagery can
also be `linked` (the whole scene COG on the source STAC API, for the reader to
window); the coverage table below says which, per collection, and a collection
may carry no imagery at all. Every
chip carries a `ftw:split` assignment of `train`, `val` or `test`, made in
spatial blocks.

Collection-level assets carry the field polygons the masks were cut from, their
boundary lines, the chips table with split assignments and field coverage, and
`items.parquet`, a stac-geoparquet mirror of every item.

The field boundaries come from the
[harmonized field boundary catalog](https://source.coop/ftw/harmonized-field-data);
each collection's Source link below names the exact source collection.

## Accessing the data

Read `items.parquet` first. It lists every item — chips and their imagery items —
with its bbox, split and asset hrefs, so a loader can select chips without
walking item JSON. It is queryable in place over HTTPS:

```sql
INSTALL spatial; LOAD spatial;
SELECT id, "ftw:split", "ftw:field_coverage_pct"
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/ee_2024/items.parquet')
WHERE "ftw:split" = 'train'
LIMIT 5;
```

Each collection's own [agent guide](https://source.coop/ftw/benchmark-data/ee_2024/AGENTS.md)
(one per collection, at `https://source.coop/ftw/benchmark-data/<id>/AGENTS.md`)
documents its columns, its data quality notes and worked queries with their
results. The STAC entry point is
[catalog.json](https://data.source.coop/ftw/benchmark-data/catalog.json); the
same tree is browsable in the
[Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json).

Links in these documents are absolute: `source.coop` URLs are pages for people,
`data.source.coop` URLs are the bytes.

## Collections

<!-- collections:start -->
**127 collections · 1,399,387 chips · 199,528,267 field polygons**

| Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at_2018) | 14,493 | 11,621/1,433/1,439 | 14,493 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2018/collection.json) |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at_2019) | 14,491 | 11,659/1,389/1,443 | 14,491 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2019/collection.json) |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at_2020) | 14,496 | 11,730/1,401/1,365 | 14,496 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2020/collection.json) |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at_2021) | 14,506 | 11,639/1,420/1,447 | 14,506 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2021/collection.json) |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at_2022) | 14,473 | 11,654/1,422/1,397 | 14,473 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2022/collection.json) |
| [Austria — 2023](https://source.coop/ftw/benchmark-data/at_2023) | 14,484 | 11,694/1,425/1,365 | 14,484 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2023/collection.json) |
| [Austria — 2024](https://source.coop/ftw/benchmark-data/at_2024) | 14,497 | 11,659/1,429/1,409 | 14,497 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2024/collection.json) |
| [Austria — 2025](https://source.coop/ftw/benchmark-data/at_2025) | 14,516 | 11,669/1,428/1,419 | 14,516 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2025/collection.json) |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg_2018) | 2,939 | 2,366/303/270 | 2,939 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2018/collection.json) |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg_2019) | 2,945 | 2,373/314/258 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2019/collection.json) |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg_2020) | 2,941 | 2,370/313/258 | 2,941 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2020/collection.json) |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg_2021) | 2,943 | 2,372/314/257 | 2,943 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2021/collection.json) |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg_2022) | 2,946 | 2,371/319/256 | 2,946 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2022/collection.json) |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg_2023) | 2,948 | 2,370/321/257 | 2,948 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2023/collection.json) |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg_2024) | 2,949 | 2,372/321/256 | 2,949 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2024/collection.json) |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg_2025) | 2,945 | 2,370/320/255 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2025/collection.json) |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,607 | 2,871/364/372 | 3,602 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/be_wal](https://source.coop/ftw/harmonized-field-data/be_wal) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal_2022/collection.json) |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg_2021) | 18,076 | 14,434/1,848/1,794 | 18,055 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2021/collection.json) |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg_2022) | 18,123 | 14,505/1,835/1,783 | 18,102 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2022/collection.json) |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg_2023) | 17,846 | 14,283/1,753/1,810 | 17,825 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2023/collection.json) |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg_2024) | 18,225 | 14,490/1,876/1,859 | 18,204 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2024/collection.json) |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg_2025) | 18,292 | 14,642/1,833/1,817 | 18,271 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2025/collection.json) |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch_ag_2025) | 346 | 267/38/41 | 346 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ag_2025/collection.json) |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ai_2025) | 14 | 10/0/4 | 14 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ai_2025/collection.json) |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ar_2025) | 34 | 24/0/10 | 34 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ar_2025/collection.json) |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch_be_2025) | 1,061 | 857/89/115 | 1,061 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_be_2025/collection.json) |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch_bl_2025) | 142 | 95/13/34 | 142 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_bl_2025/collection.json) |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch_fr_2025) | 363 | 281/29/53 | 363 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_fr_2025/collection.json) |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch_ge_2025) | 44 | 27/8/9 | 44 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ge_2025/collection.json) |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch_ju_2025) | 179 | 138/7/34 | 179 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ju_2025/collection.json) |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch_lu_2025) | 354 | 272/39/43 | 354 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_lu_2025/collection.json) |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch_sg_2025) | 339 | 275/38/26 | 339 stored | [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sg_2025/collection.json) |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch_sh_2025) | 44 | 34/1/9 | 44 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sh_2025/collection.json) |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch_so_2025) | 193 | 143/20/30 | 193 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_so_2025/collection.json) |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch_sz_2025) | 139 | 97/15/27 | 139 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sz_2025/collection.json) |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch_tg_2025) | 187 | 143/20/24 | 187 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_tg_2025/collection.json) |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch_ur_2025) | 15 | 8/0/7 | 15 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ur_2025/collection.json) |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch_vs_2025) | 145 | 113/9/23 | 145 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_vs_2025/collection.json) |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 23/0/9 | 32 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_zg_2025/collection.json) |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch_zh_2025) | 423 | 336/34/53 | 423 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_zh_2025/collection.json) |
| [Czech — 2019](https://source.coop/ftw/benchmark-data/cz_2019) | 14,444 | 11,571/1,427/1,446 | 14,437 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2019/collection.json) |
| [Czech — 2020](https://source.coop/ftw/benchmark-data/cz_2020) | 14,576 | 11,683/1,442/1,451 | 14,569 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2020/collection.json) |
| [Czech — 2021](https://source.coop/ftw/benchmark-data/cz_2021) | 14,572 | 11,611/1,477/1,484 | 14,565 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2021/collection.json) |
| [Czech — 2022](https://source.coop/ftw/benchmark-data/cz_2022) | 14,604 | 11,726/1,434/1,444 | 14,597 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2022/collection.json) |
| [Czech — 2023](https://source.coop/ftw/benchmark-data/cz_2023) | 15,060 | 12,027/1,511/1,522 | 15,053 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2023/collection.json) |
| [Czech — 2024](https://source.coop/ftw/benchmark-data/cz_2024) | 15,064 | 11,996/1,547/1,521 | 15,057 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2024/collection.json) |
| [Czech — 2025](https://source.coop/ftw/benchmark-data/cz_2025) | 14,836 | 11,898/1,462/1,476 | 14,829 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz_2025/collection.json) |
| [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds_2025) | 10,891 | 8,714/1,075/1,102 | 10,891 stored | [DL-DE-BY-2.0](https://spdx.org/licenses/DL-DE-BY-2.0.html) | [harmonized/de_nds](https://source.coop/ftw/harmonized-field-data/de_nds) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_nds_2025/collection.json) |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 2,753/346/353 | 3,452 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh_2023/collection.json) |
| [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh_2024) | 3,451 | 2,752/346/353 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh_2024/collection.json) |
| [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh_2025) | 3,451 | 2,752/346/353 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh_2025/collection.json) |
| [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk_2017) | 9,688 | 7,750/999/939 | 9,688 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2017/collection.json) |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 7,636/999/994 | 9,629 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2018/collection.json) |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 7,641/1,005/978 | 9,624 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2019/collection.json) |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 7,672/993/989 | 9,654 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2020/collection.json) |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 7,621/989/1,037 | 9,647 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2021/collection.json) |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 7,618/988/1,034 | 9,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2022/collection.json) |
| [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk_2023) | 9,630 | 7,614/1,005/1,011 | 9,630 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2023/collection.json) |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk_2024) | 9,672 | 7,724/963/985 | 9,672 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2024/collection.json) |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk_2025) | 9,639 | 7,663/982/994 | 9,639 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2025/collection.json) |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt_2021) | 13,468 | 10,786/1,349/1,333 | 13,468 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/ec_lt](https://source.coop/ftw/harmonized-field-data/ec_lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ec_lt_2021/collection.json) |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee_2017) | 7,745 | 6,194/776/775 | 7,745 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2017/collection.json) |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee_2018) | 7,765 | 6,249/734/782 | 7,765 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2018/collection.json) |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee_2019) | 7,787 | 6,179/749/859 | 7,787 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2019/collection.json) |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee_2020) | 7,807 | 6,228/765/814 | 7,807 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2020/collection.json) |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee_2021) | 7,853 | 6,231/800/822 | 7,853 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2021/collection.json) |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee_2022) | 7,871 | 6,229/804/838 | 7,871 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2022/collection.json) |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee_2023) | 7,606 | 6,011/764/831 | 7,606 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2023/collection.json) |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 7,562 | 6,037/733/792 | 7,562 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2024/collection.json) |
| [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat_2024) | 5,814 | 4,613/614/587 | 5,814 stored | [License](https://administraciodigital.gencat.cat/ca/dades/dades-obertes/informacio-practica/llicencies/) | [harmonized/es_cat](https://source.coop/ftw/harmonized-field-data/es_cat) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cat_2024/collection.json) |
| [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm_2024) | 17,833 | 14,289/1,781/1,763 | 17,833 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/es_cm](https://source.coop/ftw/harmonized-field-data/es_cm) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cm_2024/collection.json) |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 661/87/89 | 837 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_ib](https://source.coop/ftw/harmonized-field-data/es_ib) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_ib_2024/collection.json) |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es_po_2025) | 29,795 | 23,795/2,995/3,005 | 29,795 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_po_2025/collection.json) |
| [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc_2024) | 4,926 | 3,983/443/500 | 4,926 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_vc](https://source.coop/ftw/harmonized-field-data/es_vc) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_vc_2024/collection.json) |
| [Finland — 2023](https://source.coop/ftw/benchmark-data/fi_2023) | 36,621 | 29,198/3,714/3,709 | 36,620 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi_2023/collection.json) |
| [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr_2017) | 9,676 | 7,792/932/952 | 9,676 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2017/collection.json) |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 7,735/999/970 | 9,704 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2018/collection.json) |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 7,748/970/1,006 | 9,724 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2019/collection.json) |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 7,718/1,004/981 | 9,703 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2020/collection.json) |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 7,816/959/959 | 9,734 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2021/collection.json) |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 7,781/976/958 | 9,715 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2022/collection.json) |
| [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr_2023) | 9,680 | 7,721/975/984 | 9,680 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2023/collection.json) |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 7,605/973/1,010 | 9,588 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2024/collection.json) |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 13,374/1,653/1,707 | 16,734 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2022/collection.json) |
| [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie_2023) | 16,762 | 13,469/1,651/1,642 | 16,762 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2023/collection.json) |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 48,849/6,093/6,074 | 61,000 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2021/collection.json) |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 48,799/6,146/6,016 | 60,945 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2022/collection.json) |
| [Japan — 2023](https://source.coop/ftw/benchmark-data/jp_2023) | 60,957 | 48,800/6,146/6,011 | 60,941 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2023/collection.json) |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 48,789/6,143/6,011 | 60,927 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2024/collection.json) |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 11,297/1,399/1,427 | 14,123 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2024/collection.json) |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 11,323/1,388/1,429 | 14,140 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2025/collection.json) |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 10,383/1,308/1,325 | 13,016 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2017/collection.json) |
| [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv_2018) | 13,028 | 10,385/1,317/1,326 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2018/collection.json) |
| [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv_2019) | 13,074 | 10,448/1,332/1,294 | 13,074 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2019/collection.json) |
| [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv_2020) | 13,088 | 10,479/1,285/1,324 | 13,088 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2020/collection.json) |
| [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv_2021) | 13,073 | 10,452/1,298/1,323 | 13,073 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2021/collection.json) |
| [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv_2022) | 13,066 | 10,447/1,299/1,320 | 13,066 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2022/collection.json) |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 10,371/1,310/1,347 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2023/collection.json) |
| [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv_2024) | 13,056 | 10,382/1,349/1,325 | 13,056 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2024/collection.json) |
| [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv_2025) | 13,061 | 10,416/1,339/1,306 | 13,061 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2025/collection.json) |
| [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl_2017) | 7,600 | 6,066/743/791 | 7,594 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2017/collection.json) |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 6,067/796/731 | 7,588 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2018/collection.json) |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 6,077/741/764 | 7,576 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2019/collection.json) |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 6,085/745/762 | 7,586 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2020/collection.json) |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 6,116/722/758 | 7,590 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2021/collection.json) |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 6,113/719/758 | 7,584 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2022/collection.json) |
| [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl_2023) | 7,610 | 6,070/758/782 | 7,604 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2023/collection.json) |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 6,090/735/759 | 7,578 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2024/collection.json) |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 6,041/737/796 | 7,568 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2025/collection.json) |
| [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt_2017) | 20,027 | 15,961/2,002/2,064 | 20,027 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt_2017/collection.json) |
| [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt_2023) | 20,002 | 15,964/2,043/1,995 | 20,002 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt_2023/collection.json) |
| [Sweden — 2017](https://source.coop/ftw/benchmark-data/se_2017) | 32,935 | 26,187/3,324/3,424 | 32,935 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se_2017/collection.json) |
| [Sweden — 2023](https://source.coop/ftw/benchmark-data/se_2023) | 32,640 | 26,019/3,319/3,302 | 32,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se_2023/collection.json) |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 3,430/457/413 | 4,300 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2019/collection.json) |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 3,423/438/421 | 4,282 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2020/collection.json) |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 3,424/438/424 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2021/collection.json) |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 3,445/422/419 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2022/collection.json) |
| [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si_2023) | 4,287 | 3,428/424/435 | 4,287 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2023/collection.json) |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si_2024) | 4,291 | 3,431/424/436 | 4,291 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2024/collection.json) |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk_2018) | 9,806 | 7,842/962/1,002 | 9,785 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2018/collection.json) |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk_2019) | 9,856 | 7,885/984/987 | 9,835 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2019/collection.json) |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk_2020) | 9,885 | 7,949/969/967 | 9,864 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2020/collection.json) |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk_2021) | 9,875 | 7,904/994/977 | 9,854 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2021/collection.json) |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk_2022) | 9,866 | 7,899/985/982 | 9,845 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2022/collection.json) |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk_2023) | 9,571 | 7,624/946/1,001 | 9,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2023/collection.json) |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk_2024) | 9,986 | 7,975/999/1,012 | 9,965 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2024/collection.json) |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk_2025) | 9,985 | 7,991/975/1,019 | 9,964 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2025/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at_2018) | 14,493 | 14,493 stored | 14,493 |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at_2019) | 14,491 | 14,491 stored | 14,491 |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at_2020) | 14,496 | 14,496 stored | 14,496 |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at_2021) | 14,506 | 14,506 stored | 14,506 |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at_2022) | 14,473 | 14,473 stored | 14,473 |
| [Austria — 2023](https://source.coop/ftw/benchmark-data/at_2023) | 14,484 | 14,484 stored | 14,484 |
| [Austria — 2024](https://source.coop/ftw/benchmark-data/at_2024) | 14,497 | 14,497 stored | 14,497 |
| [Austria — 2025](https://source.coop/ftw/benchmark-data/at_2025) | 14,516 | 14,516 stored | 14,516 |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg_2018) | 2,939 | 2,939 stored | 2,939 |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg_2019) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg_2020) | 2,941 | 2,941 stored | 2,941 |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg_2021) | 2,943 | 2,943 stored | 2,943 |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg_2022) | 2,946 | 2,946 stored | 2,946 |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg_2023) | 2,948 | 2,948 stored | 2,948 |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg_2024) | 2,949 | 2,949 stored | 2,949 |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg_2025) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,607 | 3,602 stored | 3,607 |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg_2021) | 18,076 | 18,055 stored | none |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg_2022) | 18,123 | 18,102 stored | none |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg_2023) | 17,846 | 17,825 stored | none |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg_2024) | 18,225 | 18,204 stored | none |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg_2025) | 18,292 | 18,271 stored | none |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch_ag_2025) | 346 | 346 stored | 346 |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ai_2025) | 14 | 14 stored | 14 |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ar_2025) | 34 | 34 stored | 34 |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch_be_2025) | 1,061 | 1,061 stored | 1,061 |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch_bl_2025) | 142 | 142 stored | 142 |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch_fr_2025) | 363 | 363 stored | 363 |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch_ge_2025) | 44 | 44 stored | 44 |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch_ju_2025) | 179 | 179 stored | 179 |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch_lu_2025) | 354 | 354 stored | 354 |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch_sg_2025) | 339 | 339 stored | 339 |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch_sh_2025) | 44 | 44 stored | 44 |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch_so_2025) | 193 | 193 stored | 193 |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch_sz_2025) | 139 | 139 stored | 139 |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch_tg_2025) | 187 | 187 stored | 187 |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch_ur_2025) | 15 | 15 stored | 15 |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch_vs_2025) | 145 | 145 stored | 145 |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 32 stored | 32 |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch_zh_2025) | 423 | 423 stored | 423 |
| [Czech — 2019](https://source.coop/ftw/benchmark-data/cz_2019) | 14,444 | 14,437 stored | 14,444 |
| [Czech — 2020](https://source.coop/ftw/benchmark-data/cz_2020) | 14,576 | 14,569 stored | 14,576 |
| [Czech — 2021](https://source.coop/ftw/benchmark-data/cz_2021) | 14,572 | 14,565 stored | 14,572 |
| [Czech — 2022](https://source.coop/ftw/benchmark-data/cz_2022) | 14,604 | 14,597 stored | 14,604 |
| [Czech — 2023](https://source.coop/ftw/benchmark-data/cz_2023) | 15,060 | 15,053 stored | 15,060 |
| [Czech — 2024](https://source.coop/ftw/benchmark-data/cz_2024) | 15,064 | 15,057 stored | 15,064 |
| [Czech — 2025](https://source.coop/ftw/benchmark-data/cz_2025) | 14,836 | 14,829 stored | 14,836 |
| [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds_2025) | 10,891 | 10,891 stored | 10,891 |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 3,452 stored | none |
| [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh_2024) | 3,451 | 3,451 stored | none |
| [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh_2025) | 3,451 | 3,451 stored | none |
| [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk_2017) | 9,688 | 9,688 stored | 9,688 |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 9,629 stored | 9,629 |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 9,624 stored | 9,624 |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 9,654 stored | 9,654 |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 9,647 stored | 9,647 |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 9,640 stored | 9,640 |
| [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk_2023) | 9,630 | 9,630 stored | 9,630 |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk_2024) | 9,672 | 9,672 stored | 9,672 |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk_2025) | 9,639 | 9,639 stored | 9,639 |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt_2021) | 13,468 | 13,468 stored | 13,468 |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee_2017) | 7,745 | 7,745 stored | 7,745 |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee_2018) | 7,765 | 7,765 stored | 7,765 |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee_2019) | 7,787 | 7,787 stored | 7,787 |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee_2020) | 7,807 | 7,807 stored | 7,807 |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee_2021) | 7,853 | 7,853 stored | 7,853 |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee_2022) | 7,871 | 7,871 stored | 7,871 |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee_2023) | 7,606 | 7,606 stored | 7,606 |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 7,562 | 7,562 stored | 7,562 |
| [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat_2024) | 5,814 | 5,814 stored | 5,814 |
| [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm_2024) | 17,833 | 17,833 stored | 17,833 |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 837 stored | none |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es_po_2025) | 29,795 | 29,795 stored | 29,795 |
| [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc_2024) | 4,926 | 4,926 stored | 4,926 |
| [Finland — 2023](https://source.coop/ftw/benchmark-data/fi_2023) | 36,621 | 36,620 stored | 36,621 |
| [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr_2017) | 9,676 | 9,676 stored | 9,676 |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 9,704 stored | 9,704 |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 9,724 stored | 9,724 |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 9,703 stored | 9,703 |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 9,734 stored | 9,734 |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 9,715 stored | 9,715 |
| [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr_2023) | 9,680 | 9,680 stored | 9,680 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 9,588 stored | 9,588 |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 16,734 stored | 16,734 |
| [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie_2023) | 16,762 | 16,762 stored | 16,762 |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 61,000 stored | none |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 60,945 stored | none |
| [Japan — 2023](https://source.coop/ftw/benchmark-data/jp_2023) | 60,957 | 60,941 stored | none |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 60,927 stored | none |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 14,123 stored | 14,123 |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 14,140 stored | 14,140 |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 13,016 stored | 13,016 |
| [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv_2018) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv_2019) | 13,074 | 13,074 stored | 13,074 |
| [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv_2020) | 13,088 | 13,088 stored | 13,088 |
| [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv_2021) | 13,073 | 13,073 stored | 13,073 |
| [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv_2022) | 13,066 | 13,066 stored | 13,066 |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv_2024) | 13,056 | 13,056 stored | 13,056 |
| [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv_2025) | 13,061 | 13,061 stored | 13,061 |
| [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl_2017) | 7,600 | 7,594 stored | 7,587 |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 7,588 stored | 7,569 |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 7,576 stored | 7,582 |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 7,586 stored | 7,592 |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 7,590 stored | 7,596 |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 7,584 stored | 7,590 |
| [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl_2023) | 7,610 | 7,604 stored | 7,610 |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 7,578 stored | 7,584 |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 7,568 stored | 7,574 |
| [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt_2017) | 20,027 | 20,027 stored | 20,027 |
| [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt_2023) | 20,002 | 20,002 stored | 20,002 |
| [Sweden — 2017](https://source.coop/ftw/benchmark-data/se_2017) | 32,935 | 32,935 stored | 32,935 |
| [Sweden — 2023](https://source.coop/ftw/benchmark-data/se_2023) | 32,640 | 32,640 stored | 32,640 |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 4,300 stored | 4,300 |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 4,282 stored | 4,282 |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si_2023) | 4,287 | 4,287 stored | 4,287 |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si_2024) | 4,291 | 4,291 stored | 4,291 |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk_2018) | 9,806 | 9,785 stored | 9,806 |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk_2019) | 9,856 | 9,835 stored | 9,856 |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk_2020) | 9,885 | 9,864 stored | 9,885 |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk_2021) | 9,875 | 9,854 stored | 9,875 |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk_2022) | 9,866 | 9,845 stored | 9,866 |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk_2023) | 9,571 | 9,552 stored | 9,571 |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk_2024) | 9,986 | 9,965 stored | 9,986 |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk_2025) | 9,985 | 9,964 stored | 9,985 |

`stored` means four-band GeoTIFFs (red, green, blue, NIR at 10 m) clipped to the chip's mask grid and published with it: the Q1-Q4 Sentinel-2 quarterly cloudless mosaics of the collection's year (and planting/harvest scenes, where a collection has them). `linked` means the chip's imagery items point at whole Sentinel-2 scenes on the source STAC API, for a reader to window. A chip with no imagery still carries its masks and its split — pair it with imagery of your own, on the footprint in `items.parquet`.
<!-- collections:end -->

Every number above is measured, not declared: chips and splits from each
collection's `<id>_chips.parquet`, field polygons from the `<id>_fields`
table the masks were cut from, imagery from the imagery child items on disk,
and crop labels from the `ftw:hcat_dominant_code` property in `items.parquet`.
Do not assume a collection carries imagery or crop labels because its
neighbours do — check the coverage table, or the collection's own assets.

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
