# Latvia — 2018

Benchmark chips for Latvia cut from the 2018 edition of the harmonized field boundary collection lv.

<!-- browse:start -->
![Latvia — 2018 thumbnail](https://data.source.coop/ftw/benchmark-data/lv_2018/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2018/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/lv_2018/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/lv_2018/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 13,028 chips and 414,914 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 10,385 |
| val | 1,317 |
| test | 1,326 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 1.1% |
| 25th | 10.7% |
| 50th | 25.8% |
| 75th | 43.9% |
| 95th | 71.0% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

13,028 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Permanent grasslands | 3302000000 | 34.2% |
| Wheat winter | 3301010101 | 14.3% |
| Wheat in summer with grass or legume sowing | 3301010102 | 13.6% |
| Grasses not elsewhere specified or included | 3301090200 | 11.2% |
| Barley summer | 3301010402 | 7.8% |
| Oats | 3301010500 | 6.1% |
| Rape winter | 3301060401 | 4.9% |
| Rape summer | 3301060403 | 3.4% |
| Field beans | 3301020100 | 2.7% |
| Buckwheat | 3301150200 | 1.9% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Rural Support Service Republic of Latvia (Lauku atbalsta dienests)](https://www.lad.gov.lv/lv/lauku-registra-dati): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html)
- Source data: [Latvia Lauki Parcels](https://source.coop/ftw/harmonized-field-data/lv) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/lv/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/lv_2018/AGENTS.md) for the schema, field notes and more queries.
