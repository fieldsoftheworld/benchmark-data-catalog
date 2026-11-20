# Crop Fields for Lower Saxony / Bremen / Hamburg, Germany: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Crop Fields for Lower Saxony / Bremen / Hamburg, Germany](https://source.coop/ftw/harmonized-field-data/de_nds) (`de_nds`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `de_nds_2025` (2025): [agent guide](https://source.coop/ftw/benchmark-data/de_nds/de_nds_2025/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/de_nds/de_nds_2025/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/de_nds/de_nds_2025/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Keep each year's own train, validation and test split rather than pooling chips across years, or the same field can land on both sides of a split.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
