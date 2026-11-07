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
**72 collections · 802,990 chips · 132,492,814 field polygons**

| Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at_2018) | 14,493 | 11,621/1,433/1,439 | 14,493 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2018/collection.json) |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at_2019) | 14,491 | 11,659/1,389/1,443 | 14,491 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2019/collection.json) |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at_2020) | 14,496 | 11,730/1,401/1,365 | 14,496 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2020/collection.json) |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at_2021) | 14,506 | 11,639/1,420/1,447 | 14,506 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2021/collection.json) |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at_2022) | 14,473 | 11,654/1,422/1,397 | 14,473 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2022/collection.json) |
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
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 23/0/9 | 32 stored | [License](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_zg_2025/collection.json) |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 2,753/346/353 | 3,452 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh_2023/collection.json) |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 7,636/999/994 | 9,629 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2018/collection.json) |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 7,641/1,005/978 | 9,624 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2019/collection.json) |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 7,672/993/989 | 9,654 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2020/collection.json) |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 7,621/989/1,037 | 9,647 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2021/collection.json) |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 7,618/988/1,034 | 9,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2022/collection.json) |
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
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 661/87/89 | 837 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_ib](https://source.coop/ftw/harmonized-field-data/es_ib) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_ib_2024/collection.json) |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 7,735/999/970 | 9,704 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2018/collection.json) |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 7,748/970/1,006 | 9,724 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2019/collection.json) |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 7,718/1,004/981 | 9,703 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2020/collection.json) |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 7,816/959/959 | 9,734 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2021/collection.json) |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 7,781/976/958 | 9,715 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2022/collection.json) |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 7,605/973/1,010 | 9,588 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2024/collection.json) |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 13,374/1,653/1,707 | 16,734 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2022/collection.json) |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 48,849/6,093/6,074 | 61,000 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2021/collection.json) |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 48,799/6,146/6,016 | 60,945 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2022/collection.json) |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 48,789/6,143/6,011 | 60,927 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2024/collection.json) |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 11,297/1,399/1,427 | 14,123 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2024/collection.json) |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 11,323/1,388/1,429 | 14,140 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2025/collection.json) |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 10,383/1,308/1,325 | 13,016 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2017/collection.json) |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 10,371/1,310/1,347 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2023/collection.json) |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 6,067/796/731 | 7,588 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2018/collection.json) |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 6,077/741/764 | 7,576 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2019/collection.json) |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 6,085/745/762 | 7,586 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2020/collection.json) |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 6,116/722/758 | 7,590 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2021/collection.json) |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 6,113/719/758 | 7,584 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2022/collection.json) |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 6,090/735/759 | 7,578 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2024/collection.json) |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 6,041/737/796 | 7,568 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2025/collection.json) |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 3,430/457/413 | 4,300 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2019/collection.json) |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 3,423/438/421 | 4,282 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2020/collection.json) |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 3,424/438/424 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2021/collection.json) |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 3,445/422/419 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2022/collection.json) |
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
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 32 stored | 32 |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 3,452 stored | none |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 9,629 stored | 9,629 |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 9,624 stored | 9,624 |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 9,654 stored | 9,654 |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 9,647 stored | 9,647 |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 9,640 stored | 9,640 |
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
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 837 stored | none |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 9,704 stored | 9,704 |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 9,724 stored | 9,724 |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 9,703 stored | 9,703 |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 9,734 stored | 9,734 |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 9,715 stored | 9,715 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 9,588 stored | 9,588 |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 16,734 stored | 16,734 |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 61,000 stored | none |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 60,945 stored | none |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 60,927 stored | none |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 14,123 stored | 14,123 |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 14,140 stored | 14,140 |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 13,016 stored | 13,016 |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 13,028 stored | 13,028 |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 7,588 stored | 7,569 |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 7,576 stored | 7,582 |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 7,586 stored | 7,592 |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 7,590 stored | 7,596 |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 7,584 stored | 7,590 |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 7,578 stored | 7,584 |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 7,568 stored | 7,574 |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 4,300 stored | 4,300 |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 4,282 stored | 4,282 |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 4,286 stored | 4,286 |
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
