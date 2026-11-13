# Trazo with splits — 2024

## Overview

Benchmark chips for South America (Trazo regions) cut from the 2024 edition of the harmonized field boundary collection wri_trazo_ml.


It contains 1,360 chips and 6,092 field polygons. Chips are pre-assigned to benchmark splits (train 1,088, val 272).

Licensed [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html).

## Accessing the data

Browse the collection in the [Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml_2024/collection.json), or read the files below straight from [collection.json](https://data.source.coop/ftw/benchmark-data/wri_trazo_ml_2024/collection.json).

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `wri_trazo_ml_2024_fields.parquet` | Field boundary polygons |
| `wri_trazo_ml_2024_boundary_lines.parquet` | Field boundary lines |
| `wri_trazo_ml_2024_chips.parquet` | Chip definitions with field coverage |
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
- `label_extent_pct`: percent of the chip's area inside the label extent, where unlabelled pixels are background rather than unknown
- `label_extent_sha256`: sha256 of the label extent file the chips were selected with
- `split`: which benchmark split the chip belongs to (train / val / test)
- `geometry`: the chip footprint, a square polygon in EPSG:4326
- `bbox`: bounding box of the chip footprint

FTW properties on each STAC item:

- `ftw:calendar_year`: calendar year of the crop cycle the chip documents
- `ftw:field_coverage_pct`: percent of the chip's area covered by mapped field polygons
- `ftw:label_extent_pct`: percent of the chip's area inside the label extent, where unlabelled pixels are background rather than unknown
- `ftw:split`: which benchmark split the chip belongs to (train / val / test)
- `ftw:summer_harvest_day`: WorldCereal crop calendar: summer crops' end of season, day of year
- `ftw:summer_planting_day`: WorldCereal crop calendar: summer crops' start of season, day of year
- `ftw:winter_harvest_day`: WorldCereal crop calendar: winter crops' end of season, day of year
- `ftw:winter_planting_day`: WorldCereal crop calendar: winter crops' start of season, day of year (usually in the autumn before harvest)

Label rasters available as item assets: `semantic_2class_mask`, `semantic_3class_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 44.8% mapped field while the bottom 5% sit at or below 3.4%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
- Masks are derived from boundaries declared for one year; later parcel changes are not reflected.
- Empty area inside a chip means unmapped, not necessarily fieldless.
- Chips on the dataset border may be only partly covered by the source boundaries.
- Quarterly mosaics are cloudless composites, but where every scene of a quarter was cloudy they have no data (-32768) rather than the chip being dropped; check `ftw:nodata_pct` on each quarter's child item.
- The splits came from the source dataset rather than being assigned here.

## Example queries

Every query below was run against this collection when this file was written; the `-- result:` lines are its first rows. Run them from the collection directory.

### Chips per split

```sql
SELECT "ftw:split" AS split, count(*) AS chips FROM read_parquet('items.parquet') GROUP BY 1 ORDER BY 1;
-- result: train | 1088
-- result: val | 272
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('wri_trazo_ml_2024_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-23MKS3806 | 99.54
-- result: ftw-21JVL6620 | 99.19
-- result: ftw-21JVL6618 | 98.67
-- result: ... 2 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('wri_trazo_ml_2024_fields.parquet') f, (SELECT geometry FROM read_parquet('wri_trazo_ml_2024_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 4
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/wri_trazo_ml/collection.json); consult it for the original attributes, licensing terms and update cadence.
