# Slovakia — 2021

Benchmark chips for Slovakia cut from the 2021 edition of the harmonized field boundary collection sk.

<!-- browse:start -->
![Slovakia — 2021 thumbnail](https://data.source.coop/ftw/benchmark-data/sk_2021/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2021/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/sk_2021/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/sk_2021/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 9,875 chips and 219,309 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 7,904 |
| val | 994 |
| test | 977 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.6% |
| 25th | 8.1% |
| 50th | 32.4% |
| 75th | 63.3% |
| 95th | 89.4% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

9,854 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Permanent grassland | 3302000000 | 26.9% |
| Winter wheat | 3301010101 | 19.7% |
| Popcorn | 3301010600 | 15.2% |
| Rapeseed - winter | 3301060401 | 9.9% |
| Spring barley | 3301010402 | 5.5% |
| Annual sunflower | 3301060500 | 5.4% |
| Soy beans | 3301160000 | 4.8% |
| Corn for silage | 3301090400 | 4.7% |
| Lucerne seed | 3301090301 | 4.0% |
| Grasses and other vegetable fodder | 3301090000 | 4.0% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Pôdohospodárska platobná agentúra](https://www.apa.sk): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html)
- Source data: [Slovakia Agricultural Land Identification System](https://source.coop/ftw/harmonized-field-data/sk) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/sk/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/sk_2021/AGENTS.md) for the schema, field notes and more queries.
