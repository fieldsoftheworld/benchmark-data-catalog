# Mapping Africa — 2022

Benchmark chips for Africa (Mapping Africa sites) cut from the 2022 edition of the harmonized field boundary collection lacuna.

<!-- browse:start -->
Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna_2022/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/lacuna_2022/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna_2022/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 7,262 chips and 94,510 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 5,835 |
| val | 710 |
| test | 717 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.1% |
| 25th | 0.8% |
| 50th | 2.2% |
| 75th | 4.6% |
| 95th | 8.5% |

Every chip carries these label rasters as STAC assets: `semantic_2class_mask`, `semantic_3class_mask`.

7,260 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Agricultural Impacts Research Group, Clark University](https://github.com/agroimpacts/lacunalabels): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://go.planet.com/nicfi-pla-2024)
- Source data: [Mapping Africa: crop field boundary labels for Africa, 2017-2023](https://source.coop/ftw/harmonized-field-data/lacuna) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/lacuna/collection.json))
- Chips are 2 km (2,000 m) on a side
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel on each chip's own UTM zone grid

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.

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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/lacuna_2022/AGENTS.md) for the schema, field notes and more queries.
