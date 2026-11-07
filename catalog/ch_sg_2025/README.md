# Switzerland, St. Gallen — 2025

Benchmark chips for Switzerland cut from the 2025 edition of the harmonized field boundary collection ch.

<!-- browse:start -->
![Switzerland, St. Gallen — 2025 thumbnail](https://data.source.coop/ftw/benchmark-data/ch_sg_2025/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sg_2025/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/ch_sg_2025/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/ch_sg_2025/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 339 chips and 89,275 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 275 |
| val | 38 |
| test | 26 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.5% |
| 25th | 11.8% |
| 50th | 38.4% |
| 75th | 60.0% |
| 95th | 72.2% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

339 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Extensively used meadows (without pastures) | 3302000000 | 86.4% |
| Artificial meadows (without pastures) | 3301090100 | 5.6% |
| Silage and green maize | 3301090400 | 3.4% |
| Annual open-field vegetables (excl. canning) | 3301070000 | 1.5% |
| Winter wheat (excluding feed list) | 3301010101 | 0.9% |
| Managed chestnut groves | 3303010000 | 0.5% |
| Grain maize | 3301010600 | 0.5% |
| Potatoes | 3301030000 | 0.5% |
| Winter barley | 3301010401 | 0.4% |
| Feed wheat according to swiss granum list | 3301010100 | 0.3% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Kanton St. Gallen, via geodienste.ch](https://www.geodienste.ch/services/lwb_nutzungsflaechen): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html)
- Source data: [Field boundaries for Switzerland](https://source.coop/ftw/harmonized-field-data/ch) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/ch/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/ch_sg_2025/AGENTS.md) for the schema, field notes and more queries.
