# West Bahia, Brazil — 2020

## Overview

Benchmark chips for Brazil (west Bahia, LEM) cut from the 2020 edition of the harmonized field boundary collection br_ba_lem.


It contains 1,268 chips and 1,854 field polygons. Chips are pre-assigned to benchmark splits (train 1,000, val 126, test 142).

Licensed [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html).

## Accessing the data

Browse the collection in the [Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/br_ba_lem_2020/collection.json), or read the files below straight from [collection.json](https://data.source.coop/ftw/benchmark-data/br_ba_lem_2020/collection.json).

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `br_ba_lem_2020_fields.parquet` | Field boundary polygons |
| `br_ba_lem_2020_boundary_lines.parquet` | Field boundary lines |
| `br_ba_lem_2020_chips.parquet` | Chip definitions with field coverage |
| `items.parquet` | STAC items in GeoParquet format (collection mirror) |
| `chips.pmtiles` | Chips (PMTiles) |
| `fields.pmtiles` | Field boundaries (PMTiles) |
| `styles/split.json` | Chips by split |
| `styles/field-coverage.json` | Field coverage |
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
- `split`: which benchmark split the chip belongs to (train / val / test)
- `geometry`: the chip footprint, a square polygon in EPSG:4326
- `bbox`: bounding box of the chip footprint

FTW properties on each STAC item:

- `ftw:calendar_year`: calendar year of the crop cycle the chip documents
- `ftw:field_coverage_pct`: percent of the chip's area covered by mapped field polygons
- `ftw:split`: which benchmark split the chip belongs to (train / val / test)
- `ftw:summer_harvest_day`: WorldCereal crop calendar: summer crops' end of season, day of year
- `ftw:summer_planting_day`: WorldCereal crop calendar: summer crops' start of season, day of year
- `ftw:winter_harvest_day`: WorldCereal crop calendar: winter crops' end of season, day of year
- `ftw:winter_planting_day`: WorldCereal crop calendar: winter crops' start of season, day of year (usually in the autumn before harvest)

Label rasters available as item assets: `semantic_2class_mask`, `semantic_3class_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 49.7% mapped field while the bottom 5% sit at or below 1.3%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
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
-- result: test | 142
-- result: train | 1000
-- result: val | 126
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('br_ba_lem_2020_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-23LMG3060 | 97.43
-- result: ftw-23LLG7608 | 97.39
-- result: ftw-23LLG6474 | 97.22
-- result: ... 2 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('br_ba_lem_2020_fields.parquet') f, (SELECT geometry FROM read_parquet('br_ba_lem_2020_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 1
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/br_ba_lem/collection.json); consult it for the original attributes, licensing terms and update cadence.
