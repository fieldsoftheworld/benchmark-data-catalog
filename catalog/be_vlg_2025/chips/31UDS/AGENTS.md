# Belgium, Flanders — 2025 — MGRS square 31UDS

## Overview

This is a sub-catalog of chips in MGRS 100 km square 31UDS. See the [collection agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2025/AGENTS.md) for the full collection.

## Accessing the data

Query this square's items out of the collection's `items.parquet`, filtered on the square prefix of the item id:

```sql
SELECT * FROM read_parquet('https://data.source.coop/ftw/benchmark-data/be_vlg_2025/items.parquet') WHERE id LIKE 'ftw-31UDS%';
```

## Schema & field notes

Every column and property is documented in the [collection agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2025/AGENTS.md); nothing here is specific to this square.

## Data quality & usage notes

Every data quality note in the [collection agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2025/AGENTS.md) applies equally to this square.

## Example queries

See the [collection agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2025/AGENTS.md) for worked examples against the full collection; the query above scopes any of them to this square.

## Related collections

See the [collection agent guide](https://source.coop/ftw/benchmark-data/be_vlg_2025/AGENTS.md) for related collections and the source field boundary data.
