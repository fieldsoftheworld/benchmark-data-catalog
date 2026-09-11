# Fields of the World Benchmark Data

Training and evaluation data for models that delineate agricultural field
boundaries. Each chip is a fixed 2 km cell of a shared, MGRS-derived grid,
carrying label masks rasterized from official field boundary declarations, a
train / validation / test assignment, and — in most collections — paired
Sentinel-2 imagery. One collection per country or region.

This is version 2 of the benchmark introduced in [Fields of The World
(AAAI 2025)](https://doi.org/10.1609/aaai.v39i27.35034). The boundaries come
from the [harmonized field boundary
catalog](https://source.coop/ftw/harmonized-field-data), which republishes each
country's own parcel declarations in one schema; the chips, masks and imagery
here are cut from it with
[ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools)
(`ftwd`) from a recipe committed in the [source
repository](https://github.com/fieldsoftheworld/benchmark-data-catalog/tree/main/datasets),
so any collection can be rebuilt from the harmonized edition it names.

[Browse the whole catalog](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json)
· [agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md)
· [the paper](https://arxiv.org/abs/2409.16252)
· [version 1.0](https://source.coop/kerner-lab/fields-of-the-world)

## Collections

<!-- collections:start -->
**3 collections · 17,120 chips · 1,553,660 field polygons**

| Thumbnail | Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <img src="https://data.source.coop/ftw/benchmark-data/at/thumbnail.webp" alt="Austria" width="120"> | [Austria](https://source.coop/ftw/benchmark-data/at) | 11,242 | 9,018/1,153/1,071 | 1,022 linked | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lu/thumbnail.webp" alt="Luxembourg" width="120"> | [Luxembourg](https://source.coop/ftw/benchmark-data/lu) | 775 | 601/79/95 | 680 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lu](https://source.coop/ftw/harmonized-field-data/lu) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lu/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/thumbnail.webp" alt="Slovenia" width="120"> | [Slovenia](https://source.coop/ftw/benchmark-data/si) | 5,103 | 4,078/512/513 | 2,857 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Austria](https://source.coop/ftw/benchmark-data/at) | 11,242 | 1,022 linked | 11,242 |
| [Luxembourg](https://source.coop/ftw/benchmark-data/lu) | 775 | 680 stored | none |
| [Slovenia](https://source.coop/ftw/benchmark-data/si) | 5,103 | 2,857 stored | 5,103 |

`stored` means a four-band GeoTIFF clipped to the chip and published with it; `linked` means the chip's season item points at the whole Sentinel-2 scene on the source STAC API, for a reader to window. A chip with no scene still carries its masks and its split — pair it with imagery of your own, on the footprint in `items.parquet`.
<!-- collections:end -->

## Quick start

Everything here runs against the published files over HTTPS: no download, no
credentials, no catalog walk.

Each collection publishes `items.parquet`, a
[stac-geoparquet](https://github.com/stac-utils/stac-geoparquet) mirror of every
STAC item it holds, carrying a public URL for every asset. One query is
therefore enough to build a training list — chip id, split, and the URLs of the
rasters themselves:

```sql
INSTALL httpfs; LOAD httpfs;

SELECT id,
       "ftw:split",
       "ftw:field_coverage_pct",
       assets.semantic_2class_mask.href AS mask,
       assets.planting_image.href       AS planting_image
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/lu/items.parquet')
WHERE "ftw:split" = 'train'
LIMIT 5;
```

Swap `lu` for any collection id in the table above. `assets` is a struct, so
`DESCRIBE SELECT assets.* FROM read_parquet(...)` lists what a given
collection's chips actually carry: where imagery is `linked` rather than
`stored`, ask for `assets.planting_visual.href` and window the scene yourself.

To look before you query, open the [data
browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json).
It renders the collections, their chip footprints and the map styles each one
ships; the Browse column above opens a single collection in it.

## What a chip carries

Every chip is a STAC item on the FTW grid, so a cell id is the same square of
ground in every collection. Each chip carries:

- **Instance masks** — one integer label per field polygon, for instance
  segmentation.
- **Semantic masks** — 2-class (field / not field) and 3-class (interior /
  boundary / not field), the two semantic label forms the FTW paper benchmarks.
- **DECODE masks** — a boundary mask and a normalized distance-to-boundary map,
  after [Waldner et al. (2021)](https://doi.org/10.3390/rs13112197). A distance
  surface lets a watershed separate touching fields that a binary extent mask
  merges into one. New in 2.0.
- **A split assignment** — `train`, `val` or `test`, drawn in 3×3 spatial blocks
  (80 / 10 / 10) so that neighbouring chips do not straddle two splits and a
  model cannot learn a test chip from its training neighbour.
- **Field coverage**, the share of the chip's area that is mapped field, and —
  where the harmonized source carries
  [EuroCrops HCAT](https://github.com/maja601/EuroCrops) codes — the crop
  composition of the fields inside it.
- **Sentinel-2 scenes**, in the collections that have them: one from the
  planting window and one from the harvest window of the region's crop
  calendar, published as child items alongside the chip. Which collections
  carry imagery, and in what shape, is in the coverage table above.

## What a collection carries

Alongside the chip items, each collection publishes the tables the chips were
cut from and a mirror of the items themselves:

- `<id>_fields.parquet`, the field polygons used, and
  `<id>_boundary_lines.parquet`, their boundaries as lines.
- `<id>_chips.parquet`: every chip with its footprint, split assignment and
  field coverage.
- `items.parquet`: the stac-geoparquet mirror the quick start queries.
- `chips.pmtiles` and `fields.pmtiles`, with ready-made map styles under
  `styles/`, for looking at a collection before training on it.
- `README.md`, `AGENTS.md`, `llms.txt` and a thumbnail. A collection's README
  carries the numbers measured for that collection — split counts, the
  field-coverage distribution, imagery dates and cloud cover; its agent guide
  documents every column and ships worked queries with their results.

## Limitations

Worth reading before publishing a number from this benchmark.

- **Imagery is not uniform.** See the coverage table above. A labels-only
  collection is still usable — every chip's footprint and grid cell are in
  `items.parquet` — but it is not a drop-in substitute for one with scenes.
- **Labels are declarations, not observations.** Masks come from parcels
  declared for one year, and the declaration year differs between collections.
  Parcels subdivided, merged or reshaped after that declaration are not
  reflected.
- **Empty means unmapped, not fieldless.** Area inside a chip with no polygon
  may be a field nobody declared. Chips on the edge of a source dataset may be
  only partly covered by it.
- **Field coverage is skewed.** Filter on `ftw:field_coverage_pct` when sparse
  chips would distort an evaluation; each collection's README gives its own
  distribution.
- **Respect the splits.** They are spatially blocked. Resampling chips at
  random leaks information between train and test.
- **Cloud-free is not guaranteed.** Scenes are selected against a crop calendar
  within a cloud threshold, so acquisition dates and residual cloud vary
  between chips — check `ftw:planting_cloud_cover` and
  `ftw:harvest_cloud_cover`.

## Compared with Fields of the World 1.0

Version 1.0 remains published, unchanged, at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world):
24 countries, some 70,000 chips and 1.6 million field polygons, one zipped
folder per country. Version 2 is a rebuild rather than a re-release. It cuts
every collection from the harmonized field boundary catalog instead of a
one-off per-country conversion, so a collection can be regenerated when its
source publishes a new edition; it adds the DECODE boundary and distance masks;
and it publishes the chips as STAC with a queryable item mirror rather than
folders of files. Each collection's own README states, in measured numbers, how
it compares with the 1.0 folder it supersedes.

Version 2 is still being built out and does not yet cover everything 1.0 does —
the collections table above is the whole of it. Use 1.0 for anything version 2
has not published yet.

## Versioning

This edition is `2.0.0-alpha.1`. While it is in alpha, collections are updated
in place: a rebuild replaces the published files at the same URLs, and the
`updated` stamp in a collection's `collection.json` says when that last
happened. Treat any collection here as a moving target until 2.0.0 is released.

## License

There is no single license for this catalog. Each collection carries the
license of the field boundary data it was cut from — the License column above,
and the collection's own page — and the masks derived from those boundaries are
published under the same terms as their source. Check the collection you intend
to use before redistributing it or the models trained on it. Sentinel-2 imagery
is Copernicus data, free and open.

## Citation

If you use this data in published work, please cite the benchmark paper and
name the release you used.

```bibtex
@article{kerner2025fields,
  title   = {Fields of The World: A Machine Learning Benchmark Dataset for Global Agricultural Field Boundary Segmentation},
  author  = {Kerner, Hannah and Chaudhari, Snehal and Ghosh, Aninda and Robinson, Caleb and Ahmad, Adeel and Choi, Eddie and Jacobs, Nathan and Holmes, Chris and Mohr, Matthias and Dodhia, Rahul and Lavista Ferres, Juan M and Marcus, Jennifer},
  journal = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume  = {39},
  number  = {27},
  pages   = {28151--28159},
  year    = {2025},
  doi     = {10.1609/aaai.v39i27.35034},
  url     = {https://ojs.aaai.org/index.php/AAAI/article/view/35034}
}
```

For the data itself: *Fields of the World Benchmark Data*, version
`2.0.0-alpha.1`, [Source Cooperative](https://source.coop/ftw/benchmark-data),
accessed *YYYY-MM-DD*. Collections are updated in place while in alpha, so
record the date you took them, and the `updated` stamp of each collection you
used.

## Contact

Open an
[issue](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues) for a
problem with the data or a request for a country. Agents should start from the
[agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md), the
machine-readable tour of the same material;
[llms.txt](https://data.source.coop/ftw/benchmark-data/llms.txt) is the short
index.
