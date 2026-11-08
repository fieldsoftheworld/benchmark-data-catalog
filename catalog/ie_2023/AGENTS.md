# Ireland — 2023

## Overview

Benchmark chips for Ireland cut from the 2023 edition of the harmonized field boundary collection ie.


It contains 16,762 chips and 1,077,312 field polygons. Chips are pre-assigned to benchmark splits (train 13,469, val 1,651, test 1,642).

Licensed [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html).

## Accessing the data

Browse the collection in the [Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2023/collection.json), or read the files below straight from [collection.json](https://data.source.coop/ftw/benchmark-data/ie_2023/collection.json).

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `ie_2023_fields.parquet` | Field boundary polygons |
| `ie_2023_fields_filtered.parquet` | Field polygons after the class filter |
| `ie_2023_boundary_lines.parquet` | Field boundary lines |
| `ie_2023_chips.parquet` | Chip definitions with field coverage |
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

- `ftw:calendar_year`: calendar year of the crop cycle the chip documents
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
- `ftw:nodata_pct`: share of the chip (0-100) the quarter's mosaic has no data for
- `ftw:season`: which crop-calendar window (or mosaic quarter) a child imagery item covers
- `ftw:source`: satellite mission the imagery came from
- `ftw:split`: which benchmark split the chip belongs to (train / val / test)
- `ftw:summer_harvest_day`: WorldCereal crop calendar: summer crops' end of season, day of year
- `ftw:summer_planting_day`: WorldCereal crop calendar: summer crops' start of season, day of year
- `ftw:winter_harvest_day`: WorldCereal crop calendar: winter crops' end of season, day of year
- `ftw:winter_planting_day`: WorldCereal crop calendar: winter crops' start of season, day of year (usually in the autumn before harvest)

Label rasters available as item assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 75.0% mapped field while the bottom 5% sit at or below 19.7%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
- Masks are derived from boundaries declared for one year; later parcel changes are not reflected.
- Empty area inside a chip means unmapped, not necessarily fieldless.
- Chips on the dataset border may be only partly covered by the source boundaries.
- Quarterly mosaics are cloudless composites, but where every scene of a quarter was cloudy they have no data (-32768) rather than the chip being dropped; check `ftw:nodata_pct` on each quarter's child item.
- Respect the pre-assigned splits: they are spatially blocked, so resampling chips at random leaks information between train and test.

## Example queries

Every query below was run against this collection when this file was written; the `-- result:` lines are its first rows. Run them from the collection directory.

### Chips per split

```sql
SELECT "ftw:split" AS split, count(*) AS chips FROM read_parquet('items.parquet') GROUP BY 1 ORDER BY 1;
-- result: test | 1642
-- result: train | 13469
-- result: val | 1651
-- result: ... 1 more rows
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('ie_2023_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-29UMT2484 | 100
-- result: ftw-29UMT3680 | 100
-- result: ftw-29UMT4482 | 100
-- result: ... 2 more rows
```

### Dominant crops across chips

```sql
SELECT hcat_dominant_name_en AS crop, count(*) AS chips FROM read_parquet('ie_2023_chips.parquet') WHERE hcat_dominant_code IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
-- result: pasture_meadow_grassland_grass | 16568
-- result: spring_barley | 78
-- result: winter_common_soft_wheat | 58
-- result: ... 7 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('ie_2023_fields.parquet') f, (SELECT geometry FROM read_parquet('ie_2023_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 26
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/ie/collection.json); consult it for the original attributes, licensing terms and update cadence.
