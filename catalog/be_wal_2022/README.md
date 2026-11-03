# Belgium, Wallonia — 2022

Benchmark chips for Belgium-Wallonia cut from the 2022 edition of the harmonized field boundary collection be_wal.

<!-- browse:start -->
![Belgium, Wallonia — 2022 thumbnail](https://data.source.coop/ftw/benchmark-data/be_wal_2022/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal_2022/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/be_wal_2022/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/be_wal_2022/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 3,203 chips and 122,200 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 2,559 |
| val | 336 |
| test | 308 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 0.4% |
| 25th | 5.1% |
| 50th | 18.1% |
| 75th | 46.4% |
| 95th | 73.1% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

3,203 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Winter wheat | 3301010101 | 36.9% |
| Corn silage | 3301090400 | 16.6% |
| Early potatoes  | 3301030000 | 12.2% |
| Sugar beet | 3301290700 | 10.5% |
| Winter barley | 3301010401 | 7.8% |
| Winter spelt | 3301011001 | 4.0% |
| Textile linen | 3301060701 | 3.6% |
| Grain corn | 3301010600 | 3.0% |
| Chicory with inulin | 3301310200 | 2.7% |
| Peas harvested fresh,canning peas | 3301020600 | 2.7% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html)
- Source data: [Belgium Wallonia: Parcellaire Agricole Anonyme](https://source.coop/ftw/harmonized-field-data/be_wal) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/be_wal/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/be_wal_2022/AGENTS.md) for the schema, field notes and more queries.
