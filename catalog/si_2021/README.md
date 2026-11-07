# Slovenia — 2021

Benchmark chips for Slovenia cut from the 2021 edition of the harmonized field boundary collection si.

<!-- browse:start -->
![Slovenia — 2021 thumbnail](https://data.source.coop/ftw/benchmark-data/si_2021/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2021/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/si_2021/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/si_2021/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 4,286 chips and 821,021 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 3,424 |
| val | 438 |
| test | 424 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 1.0% |
| 25th | 9.4% |
| 50th | 20.9% |
| 75th | 35.0% |
| 95th | 62.5% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

4,286 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Permanent grassland | 3302000000 | 62.2% |
| Grain maize | 3301010600 | 9.6% |
| Silo Maize | 3301090400 | 6.3% |
| Common wheat winter | 3301010101 | 5.8% |
| Barley winter | 3301010401 | 4.8% |
| Grass clover mixture | 3301090100 | 4.2% |
| Common grape vine | 3303060000 | 2.9% |
| Japanese Persimmon | 3303010000 | 1.7% |
| Clover grass mixture | 3301090303 | 1.4% |
| Triticale winter | 3301010801 | 1.1% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Ministry of Agriculture, Forestry and Food (Ministrstvo za kmetijstvo, gozdarstvo in prehrano)](https://www.gov.si/drzavni-organi/ministrstva/ministrstvo-za-kmetijstvo-gozdarstvo-in-prehrano/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://rkg.gov.si/vstop/)
- Source data: [Slovenia Crop Fields](https://source.coop/ftw/harmonized-field-data/si) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/si/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/si_2021/AGENTS.md) for the schema, field notes and more queries.
