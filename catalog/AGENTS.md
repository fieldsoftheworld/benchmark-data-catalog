# Agent guide: Fields of the World Benchmark Data

Every claim in this file is quoted from a source or measured from the data.

## What this catalog is

One collection per country or region. Each collection will hold chip items on
the FTW grid; each item will carry label masks (instance, 2-class, 3-class,
optional DECODE layers) and, when imagery was downloaded, two clipped
Sentinel-2 scenes. Collection-level assets will carry the field polygons used,
their boundary lines, the chips table with split assignments, and
`items.parquet`, a stac-geoparquet mirror of every item.

## Accessing the data (once collections are published)

Read `items.parquet` first; it lists every chip with its bbox, split, and asset
hrefs, so a model loader can select chips without walking item JSON.

## Collections

<!-- collections:start -->
| ID | Title | Chips | Splits (train/val/test) | License | Link |
| --- | --- | --- | --- | --- | --- |
| lu | Luxembourg | 775 | 601/79/95 | CC-BY-4.0 | [lu/](lu/) |
| si | Slovenia | 5103 | 4078/512/513 | other | [si/](si/) |
<!-- collections:end -->

None published yet.
