# Mapping Africa: crop field boundary labels for Africa, 2017-2023: benchmark collections

## Overview

This group holds the Fields of the World benchmark collections cut from the harmonized field boundary collection [Mapping Africa: crop field boundary labels for Africa, 2017-2023](https://source.coop/ftw/harmonized-field-data/lacuna) (`lacuna`), one per year. See the [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) for what every collection carries.

## Accessing the data

- `lacuna_2017` (2017): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2017/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2017/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2017/items.parquet)
- `lacuna_2018` (2018): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2018/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2018/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2018/items.parquet)
- `lacuna_2019` (2019): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2019/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2019/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2019/items.parquet)
- `lacuna_2020` (2020): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2020/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2020/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2020/items.parquet)
- `lacuna_2021` (2021): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2021/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2021/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2021/items.parquet)
- `lacuna_2022` (2022): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2022/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2022/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2022/items.parquet)
- `lacuna_2023` (2023): [agent guide](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2023/AGENTS.md), [collection.json](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2023/collection.json), [items.parquet](https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2023/items.parquet)

## Schema & field notes

Every column and asset is documented in each collection's own agent guide; the collections in this group share one schema.

## Data quality & usage notes

Years of the same source can overlap in space. Take splits from the chips table of the [all-chips collection](https://source.coop/ftw/benchmark-data/chips/AGENTS.md) ([`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips/chips.parquet)), whose `split_hash_v1` and `split_admin2_v1` give a location the same split in every year, so pooling years never puts the same field on both sides.

## Example queries

See each collection's agent guide for worked examples against its `items.parquet`.

## Related collections

The [catalog agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md) lists every source group and collection.
