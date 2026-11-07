# Austria — 2021

Benchmark chips for Austria cut from the 2021 edition of the harmonized field boundary collection at.

<!-- browse:start -->
![Austria — 2021 thumbnail](https://data.source.coop/ftw/benchmark-data/at_2021/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2021/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/at_2021/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/at_2021/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 14,506 chips and 1,836,737 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 11,639 |
| val | 1,420 |
| test | 1,447 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.5% |
| 25th | 9.6% |
| 50th | 29.8% |
| 75th | 52.8% |
| 95th | 78.7% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

14,506 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| ALTERNATE MEADOW (EGART | 3302000000 | 48.7% |
| WINTER SOFT WHEAT | 3301010101 | 13.4% |
| CORN / BEETLE BEANS IN SEPARATED ROWS | 3301010600 | 12.5% |
| WINTER BARLEY | 3301010401 | 5.2% |
| GREEN CORN | 3301090400 | 4.8% |
| SOYBEANS | 3301160000 | 4.3% |
| CLOVER | 3301090303 | 3.5% |
| WINTER TRITICALE | 3301010801 | 2.8% |
| CUT WINE GARDEN | 3303060000 | 2.6% |
| OIL PUMPKIN | 3301140400 | 2.3% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Agrarmarkt Austria](https://geometadatensuche.inspire.gv.at/metadatensuche/inspire/api/records/9db8a0c3-e92a-4df4-9d55-8210e326a7ed): producer, licensor
- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Field boundaries for Austria](https://source.coop/ftw/harmonized-field-data/at) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/at/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/at_2021/AGENTS.md) for the schema, field notes and more queries.
