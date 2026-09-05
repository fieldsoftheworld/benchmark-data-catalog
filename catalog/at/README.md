# Austria

Benchmark chips for Austria cut from the harmonized field boundary collection for Austria (edition 2025).

## What is in this collection

This collection holds 11,242 chips and 656,619 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 9,018 |
| val | 1,153 |
| test | 1,071 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.1% |
| 25th | 3.7% |
| 50th | 18.2% |
| 75th | 44.3% |
| 95th | 75.6% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| WINTER SOFT WHEAT | 3301010101 | 26.1% |
| CORN CORN COB MIX (CCM) / FIELD VEGETABLES | 3301010600 | 24.2% |
| WINTER BARLEY | 3301010401 | 10.5% |
| SOYBEANS | 3301160000 | 9.3% |
| GREEN CORN | 3301090400 | 9.1% |
| CLOVER | 3301090303 | 5.8% |
| WINTER TRITICALE | 3301010801 | 5.1% |
| OIL PUMPKIN | 3301140400 | 3.9% |
| WINTER RYE | 3301010301 | 3.0% |
| SUNFLOWERS | 3301060500 | 2.9% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Agrarmarkt Austria](https://geometadatensuche.inspire.gv.at/metadatensuche/inspire/api/records/9db8a0c3-e92a-4df4-9d55-8210e326a7ed): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Derived from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/at/collection.json)
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.
- Sampling field polygons for crop-type work, using the harmonized HCAT codes.

## Limitations

- Masks are derived from field boundaries declared for a given year; parcels that changed shape, were subdivided or merged after that declaration are not reflected.
- Chips on the border of the source dataset may be only partly covered by field boundaries, and empty area there means unmapped, not fieldless.

## Access

`items.parquet` mirrors every chip item, so the whole collection can be queried without walking the catalog:

```sql
INSTALL spatial; LOAD spatial;
SELECT * FROM read_parquet('items.parquet') LIMIT 5;
```

See [AGENTS.md](AGENTS.md) for the schema, field notes and more queries.

## Compared with Fields of the World 1.0

Fields of the World 1.0 published `austria` with `6686` chips (`5304` train / `637` val / `745` test) cut from `196101` parcels declared for `2021`, under `CC-BY-4.0`. This collection has `11242` chips (`9018`/`1153`/`1071`) cut from `656619` fields declared for `2025`.
