# Ireland — 2022

Benchmark chips for Ireland cut from the 2022 edition of the harmonized field boundary collection ie.

<!-- browse:start -->
![Ireland — 2022 thumbnail](https://data.source.coop/ftw/benchmark-data/ie_2022/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2022/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/ie_2022/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/ie_2022/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 16,734 chips and 1,000,290 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 13,374 |
| val | 1,653 |
| test | 1,707 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 17.9% |
| 25th | 51.5% |
| 50th | 68.1% |
| 75th | 80.7% |
| 95th | 92.0% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

16,734 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| HCAT 3302000000 | 3302000000 | 92.3% |
| HCAT 3301010402 | 3301010402 | 2.4% |
| HCAT 3301010401 | 3301010401 | 1.4% |
| HCAT 3301090100 | 3301090100 | 1.4% |
| HCAT 3301010101 | 3301010101 | 1.1% |
| HCAT 3301010600 | 3301010600 | 0.3% |
| HCAT 3301010501 | 3301010501 | 0.3% |
| HCAT 3301010502 | 3301010502 | 0.3% |
| HCAT 3301060401 | 3301060401 | 0.3% |
| HCAT 3301020100 | 3301020100 | 0.2% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Department of Agriculture, Food and the Marine](https://www.gov.ie/en/organisation/department-of-agriculture-food-and-the-marine/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Ireland INSPIRE Geospatial aid application (GSAA) dataset](https://source.coop/ftw/harmonized-field-data/ie) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/ie/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/ie_2022/AGENTS.md) for the schema, field notes and more queries.
