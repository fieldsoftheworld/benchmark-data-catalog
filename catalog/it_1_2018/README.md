# Italy, Tuscany — 2018

Benchmark chips for Italy-Tuscany cut from the 2018 edition of the harmonized field boundary collection it_1.

<!-- browse:start -->
![Italy, Tuscany — 2018 thumbnail](https://data.source.coop/ftw/benchmark-data/it_1_2018/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1_2018/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/it_1_2018/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/it_1_2018/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 4,515 chips and 499,100 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 3,596 |
| val | 459 |
| test | 460 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.4% |
| 25th | 7.6% |
| 50th | 22.0% |
| 75th | 42.4% |
| 95th | 72.1% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

4,512 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| ARABLE LAND | 3301000000 | 14.7% |
| OLIVE NURSERY | 3303050000 | 14.0% |
| Durum wheat | 3301010200 | 13.6% |
| forage grass less than a year | 3301090200 | 12.9% |
| GRAPE | 3303060000 | 12.2% |
| ALFAFA | 3301090301 | 9.3% |
| Multifloral Meadow | 3302000000 | 9.1% |
| Common soft wheat | 3301010100 | 5.5% |
| CLOVER (SP. TRIFOLIUM SQUARROSUM L.) | 3301090303 | 4.8% |
| Barley | 3301010400 | 3.9% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Italy Tuscany (ITI1) Crop Fields — EuroCropsV2](https://source.coop/ftw/harmonized-field-data/it_1) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/it_1/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/it_1_2018/AGENTS.md) for the schema, field notes and more queries.
