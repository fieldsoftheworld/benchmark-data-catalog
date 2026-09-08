# Slovenia

Benchmark chips for Slovenia cut from the harmonized field boundary collection for Slovenia (edition 2024).

## What is in this collection

This collection holds 5,103 chips and 809,044 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 4,078 |
| val | 512 |
| test | 513 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.6% |
| 25th | 7.5% |
| 50th | 18.8% |
| 75th | 33.2% |
| 95th | 60.5% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`.

2,857 chips have Sentinel-2 scenes selected for them, one in the planting window and one in the harvest window of the crop calendar. Planting imagery was acquired between 2024-03-05T10:08:07.326000Z and 2024-05-24T10:07:47.398000Z, averaging 0.1% cloud cover (worst 2.0%). Harvest imagery was acquired between 2024-08-25T10:17:50.795000Z and 2024-11-25T10:08:08.116000Z, averaging 0.1% cloud cover (worst 2.0%).

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Permanent grassland | 3302000000 | 62.1% |
| Grain maize | 3301010600 | 9.7% |
| Common wheat winter | 3301010101 | 6.3% |
| Silo Maize | 3301090400 | 6.2% |
| Barley winter | 3301010401 | 4.7% |
| Grass clover mixture | 3301090100 | 3.8% |
| Common grape vine | 3303060000 | 2.7% |
| Japanese Persimmon | 3303010000 | 1.7% |
| Clover grass mixture | 3301090303 | 1.7% |
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
- Derived from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/si/collection.json)
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.
- Sampling field polygons for crop-type work, using the harmonized HCAT codes.

## Limitations

- Masks are derived from field boundaries declared for a given year; parcels that changed shape, were subdivided or merged after that declaration are not reflected.
- Imagery windows follow a crop calendar rather than a fixed date, so acquisition dates differ between chips and cloud-free scenes are not guaranteed.
- Chips on the border of the source dataset may be only partly covered by field boundaries, and empty area there means unmapped, not fieldless.

## Access

`items.parquet` mirrors every chip item, so the whole collection can be queried without walking the catalog:

```sql
INSTALL spatial; LOAD spatial;
SELECT * FROM read_parquet('items.parquet') LIMIT 5;
```

See [AGENTS.md](AGENTS.md) for the schema, field notes and more queries.

## Compared with Fields of the World 1.0

Fields of the World 1.0 published `slovenia` with `2177` chips (`1733` train / `216` val / `228` test) cut from `67488` parcels declared for `2021`, under `CC-BY-4.0`. This collection has `5103` chips (`4078`/`512`/`513`) cut from `809044` fields declared for `2024`.
