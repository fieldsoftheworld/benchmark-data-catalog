# Croatia — 2024

Benchmark chips for Croatia cut from the 2024 edition of the harmonized field boundary collection hr.

<!-- browse:start -->
![Croatia — 2024 thumbnail](https://data.source.coop/ftw/benchmark-data/hr_2024/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2024/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/hr_2024/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/hr_2024/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 8,803 chips and 929,854 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 7,089 |
| val | 854 |
| test | 860 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.1% |
| 25th | 1.6% |
| 50th | 8.7% |
| 75th | 38.3% |
| 95th | 80.6% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

8,803 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Arable land | 3301000000 | 92.0% |
| Orchard | 3303010000 | 4.2% |
| Olive grove | 3303050000 | 1.8% |
| Mother block of vines | 3303060000 | 1.8% |
| Mixed perennial crops | 3303000000 | 0.2% |
| Nursery | 3303070000 | 0.0% |
| Short rotation coppice | 3306000000 | 0.0% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Agencija za plaćanja u poljoprivredi, ribarstvu i ruralnom razvoju](https://www.apprrr.hr/prostorni-podaci-servisi/): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://www.apprrr.hr/prostorni-podaci-servisi/)
- Source data: [Croatian Field Boundaries](https://source.coop/ftw/harmonized-field-data/hr) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/hr/collection.json))
- Chips are 2 km (2,000 m) on a side
- Splits assigned with the `block3x3` strategy, random seed 42
- Masks rasterized at 10 m per pixel on each chip's own UTM zone grid

## Suggested uses

- Training and evaluating field boundary delineation models on the pre-assigned, reproducible split.
- Comparing model performance across regions by filtering chips on `id`, which carries the grid cell each chip was cut from.
- Sampling field polygons for crop-type work, using the harmonized HCAT codes.

## Limitations

- Masks are derived from field boundaries declared for a given year; parcels that changed shape, were subdivided or merged after that declaration are not reflected.
- Imagery windows follow a crop calendar rather than a fixed date, so acquisition dates differ between chips and cloud-free scenes are not guaranteed.
- Chips on the border of the source dataset may be only partly covered by field boundaries, and empty area there means unmapped, not fieldless.

## Access

`items.parquet` mirrors every chip item, so the whole collection can be queried without walking the catalog:

```sql
INSTALL spatial; LOAD spatial;
SELECT * FROM read_parquet('items.parquet') LIMIT 5;
```

See [AGENTS.md](https://source.coop/ftw/benchmark-data/hr_2024/AGENTS.md) for the schema, field notes and more queries.
