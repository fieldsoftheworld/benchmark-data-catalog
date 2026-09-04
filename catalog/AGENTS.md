# Agent guide: Fields of the World Benchmark Data

Every claim in this file is quoted from a source or measured from the data.

## What this catalog is

One collection per country or region. A collection holds chip items on the FTW
grid; each item carries label masks (instance, 2-class, 3-class, optional
DECODE layers) and, when imagery was downloaded, two clipped Sentinel-2 scenes.
Collection-level assets carry the field polygons used, their boundary lines,
the chips table with split assignments, and `items.parquet`, a
stac-geoparquet mirror of every item.

## Accessing the data

Read `items.parquet` first; it lists every chip with its bbox, split, and asset
hrefs, so a model loader can select chips without walking item JSON.

## Collections

None published yet.
