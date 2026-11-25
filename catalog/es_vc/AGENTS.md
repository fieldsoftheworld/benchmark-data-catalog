# Spain Valencia Crop Fields: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Spain Valencia Crop Fields](https://source.coop/ftw/harmonized-field-data/es_vc) (`es_vc`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `es_vc_2024` (2024): [agent guide](https://source.coop/ftw/benchmark-data/es_vc/es_vc_2024/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/es_vc/es_vc_2024/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/es_vc/es_vc_2024/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Take splits from the chips table of the [all-chips collection](https://source.coop/ftw/benchmark-data/chips/AGENTS.md) ([`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips/chips.parquet)), whose `split_hash_v1` and `split_admin2_v1` give a location the same split in every year, so pooling years never puts the same field on both sides.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
