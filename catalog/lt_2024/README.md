# Lithuania — 2024

Benchmark chips for Lithuania cut from the 2024 edition of the harmonized field boundary collection lt.

<!-- browse:start -->
![Lithuania — 2024 thumbnail](https://data.source.coop/ftw/benchmark-data/lt_2024/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2024/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/lt_2024/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/lt_2024/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 14,123 chips and 999,975 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 11,297 |
| val | 1,399 |
| test | 1,427 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 2.2% |
| 25th | 23.9% |
| 50th | 47.9% |
| 75th | 68.2% |
| 95th | 85.8% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

14,123 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Winter cereals | 3301011501 | 32.6% |
| Pastures-meadows over 5m. | 3302000000 | 28.4% |
| Rape | 3301060400 | 12.1% |
| Summer cereals | 3301011503 | 9.5% |
| Early cereals | 3301011502 | 7.4% |
| Oats | 3301010500 | 4.0% |
| Corn | 3301010600 | 2.1% |
| Other arable land | 3301990000 | 1.9% |
| Buckwheat | 3301150200 | 1.4% |
| Vegetables | 3301070000 | 0.7% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos](https://www.nma.lt>, Europe-LAND HE Project <https://doi.org/10.5281/zenodo.14230620): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Lithuania crop fields](https://source.coop/ftw/harmonized-field-data/lt) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/lt/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/lt_2024/AGENTS.md) for the schema, field notes and more queries.
