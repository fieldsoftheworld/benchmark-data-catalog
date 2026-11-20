# Italy Tuscany (ITI1) Crop Fields — EuroCropsV2: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Italy Tuscany (ITI1) Crop Fields — EuroCropsV2](https://source.coop/ftw/harmonized-field-data/it_1) (`it_1`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `it_1_2018` (2018): [agent guide](https://source.coop/ftw/benchmark-data/it_1/it_1_2018/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2018/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2018/items.parquet)
- `it_1_2019` (2019): [agent guide](https://source.coop/ftw/benchmark-data/it_1/it_1_2019/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2019/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2019/items.parquet)
- `it_1_2020` (2020): [agent guide](https://source.coop/ftw/benchmark-data/it_1/it_1_2020/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2020/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2020/items.parquet)
- `it_1_2022` (2022): [agent guide](https://source.coop/ftw/benchmark-data/it_1/it_1_2022/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2022/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/it_1/it_1_2022/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Keep each year's own train, validation and test split rather than pooling chips across years, or the same field can land on both sides of a split.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
