# Belgium, Flanders — 2019

Benchmark chips for Belgium-Flanders cut from the 2019 edition of the harmonized field boundary collection be_vlg.

<!-- browse:start -->
![Belgium, Flanders — 2019 thumbnail](https://data.source.coop/ftw/benchmark-data/be_vlg_2019/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2019/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2019/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/be_vlg_2019/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 2,945 chips and 463,818 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 2,373 |
| val | 314 |
| test | 258 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 4.5% |
| 25th | 27.9% |
| 50th | 49.3% |
| 75th | 67.7% |
| 95th | 83.1% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

2,945 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Grassland | 3302000000 | 38.8% |
| Silage maize | 3301090400 | 21.7% |
| winter wheat | 3301010101 | 10.9% |
| Potatoes (planned harvest for 1/9) | 3301030000 | 9.6% |
| grain corn | 3301010600 | 7.7% |
| sugar beets | 3301290700 | 3.2% |
| Perennial Clover | 3301090303 | 2.9% |
| winter barley | 3301010401 | 2.7% |
| Perennial fruit crops (pear) | 3303011200 | 1.6% |
| Perennial fruit crops (apple) | 3303010200 | 0.9% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Agentschap Landbouw & Zeevisserij (Government)](https://landbouwcijfers.vlaanderen.be/open-geodata-landbouwgebruikspercelen): producer, licensor
- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0)
- Source data: [Field boundaries for Flanders, Belgium](https://source.coop/ftw/harmonized-field-data/be_vlg) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/be_vlg/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/be_vlg_2019/AGENTS.md) for the schema, field notes and more queries.
