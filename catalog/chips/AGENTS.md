# Agent guide: All chips: every benchmark chip across the collections

## Overview

Every chip of every Fields of the World benchmark collection in one table, one row per collection and chip, with one column per split scheme: split_hash_v1 and split_admin2_v1 give a location the same split in every collection, so collections can be pooled without a location on both sides. The tiles map every chip location by its admin2 split. Each row carries its collection's license. Open it in the [data browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/chips/collection.json); the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) describes the collections themselves.

## Accessing the data

- [`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips/chips.parquet): GeoParquet, one row per collection and chip.
- [`chips.pmtiles`](https://data.source.coop/ftw/benchmark-data/chips/chips.pmtiles): vector tiles, layers `overview_train`, `overview_val`, `overview_test`, `chips`.
- [MapLibre style](https://data.source.coop/ftw/benchmark-data/chips/styles/split-admin2.json).

## Schema & field notes

- `dataset`: The collection the chip is in (its id, such as at_2024).
- `group`: The source group the collection is published under: the harmonized source collection it was cut from.
- `id`: The chip's cell id on the FTW grid: the same id is the same square of ground in every collection.
- `block`: The chip's 3x3 block of grid cells, the unit split_hash_v1 is drawn for.
- `admin0_iso3`: ISO 3166-1 alpha-3 code of the chip's country (FAO GAUL 2024).
- `admin0_name`: The chip's country (FAO GAUL 2024).
- `admin1_name`: The chip's first-level administrative unit (FAO GAUL 2024).
- `admin2_name`: The chip's second-level administrative unit (FAO GAUL 2024).
- `license`: The collection's license, an SPDX id or other.
- `license_url`: The collection's own license link (the SPDX page for a standard id).
- `license_category`: The license sorted for filtering: public-domain, attribution and share-alike allow any use, including commercial; then non-commercial, restricted, and unknown where the terms aren't judged yet.
- `presence_only`: The collection's ftw:presence_only: its labels mark fields that exist, not where fields are absent.
- `split_legacy`: What the collection published before this table (a seeded block3x3 or predefined split). Frozen, so chips added later are null.
- `split_predefined`: The source's own split, for collections whose source defines one.
- `split_hash_v1`: train, val or test from a stable hash of the chip's block, 80/10/10: a location has the same split in every collection and year.
- `unit_admin2_v1`: The unit split_admin2_v1 assigns: the chip's admin2 area (its admin1 when it has no admin2 name, or its block where a country has too few admin2 areas to balance).
- `split_admin2_v1`: train, val or test for whole admin2 units, balanced to 80/10/10 within each country. A unit with a presence-only chip is train.
- `geometry`: The chip's footprint (OGC:CRS84).
- `bbox`: The footprint's bounding box.

## Data quality & usage notes

Each collection assigns its own train / validation / test split, so a location in several collections (other years of a country, or overlapping regions) can be test in one and train in another. This table gives every chip of every collection one column per split scheme; model code picks the column:

- `split_legacy`: what each collection published before this table. Frozen, so chips added later are null.
- `split_predefined`: the source's own split, for collections whose source defines one.
- `split_hash_v1`: one split per location in every collection, from a stable hash of the chip's 3x3 block of grid cells (80 / 10 / 10 overall). Use it to train and test across collections without a location on both sides.
- `split_admin2_v1`: whole admin2 areas (`unit_admin2_v1`), balanced to 80 / 10 / 10 within each country, so every country with three areas or more without presence-only chips has all three splits, and no area is on both sides. An area with any chip from a presence-only collection is train, since presence-only labels can't be scored; countries whose chips are all presence-only (India and most of Africa) are train only. Frozen once published.

A location in several collections has one row per collection, and the same `split_hash_v1` and `split_admin2_v1` in each. Take a chip's imagery and masks from its collection (`group`/`dataset`), whose `items.parquet` lists them by `id`.

## License

The table mixes licenses, so the collection's license is `other`: each row carries its own collection's `license` and `license_url` (the collection's own license link, the SPDX page for a standard id), and `license_category` sorts them for filtering: `public-domain`, `attribution` and `share-alike` allow any use, including commercial; then `non-commercial`, `restricted`, and `unknown` where the terms aren't judged yet. A chip is published under the terms of the collection it is in.

## Example queries

```sql
INSTALL spatial; LOAD spatial;
SELECT split_admin2_v1, count(*)
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/chips/chips.parquet')
WHERE license_category IN ('public-domain', 'attribution', 'share-alike')
GROUP BY 1;
```

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
