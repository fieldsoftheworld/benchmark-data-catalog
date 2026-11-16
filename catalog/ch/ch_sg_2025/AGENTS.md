# Switzerland, St. Gallen — 2025

## Overview

Benchmark chips for Switzerland cut from the 2025 edition of the harmonized field boundary collection ch.


It contains 339 chips and 89,275 field polygons. Chips are pre-assigned to benchmark splits (train 275, val 38, test 26).

Licensed [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html).

## Accessing the data

Browse the collection in the [Portolan data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sg_2025/collection.json), or read the files below straight from [collection.json](https://data.source.coop/ftw/benchmark-data/ch/ch_sg_2025/collection.json).

The collection ships these files alongside `collection.json`:

| file | what it is |
| --- | --- |
| `ch_sg_2025_fields.parquet` | Field boundary polygons |
| `ch_sg_2025_fields_filtered.parquet` | Field polygons after the class filter |
| `ch_sg_2025_boundary_lines.parquet` | Field boundary lines |
| `ch_sg_2025_chips.parquet` | Chip definitions with field coverage |
| `items.parquet` | STAC items in GeoParquet format (collection mirror) |
| `chips.pmtiles` | Chips (PMTiles) |
| `fields.pmtiles` | Field boundaries (PMTiles) |
| `styles/split.json` | Chips by split |
| `styles/field-coverage.json` | Field coverage |
| `styles/dominant-crop.json` | Dominant crop per chip |
| `styles/crops.json` | Crops |
| `styles/outline.json` | Field outlines |
| `ch_sg_2025_field_embeddings.parquet` | Per-field embedding statistics (AlphaEarth Foundations, OlmoEarth v1.3) |

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
- `admin0_iso3`: ISO 3166-1 alpha-3 code of the country: the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024); GAUL gives disputed areas its own x-prefixed codes such as xJK
- `admin0_name`: country: the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `admin1_name`: first-level administrative unit (state, province, region): the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `admin2_name`: second-level administrative unit (district, county, department): the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `geometry`: the chip footprint, a square polygon in EPSG:4326
- `bbox`: bounding box of the chip footprint

FTW properties on each STAC item:

- `ftw:admin0_iso3`: ISO 3166-1 alpha-3 code of the country: the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024); GAUL gives disputed areas its own x-prefixed codes such as xJK
- `ftw:admin0_name`: country: the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `ftw:admin1_name`: first-level administrative unit (state, province, region): the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `ftw:admin2_name`: second-level administrative unit (district, county, department): the unit containing the chip's centre, or the one it overlaps most when its centre is in none (FAO GAUL 2024)
- `ftw:calendar_year`: calendar year of the crop cycle the chip documents
- `ftw:field_coverage_pct`: percent of the chip's area covered by mapped field polygons
- `ftw:hcat_dominant_code`: EuroCrops HCAT code of the crop covering most of the chip's fields
- `ftw:hcat_dominant_name_en`: English name for hcat_dominant_code
- `ftw:hcat_dominant_pct`: share of the chip's field area under the dominant crop
- `ftw:hcat_top`: the crops covering the chip's field area, as {code, name_en, pct} entries ordered by share (top 5)
- `ftw:imagery_modes`: imagery the chip holds: scenes (planting/harvest), mosaics (quarterly, Q1-Q4), or both
- `ftw:mosaic_requested_year`: mosaic year the selection asked for
- `ftw:mosaic_year`: mosaic year used
- `ftw:split`: which benchmark split the chip belongs to (train / val / test)
- `ftw:summer_harvest_day`: WorldCereal crop calendar: summer crops' end of season, day of year
- `ftw:summer_planting_day`: WorldCereal crop calendar: summer crops' start of season, day of year
- `ftw:winter_harvest_day`: WorldCereal crop calendar: winter crops' end of season, day of year
- `ftw:winter_planting_day`: WorldCereal crop calendar: winter crops' start of season, day of year (usually in the autumn before harvest)

Label rasters available as item assets: `instance_mask`, `semantic_2class_mask`, `semantic_3class_mask`, `decode_boundary_mask`, `decode_distance_mask`.

## Data quality & usage notes

- Field coverage is uneven: the median chip is 38.4% mapped field while the bottom 5% sit at or below 0.5%. Filter on `field_coverage_pct` when sparse chips would skew an evaluation.
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
-- result: test | 26
-- result: train | 275
-- result: val | 38
```

### Chips with the highest field coverage

```sql
SELECT id, field_coverage_pct FROM read_parquet('ch_sg_2025_chips.parquet') ORDER BY field_coverage_pct DESC LIMIT 5;
-- result: ftw-32TNT4044 | 82.73
-- result: ftw-32TNT4042 | 81.19
-- result: ftw-32TNT3428 | 80.32
-- result: ... 2 more rows
```

### Dominant crops across chips

```sql
SELECT hcat_dominant_name_en AS crop, count(*) AS chips FROM read_parquet('ch_sg_2025_chips.parquet') WHERE hcat_dominant_code IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
-- result: Extensively used meadows (without pastures) | 314
-- result: Extensively used pastures | 12
-- result: Other permanent meadows (without pastures) | 7
-- result: ... 3 more rows
```

### Field polygons intersecting one chip

```sql
SELECT count(*) AS fields FROM read_parquet('ch_sg_2025_fields.parquet') f, (SELECT geometry FROM read_parquet('ch_sg_2025_chips.parquet') LIMIT 1) c WHERE ST_Intersects(f.geometry, c.geometry);
-- result: 7
```

## Field embeddings

`ch_sg_2025_field_embeddings.parquet` has one row per field in `ch_sg_2025_fields.parquet`, keyed by `id`. For each product it holds the mean (`<product>_mean`) and standard deviation (`<product>_std`, population std) of every embedding dimension over the field's 10 m pixels, as 64-value float lists, and the pixels used (`<product>_pixels`):

- `aef_*`: [AlphaEarth Foundations Satellite Embedding, annual v1](https://source.coop/tge-labs/aef). 64 dimensions; each pixel's vector has unit length. CC-BY-4.0.
- `olmoearth_*`: [OlmoEarth v1.3 embeddings, first 64 of 128 dimensions](https://source.coop/olmoearth/olmoearth-v1-3-embeddings). First 64 of 128 dimensions, which form a complete embedding on their own. Vectors are not normalised. Ai2 asks that 64- and 128-dimension vectors are not compared with each other. [OlmoEarth Artifact License](https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt): cite Ai2, and its use restrictions (Section 2) apply to anything derived from these columns.

A field takes the pixels whose centre is inside it; a field too small to hold one uses every pixel it touches (`pixel_rule = 'touched'`). The values are already dequantised. Fields with no pixels a product covers have no value for it.

```sql
INSTALL spatial; LOAD spatial;
SELECT f.*, e.aef_mean, e.olmoearth_mean FROM read_parquet('ch_sg_2025_fields.parquet') f
JOIN read_parquet('ch_sg_2025_field_embeddings.parquet') e USING (id) LIMIT 5;
```

## Related collections

The field boundaries here come from [Source field boundary collection](https://data.source.coop/ftw/harmonized-field-data/ch/collection.json); consult it for the original attributes, licensing terms and update cadence.
