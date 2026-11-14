# Spain Balearic Islands Crop fields: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Spain Balearic Islands Crop fields](https://source.coop/ftw/harmonized-field-data/es_ib) (`es_ib`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `es_ib_2024` (2024): [agent guide](https://source.coop/ftw/benchmark-data/es_ib/es_ib_2024/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/es_ib/es_ib_2024/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/es_ib/es_ib_2024/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Keep each year's own train, validation and test split rather than pooling chips across years, or the same field can land on both sides of a split.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
