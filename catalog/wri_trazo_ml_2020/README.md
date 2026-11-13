# Trazo with splits — 2020

Benchmark chips for South America (Trazo regions) cut from the 2020 edition of the harmonized field boundary collection wri_trazo_ml.

<!-- browse:start -->
![Trazo with splits — 2020 thumbnail](https://data.source.coop/ftw/benchmark-data/wri_trazo_ml_2020/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml_2020/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/wri_trazo_ml_2020/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/wri_trazo_ml_2020/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 3,687 chips and 37,048 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 2,176 |
| val | 543 |
| test | 968 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 1.0% |
| 25th | 9.2% |
| 50th | 23.6% |
| 75th | 44.7% |
| 95th | 76.8% |

Every chip carries these label rasters as STAC assets: `semantic_2class_mask`, `semantic_3class_mask`.

3,686 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [World Resources Institute and Arizona State University](https://source.coop/wri-data-lab/trazoannotations): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Trazo field boundary annotations for South America with splits](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/wri_trazo_ml/collection.json))
- Chips are 2 km (2,000 m) on a side
- Splits assigned with the `predefined` strategy, random seed 42
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/wri_trazo_ml_2020/AGENTS.md) for the schema, field notes and more queries.
