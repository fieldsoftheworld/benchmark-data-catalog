# Luxembourg

## Overview

Benchmark chips for Luxembourg cut from the harmonized field boundary collection for Luxembourg (edition 2026).


It contains 775 chips and 87,997 field polygons. Chips are pre-assigned to benchmark splits (train 601, val 79, test 95).

Licensed [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html).

## Accessing the data

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `lu_fields.parquet` | Field boundary polygons |
| `lu_boundary_lines.parquet` | Field boundary lines |
| `lu_chips.parquet` | Chip definitions with field coverage |
| `items.parquet` | STAC items in GeoParquet format (collection mirror) |

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

Label rasters available as item assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 44.6% mapped field while the bottom 5% sit at or below 4.0%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
- Masks are derived from boundaries declared for one year; later parcel changes are not reflected.
- Empty area inside a chip means unmapped, not necessarily fieldless.
- Chips on the dataset border may be only partly covered by the source boundaries.
- Respect the pre-assigned splits: they are spatially blocked, so resampling chips at random leaks information between train and test.

## Example queries

Every query below was run against this collection when this file was written; the `-- result:` lines are its first rows. Run them from the collection directory.

### Chips per split

```sql
SELECT "ftw:split" AS split, count(*) AS chips FROM read_parquet('items.parquet') GROUP BY 1 ORDER BY 1;
-- result: test | 95
-- result: train | 601
-- result: val | 79
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('lu_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-31UGR1616 | 100
-- result: ftw-32UKA8216 | 99.09
-- result: ftw-32UKA8458 | 94.65
-- result: ... 2 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('lu_fields.parquet') f, (SELECT geometry FROM read_parquet('lu_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 25
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/lu/collection.json); consult it for the original attributes, licensing terms and update cadence.
