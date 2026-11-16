# Trazo with splits — 2024

Benchmark chips for South America (Trazo regions) cut from the 2024 edition of the harmonized field boundary collection wri_trazo_ml.

<!-- browse:start -->
![Trazo with splits — 2024 thumbnail](https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 1,360 chips and 6,092 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 1,088 |
| val | 272 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 3.4% |
| 25th | 21.9% |
| 50th | 44.8% |
| 75th | 65.3% |
| 95th | 89.7% |

Every chip carries these label rasters as STAC assets: `semantic_2class_mask`, `semantic_3class_mask`.

1,358 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/AGENTS.md) for the schema, field notes and more queries.

## Field embeddings

`wri_trazo_ml_2024_field_embeddings.parquet` has one row per field in `wri_trazo_ml_2024_fields.parquet`, keyed by `id`. For each product it holds the mean (`<product>_mean`) and standard deviation (`<product>_std`, population std) of every embedding dimension over the field's 10 m pixels, as 64-value float lists, and the pixels used (`<product>_pixels`):

- `aef_*`: [AlphaEarth Foundations Satellite Embedding, annual v1](https://source.coop/tge-labs/aef). 64 dimensions; each pixel's vector has unit length. CC-BY-4.0.
- `olmoearth_*`: [OlmoEarth v1.3 embeddings, first 64 of 128 dimensions](https://source.coop/olmoearth/olmoearth-v1-3-embeddings). First 64 of 128 dimensions, which form a complete embedding on their own. Vectors are not normalised. Ai2 asks that 64- and 128-dimension vectors are not compared with each other. [OlmoEarth Artifact License](https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt): cite Ai2, and its use restrictions (Section 2) apply to anything derived from these columns.

A field takes the pixels whose centre is inside it; a field too small to hold one uses every pixel it touches (`pixel_rule = 'touched'`). The values are already dequantised. Fields with no pixels a product covers have no value for it.

```sql
INSTALL spatial; LOAD spatial;
SELECT f.*, e.aef_mean, e.olmoearth_mean FROM read_parquet('wri_trazo_ml_2024_fields.parquet') f
JOIN read_parquet('wri_trazo_ml_2024_field_embeddings.parquet') e USING (id) LIMIT 5;
```
