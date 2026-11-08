# Portugal — 2017

Benchmark chips for Portugal cut from the 2017 edition of the harmonized field boundary collection pt.

<!-- browse:start -->
![Portugal — 2017 thumbnail](https://data.source.coop/ftw/benchmark-data/pt_2017/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt_2017/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/pt_2017/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/pt_2017/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 20,027 chips and 2,100,446 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 15,961 |
| val | 2,002 |
| test | 2,064 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.6% |
| 25th | 6.1% |
| 50th | 20.9% |
| 75th | 54.5% |
| 95th | 90.8% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

20,027 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| FESCUE | 3302000000 | 67.1% |
| OLIVE VALLEY | 3303050000 | 11.6% |
| VINEYARD | 3303060000 | 5.1% |
| CORN | 3301010600 | 4.5% |
| ANNUAL AND OTHER CULT. FORAGE ANNUALS | 3301990000 | 3.8% |
| OAT | 3301010500 | 2.6% |
| CASTANIA | 3303030500 | 1.6% |
| PINE NUTS | 3306990000 | 1.3% |
| RICE | 3301010700 | 1.2% |
| WHEAT | 3301010100 | 1.2% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [IPAP - Instituto de Financiamento da Agricultura e Pescas](https://www.ifap.pt/isip/ows/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply)
- Source data: [Field boundaries for Portugal](https://source.coop/ftw/harmonized-field-data/pt) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/pt/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/pt_2017/AGENTS.md) for the schema, field notes and more queries.
