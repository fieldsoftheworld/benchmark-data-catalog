# Denmark — 2022

Benchmark chips for Denmark cut from the 2022 edition of the harmonized field boundary collection dk.

<!-- browse:start -->
![Denmark — 2022 thumbnail](https://data.source.coop/ftw/benchmark-data/dk_2022/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2022/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/dk_2022/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/dk_2022/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 9,640 chips and 504,695 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 7,618 |
| val | 988 |
| test | 1,034 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 7.2% |
| 25th | 43.1% |
| 50th | 65.2% |
| 75th | 77.7% |
| 95th | 86.9% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

9,640 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Green grain of spring barley | 3301010402 | 26.5% |
| Green grain of winter wheat | 3301010101 | 22.3% |
| Environmental grass AECM scheme 2 rotation | 3302000000 | 11.4% |
| Grass and clover grass without norm below 50% clover (rotation) | 3301090000 | 9.2% |
| Winter rape | 3301060401 | 9.0% |
| Silo maize | 3301090400 | 7.8% |
| Green grains of winter rye | 3301010301 | 5.1% |
| Green grain of spring oats | 3301010502 | 3.0% |
| Green grain of winter barley | 3301010401 | 3.0% |
| Potatoes consumption | 3301030000 | 2.8% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Danish Agricultural Agency](https://lbst.dk/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html)
- Source data: [Denmark Crop Fields (Marker)](https://source.coop/ftw/harmonized-field-data/dk) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/dk/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/dk_2022/AGENTS.md) for the schema, field notes and more queries.
