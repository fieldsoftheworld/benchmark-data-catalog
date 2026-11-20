# Slovakia Agricultural Land Identification System: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Slovakia Agricultural Land Identification System](https://source.coop/ftw/harmonized-field-data/sk) (`sk`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `sk_2018` (2018): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2018/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2018/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2018/items.parquet)
- `sk_2019` (2019): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2019/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2019/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2019/items.parquet)
- `sk_2020` (2020): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2020/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2020/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2020/items.parquet)
- `sk_2021` (2021): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2021/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2021/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2021/items.parquet)
- `sk_2022` (2022): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2022/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2022/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2022/items.parquet)
- `sk_2023` (2023): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2023/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2023/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2023/items.parquet)
- `sk_2024` (2024): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2024/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2024/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2024/items.parquet)
- `sk_2025` (2025): [agent guide](https://source.coop/ftw/benchmark-data/sk/sk_2025/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/sk/sk_2025/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/sk/sk_2025/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Keep each year's own train, validation and test split rather than pooling chips across years, or the same field can land on both sides of a split.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
