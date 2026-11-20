# South Africa Crop Field Boundaries (Fusion Competition) with splits: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [South Africa Crop Field Boundaries (Fusion Competition) with splits](https://source.coop/ftw/harmonized-field-data/za_fusion_ml) (`za_fusion_ml`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `za_fusion_ml_2017` (2017): [agent guide](https://source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Keep each year's own train, validation and test split rather than pooling chips across years, or the same field can land on both sides of a split.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
