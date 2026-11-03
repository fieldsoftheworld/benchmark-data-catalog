# Estonia — 2024

## Overview

Benchmark chips for Estonia cut from the 2024 edition of the harmonized field boundary collection ee.


It contains 6,553 chips and 86,826 field polygons. Chips are pre-assigned to benchmark splits (train 5,224, val 660, test 669).

Licensed [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html).

## Accessing the data

Browse the collection in the [Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2024/collection.json), or read the files below straight from [collection.json](https://data.source.coop/ftw/benchmark-data/ee_2024/collection.json).

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `ee_2024_fields.parquet` | Field boundary polygons |
| `ee_2024_fields_filtered.parquet` | Field polygons after the class filter |
| `ee_2024_boundary_lines.parquet` | Field boundary lines |
| `ee_2024_chips.parquet` | Chip definitions with field coverage |
| `items.parquet` | STAC items in GeoParquet format (collection mirror) |
| `chips.pmtiles` | Chips (PMTiles) |
| `fields.pmtiles` | Field boundaries (PMTiles) |
| `styles/split.json` | Chips by split |
| `styles/field-coverage.json` | Field coverage |
| `styles/dominant-crop.json` | Dominant crop per chip |
| `styles/crops.json` | Crops |
| `styles/outline.json` | Field outlines |

Query them with DuckDB from inside the collection directory, so the relative paths below resolve:

```sql
INSTALL spatial; LOAD spatial;
SELECT * FROM read_parquet('items.parquet') LIMIT 5;
```

## Schema & field notes

Columns in the chips table:

- `gzd`: MGRS grid zone designator of the chip's grid cell
- `mgrs_10km`: MGRS 100 km square plus 10 km cell identifier the chip belongs to
- `id`: chip identifier; matches the STAC item id (with the year suffix stripped)
- `field_coverage_pct`: percent of the chip's area covered by mapped field polygons
- `hcat_dominant_code`: EuroCrops HCAT code of the crop covering most of the chip's fields
- `hcat_dominant_name_en`: English name for hcat_dominant_code
- `hcat_dominant_pct`: share of the chip's field area under the dominant crop
- `hcat_top`: the crops covering the chip's field area, as {code, name_en, pct} entries ordered by share (top 5)
- `split`: which benchmark split the chip belongs to (train / val / test)
- `geometry`: the chip footprint, a square polygon in EPSG:4326
- `bbox`: bounding box of the chip footprint

FTW properties on each STAC item:

- `ftw:field_coverage_pct`: percent of the chip's area covered by mapped field polygons
- `ftw:hcat_dominant_code`: EuroCrops HCAT code of the crop covering most of the chip's fields
- `ftw:hcat_dominant_name_en`: English name for hcat_dominant_code
- `ftw:hcat_dominant_pct`: share of the chip's field area under the dominant crop
- `ftw:hcat_top`: the crops covering the chip's field area, as {code, name_en, pct} entries ordered by share (top 5)
- `ftw:imagery_modes`: imagery the chip holds: scenes (planting/harvest), mosaics (quarterly, Q1-Q4), or both
- `ftw:imagery_year`: mosaic year used
- `ftw:mosaic_requested_year`: mosaic year the selection asked for
- `ftw:mosaic_tile`: quarterly mosaic tile the imagery came from
- `ftw:mosaic_year`: mosaic year used
- `ftw:season`: which crop-calendar window (or mosaic quarter) a child imagery item covers
- `ftw:source`: satellite mission the imagery came from
- `ftw:split`: which benchmark split the chip belongs to (train / val / test)

Label rasters available as item assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 19.1% mapped field while the bottom 5% sit at or below 0.6%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
- Masks are derived from boundaries declared for one year; later parcel changes are not reflected.
- Empty area inside a chip means unmapped, not necessarily fieldless.
- Chips on the dataset border may be only partly covered by the source boundaries.
- Imagery is chosen against a crop calendar, so acquisition dates and cloud cover vary between chips; check `eo:cloud_cover` on the season child items.
- Respect the pre-assigned splits: they are spatially blocked, so resampling chips at random leaks information between train and test.

## Example queries

Every query below was run against this collection when this file was written; the `-- result:` lines are its first rows. Run them from the collection directory.

### Chips per split

```sql
SELECT "ftw:split" AS split, count(*) AS chips FROM read_parquet('items.parquet') GROUP BY 1 ORDER BY 1;
-- result: test | 669
-- result: train | 5224
-- result: val | 660
-- result: ... 1 more rows
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('ee_2024_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-35VMF1602 | 94.4
-- result: ftw-35VMF7818 | 93.09
-- result: ftw-35VMF3226 | 93.03
-- result: ... 2 more rows
```

### Dominant crops across chips

```sql
SELECT hcat_dominant_name_en AS crop, count(*) AS chips FROM read_parquet('ee_2024_chips.parquet') WHERE hcat_dominant_code IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
-- result: Winter wheat | 1568
-- result: mixture of legumes and grasses (30-80% legumes) | 912
-- result: Summer barley | 588
-- result: ... 7 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('ee_2024_fields.parquet') f, (SELECT geometry FROM read_parquet('ee_2024_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 40
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/ee/collection.json); consult it for the original attributes, licensing terms and update cadence.
