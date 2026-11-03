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
**3 collections · 18,559 chips · 1,138,880 field polygons**

| Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,203 | 2,559/336/308 | 3,203 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/be_wal](https://source.coop/ftw/harmonized-field-data/be_wal) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal_2022/collection.json) |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 6,553 | 5,224/660/669 | 6,553 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2024/collection.json) |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 8,803 | 7,089/854/860 | 8,803 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2024/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,203 | 3,203 stored | 3,203 |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 6,553 | 6,553 stored | 6,553 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 8,803 | 8,803 stored | 8,803 |

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
