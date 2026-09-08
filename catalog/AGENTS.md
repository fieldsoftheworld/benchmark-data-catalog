# Agent guide: Fields of the World Benchmark Data

Every claim in this file is quoted from a source or measured from the data.

## What this catalog is

Training and evaluation data for field boundary delineation models, one
collection per country or region. Each collection holds chip items on the FTW
grid (a fixed, MGRS-derived grid, so a cell id means the same square of ground
in every collection). Each chip item carries label masks — instance, semantic
2-class, semantic 3-class, and the DECODE boundary and distance layers — and,
where imagery was downloaded, two clipped Sentinel-2 scenes (planting and
harvest) as child items alongside it. Every chip carries a `ftw:split`
assignment of `train`, `val` or `test`, made in spatial blocks.

Collection-level assets carry the field polygons the masks were cut from, their
boundary lines, the chips table with split assignments and field coverage, and
`items.parquet`, a stac-geoparquet mirror of every item.

The field boundaries come from the
[harmonized field boundary catalog](https://source.coop/ftw/harmonized-field-data);
each collection's Source link below names the exact source collection.

## Accessing the data

Read `items.parquet` first. It lists every item — chips and season scenes —
with its bbox, split and asset hrefs, so a loader can select chips without
walking item JSON. It is queryable in place over HTTPS:

```sql
INSTALL spatial; LOAD spatial;
SELECT id, "ftw:split", "ftw:field_coverage_pct"
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/lu/items.parquet')
WHERE "ftw:split" = 'train'
LIMIT 5;
```

Each collection's own [agent guide](https://source.coop/ftw/benchmark-data/lu/AGENTS.md)
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
| Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- |
| [Austria](https://source.coop/ftw/benchmark-data/at) | 11,242 | 9,018/1,153/1,071 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/collection.json) |
| [Luxembourg](https://source.coop/ftw/benchmark-data/lu) | 775 | 601/79/95 | 679 | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lu](https://source.coop/ftw/harmonized-field-data/lu) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lu/collection.json) |
| [Slovenia](https://source.coop/ftw/benchmark-data/si) | 5,103 | 4,078/512/513 | 2,857 | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/collection.json) |
<!-- collections:end -->

Chips and splits are measured from each collection's chips table; Imagery is
the number of chips with Sentinel-2 season scenes.

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
