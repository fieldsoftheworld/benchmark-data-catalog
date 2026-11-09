# Spain — 2025

Benchmark chips for Spain cut from the 2025 edition of the harmonized field boundary collection es.

<!-- browse:start -->
![Spain — 2025 thumbnail](https://data.source.coop/ftw/benchmark-data/es_2025/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_2025/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/es_2025/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/es_2025/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 53,145 chips and 6,648,736 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 42,487 |
| val | 5,294 |
| test | 5,364 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.5% |
| 25th | 7.5% |
| 50th | 24.5% |
| 75th | 50.3% |
| 95th | 79.4% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

53,124 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| BARLEY | 3301010400 | 28.2% |
| SOFT WHEAT | 3301010100 | 15.2% |
| OLIVE | 3303050000 | 14.5% |
| GRAPEVINE ROOTSTOCKS | 3303060000 | 11.7% |
| OAT | 3301010500 | 8.2% |
| ALMOND | 3303030100 | 8.0% |
| PASTURES LESS THAN 5 YEARS OLD | 3302000000 | 4.6% |
| TRITICALE | 3301010800 | 3.5% |
| SUNFLOWER | 3301060500 | 3.4% |
| CORN-SORGHUM MIXTURE | 3301010600 | 2.5% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Fondo Español de Garantía Agraria (FEGA)](https://www.fega.gob.es): producer, licensor
- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Gobierno Vasco](https://www.euskadi.eus/web01-tramite/es/contenidos/tramite_servicio/datos_geograficos_sigpac/es_def/index.shtml): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Spain Declared Crops (Cultivos Declarados SIGPAC)](https://source.coop/ftw/harmonized-field-data/es) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/es/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/es_2025/AGENTS.md) for the schema, field notes and more queries.
