# Fields of the World Benchmark Data

Training and evaluation data for field boundary delineation models: Sentinel-2
chips paired with label masks cut from official, harmonized field boundaries.
Each collection is one country or region, with a train / validation / test
split assigned per chip so that results are comparable between models and
between runs.

The boundaries come from the [harmonized field boundary catalog](https://source.coop/ftw/harmonized-field-data),
which republishes each country's own parcel declarations in one schema. The
chips, masks and imagery here are cut from it with
[ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools)
(`ftwd`); every collection's recipe is a config file in the
[source repository](https://github.com/fieldsoftheworld/benchmark-data-catalog),
so any collection can be rebuilt from the harmonized edition it names. Agents
should start from the [agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md).

## Collections

<!-- collections:start -->
| Thumbnail | Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ![Austria](https://data.source.coop/ftw/benchmark-data/at/thumbnail.webp) | [Austria](https://source.coop/ftw/benchmark-data/at) | 11,242 | 9,018/1,153/1,071 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/collection.json) |
| ![Luxembourg](https://data.source.coop/ftw/benchmark-data/lu/thumbnail.webp) | [Luxembourg](https://source.coop/ftw/benchmark-data/lu) | 775 | 601/79/95 | 679 | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lu](https://source.coop/ftw/harmonized-field-data/lu) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lu/collection.json) |
| ![Slovenia](https://data.source.coop/ftw/benchmark-data/si/thumbnail.webp) | [Slovenia](https://source.coop/ftw/benchmark-data/si) | 5,103 | 4,078/512/513 | 2,857 | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/collection.json) |
<!-- collections:end -->

## What a chip carries

Every chip is a STAC item on the FTW grid — a fixed, MGRS-derived grid, so the
same cell is the same square of ground in every collection. Each chip carries:

- **Instance masks**: one integer label per field polygon, for instance
  segmentation.
- **Semantic masks**: 2-class (field / not field) and 3-class (interior /
  boundary / not field).
- **DECODE masks**: a boundary mask and a normalized distance-to-boundary map,
  for models that learn boundaries rather than regions.
- **Sentinel-2 scenes**, where imagery has been downloaded for the collection:
  one scene from the planting window and one from the harvest window of the
  region's crop calendar, clipped to the chip and published as child items
  alongside it.
- **A split assignment** (`train`, `val` or `test`), made in spatial blocks so
  that neighbouring chips do not straddle two splits and a model cannot learn a
  test chip from its training neighbour.
- **Field coverage**, the share of the chip's area that is mapped field, and —
  where the harmonized source carries HCAT crop codes — the crop composition of
  the fields inside it.

## What a collection carries

Alongside the chip items, each collection publishes the tables the chips were
cut from and a mirror of the items themselves:

- `<id>_fields.parquet`, the field polygons used, and
  `<id>_boundary_lines.parquet`, their boundaries as lines.
- `<id>_chips.parquet`: every chip with its footprint, split assignment and
  field coverage.
- `items.parquet`: a [stac-geoparquet](https://github.com/stac-utils/stac-geoparquet)
  mirror of every STAC item — chips and season scenes alike — carrying public
  URLs for every asset, so a loader can select chips without walking the
  catalog.
- `chips.pmtiles` and `fields.pmtiles`, with ready-made map styles under
  `styles/`, for looking at a collection before training on it.
- `README.md`, `AGENTS.md`, `llms.txt` and a thumbnail, per collection.

## Using it

Query a collection's item mirror straight from its public URL — no download, no
catalog walk:

```sql
INSTALL spatial; LOAD spatial;
SELECT id, "ftw:split", "ftw:field_coverage_pct"
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/lu/items.parquet')
WHERE "ftw:split" = 'train'
LIMIT 5;
```

Each row carries the asset hrefs for that chip's masks and scenes, so a
training loader goes straight from a query like this one to the rasters.

To look before querying, open the catalog in the
[Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json):
it renders the collections, their chip footprints and the published styles. The
Browse column above links each collection directly.

To rebuild a collection, or to cut chips for a region that is not published
here, use [ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools)
with a recipe from the
[source repository](https://github.com/fieldsoftheworld/benchmark-data-catalog/tree/main/datasets).

## How this relates to Fields of the World 1.0

This is version 2 of the benchmark introduced in [Fields of The World: A
Machine Learning Benchmark Dataset For Global Field Boundary Segmentation
(2024)](https://arxiv.org/abs/2409.16252). Version 1.0 remains published,
unchanged, at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world).
Version 2 rebuilds each country from the harmonized field boundary catalog
rather than from a one-off per-country conversion, adds the DECODE label masks,
and publishes the chips as STAC with a queryable item mirror. Each collection's
own README states, in measured numbers, how it compares with the 1.0 folder it
supersedes.

## Versioning

This edition is `2.0.0-alpha.1`. While it is in alpha, collections are updated
in place: a rebuild replaces the published files at the same URLs, and the
`updated` stamp in a collection's `collection.json` says when that last
happened. Treat any collection here as a moving target until 2.0.0 is
released.

## License

Each collection carries the license of the field boundary data it was cut from
— see the License column above, and the collection's own page. The masks and
imagery chips derived from those boundaries are published under the same terms
as the source. Sentinel-2 imagery is Copernicus data, free and open.

## Contact

Open an [issue](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues)
for a problem with the data or a request for a country, or read the
[agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for the
machine-readable tour of the same material.
