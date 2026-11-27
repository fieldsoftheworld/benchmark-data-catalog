# Fields of the World Benchmark Data

Training and evaluation data for models that delineate agricultural field
boundaries. Each chip is a fixed 2 km cell of a shared, MGRS-derived grid,
carrying label masks rasterized from official field boundary declarations, the
field outlines they were cut from, and the four quarterly Sentinel-2 mosaics of
the collection's year. One collection per country or region and year. The
benchmark's train / validation / test splits for every chip are in one root
table, [`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips.parquet).

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
· [map of every chip](https://pmtiles.io/#url=https://data.source.coop/ftw/benchmark-data/chips.pmtiles)
· [agent guide](https://source.coop/ftw/benchmark-data/AGENTS.md)
· [the paper](https://arxiv.org/abs/2409.16252)
· [version 1.0](https://source.coop/kerner-lab/fields-of-the-world)

## Collections

<!-- collections:start -->
**180 collections · 3,082,670 chips**

| Thumbnail | Collection | Chips | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- |
| <img src="https://data.source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021/thumbnail.webp" alt="Cambodia/Vietnam (AI4SF) with splits — 2021" width="120"> | [Cambodia/Vietnam (AI4SF) with splits — 2021](https://source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021) | 797 | 797 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ai4sf_ml](https://source.coop/ftw/harmonized-field-data/ai4sf_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2018/thumbnail.webp" alt="Austria — 2018" width="120"> | [Austria — 2018](https://source.coop/ftw/benchmark-data/at/at_2018) | 14,493 | 14,493 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2019/thumbnail.webp" alt="Austria — 2019" width="120"> | [Austria — 2019](https://source.coop/ftw/benchmark-data/at/at_2019) | 14,491 | 14,491 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2020/thumbnail.webp" alt="Austria — 2020" width="120"> | [Austria — 2020](https://source.coop/ftw/benchmark-data/at/at_2020) | 14,496 | 14,496 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2021/thumbnail.webp" alt="Austria — 2021" width="120"> | [Austria — 2021](https://source.coop/ftw/benchmark-data/at/at_2021) | 14,506 | 14,506 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2022/thumbnail.webp" alt="Austria — 2022" width="120"> | [Austria — 2022](https://source.coop/ftw/benchmark-data/at/at_2022) | 14,473 | 14,473 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2023/thumbnail.webp" alt="Austria — 2023" width="120"> | [Austria — 2023](https://source.coop/ftw/benchmark-data/at/at_2023) | 14,484 | 14,484 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2024/thumbnail.webp" alt="Austria — 2024" width="120"> | [Austria — 2024](https://source.coop/ftw/benchmark-data/at/at_2024) | 14,497 | 14,497 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at/at_2025/thumbnail.webp" alt="Austria — 2025" width="120"> | [Austria — 2025](https://source.coop/ftw/benchmark-data/at/at_2025) | 14,516 | 14,516 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at/at_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018/thumbnail.webp" alt="Belgium, Flanders — 2018" width="120"> | [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018) | 2,939 | 2,939 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019/thumbnail.webp" alt="Belgium, Flanders — 2019" width="120"> | [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019) | 2,945 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020/thumbnail.webp" alt="Belgium, Flanders — 2020" width="120"> | [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020) | 2,941 | 2,941 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021/thumbnail.webp" alt="Belgium, Flanders — 2021" width="120"> | [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021) | 2,943 | 2,943 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022/thumbnail.webp" alt="Belgium, Flanders — 2022" width="120"> | [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022) | 2,946 | 2,946 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023/thumbnail.webp" alt="Belgium, Flanders — 2023" width="120"> | [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023) | 2,948 | 2,948 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024/thumbnail.webp" alt="Belgium, Flanders — 2024" width="120"> | [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024) | 2,949 | 2,949 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025/thumbnail.webp" alt="Belgium, Flanders — 2025" width="120"> | [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025) | 2,945 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_wal/be_wal_2022/thumbnail.webp" alt="Belgium, Wallonia — 2022" width="120"> | [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal/be_wal_2022) | 3,607 | 3,602 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/be_wal](https://source.coop/ftw/harmonized-field-data/be_wal) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal/be_wal_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg/bg_2021/thumbnail.webp" alt="Bulgaria — 2021" width="120"> | [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg/bg_2021) | 18,076 | 18,055 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg/bg_2022/thumbnail.webp" alt="Bulgaria — 2022" width="120"> | [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg/bg_2022) | 18,123 | 18,102 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg/bg_2023/thumbnail.webp" alt="Bulgaria — 2023" width="120"> | [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg/bg_2023) | 17,846 | 17,825 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg/bg_2024/thumbnail.webp" alt="Bulgaria — 2024" width="120"> | [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg/bg_2024) | 18,225 | 18,204 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg/bg_2025/thumbnail.webp" alt="Bulgaria — 2025" width="120"> | [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg/bg_2025) | 18,292 | 18,271 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg/bg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020/thumbnail.webp" alt="West Bahia, Brazil — 2020" width="120"> | [West Bahia, Brazil — 2020](https://source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020) | 1,268 | 1,268 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/br_ba_lem](https://source.coop/ftw/harmonized-field-data/br_ba_lem) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ag_2025/thumbnail.webp" alt="Switzerland, Aargau — 2025" width="120"> | [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ag_2025) | 346 | 346 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ag_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ai_2025/thumbnail.webp" alt="Switzerland, Appenzell Innerrhoden — 2025" width="120"> | [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ai_2025) | 14 | 14 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ai_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ar_2025/thumbnail.webp" alt="Switzerland, Appenzell Ausserrhoden — 2025" width="120"> | [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ar_2025) | 34 | 34 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ar_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_be_2025/thumbnail.webp" alt="Switzerland, Bern — 2025" width="120"> | [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_be_2025) | 1,061 | 1,061 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_be_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_bl_2025/thumbnail.webp" alt="Switzerland, Basel-Landschaft — 2025" width="120"> | [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch/ch_bl_2025) | 142 | 142 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_bl_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_fr_2025/thumbnail.webp" alt="Switzerland, Fribourg — 2025" width="120"> | [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch/ch_fr_2025) | 363 | 363 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_fr_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ge_2025/thumbnail.webp" alt="Switzerland, Geneva — 2025" width="120"> | [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ge_2025) | 44 | 44 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ge_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ju_2025/thumbnail.webp" alt="Switzerland, Jura — 2025" width="120"> | [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ju_2025) | 179 | 179 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ju_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_lu_2025/thumbnail.webp" alt="Switzerland, Luzern — 2025" width="120"> | [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_lu_2025) | 354 | 354 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_lu_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_sg_2025/thumbnail.webp" alt="Switzerland, St. Gallen — 2025" width="120"> | [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sg_2025) | 339 | 339 stored | [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_sh_2025/thumbnail.webp" alt="Switzerland, Schaffhausen — 2025" width="120"> | [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sh_2025) | 44 | 44 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sh_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_so_2025/thumbnail.webp" alt="Switzerland, Solothurn — 2025" width="120"> | [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch/ch_so_2025) | 193 | 193 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_so_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_sz_2025/thumbnail.webp" alt="Switzerland, Schwyz — 2025" width="120"> | [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sz_2025) | 139 | 139 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_sz_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_tg_2025/thumbnail.webp" alt="Switzerland, Thurgau — 2025" width="120"> | [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_tg_2025) | 187 | 187 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_tg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_ur_2025/thumbnail.webp" alt="Switzerland, Uri — 2025" width="120"> | [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ur_2025) | 15 | 15 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_ur_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_vs_2025/thumbnail.webp" alt="Switzerland, Valais — 2025" width="120"> | [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch/ch_vs_2025) | 145 | 145 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_vs_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_zg_2025/thumbnail.webp" alt="Switzerland, Zug — 2025" width="120"> | [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zg_2025) | 32 | 32 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_zg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch/ch_zh_2025/thumbnail.webp" alt="Switzerland, Zürich — 2025" width="120"> | [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zh_2025) | 423 | 423 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch/ch_zh_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2019/thumbnail.webp" alt="Czech — 2019" width="120"> | [Czech — 2019](https://source.coop/ftw/benchmark-data/cz/cz_2019) | 14,444 | 14,437 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2020/thumbnail.webp" alt="Czech — 2020" width="120"> | [Czech — 2020](https://source.coop/ftw/benchmark-data/cz/cz_2020) | 14,576 | 14,569 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2021/thumbnail.webp" alt="Czech — 2021" width="120"> | [Czech — 2021](https://source.coop/ftw/benchmark-data/cz/cz_2021) | 14,572 | 14,565 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2022/thumbnail.webp" alt="Czech — 2022" width="120"> | [Czech — 2022](https://source.coop/ftw/benchmark-data/cz/cz_2022) | 14,604 | 14,597 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2023/thumbnail.webp" alt="Czech — 2023" width="120"> | [Czech — 2023](https://source.coop/ftw/benchmark-data/cz/cz_2023) | 15,060 | 15,053 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2024/thumbnail.webp" alt="Czech — 2024" width="120"> | [Czech — 2024](https://source.coop/ftw/benchmark-data/cz/cz_2024) | 15,064 | 15,057 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/cz/cz_2025/thumbnail.webp" alt="Czech — 2025" width="120"> | [Czech — 2025](https://source.coop/ftw/benchmark-data/cz/cz_2025) | 14,836 | 14,829 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/cz](https://source.coop/ftw/harmonized-field-data/cz) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/cz/cz_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/de_nds/de_nds_2025/thumbnail.webp" alt="Germany, Lower Saxony/Bremen/Hamburg — 2025" width="120"> | [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds/de_nds_2025) | 10,891 | 10,891 stored | [DL-DE-BY-2.0](https://spdx.org/licenses/DL-DE-BY-2.0.html) | [harmonized/de_nds](https://source.coop/ftw/harmonized-field-data/de_nds) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_nds/de_nds_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/de_sh/de_sh_2023/thumbnail.webp" alt="Germany, Schleswig-Holstein — 2023" width="120"> | [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2023) | 3,452 | 3,452 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/de_sh/de_sh_2024/thumbnail.webp" alt="Germany, Schleswig-Holstein — 2024" width="120"> | [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2024) | 3,451 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/de_sh/de_sh_2025/thumbnail.webp" alt="Germany, Schleswig-Holstein — 2025" width="120"> | [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2025) | 3,451 | 3,451 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh/de_sh_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2017/thumbnail.webp" alt="Denmark — 2017" width="120"> | [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk/dk_2017) | 9,688 | 9,688 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2018/thumbnail.webp" alt="Denmark — 2018" width="120"> | [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk/dk_2018) | 9,629 | 9,629 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2019/thumbnail.webp" alt="Denmark — 2019" width="120"> | [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk/dk_2019) | 9,624 | 9,624 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2020/thumbnail.webp" alt="Denmark — 2020" width="120"> | [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk/dk_2020) | 9,654 | 9,654 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2021/thumbnail.webp" alt="Denmark — 2021" width="120"> | [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk/dk_2021) | 9,647 | 9,647 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2022/thumbnail.webp" alt="Denmark — 2022" width="120"> | [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk/dk_2022) | 9,640 | 9,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2023/thumbnail.webp" alt="Denmark — 2023" width="120"> | [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk/dk_2023) | 9,630 | 9,630 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2024/thumbnail.webp" alt="Denmark — 2024" width="120"> | [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk/dk_2024) | 9,672 | 9,672 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk/dk_2025/thumbnail.webp" alt="Denmark — 2025" width="120"> | [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk/dk_2025) | 9,639 | 9,639 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk/dk_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021/thumbnail.webp" alt="Lithuania - Eurocrops 2021 — 2021" width="120"> | [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021) | 13,468 | 13,468 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/ec_lt](https://source.coop/ftw/harmonized-field-data/ec_lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2017/thumbnail.webp" alt="Estonia — 2017" width="120"> | [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee/ee_2017) | 7,745 | 7,745 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2018/thumbnail.webp" alt="Estonia — 2018" width="120"> | [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee/ee_2018) | 7,765 | 7,765 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2019/thumbnail.webp" alt="Estonia — 2019" width="120"> | [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee/ee_2019) | 7,787 | 7,787 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2020/thumbnail.webp" alt="Estonia — 2020" width="120"> | [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee/ee_2020) | 7,807 | 7,807 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2021/thumbnail.webp" alt="Estonia — 2021" width="120"> | [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee/ee_2021) | 7,853 | 7,853 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2022/thumbnail.webp" alt="Estonia — 2022" width="120"> | [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee/ee_2022) | 7,871 | 7,871 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2023/thumbnail.webp" alt="Estonia — 2023" width="120"> | [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee/ee_2023) | 7,606 | 7,606 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee/ee_2024/thumbnail.webp" alt="Estonia — 2024" width="120"> | [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee/ee_2024) | 7,562 | 7,562 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee/ee_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es/es_2025/thumbnail.webp" alt="Spain — 2025" width="120"> | [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_2025) | 53,145 | 53,124 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es/es_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es/es_po_2025/thumbnail.webp" alt="Spain — 2025" width="120"> | [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_po_2025) | 29,795 | 29,795 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es/es_po_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_cat/es_cat_2024/thumbnail.webp" alt="Catalonia — 2024" width="120"> | [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat/es_cat_2024) | 5,814 | 5,814 stored | [License](https://administraciodigital.gencat.cat/ca/dades/dades-obertes/informacio-practica/llicencies/) | [harmonized/es_cat](https://source.coop/ftw/harmonized-field-data/es_cat) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cat/es_cat_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_cm/es_cm_2024/thumbnail.webp" alt="Spain Castilla-La Mancha — 2024" width="120"> | [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm/es_cm_2024) | 17,833 | 17,833 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/es_cm](https://source.coop/ftw/harmonized-field-data/es_cm) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_cm/es_cm_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_ib/es_ib_2024/thumbnail.webp" alt="Spain Balearic Islands — 2024" width="120"> | [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib/es_ib_2024) | 837 | 837 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_ib](https://source.coop/ftw/harmonized-field-data/es_ib) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_ib/es_ib_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_vc/es_vc_2024/thumbnail.webp" alt="Spain Valencia — 2024" width="120"> | [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc/es_vc_2024) | 4,926 | 4,926 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_vc](https://source.coop/ftw/harmonized-field-data/es_vc) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_vc/es_vc_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2020/thumbnail.webp" alt="Finland — 2020" width="120"> | [Finland — 2020](https://source.coop/ftw/benchmark-data/fi/fi_2020) | 37,389 | 37,389 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2021/thumbnail.webp" alt="Finland — 2021" width="120"> | [Finland — 2021](https://source.coop/ftw/benchmark-data/fi/fi_2021) | 37,086 | 37,086 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2022/thumbnail.webp" alt="Finland — 2022" width="120"> | [Finland — 2022](https://source.coop/ftw/benchmark-data/fi/fi_2022) | 37,070 | 37,069 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2023/thumbnail.webp" alt="Finland — 2023" width="120"> | [Finland — 2023](https://source.coop/ftw/benchmark-data/fi/fi_2023) | 36,621 | 36,620 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2024/thumbnail.webp" alt="Finland — 2024" width="120"> | [Finland — 2024](https://source.coop/ftw/benchmark-data/fi/fi_2024) | 35,929 | 35,928 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fi/fi_2025/thumbnail.webp" alt="Finland — 2025" width="120"> | [Finland — 2025](https://source.coop/ftw/benchmark-data/fi/fi_2025) | 35,540 | 35,540 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fi](https://source.coop/ftw/harmonized-field-data/fi) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fi/fi_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2017/thumbnail.webp" alt="France — 2017" width="120"> | [France — 2017](https://source.coop/ftw/benchmark-data/fr/fr_2017) | 121,892 | 121,701 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2018/thumbnail.webp" alt="France — 2018" width="120"> | [France — 2018](https://source.coop/ftw/benchmark-data/fr/fr_2018) | 121,841 | 121,649 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2019/thumbnail.webp" alt="France — 2019" width="120"> | [France — 2019](https://source.coop/ftw/benchmark-data/fr/fr_2019) | 121,933 | 121,741 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2020/thumbnail.webp" alt="France — 2020" width="120"> | [France — 2020](https://source.coop/ftw/benchmark-data/fr/fr_2020) | 121,954 | 121,762 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2021/thumbnail.webp" alt="France — 2021" width="120"> | [France — 2021](https://source.coop/ftw/benchmark-data/fr/fr_2021) | 122,031 | 121,840 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2022/thumbnail.webp" alt="France — 2022" width="120"> | [France — 2022](https://source.coop/ftw/benchmark-data/fr/fr_2022) | 121,995 | 121,804 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2023/thumbnail.webp" alt="France — 2023" width="120"> | [France — 2023](https://source.coop/ftw/benchmark-data/fr/fr_2023) | 121,876 | 121,684 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/fr/fr_2024/thumbnail.webp" alt="France — 2024" width="120"> | [France — 2024](https://source.coop/ftw/benchmark-data/fr/fr_2024) | 121,860 | 121,670 stored | [License](https://etalab.gouv.fr/licence-ouverte-open-licence) | [harmonized/fr](https://source.coop/ftw/harmonized-field-data/fr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/fr/fr_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/glocab/glocab_2017/thumbnail.webp" alt="GloCAB — 2017" width="120"> | [GloCAB — 2017](https://source.coop/ftw/benchmark-data/glocab/glocab_2017) | 6,067 | 6,054 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/glocab/glocab_2018/thumbnail.webp" alt="GloCAB — 2018" width="120"> | [GloCAB — 2018](https://source.coop/ftw/benchmark-data/glocab/glocab_2018) | 598 | 598 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/glocab/glocab_2019/thumbnail.webp" alt="GloCAB — 2019" width="120"> | [GloCAB — 2019](https://source.coop/ftw/benchmark-data/glocab/glocab_2019) | 4,975 | 4,975 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/glocab/glocab_2020/thumbnail.webp" alt="GloCAB — 2020" width="120"> | [GloCAB — 2020](https://source.coop/ftw/benchmark-data/glocab/glocab_2020) | 12,452 | 12,425 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/glocab](https://source.coop/ftw/harmonized-field-data/glocab) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/glocab/glocab_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2017/thumbnail.webp" alt="Croatia — 2017" width="120"> | [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr/hr_2017) | 9,676 | 9,676 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2018/thumbnail.webp" alt="Croatia — 2018" width="120"> | [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr/hr_2018) | 9,704 | 9,704 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2019/thumbnail.webp" alt="Croatia — 2019" width="120"> | [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr/hr_2019) | 9,724 | 9,724 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2020/thumbnail.webp" alt="Croatia — 2020" width="120"> | [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr/hr_2020) | 9,703 | 9,703 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2021/thumbnail.webp" alt="Croatia — 2021" width="120"> | [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr/hr_2021) | 9,734 | 9,734 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2022/thumbnail.webp" alt="Croatia — 2022" width="120"> | [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr/hr_2022) | 9,715 | 9,715 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2023/thumbnail.webp" alt="Croatia — 2023" width="120"> | [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr/hr_2023) | 9,680 | 9,680 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr/hr_2024/thumbnail.webp" alt="Croatia — 2024" width="120"> | [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr/hr_2024) | 9,588 | 9,588 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr/hr_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ie/ie_2022/thumbnail.webp" alt="Ireland — 2022" width="120"> | [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie/ie_2022) | 16,734 | 16,734 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ie/ie_2023/thumbnail.webp" alt="Ireland — 2023" width="120"> | [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie/ie_2023) | 16,762 | 16,762 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ie/ie_2024/thumbnail.webp" alt="Ireland — 2024" width="120"> | [Ireland — 2024](https://source.coop/ftw/benchmark-data/ie/ie_2024) | 16,757 | 16,757 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie/ie_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020/thumbnail.webp" alt="India 10k with splits — 2020" width="120"> | [India 10k with splits — 2020](https://source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020) | 2,410 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/in_10k_ml](https://source.coop/ftw/harmonized-field-data/in_10k_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/it_1/it_1_2018/thumbnail.webp" alt="Italy, Tuscany — 2018" width="120"> | [Italy, Tuscany — 2018](https://source.coop/ftw/benchmark-data/it_1/it_1_2018) | 4,515 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/it_1/it_1_2019/thumbnail.webp" alt="Italy, Tuscany — 2019" width="120"> | [Italy, Tuscany — 2019](https://source.coop/ftw/benchmark-data/it_1/it_1_2019) | 4,713 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/it_1/it_1_2020/thumbnail.webp" alt="Italy, Tuscany — 2020" width="120"> | [Italy, Tuscany — 2020](https://source.coop/ftw/benchmark-data/it_1/it_1_2020) | 4,673 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/it_1/it_1_2022/thumbnail.webp" alt="Italy, Tuscany — 2022" width="120"> | [Italy, Tuscany — 2022](https://source.coop/ftw/benchmark-data/it_1/it_1_2022) | 4,679 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/it_1](https://source.coop/ftw/harmonized-field-data/it_1) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/it_1/it_1_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp/jp_2021/thumbnail.webp" alt="Japan — 2021" width="120"> | [Japan — 2021](https://source.coop/ftw/benchmark-data/jp/jp_2021) | 61,016 | 61,000 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp/jp_2022/thumbnail.webp" alt="Japan — 2022" width="120"> | [Japan — 2022](https://source.coop/ftw/benchmark-data/jp/jp_2022) | 60,961 | 60,945 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp/jp_2023/thumbnail.webp" alt="Japan — 2023" width="120"> | [Japan — 2023](https://source.coop/ftw/benchmark-data/jp/jp_2023) | 60,957 | 60,941 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp/jp_2024/thumbnail.webp" alt="Japan — 2024" width="120"> | [Japan — 2024](https://source.coop/ftw/benchmark-data/jp/jp_2024) | 60,943 | 60,927 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp/jp_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2017/thumbnail.webp" alt="Mapping Africa — 2017" width="120"> | [Mapping Africa — 2017](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2017) | 6,972 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2018/thumbnail.webp" alt="Mapping Africa — 2018" width="120"> | [Mapping Africa — 2018](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2018) | 7,215 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2019/thumbnail.webp" alt="Mapping Africa — 2019" width="120"> | [Mapping Africa — 2019](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2019) | 7,343 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2020/thumbnail.webp" alt="Mapping Africa — 2020" width="120"> | [Mapping Africa — 2020](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2020) | 7,762 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2021/thumbnail.webp" alt="Mapping Africa — 2021" width="120"> | [Mapping Africa — 2021](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2021) | 7,141 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2022/thumbnail.webp" alt="Mapping Africa — 2022" width="120"> | [Mapping Africa — 2022](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2022) | 7,262 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lacuna/lacuna_2023/thumbnail.webp" alt="Mapping Africa — 2023" width="120"> | [Mapping Africa — 2023](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2023) | 6,966 | — | [License](https://go.planet.com/nicfi-pla-2024) | [harmonized/lacuna](https://source.coop/ftw/harmonized-field-data/lacuna) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lacuna/lacuna_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lt/lt_2024/thumbnail.webp" alt="Lithuania — 2024" width="120"> | [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt/lt_2024) | 14,123 | 14,123 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt/lt_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lt/lt_2025/thumbnail.webp" alt="Lithuania — 2025" width="120"> | [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt/lt_2025) | 14,140 | 14,140 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt/lt_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2017/thumbnail.webp" alt="Latvia — 2017" width="120"> | [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv/lv_2017) | 13,016 | 13,016 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2018/thumbnail.webp" alt="Latvia — 2018" width="120"> | [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv/lv_2018) | 13,028 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2019/thumbnail.webp" alt="Latvia — 2019" width="120"> | [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv/lv_2019) | 13,074 | 13,074 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2020/thumbnail.webp" alt="Latvia — 2020" width="120"> | [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv/lv_2020) | 13,088 | 13,088 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2021/thumbnail.webp" alt="Latvia — 2021" width="120"> | [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv/lv_2021) | 13,073 | 13,073 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2022/thumbnail.webp" alt="Latvia — 2022" width="120"> | [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv/lv_2022) | 13,066 | 13,066 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2023/thumbnail.webp" alt="Latvia — 2023" width="120"> | [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv/lv_2023) | 13,028 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2024/thumbnail.webp" alt="Latvia — 2024" width="120"> | [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv/lv_2024) | 13,056 | 13,056 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv/lv_2025/thumbnail.webp" alt="Latvia — 2025" width="120"> | [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv/lv_2025) | 13,061 | 13,061 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv/lv_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2017/thumbnail.webp" alt="Netherlands (Crops) — 2017" width="120"> | [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl/nl_2017) | 7,600 | 7,594 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2018/thumbnail.webp" alt="Netherlands (Crops) — 2018" width="120"> | [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl/nl_2018) | 7,594 | 7,588 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2019/thumbnail.webp" alt="Netherlands (Crops) — 2019" width="120"> | [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl/nl_2019) | 7,582 | 7,576 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2020/thumbnail.webp" alt="Netherlands (Crops) — 2020" width="120"> | [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl/nl_2020) | 7,592 | 7,586 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2021/thumbnail.webp" alt="Netherlands (Crops) — 2021" width="120"> | [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl/nl_2021) | 7,596 | 7,590 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2022/thumbnail.webp" alt="Netherlands (Crops) — 2022" width="120"> | [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl/nl_2022) | 7,590 | 7,584 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2023/thumbnail.webp" alt="Netherlands (Crops) — 2023" width="120"> | [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl/nl_2023) | 7,610 | 7,604 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2024/thumbnail.webp" alt="Netherlands (Crops) — 2024" width="120"> | [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl/nl_2024) | 7,584 | 7,578 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl/nl_2025/thumbnail.webp" alt="Netherlands (Crops) — 2025" width="120"> | [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl/nl_2025) | 7,574 | 7,568 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl/nl_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2017/thumbnail.webp" alt="Portugal — 2017" width="120"> | [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt/pt_2017) | 20,027 | 20,027 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2018/thumbnail.webp" alt="Portugal — 2018" width="120"> | [Portugal — 2018](https://source.coop/ftw/benchmark-data/pt/pt_2018) | 20,085 | 20,085 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2019/thumbnail.webp" alt="Portugal — 2019" width="120"> | [Portugal — 2019](https://source.coop/ftw/benchmark-data/pt/pt_2019) | 20,328 | 20,328 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2020/thumbnail.webp" alt="Portugal — 2020" width="120"> | [Portugal — 2020](https://source.coop/ftw/benchmark-data/pt/pt_2020) | 20,030 | 20,030 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2021/thumbnail.webp" alt="Portugal — 2021" width="120"> | [Portugal — 2021](https://source.coop/ftw/benchmark-data/pt/pt_2021) | 20,329 | 20,329 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2022/thumbnail.webp" alt="Portugal — 2022" width="120"> | [Portugal — 2022](https://source.coop/ftw/benchmark-data/pt/pt_2022) | 20,361 | 20,361 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2023/thumbnail.webp" alt="Portugal — 2023" width="120"> | [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt/pt_2023) | 20,002 | 20,002 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/pt/pt_2025/thumbnail.webp" alt="Portugal — 2025" width="120"> | [Portugal — 2025](https://source.coop/ftw/benchmark-data/pt/pt_2025) | 20,298 | 20,298 stored | [License](https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply) | [harmonized/pt](https://source.coop/ftw/harmonized-field-data/pt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/pt/pt_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021/thumbnail.webp" alt="Rwanda with splits — 2021" width="120"> | [Rwanda with splits — 2021](https://source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021) | 73 | 73 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/rw_rwanda_ml](https://source.coop/ftw/harmonized-field-data/rw_rwanda_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2017/thumbnail.webp" alt="Sweden — 2017" width="120"> | [Sweden — 2017](https://source.coop/ftw/benchmark-data/se/se_2017) | 32,935 | 32,935 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2018/thumbnail.webp" alt="Sweden — 2018" width="120"> | [Sweden — 2018](https://source.coop/ftw/benchmark-data/se/se_2018) | 32,623 | 32,623 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2019/thumbnail.webp" alt="Sweden — 2019" width="120"> | [Sweden — 2019](https://source.coop/ftw/benchmark-data/se/se_2019) | 32,880 | 32,880 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2020/thumbnail.webp" alt="Sweden — 2020" width="120"> | [Sweden — 2020](https://source.coop/ftw/benchmark-data/se/se_2020) | 32,771 | 32,771 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2021/thumbnail.webp" alt="Sweden — 2021" width="120"> | [Sweden — 2021](https://source.coop/ftw/benchmark-data/se/se_2021) | 32,822 | 32,822 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2022/thumbnail.webp" alt="Sweden — 2022" width="120"> | [Sweden — 2022](https://source.coop/ftw/benchmark-data/se/se_2022) | 32,742 | 32,742 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2023/thumbnail.webp" alt="Sweden — 2023" width="120"> | [Sweden — 2023](https://source.coop/ftw/benchmark-data/se/se_2023) | 32,640 | 32,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2024/thumbnail.webp" alt="Sweden — 2024" width="120"> | [Sweden — 2024](https://source.coop/ftw/benchmark-data/se/se_2024) | 32,410 | 32,410 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/se/se_2025/thumbnail.webp" alt="Sweden — 2025" width="120"> | [Sweden — 2025](https://source.coop/ftw/benchmark-data/se/se_2025) | 32,552 | 32,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/se](https://source.coop/ftw/harmonized-field-data/se) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/se/se_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2019/thumbnail.webp" alt="Slovenia — 2019" width="120"> | [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si/si_2019) | 4,300 | 4,300 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2020/thumbnail.webp" alt="Slovenia — 2020" width="120"> | [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si/si_2020) | 4,282 | 4,282 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2021/thumbnail.webp" alt="Slovenia — 2021" width="120"> | [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si/si_2021) | 4,286 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2022/thumbnail.webp" alt="Slovenia — 2022" width="120"> | [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si/si_2022) | 4,286 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2023/thumbnail.webp" alt="Slovenia — 2023" width="120"> | [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si/si_2023) | 4,287 | 4,287 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si/si_2024/thumbnail.webp" alt="Slovenia — 2024" width="120"> | [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si/si_2024) | 4,291 | 4,291 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si/si_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2018/thumbnail.webp" alt="Slovakia — 2018" width="120"> | [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk/sk_2018) | 9,806 | 9,785 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2019/thumbnail.webp" alt="Slovakia — 2019" width="120"> | [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk/sk_2019) | 9,856 | 9,835 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2020/thumbnail.webp" alt="Slovakia — 2020" width="120"> | [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk/sk_2020) | 9,885 | 9,864 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2021/thumbnail.webp" alt="Slovakia — 2021" width="120"> | [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk/sk_2021) | 9,875 | 9,854 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2022/thumbnail.webp" alt="Slovakia — 2022" width="120"> | [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk/sk_2022) | 9,866 | 9,845 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2023/thumbnail.webp" alt="Slovakia — 2023" width="120"> | [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk/sk_2023) | 9,571 | 9,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2024/thumbnail.webp" alt="Slovakia — 2024" width="120"> | [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk/sk_2024) | 9,986 | 9,965 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk/sk_2025/thumbnail.webp" alt="Slovakia — 2025" width="120"> | [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk/sk_2025) | 9,985 | 9,964 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk/sk_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020/thumbnail.webp" alt="Trazo with splits — 2020" width="120"> | [Trazo with splits — 2020](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020) | 3,687 | 3,686 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021/thumbnail.webp" alt="Trazo with splits — 2021" width="120"> | [Trazo with splits — 2021](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021) | 498 | 498 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022/thumbnail.webp" alt="Trazo with splits — 2022" width="120"> | [Trazo with splits — 2022](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022) | 590 | 590 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023/thumbnail.webp" alt="Trazo with splits — 2023" width="120"> | [Trazo with splits — 2023](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023) | 499 | 499 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/thumbnail.webp" alt="Trazo with splits — 2024" width="120"> | [Trazo with splits — 2024](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024) | 1,360 | 1,358 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/wri_trazo_ml](https://source.coop/ftw/harmonized-field-data/wri_trazo_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/thumbnail.webp" alt="South Africa (Fusion) with splits — 2017" width="120"> | [South Africa (Fusion) with splits — 2017](https://source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017) | 239 | — | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/za_fusion_ml](https://source.coop/ftw/harmonized-field-data/za_fusion_ml) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Cambodia/Vietnam (AI4SF) with splits — 2021](https://source.coop/ftw/benchmark-data/ai4sf_ml/ai4sf_ml_2021) | 797 | 797 stored | none |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at/at_2018) | 14,493 | 14,493 stored | 14,493 |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at/at_2019) | 14,491 | 14,491 stored | 14,491 |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at/at_2020) | 14,496 | 14,496 stored | 14,496 |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at/at_2021) | 14,506 | 14,506 stored | 14,506 |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at/at_2022) | 14,473 | 14,473 stored | 14,473 |
| [Austria — 2023](https://source.coop/ftw/benchmark-data/at/at_2023) | 14,484 | 14,484 stored | 14,484 |
| [Austria — 2024](https://source.coop/ftw/benchmark-data/at/at_2024) | 14,497 | 14,497 stored | 14,497 |
| [Austria — 2025](https://source.coop/ftw/benchmark-data/at/at_2025) | 14,516 | 14,516 stored | 14,516 |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2018) | 2,939 | 2,939 stored | 2,939 |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2019) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2020) | 2,941 | 2,941 stored | 2,941 |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2021) | 2,943 | 2,943 stored | 2,943 |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2022) | 2,946 | 2,946 stored | 2,946 |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2023) | 2,948 | 2,948 stored | 2,948 |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2024) | 2,949 | 2,949 stored | 2,949 |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg/be_vlg_2025) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal/be_wal_2022) | 3,607 | 3,602 stored | 3,607 |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg/bg_2021) | 18,076 | 18,055 stored | none |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg/bg_2022) | 18,123 | 18,102 stored | none |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg/bg_2023) | 17,846 | 17,825 stored | none |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg/bg_2024) | 18,225 | 18,204 stored | none |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg/bg_2025) | 18,292 | 18,271 stored | none |
| [West Bahia, Brazil — 2020](https://source.coop/ftw/benchmark-data/br_ba_lem/br_ba_lem_2020) | 1,268 | 1,268 stored | none |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ag_2025) | 346 | 346 stored | 346 |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ai_2025) | 14 | 14 stored | 14 |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ar_2025) | 34 | 34 stored | 34 |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_be_2025) | 1,061 | 1,061 stored | 1,061 |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch/ch_bl_2025) | 142 | 142 stored | 142 |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch/ch_fr_2025) | 363 | 363 stored | 363 |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ge_2025) | 44 | 44 stored | 44 |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ju_2025) | 179 | 179 stored | 179 |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch/ch_lu_2025) | 354 | 354 stored | 354 |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sg_2025) | 339 | 339 stored | 339 |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sh_2025) | 44 | 44 stored | 44 |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch/ch_so_2025) | 193 | 193 stored | 193 |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch/ch_sz_2025) | 139 | 139 stored | 139 |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch/ch_tg_2025) | 187 | 187 stored | 187 |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch/ch_ur_2025) | 15 | 15 stored | 15 |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch/ch_vs_2025) | 145 | 145 stored | 145 |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zg_2025) | 32 | 32 stored | 32 |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch/ch_zh_2025) | 423 | 423 stored | 423 |
| [Czech — 2019](https://source.coop/ftw/benchmark-data/cz/cz_2019) | 14,444 | 14,437 stored | 14,444 |
| [Czech — 2020](https://source.coop/ftw/benchmark-data/cz/cz_2020) | 14,576 | 14,569 stored | 14,576 |
| [Czech — 2021](https://source.coop/ftw/benchmark-data/cz/cz_2021) | 14,572 | 14,565 stored | 14,572 |
| [Czech — 2022](https://source.coop/ftw/benchmark-data/cz/cz_2022) | 14,604 | 14,597 stored | 14,604 |
| [Czech — 2023](https://source.coop/ftw/benchmark-data/cz/cz_2023) | 15,060 | 15,053 stored | 15,060 |
| [Czech — 2024](https://source.coop/ftw/benchmark-data/cz/cz_2024) | 15,064 | 15,057 stored | 15,064 |
| [Czech — 2025](https://source.coop/ftw/benchmark-data/cz/cz_2025) | 14,836 | 14,829 stored | 14,836 |
| [Germany, Lower Saxony/Bremen/Hamburg — 2025](https://source.coop/ftw/benchmark-data/de_nds/de_nds_2025) | 10,891 | 10,891 stored | 10,891 |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2023) | 3,452 | 3,452 stored | none |
| [Germany, Schleswig-Holstein — 2024](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2024) | 3,451 | 3,451 stored | none |
| [Germany, Schleswig-Holstein — 2025](https://source.coop/ftw/benchmark-data/de_sh/de_sh_2025) | 3,451 | 3,451 stored | none |
| [Denmark — 2017](https://source.coop/ftw/benchmark-data/dk/dk_2017) | 9,688 | 9,688 stored | 9,688 |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk/dk_2018) | 9,629 | 9,629 stored | 9,629 |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk/dk_2019) | 9,624 | 9,624 stored | 9,624 |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk/dk_2020) | 9,654 | 9,654 stored | 9,654 |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk/dk_2021) | 9,647 | 9,647 stored | 9,647 |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk/dk_2022) | 9,640 | 9,640 stored | 9,640 |
| [Denmark — 2023](https://source.coop/ftw/benchmark-data/dk/dk_2023) | 9,630 | 9,630 stored | 9,630 |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk/dk_2024) | 9,672 | 9,672 stored | 9,672 |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk/dk_2025) | 9,639 | 9,639 stored | 9,639 |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt/ec_lt_2021) | 13,468 | 13,468 stored | 13,468 |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee/ee_2017) | 7,745 | 7,745 stored | 7,745 |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee/ee_2018) | 7,765 | 7,765 stored | 7,765 |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee/ee_2019) | 7,787 | 7,787 stored | 7,787 |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee/ee_2020) | 7,807 | 7,807 stored | 7,807 |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee/ee_2021) | 7,853 | 7,853 stored | 7,853 |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee/ee_2022) | 7,871 | 7,871 stored | 7,871 |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee/ee_2023) | 7,606 | 7,606 stored | 7,606 |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee/ee_2024) | 7,562 | 7,562 stored | 7,562 |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_2025) | 53,145 | 53,124 stored | 53,039 |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es/es_po_2025) | 29,795 | 29,795 stored | 29,795 |
| [Catalonia — 2024](https://source.coop/ftw/benchmark-data/es_cat/es_cat_2024) | 5,814 | 5,814 stored | 5,814 |
| [Spain Castilla-La Mancha — 2024](https://source.coop/ftw/benchmark-data/es_cm/es_cm_2024) | 17,833 | 17,833 stored | 17,833 |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib/es_ib_2024) | 837 | 837 stored | none |
| [Spain Valencia — 2024](https://source.coop/ftw/benchmark-data/es_vc/es_vc_2024) | 4,926 | 4,926 stored | 4,926 |
| [Finland — 2020](https://source.coop/ftw/benchmark-data/fi/fi_2020) | 37,389 | 37,389 stored | 37,389 |
| [Finland — 2021](https://source.coop/ftw/benchmark-data/fi/fi_2021) | 37,086 | 37,086 stored | 37,086 |
| [Finland — 2022](https://source.coop/ftw/benchmark-data/fi/fi_2022) | 37,070 | 37,069 stored | 37,070 |
| [Finland — 2023](https://source.coop/ftw/benchmark-data/fi/fi_2023) | 36,621 | 36,620 stored | 36,621 |
| [Finland — 2024](https://source.coop/ftw/benchmark-data/fi/fi_2024) | 35,929 | 35,928 stored | 35,929 |
| [Finland — 2025](https://source.coop/ftw/benchmark-data/fi/fi_2025) | 35,540 | 35,540 stored | 35,540 |
| [France — 2017](https://source.coop/ftw/benchmark-data/fr/fr_2017) | 121,892 | 121,701 stored | 121,892 |
| [France — 2018](https://source.coop/ftw/benchmark-data/fr/fr_2018) | 121,841 | 121,649 stored | 121,841 |
| [France — 2019](https://source.coop/ftw/benchmark-data/fr/fr_2019) | 121,933 | 121,741 stored | 121,933 |
| [France — 2020](https://source.coop/ftw/benchmark-data/fr/fr_2020) | 121,954 | 121,762 stored | 121,954 |
| [France — 2021](https://source.coop/ftw/benchmark-data/fr/fr_2021) | 122,031 | 121,840 stored | 122,031 |
| [France — 2022](https://source.coop/ftw/benchmark-data/fr/fr_2022) | 121,995 | 121,804 stored | 121,995 |
| [France — 2023](https://source.coop/ftw/benchmark-data/fr/fr_2023) | 121,876 | 121,684 stored | 121,840 |
| [France — 2024](https://source.coop/ftw/benchmark-data/fr/fr_2024) | 121,860 | 121,670 stored | 121,829 |
| [GloCAB — 2017](https://source.coop/ftw/benchmark-data/glocab/glocab_2017) | 6,067 | 6,054 stored | none |
| [GloCAB — 2018](https://source.coop/ftw/benchmark-data/glocab/glocab_2018) | 598 | 598 stored | none |
| [GloCAB — 2019](https://source.coop/ftw/benchmark-data/glocab/glocab_2019) | 4,975 | 4,975 stored | none |
| [GloCAB — 2020](https://source.coop/ftw/benchmark-data/glocab/glocab_2020) | 12,452 | 12,425 stored | none |
| [Croatia — 2017](https://source.coop/ftw/benchmark-data/hr/hr_2017) | 9,676 | 9,676 stored | 9,676 |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr/hr_2018) | 9,704 | 9,704 stored | 9,704 |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr/hr_2019) | 9,724 | 9,724 stored | 9,724 |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr/hr_2020) | 9,703 | 9,703 stored | 9,703 |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr/hr_2021) | 9,734 | 9,734 stored | 9,734 |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr/hr_2022) | 9,715 | 9,715 stored | 9,715 |
| [Croatia — 2023](https://source.coop/ftw/benchmark-data/hr/hr_2023) | 9,680 | 9,680 stored | 9,680 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr/hr_2024) | 9,588 | 9,588 stored | 9,588 |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie/ie_2022) | 16,734 | 16,734 stored | 16,734 |
| [Ireland — 2023](https://source.coop/ftw/benchmark-data/ie/ie_2023) | 16,762 | 16,762 stored | 16,762 |
| [Ireland — 2024](https://source.coop/ftw/benchmark-data/ie/ie_2024) | 16,757 | 16,757 stored | 16,757 |
| [India 10k with splits — 2020](https://source.coop/ftw/benchmark-data/in_10k_ml/in_10k_ml_2020) | 2,410 | — | — |
| [Italy, Tuscany — 2018](https://source.coop/ftw/benchmark-data/it_1/it_1_2018) | 4,515 | — | — |
| [Italy, Tuscany — 2019](https://source.coop/ftw/benchmark-data/it_1/it_1_2019) | 4,713 | — | — |
| [Italy, Tuscany — 2020](https://source.coop/ftw/benchmark-data/it_1/it_1_2020) | 4,673 | — | — |
| [Italy, Tuscany — 2022](https://source.coop/ftw/benchmark-data/it_1/it_1_2022) | 4,679 | — | — |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp/jp_2021) | 61,016 | 61,000 stored | none |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp/jp_2022) | 60,961 | 60,945 stored | none |
| [Japan — 2023](https://source.coop/ftw/benchmark-data/jp/jp_2023) | 60,957 | 60,941 stored | none |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp/jp_2024) | 60,943 | 60,927 stored | none |
| [Mapping Africa — 2017](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2017) | 6,972 | — | — |
| [Mapping Africa — 2018](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2018) | 7,215 | — | — |
| [Mapping Africa — 2019](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2019) | 7,343 | — | — |
| [Mapping Africa — 2020](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2020) | 7,762 | — | — |
| [Mapping Africa — 2021](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2021) | 7,141 | — | — |
| [Mapping Africa — 2022](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2022) | 7,262 | — | — |
| [Mapping Africa — 2023](https://source.coop/ftw/benchmark-data/lacuna/lacuna_2023) | 6,966 | — | — |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt/lt_2024) | 14,123 | 14,123 stored | 14,123 |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt/lt_2025) | 14,140 | 14,140 stored | 14,140 |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv/lv_2017) | 13,016 | 13,016 stored | 13,016 |
| [Latvia — 2018](https://source.coop/ftw/benchmark-data/lv/lv_2018) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2019](https://source.coop/ftw/benchmark-data/lv/lv_2019) | 13,074 | 13,074 stored | 13,074 |
| [Latvia — 2020](https://source.coop/ftw/benchmark-data/lv/lv_2020) | 13,088 | 13,088 stored | 13,088 |
| [Latvia — 2021](https://source.coop/ftw/benchmark-data/lv/lv_2021) | 13,073 | 13,073 stored | 13,073 |
| [Latvia — 2022](https://source.coop/ftw/benchmark-data/lv/lv_2022) | 13,066 | 13,066 stored | 13,066 |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv/lv_2023) | 13,028 | 13,028 stored | 13,028 |
| [Latvia — 2024](https://source.coop/ftw/benchmark-data/lv/lv_2024) | 13,056 | 13,056 stored | 13,056 |
| [Latvia — 2025](https://source.coop/ftw/benchmark-data/lv/lv_2025) | 13,061 | 13,061 stored | 13,061 |
| [Netherlands (Crops) — 2017](https://source.coop/ftw/benchmark-data/nl/nl_2017) | 7,600 | 7,594 stored | 7,587 |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl/nl_2018) | 7,594 | 7,588 stored | 7,569 |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl/nl_2019) | 7,582 | 7,576 stored | 7,582 |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl/nl_2020) | 7,592 | 7,586 stored | 7,592 |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl/nl_2021) | 7,596 | 7,590 stored | 7,596 |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl/nl_2022) | 7,590 | 7,584 stored | 7,590 |
| [Netherlands (Crops) — 2023](https://source.coop/ftw/benchmark-data/nl/nl_2023) | 7,610 | 7,604 stored | 7,610 |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl/nl_2024) | 7,584 | 7,578 stored | 7,584 |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl/nl_2025) | 7,574 | 7,568 stored | 7,574 |
| [Portugal — 2017](https://source.coop/ftw/benchmark-data/pt/pt_2017) | 20,027 | 20,027 stored | 20,027 |
| [Portugal — 2018](https://source.coop/ftw/benchmark-data/pt/pt_2018) | 20,085 | 20,085 stored | 20,085 |
| [Portugal — 2019](https://source.coop/ftw/benchmark-data/pt/pt_2019) | 20,328 | 20,328 stored | 20,328 |
| [Portugal — 2020](https://source.coop/ftw/benchmark-data/pt/pt_2020) | 20,030 | 20,030 stored | 20,030 |
| [Portugal — 2021](https://source.coop/ftw/benchmark-data/pt/pt_2021) | 20,329 | 20,329 stored | 20,329 |
| [Portugal — 2022](https://source.coop/ftw/benchmark-data/pt/pt_2022) | 20,361 | 20,361 stored | 20,361 |
| [Portugal — 2023](https://source.coop/ftw/benchmark-data/pt/pt_2023) | 20,002 | 20,002 stored | 20,002 |
| [Portugal — 2025](https://source.coop/ftw/benchmark-data/pt/pt_2025) | 20,298 | 20,298 stored | 20,298 |
| [Rwanda with splits — 2021](https://source.coop/ftw/benchmark-data/rw_rwanda_ml/rw_rwanda_ml_2021) | 73 | 73 stored | none |
| [Sweden — 2017](https://source.coop/ftw/benchmark-data/se/se_2017) | 32,935 | 32,935 stored | 32,935 |
| [Sweden — 2018](https://source.coop/ftw/benchmark-data/se/se_2018) | 32,623 | 32,623 stored | 32,623 |
| [Sweden — 2019](https://source.coop/ftw/benchmark-data/se/se_2019) | 32,880 | 32,880 stored | 32,880 |
| [Sweden — 2020](https://source.coop/ftw/benchmark-data/se/se_2020) | 32,771 | 32,771 stored | 32,771 |
| [Sweden — 2021](https://source.coop/ftw/benchmark-data/se/se_2021) | 32,822 | 32,822 stored | 32,822 |
| [Sweden — 2022](https://source.coop/ftw/benchmark-data/se/se_2022) | 32,742 | 32,742 stored | 32,742 |
| [Sweden — 2023](https://source.coop/ftw/benchmark-data/se/se_2023) | 32,640 | 32,640 stored | 32,640 |
| [Sweden — 2024](https://source.coop/ftw/benchmark-data/se/se_2024) | 32,410 | 32,410 stored | 32,410 |
| [Sweden — 2025](https://source.coop/ftw/benchmark-data/se/se_2025) | 32,552 | 32,552 stored | 32,552 |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si/si_2019) | 4,300 | 4,300 stored | 4,300 |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si/si_2020) | 4,282 | 4,282 stored | 4,282 |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si/si_2021) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si/si_2022) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2023](https://source.coop/ftw/benchmark-data/si/si_2023) | 4,287 | 4,287 stored | 4,287 |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si/si_2024) | 4,291 | 4,291 stored | 4,291 |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk/sk_2018) | 9,806 | 9,785 stored | 9,806 |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk/sk_2019) | 9,856 | 9,835 stored | 9,856 |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk/sk_2020) | 9,885 | 9,864 stored | 9,885 |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk/sk_2021) | 9,875 | 9,854 stored | 9,875 |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk/sk_2022) | 9,866 | 9,845 stored | 9,866 |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk/sk_2023) | 9,571 | 9,552 stored | 9,571 |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk/sk_2024) | 9,986 | 9,965 stored | 9,986 |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk/sk_2025) | 9,985 | 9,964 stored | 9,985 |
| [Trazo with splits — 2020](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2020) | 3,687 | 3,686 stored | none |
| [Trazo with splits — 2021](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2021) | 498 | 498 stored | none |
| [Trazo with splits — 2022](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2022) | 590 | 590 stored | none |
| [Trazo with splits — 2023](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2023) | 499 | 499 stored | none |
| [Trazo with splits — 2024](https://source.coop/ftw/benchmark-data/wri_trazo_ml/wri_trazo_ml_2024) | 1,360 | 1,358 stored | none |
| [South Africa (Fusion) with splits — 2017](https://source.coop/ftw/benchmark-data/za_fusion_ml/za_fusion_ml_2017) | 239 | — | — |

`stored` means four-band GeoTIFFs (red, green, blue, NIR at 10 m) clipped to the chip's mask footprint and published with it: the Q1-Q4 Sentinel-2 quarterly cloudless mosaics of the collection's year (and planting/harvest scenes, where a collection has them). `linked` means the chip's imagery items point at whole Sentinel-2 scenes on the source STAC API, for a reader to window. A chip with no imagery still carries its masks (and its row in the root chips table) — pair it with imagery of your own, on the footprint in `items.parquet`.
<!-- collections:end -->

## Quick start

Everything here runs against the published files over HTTPS: no download, no
credentials, no catalog walk.

Each collection publishes `items.parquet`, a
[stac-geoparquet](https://github.com/stac-utils/stac-geoparquet) mirror of every
STAC item it holds, carrying a public URL for every asset. Joined with the root
chips table, which holds the splits, one query is enough to build a training
list — chip id, split, and the URLs of the rasters themselves:

```sql
INSTALL httpfs; LOAD httpfs;

SELECT i.id,
       c.split_admin2_v1 AS split,
       i."ftw:field_coverage_pct",
       i.assets.semantic_2class_mask.href AS mask,
       i.assets.q3_image.href             AS q3_image
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/ee/ee_2024/items.parquet') i
JOIN read_parquet('https://data.source.coop/ftw/benchmark-data/chips.parquet') c
  ON c.dataset = 'ee_2024' AND i.id = c.id || '_2024'
WHERE c.split_admin2_v1 = 'train'
LIMIT 5;
```

Swap `ee_2024` (and its year) for any collection id in the table above, and
`split_admin2_v1` for any split column (see "Splits across collections" below).
Item ids are the chip id with the collection's year appended; `items.parquet`
also lists each chip's quarterly imagery items, which the join leaves out. `assets` is a struct, so
`DESCRIBE SELECT assets.* FROM read_parquet(...)` lists what a given
collection's chips carry.

To look before you query, open the [data
browser](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/catalog.json).
It renders the collections, their chip footprints and the map styles each one
ships; the Browse column above opens a single collection in it.

## Splits across collections

![Chip locations of every collection, coloured by their admin2 split: train green, validation orange, test purple](https://data.source.coop/ftw/benchmark-data/thumbnail.webp)

Collections carry no split of their own, except the five `wri_trazo_ml` years,
which keep the split their source defines (`ftw:split` on their items, `split` in
their chips file).
[`chips.parquet`](https://data.source.coop/ftw/benchmark-data/chips.parquet) lists
every chip of every collection with one column per split scheme:

- `split_legacy`: the split each collection published before this table existed,
  chosen per collection, so a location in several collections (other years of a
  country, or overlapping regions) can be test in one and train in another. Frozen:
  every rebuild of the table carries it over from the previous one, and chips added
  since have none.
- `split_predefined`: the source's split, for collections whose source defines one.
- `split_hash_v1`: one split per location in every collection, from a stable hash of
  the chip's 3x3 block of grid cells (80 / 10 / 10 overall). Use it to train and test
  across collections without a location on both sides.
- `split_admin2_v1`: whole admin2 areas (`unit_admin2_v1`), balanced to 80 / 10 / 10
  within each country, so every country with three areas or more without presence-only
  chips has all three splits, and no area is on both sides. An area with any chip from a presence-only collection
  is train, since presence-only labels can't be scored; countries whose chips are all
  presence-only (India and most of Africa) are train only.

Each row also has the chip's `dataset`, `group` (its source folder), `id`, `block`
(its 3x3 block of grid cells), `unit_admin2_v1`, its
`admin0_iso3`, `admin0_name`, `admin1_name` and `admin2_name`, and the collection's
`license`, `license_url` and `license_category`
(`public-domain`, `attribution` and `share-alike` allow any use, including commercial;
then `non-commercial`, `restricted`, and `unknown` where the terms aren't clear yet),
and `presence_only`.

Read one collection's rows with
`SELECT * FROM 'https://data.source.coop/ftw/benchmark-data/chips.parquet' WHERE dataset = 'at_2024'`,
or the openly licensed chips with
`... WHERE license_category IN ('public-domain', 'attribution', 'share-alike')`.

[`chips.pmtiles`](https://data.source.coop/ftw/benchmark-data/chips.pmtiles) maps one
polygon per location from zoom 7, with its `split_admin2_v1`, `split_hash_v1`, whether
any of its collections is presence-only, and whether its collections'
`split_legacy` values disagree there (`legacy_conflict`). Below zoom 7 its
`overview_train`, `overview_val` and `overview_test` layers cluster each split's chip centres separately, each cluster counting
its locations. [Open it in a map viewer](https://pmtiles.io/#url=https://data.source.coop/ftw/benchmark-data/chips.pmtiles),
or use the [MapLibre style](https://data.source.coop/ftw/benchmark-data/chips.style.json)
the image above is rendered from: train green, validation orange, test purple. From zoom
7, chips are filled by `split_admin2_v1`, paler where a collection is presence-only, and
outlined in red where their `split_legacy` values disagree.

## What a chip carries

Every chip is a STAC item on the FTW grid, so a cell id is the same square of
ground in every collection. Masks are 2.5 m (800×800 for a 2 km chip), with
boundary lines one to two pixels (2.5–5 m) wide, so you can dilate them to taste;
imagery is 10 m on the same footprint. Each chip carries:

- **Instance masks** — one integer label per field polygon, for instance
  segmentation.
- **Semantic masks** — 2-class (field / not field) and 3-class (interior /
  boundary / not field), the two semantic label forms the FTW paper benchmarks.
- **DECODE masks** — a boundary mask and a normalized distance-to-boundary map,
  after [Waldner et al. (2021)](https://doi.org/10.3390/rs13112197). A distance
  surface lets a watershed separate touching fields that a binary extent mask
  merges into one. New in 2.0.
- **Field outlines** — `<item_id>_fields.parquet` (asset `field_boundaries`): the
  fields cut to the chip, in the masks' CRS, with every column of the fields file.
- **Administrative names** — `ftw:admin0_iso3`, `ftw:admin0_name`,
  `ftw:admin1_name` and `ftw:admin2_name`: the country and the first- and
  second-level units containing the chip's centre (or, when its centre is in
  none, overlapping it most), from
  [FAO GAUL 2024](https://source.coop/nlebovits/gaul-l2-admin). Empty where GAUL has
  no name for the unit or no unit there, as on some coasts and islands.
- **Field coverage**, the share of the chip's area that is mapped field, and —
  where the harmonized source carries
  [EuroCrops HCAT](https://github.com/maja601/EuroCrops) codes — the crop
  composition of the fields inside it.
- **Sentinel-2 imagery**: the four quarterly cloudless mosaics (Q1-Q4) of the
  collection's own year, assets `q1_image` to `q4_image`, each a four-band
  GeoTIFF (red, green, blue, NIR; 10 m) clipped to the chip's mask footprint and
  published as a child item alongside the chip. Every chip has all four. Pixels a
  quarter's mosaic has no data for are nodata (-32768), and the chip records each
  quarter's share of them in `ftw:q1_nodata_pct` to `ftw:q4_nodata_pct`.

## What a collection carries

Alongside the chip items, each collection publishes the tables the chips were
cut from and a mirror of the items themselves:

- `<id>_fields.parquet`, the field polygons used, and
  `<id>_boundary_lines.parquet`, their boundaries as lines.
- `<id>_chips.parquet`: every chip with its footprint, field coverage, admin
  names and, where the source carries HCAT codes, its dominant crop. It has no
  split, except in the `wri_trazo_ml` years; the splits are in the root
  `chips.parquet`.
- `<id>_field_embeddings.parquet`: one row per field of `<id>_fields.parquet`,
  keyed by `id`. For each product it holds the mean (`<product>_mean`) and
  standard deviation (`<product>_std`) of every embedding dimension over the
  field's 10 m pixels, as 64-value float lists, and the pixels used
  (`<product>_pixels`); `pixels` and `pixel_rule` say which pixels the field took
  (centre inside it, or every pixel it touches for a field too small to hold
  one). The products are
  [AlphaEarth Foundations](https://source.coop/tge-labs/aef) (`aef_mean`,
  `aef_std`, `aef_pixels`; CC-BY-4.0) and
  [OlmoEarth v1.3](https://source.coop/olmoearth/olmoearth-v1-3-embeddings)
  (`olmoearth_mean`, `olmoearth_std`, `olmoearth_pixels`; its first 64 of 128
  dimensions, under the
  [OlmoEarth Artifact License](https://data.source.coop/olmoearth/olmoearth-v1-3-embeddings/LICENSE.txt),
  whose use restrictions apply to anything derived from those columns).
- `items.parquet`: the stac-geoparquet mirror the quick start queries.
- `chips.pmtiles` and `fields.pmtiles`, with ready-made map styles under
  `styles/`, for looking at a collection before training on it.
- `README.md`, `AGENTS.md`, `llms.txt` and a thumbnail. A collection's README
  carries the numbers measured for that collection — the field-coverage
  distribution, crop shares and imagery; its agent guide
  documents every column and ships worked queries with their results.

## Limitations

Worth reading before publishing a number from this benchmark.

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
- **Respect the splits.** `split_hash_v1` and `split_admin2_v1` are spatially
  blocked and give a location the same split in every collection. Resampling
  chips at random, or pooling collections under `split_legacy`, leaks information
  between train and test.
- **Imagery can have gaps.** Where every scene of a quarter was cloudy, its
  mosaic has no data; those pixels are kept as nodata (-32768) rather than the
  chip being dropped. Filter on `ftw:q1_nodata_pct` to `ftw:q4_nodata_pct` when
  that matters. The imagery is always from the collection's own year, never a
  neighbouring one.

## Compared with Fields of the World 1.0

Version 1.0 remains published, unchanged, at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world):
24 countries, some 70,000 chips and 1.6 million field polygons, one zipped
folder per country. Version 2 is a rebuild rather than a re-release. It cuts
every collection from the harmonized field boundary catalog instead of a
one-off per-country conversion, so a collection can be regenerated when its
source publishes a new edition; it adds the DECODE boundary and distance masks,
per-chip field outlines, per-field embeddings and splits that hold across
collections; and it publishes the chips as STAC with a queryable item mirror
rather than folders of files.

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
