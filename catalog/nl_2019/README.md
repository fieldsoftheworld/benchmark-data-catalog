# Netherlands (Crops) — 2019

Benchmark chips for Netherlands cut from the 2019 edition of the harmonized field boundary collection nl.

<!-- browse:start -->
![Netherlands (Crops) — 2019 thumbnail](https://data.source.coop/ftw/benchmark-data/nl_2019/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2019/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/nl_2019/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/nl_2019/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 7,582 chips and 721,521 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 6,077 |
| val | 741 |
| test | 764 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 3.3% |
| 25th | 32.0% |
| 50th | 57.7% |
| 75th | 73.6% |
| 95th | 85.8% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

7,576 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Grassland natural. Main function agriculture. | 3302000000 | 47.7% |
| Grassland temporary | 3301090100 | 13.3% |
| Corn silage | 3301090400 | 11.5% |
| Potatoes AM . control measure | 3301030000 | 10.3% |
| wheat winter | 3301010101 | 6.9% |
| beets sugar | 3301290700 | 4.8% |
| Onions leg and plant first year | 3301220400 | 2.2% |
| barley summer | 3301010402 | 1.4% |
| Corn corncob mix | 3301010600 | 1.2% |
| barley winter | 3301010401 | 0.7% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [RVO / PDOK](https://www.pdok.nl/introductie/-/article/basisregistratie-gewaspercelen-brp-): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html)
- Source data: [BRP Crop Field Boundaries for The Netherlands (CAP-based)](https://source.coop/ftw/harmonized-field-data/nl) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/nl/collection.json))
- Chips are 2 km (2,000 m) on a side
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel on each chip's own UTM zone grid

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.
- Sampling field polygons for crop-type work, using the harmonized HCAT codes.

## Limitations

- Masks are derived from field boundaries declared for a given year; parcels that changed shape, were subdivided or merged after that declaration are not reflected.
- Quarterly mosaics are cloudless composites, but where every scene of a quarter was cloudy they have no data (-32768) rather than the chip being dropped; check `ftw:nodata_pct` on each quarter's child item.
- Chips on the border of the source dataset may be only partly covered by field boundaries, and empty area there means unmapped, not fieldless.

## Access

`items.parquet` mirrors every chip item, so the whole collection can be queried without walking the catalog:

```sql
INSTALL spatial; LOAD spatial;
SELECT * FROM read_parquet('items.parquet') LIMIT 5;
```

See [AGENTS.md](https://source.coop/ftw/benchmark-data/nl_2019/AGENTS.md) for the schema, field notes and more queries.
