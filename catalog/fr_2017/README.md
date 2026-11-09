# France — 2017

Benchmark chips for France cut from the 2017 edition of the harmonized field boundary collection fr.

<!-- browse:start -->
![France — 2017 thumbnail](https://data.source.coop/ftw/benchmark-data/fr_2017/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr_2017/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/fr_2017/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/fr_2017/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 121,892 chips and 7,697,005 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 97,615 |
| val | 12,086 |
| test | 12,191 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 3.0% |
| 25th | 27.1% |
| 50th | 54.1% |
| 75th | 73.6% |
| 95th | 88.3% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

121,701 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Long rotation meadow (6 years or more) | 3302000000 | 31.9% |
| Soft winter wheat | 3301010101 | 23.8% |
| Other pure forage grass 5 years or less | 3301090100 | 9.8% |
| Maize | 3301010600 | 7.3% |
| Other winter oilseeds of the species Brassica napus | 3301060401 | 6.7% |
| Other winter cereal of the genus Hordeum | 3301010401 | 6.7% |
| Silage Maize | 3301090400 | 6.2% |
| Other oilseeds of the species Helianthus | 3301060500 | 2.7% |
| Vine: table grapes | 3303060000 | 2.6% |
| Non-forage beet / Swiss chard | 3301290700 | 2.5% |

## Styles

Ready-made map styles ship with the collection:

- **Chips by split** (the default view): chips coloured by their train / val / test assignment.
- **Field coverage**: chips shaded light to dark by the share of their area covered by fields.
- **Dominant crop per chip**: chips coloured by the crop covering most of their field area.
- **Crops**: fields coloured by their harmonized crop (EuroCrops HCAT).
- **Field outlines**: every field in one colour, for reading the boundaries themselves.

## Provenance

- [Anstitut National de l'Information Géographique et Forestière](https://www.data.gouv.fr/en/datasets/registre-parcellaire-graphique-rpg-contours-des-parcelles-et-ilots-culturaux-et-leur-groupe-de-cultures-majoritaire/): producer, licensor
- [Joint Research Centre, European Commission](https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3): producer, licensor
- [Fields of the World](https://fieldsofthe.world): processor
- License: [License](https://etalab.gouv.fr/licence-ouverte-open-licence)
- Source data: [Registre Parcellaire Graphique; Crop Fields France](https://source.coop/ftw/harmonized-field-data/fr) (harmonized field boundaries; STAC [collection.json](https://data.source.coop/ftw/harmonized-field-data/fr/collection.json))
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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/fr_2017/AGENTS.md) for the schema, field notes and more queries.
