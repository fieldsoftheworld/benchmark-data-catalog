# France — 2023

Benchmark chips for France cut from the 2023 edition of the harmonized field boundary collection fr.

<!-- browse:start -->
![France — 2023 thumbnail](https://data.source.coop/ftw/benchmark-data/fr_2023/thumbnail.webp)

Open this collection in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr_2023/collection.json), read the [agent guide](https://source.coop/ftw/benchmark-data/fr_2023/AGENTS.md), or query [items.parquet](https://data.source.coop/ftw/benchmark-data/fr_2023/items.parquet) directly.
<!-- browse:end -->

## What is in this collection

This collection holds 121,876 chips and 7,907,678 field polygons. Each chip is a square STAC item carrying the label masks rasterized from the field boundaries that fall inside it.

Chips per benchmark split:

| split | chips |
| --- | --- |
| train | 97,747 |
| val | 12,007 |
| test | 12,122 |

How much of a chip is mapped field, as a distribution over the chips (`field_coverage_pct`):

| percentile | field coverage |
| --- | --- |
| 5th | 2.9% |
| 25th | 26.7% |
| 50th | 53.2% |
| 75th | 72.5% |
| 95th | 87.6% |

Every chip carries these label rasters as STAC assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

121,684 chips have Sentinel-2 quarterly cloudless mosaics selected for them, one for each quarter (Q1-Q4) of a single year.

## Crops

Crops are harmonized to the EuroCrops HCAT taxonomy. The classes covering most of this collection:

| crop | HCAT code | share |
| --- | --- | --- |
| Permanent pasture - predominantly grass (woody fodder resources absent or scarce) | 3302000000 | 35.3% |
| Soft winter wheat | 3301010101 | 22.4% |
| Maize | 3301010600 | 12.1% |
| Winter barley | 3301010401 | 6.5% |
| Other temporary grassland 5 years or less | 3301090100 | 6.5% |
| Other winter oilseeds of the species Brassica rapa | 3301060401 | 6.4% |
| Sunflower | 3301060500 | 3.8% |
| Vine: wine grapes | 3303060000 | 2.7% |
| Other alfalfa | 3301090301 | 2.1% |
| Spring barley | 3301010402 | 2.1% |

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

See [AGENTS.md](https://source.coop/ftw/benchmark-data/fr_2023/AGENTS.md) for the schema, field notes and more queries.
