# Finland — 2025

Benchmark chips for Finland cut from the 2025 edition of the harmonized field boundary collection fi.

<!-- browse:start -->
![Finland — 2025 thumbnail](https://data.source.coop/ftw/benchmark-data/fi/fi_2025/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2025/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/fi/fi_2025/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/fi/fi_2025/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 35,540 chips and 783,770 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 28,609 |
| val | 3,445 |
| test | 3,486 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.3% |
| 25th | 2.3% |
| 50th | 7.2% |
| 75th | 19.0% |
| 95th | 47.5% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

35,540 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Forage grass | 3302000000 | 42.9% |
| Feed Barley | 3301010400 | 19.3% |
| Green fodder grain (oats) | 3301010500 | 16.8% |
| Spring wheat | 3301010102 | 8.2% |
| Winter wheat | 3301010101 | 3.6% |
| Spring rape | 3301060402 | 2.7% |
| Field Pea | 3301020600 | 2.5% |
| Green fodder grain (mixed cereals) | 3301010000 | 1.9% |
| Caraway | 3301061211 | 1.1% |
| Autumn rye | 3301010301 | 1.0% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Finnish Food Authority](https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Finnish Crop Fields (Maatalousmaa)](https://source.coop/ftw/harmonized-field-data/fi) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/fi/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/fi/fi_2025/AGENTS.md) for the schema, field notes and more queries.

## Field embeddings

`fi_2025_field_embeddings.parquet` has one row per field in `fi_2025_fields.parquet`, keyed by `id`. For each product it holds the mean (`<product>_mean`) and standard deviation (`<product>_std`, population std) of every embedding dimension over the field's 10 m pixels, as 64-value float lists, and the pixels used (`<product>_pixels`):

- `aef_*`: [AlphaEarth Foundations Satellite Embedding, annual v1](https://source.coop/tge-labs/aef). 64 dimensions; each pixel's vector has unit length. CC-BY-4.0.
- `olmoearth_*`: [OlmoEarth v1.3 embeddings, first 64 of 128 dimensions](https://source.coop/olmoearth/olmoearth-v1-3-embeddings). First 64 of 128 dimensions, which form a complete embedding on their own. Vectors are not normalised. Ai2 asks that 64- and 128-dimension vectors are not compared with each other. [OlmoEarth Artifact License](https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt): cite Ai2, and its use restrictions (Section 2) apply to anything derived from these columns.

A field takes the pixels whose centre is inside it; a field too small to hold one uses every pixel it touches (`pixel_rule = 'touched'`). The values are already dequantised. Fields with no pixels a product covers have no value for it.

```sql
INSTALL spatial; LOAD spatial;
SELECT f.*, e.aef_mean, e.olmoearth_mean FROM read_parquet('fi_2025_fields.parquet') f
JOIN read_parquet('fi_2025_field_embeddings.parquet') e USING (id) LIMIT 5;
```
