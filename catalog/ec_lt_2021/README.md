# Lithuania - Eurocrops 2021 — 2021

Benchmark chips for Lithuania cut from the 2021 edition of the harmonized field boundary collection ec_lt.

<!-- browse:start -->
![Lithuania - Eurocrops 2021 — 2021 thumbnail](https://data.source.coop/ftw/benchmark-data/ec_lt_2021/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ec_lt_2021/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/ec_lt_2021/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/ec_lt_2021/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 13,468 chips and 439,199 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 10,786 |
| val | 1,349 |
| test | 1,333 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.7% |
| 25th | 9.0% |
| 50th | 23.7% |
| 75th | 41.9% |
| 95th | 64.9% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

13,468 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Winter cereals | 3301011501 | 57.4% |
| Summer cereals | 3301011503 | 18.5% |
| Leguminous crops | 3301020000 | 9.4% |
| Oats | 3301010500 | 6.0% |
| Buckwheat | 3301150200 | 3.1% |
| Corn | 3301010600 | 3.1% |
| Vegetables | 3301070000 | 1.0% |
| Sugar beet | 3301290700 | 1.0% |
| Berries | 3303020000 | 0.5% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Construction Sector Development Agency](https://www.geoportal.lt/geoportal/nacionaline-mokejimo-agentura-prie-zemes-ukio-ministerijos#savedSearchId={56542726-DC0B-461E-A32C-3E9A4A693E27}&collapsed=true>, EuroCrops <https://github.com/maja601/EuroCrops): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html)
- Source data: [Field boundaries for Lithuania - Eurocrops 2021](https://source.coop/ftw/harmonized-field-data/ec_lt) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/ec_lt/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/ec_lt_2021/AGENTS.md) for the schema, field notes and more queries.
