# Switzerland, Geneva — 2025

Benchmark chips for Switzerland cut from the 2025 edition of the harmonized field boundary collection ch.

<!-- browse:start -->
![Switzerland, Geneva — 2025 thumbnail](https://data.source.coop/ftw/benchmark-data/ch_ge_2025/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ge_2025/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/ch_ge_2025/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/ch_ge_2025/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 44 chips and 8,143 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 27 |
| val | 8 |
| test | 9 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.1% |
| 25th | 6.4% |
| 50th | 23.6% |
| 75th | 41.6% |
| 95th | 68.9% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

44 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Winter wheat (excluding feed list) | 3301010101 | 26.5% |
| Extensively used meadows (without pastures) | 3302000000 | 19.8% |
| Vines/vineyards | 3303060000 | 14.1% |
| Winter rapeseed for edible oil | 3301060400 | 10.3% |
| Artificial meadows (without pastures) | 3301090100 | 8.8% |
| Sunflowers for edible oil | 3301060500 | 6.1% |
| Soy | 3301160000 | 4.7% |
| Grain maize | 3301010600 | 4.0% |
| Winter barley | 3301010401 | 3.7% |
| Sugar beet | 3301290700 | 1.9% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [État de Genève, Office cantonal de l'agriculture et de la nature](https://ge.ch/sitg/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Field boundaries for Switzerland](https://source.coop/ftw/harmonized-field-data/ch) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/ch/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/ch_ge_2025/AGENTS.md) for the schema, field notes and more queries.
