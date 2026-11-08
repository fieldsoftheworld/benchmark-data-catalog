# Sweden — 2017

Benchmark chips for Sweden cut from the 2017 edition of the harmonized field boundary collection se.

<!-- browse:start -->
![Sweden — 2017 thumbnail](https://data.source.coop/ftw/benchmark-data/se_2017/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se_2017/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/se_2017/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/se_2017/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 32,935 chips and 797,107 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 26,187 |
| val | 3,324 |
| test | 3,424 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.3% |
| 25th | 2.2% |
| 50th | 7.3% |
| 75th | 19.9% |
| 95th | 58.9% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

32,935 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Mowing and grazing on arable land | 3302000000 | 48.2% |
| Wheat (autumn) | 3301010101 | 18.2% |
| Barley (spring) | 3301010402 | 13.5% |
| Oats | 3301010500 | 7.2% |
| Rapeseed (autumn) | 3301060401 | 4.6% |
| Wheat (spring) | 3301010102 | 3.0% |
| Brown beans | 3301020100 | 1.4% |
| Cereals for green fodder / silage | 3301010000 | 1.4% |
| Sugar beet | 3301290700 | 1.3% |
| Pea for preserving | 3301020600 | 1.2% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Jordbruksverket (The Swedish Board of Agriculture)](https://jordbruksverket.se): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html)
- Source data: [Swedish Crop Fields (Jordbruksskiften)](https://source.coop/ftw/harmonized-field-data/se) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/se/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/se_2017/AGENTS.md) for the schema, field notes and more queries.
