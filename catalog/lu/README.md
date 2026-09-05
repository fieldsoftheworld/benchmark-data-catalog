# Luxembourg

Benchmark chips for Luxembourg cut from the harmonized field boundary collection for Luxembourg (edition 2026).

## What is in this collection

This collection holds 775 chips and 87,997 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 601 |
| val | 79 |
| test | 95 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 4.0% |
| 25th | 25.4% |
| 50th | 44.6% |
| 75th | 63.5% |
| 95th | 82.2% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`.

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Administration des services techniques de l'agriculture](https://asta.etat.lu/en): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Derived from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/lu/collection.json)
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.

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

Fields of the World 1.0 published `luxembourg` with `808` chips (`643` train / `81` val / `84` test) cut from `29018` parcels declared for `2022`, under `CC0-1.0`. This collection has `775` chips (`601`/`79`/`95`) cut from `87997` fields declared for `2026`.
