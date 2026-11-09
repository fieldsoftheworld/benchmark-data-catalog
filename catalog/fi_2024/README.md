# Finland — 2024

Benchmark chips for Finland cut from the 2024 edition of the harmonized field boundary collection fi.

<!-- browse:start -->
![Finland — 2024 thumbnail](https://data.source.coop/ftw/benchmark-data/fi_2024/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi_2024/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/fi_2024/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/fi_2024/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 35,929 chips and 806,986 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 28,840 |
| val | 3,547 |
| test | 3,542 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.3% |
| 25th | 2.3% |
| 50th | 7.2% |
| 75th | 19.1% |
| 95th | 47.7% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

35,928 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Forage grass | 3302000000 | 43.2% |
| Feed Barley | 3301010400 | 19.3% |
| Green fodder grain (oats) | 3301010500 | 18.1% |
| Spring wheat | 3301010102 | 8.5% |
| Winter wheat | 3301010101 | 2.8% |
| Field Pea | 3301020600 | 2.3% |
| Green fodder grain (mixed cereals) | 3301010000 | 2.0% |
| Spring rape | 3301060402 | 1.9% |
| Caraway | 3301061211 | 1.0% |
| Early potato (under cover) | 3301030000 | 0.9% |

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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/fi_2024/AGENTS.md) for the schema, field notes and more queries.
