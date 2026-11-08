# Germany, Lower Saxony/Bremen/Hamburg — 2025

Benchmark chips for Germany-NDS cut from the 2025 edition of the harmonized field boundary collection de_nds.

<!-- browse:start -->
![Germany, Lower Saxony/Bremen/Hamburg — 2025 thumbnail](https://data.source.coop/ftw/benchmark-data/de_nds_2025/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_nds_2025/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/de_nds_2025/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/de_nds_2025/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 10,891 chips and 766,838 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 8,714 |
| val | 1,075 |
| test | 1,102 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 6.2% |
| 25th | 36.1% |
| 50th | 56.8% |
| 75th | 71.2% |
| 95th | 83.3% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

10,891 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Alternating grassland | 3302000000 | 30.7% |
| Silage maize (as staple feed) | 3301090400 | 20.3% |
| Winter soft wheat | 3301010101 | 15.8% |
| Winter barley | 3301010401 | 6.5% |
| Potatoes (food)/potatoes | 3301030000 | 6.3% |
| Winter rye | 3301010301 | 5.7% |
| Sugar beet | 3301290700 | 4.4% |
| Corn without silage maize | 3301010600 | 4.4% |
| Winter rape | 3301060401 | 4.1% |
| Summer barley | 3301010402 | 1.7% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [ML/SLA Niedersachsen](https://sla.niedersachsen.de/landentwicklung/LEA/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [DL-DE-BY-2.0](https://spdx.org/licenses/DL-DE-BY-2.0.html)
- Source data: [Crop Fields for Lower Saxony / Bremen / Hamburg, Germany](https://source.coop/ftw/harmonized-field-data/de_nds) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/de_nds/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/de_nds_2025/AGENTS.md) for the schema, field notes and more queries.
