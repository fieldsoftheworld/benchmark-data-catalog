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
**90 collections · 836,807 chips · 137,489,839 field polygons**

| Thumbnail | Collection | Chips | Splits (train/val/test) | Imagery | License | Source | Browse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <img src="https://data.source.coop/ftw/benchmark-data/at_2018/thumbnail.webp" alt="Austria — 2018" width="120"> | [Austria — 2018](https://source.coop/ftw/benchmark-data/at_2018) | 14,493 | 11,621/1,433/1,439 | 14,493 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at_2019/thumbnail.webp" alt="Austria — 2019" width="120"> | [Austria — 2019](https://source.coop/ftw/benchmark-data/at_2019) | 14,491 | 11,659/1,389/1,443 | 14,491 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at_2020/thumbnail.webp" alt="Austria — 2020" width="120"> | [Austria — 2020](https://source.coop/ftw/benchmark-data/at_2020) | 14,496 | 11,730/1,401/1,365 | 14,496 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at_2021/thumbnail.webp" alt="Austria — 2021" width="120"> | [Austria — 2021](https://source.coop/ftw/benchmark-data/at_2021) | 14,506 | 11,639/1,420/1,447 | 14,506 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/at_2022/thumbnail.webp" alt="Austria — 2022" width="120"> | [Austria — 2022](https://source.coop/ftw/benchmark-data/at_2022) | 14,473 | 11,654/1,422/1,397 | 14,473 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/at](https://source.coop/ftw/harmonized-field-data/at) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/at_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2018/thumbnail.webp" alt="Belgium, Flanders — 2018" width="120"> | [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg_2018) | 2,939 | 2,366/303/270 | 2,939 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2019/thumbnail.webp" alt="Belgium, Flanders — 2019" width="120"> | [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg_2019) | 2,945 | 2,373/314/258 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2020/thumbnail.webp" alt="Belgium, Flanders — 2020" width="120"> | [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg_2020) | 2,941 | 2,370/313/258 | 2,941 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2021/thumbnail.webp" alt="Belgium, Flanders — 2021" width="120"> | [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg_2021) | 2,943 | 2,372/314/257 | 2,943 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2022/thumbnail.webp" alt="Belgium, Flanders — 2022" width="120"> | [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg_2022) | 2,946 | 2,371/319/256 | 2,946 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2023/thumbnail.webp" alt="Belgium, Flanders — 2023" width="120"> | [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg_2023) | 2,948 | 2,370/321/257 | 2,948 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2024/thumbnail.webp" alt="Belgium, Flanders — 2024" width="120"> | [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg_2024) | 2,949 | 2,372/321/256 | 2,949 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_vlg_2025/thumbnail.webp" alt="Belgium, Flanders — 2025" width="120"> | [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg_2025) | 2,945 | 2,370/320/255 | 2,945 stored | [License](https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0) | [harmonized/be_vlg](https://source.coop/ftw/harmonized-field-data/be_vlg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_vlg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/be_wal_2022/thumbnail.webp" alt="Belgium, Wallonia — 2022" width="120"> | [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,607 | 2,871/364/372 | 3,602 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/be_wal](https://source.coop/ftw/harmonized-field-data/be_wal) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/be_wal_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg_2021/thumbnail.webp" alt="Bulgaria — 2021" width="120"> | [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg_2021) | 18,076 | 14,434/1,848/1,794 | 18,055 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg_2022/thumbnail.webp" alt="Bulgaria — 2022" width="120"> | [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg_2022) | 18,123 | 14,505/1,835/1,783 | 18,102 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg_2023/thumbnail.webp" alt="Bulgaria — 2023" width="120"> | [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg_2023) | 17,846 | 14,283/1,753/1,810 | 17,825 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg_2024/thumbnail.webp" alt="Bulgaria — 2024" width="120"> | [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg_2024) | 18,225 | 14,490/1,876/1,859 | 18,204 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/bg_2025/thumbnail.webp" alt="Bulgaria — 2025" width="120"> | [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg_2025) | 18,292 | 14,642/1,833/1,817 | 18,271 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/bg](https://source.coop/ftw/harmonized-field-data/bg) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/bg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ag_2025/thumbnail.webp" alt="Switzerland, Aargau — 2025" width="120"> | [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch_ag_2025) | 346 | 267/38/41 | 346 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ag_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ai_2025/thumbnail.webp" alt="Switzerland, Appenzell Innerrhoden — 2025" width="120"> | [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ai_2025) | 14 | 10/0/4 | 14 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ai_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ar_2025/thumbnail.webp" alt="Switzerland, Appenzell Ausserrhoden — 2025" width="120"> | [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ar_2025) | 34 | 24/0/10 | 34 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ar_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_be_2025/thumbnail.webp" alt="Switzerland, Bern — 2025" width="120"> | [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch_be_2025) | 1,061 | 857/89/115 | 1,061 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_be_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_bl_2025/thumbnail.webp" alt="Switzerland, Basel-Landschaft — 2025" width="120"> | [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch_bl_2025) | 142 | 95/13/34 | 142 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_bl_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_fr_2025/thumbnail.webp" alt="Switzerland, Fribourg — 2025" width="120"> | [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch_fr_2025) | 363 | 281/29/53 | 363 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_fr_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ge_2025/thumbnail.webp" alt="Switzerland, Geneva — 2025" width="120"> | [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch_ge_2025) | 44 | 27/8/9 | 44 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ge_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ju_2025/thumbnail.webp" alt="Switzerland, Jura — 2025" width="120"> | [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch_ju_2025) | 179 | 138/7/34 | 179 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ju_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_lu_2025/thumbnail.webp" alt="Switzerland, Luzern — 2025" width="120"> | [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch_lu_2025) | 354 | 272/39/43 | 354 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_lu_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_sg_2025/thumbnail.webp" alt="Switzerland, St. Gallen — 2025" width="120"> | [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch_sg_2025) | 339 | 275/38/26 | 339 stored | [License](https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_sh_2025/thumbnail.webp" alt="Switzerland, Schaffhausen — 2025" width="120"> | [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch_sh_2025) | 44 | 34/1/9 | 44 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sh_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_so_2025/thumbnail.webp" alt="Switzerland, Solothurn — 2025" width="120"> | [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch_so_2025) | 193 | 143/20/30 | 193 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_so_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_sz_2025/thumbnail.webp" alt="Switzerland, Schwyz — 2025" width="120"> | [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch_sz_2025) | 139 | 97/15/27 | 139 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_sz_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_tg_2025/thumbnail.webp" alt="Switzerland, Thurgau — 2025" width="120"> | [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch_tg_2025) | 187 | 143/20/24 | 187 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_tg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_ur_2025/thumbnail.webp" alt="Switzerland, Uri — 2025" width="120"> | [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch_ur_2025) | 15 | 8/0/7 | 15 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_ur_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_vs_2025/thumbnail.webp" alt="Switzerland, Valais — 2025" width="120"> | [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch_vs_2025) | 145 | 113/9/23 | 145 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_vs_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_zg_2025/thumbnail.webp" alt="Switzerland, Zug — 2025" width="120"> | [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 23/0/9 | 32 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_zg_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ch_zh_2025/thumbnail.webp" alt="Switzerland, Zürich — 2025" width="120"> | [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch_zh_2025) | 423 | 336/34/53 | 423 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/ch](https://source.coop/ftw/harmonized-field-data/ch) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ch_zh_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/de_sh_2023/thumbnail.webp" alt="Germany, Schleswig-Holstein — 2023" width="120"> | [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 2,753/346/353 | 3,452 stored | [DL-DE-ZERO-2.0](https://spdx.org/licenses/DL-DE-ZERO-2.0.html) | [harmonized/de_sh](https://source.coop/ftw/harmonized-field-data/de_sh) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/de_sh_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2018/thumbnail.webp" alt="Denmark — 2018" width="120"> | [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 7,636/999/994 | 9,629 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2019/thumbnail.webp" alt="Denmark — 2019" width="120"> | [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 7,641/1,005/978 | 9,624 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2020/thumbnail.webp" alt="Denmark — 2020" width="120"> | [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 7,672/993/989 | 9,654 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2021/thumbnail.webp" alt="Denmark — 2021" width="120"> | [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 7,621/989/1,037 | 9,647 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2022/thumbnail.webp" alt="Denmark — 2022" width="120"> | [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 7,618/988/1,034 | 9,640 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2024/thumbnail.webp" alt="Denmark — 2024" width="120"> | [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk_2024) | 9,672 | 7,724/963/985 | 9,672 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/dk_2025/thumbnail.webp" alt="Denmark — 2025" width="120"> | [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk_2025) | 9,639 | 7,663/982/994 | 9,639 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/dk](https://source.coop/ftw/harmonized-field-data/dk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/dk_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ec_lt_2021/thumbnail.webp" alt="Lithuania - Eurocrops 2021 — 2021" width="120"> | [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt_2021) | 13,468 | 10,786/1,349/1,333 | 13,468 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/ec_lt](https://source.coop/ftw/harmonized-field-data/ec_lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ec_lt_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2017/thumbnail.webp" alt="Estonia — 2017" width="120"> | [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee_2017) | 7,745 | 6,194/776/775 | 7,745 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2018/thumbnail.webp" alt="Estonia — 2018" width="120"> | [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee_2018) | 7,765 | 6,249/734/782 | 7,765 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2019/thumbnail.webp" alt="Estonia — 2019" width="120"> | [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee_2019) | 7,787 | 6,179/749/859 | 7,787 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2020/thumbnail.webp" alt="Estonia — 2020" width="120"> | [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee_2020) | 7,807 | 6,228/765/814 | 7,807 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2021/thumbnail.webp" alt="Estonia — 2021" width="120"> | [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee_2021) | 7,853 | 6,231/800/822 | 7,853 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2022/thumbnail.webp" alt="Estonia — 2022" width="120"> | [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee_2022) | 7,871 | 6,229/804/838 | 7,871 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2023/thumbnail.webp" alt="Estonia — 2023" width="120"> | [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee_2023) | 7,606 | 6,011/764/831 | 7,606 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ee_2024/thumbnail.webp" alt="Estonia — 2024" width="120"> | [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 7,562 | 6,037/733/792 | 7,562 stored | [CC-BY-SA-3.0](https://spdx.org/licenses/CC-BY-SA-3.0.html) | [harmonized/ee](https://source.coop/ftw/harmonized-field-data/ee) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ee_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_ib_2024/thumbnail.webp" alt="Spain Balearic Islands — 2024" width="120"> | [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 661/87/89 | 837 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es_ib](https://source.coop/ftw/harmonized-field-data/es_ib) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_ib_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/es_po_2025/thumbnail.webp" alt="Spain — 2025" width="120"> | [Spain — 2025](https://source.coop/ftw/benchmark-data/es_po_2025) | 29,795 | 23,795/2,995/3,005 | 29,795 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/es](https://source.coop/ftw/harmonized-field-data/es) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/es_po_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2018/thumbnail.webp" alt="Croatia — 2018" width="120"> | [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 7,735/999/970 | 9,704 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2019/thumbnail.webp" alt="Croatia — 2019" width="120"> | [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 7,748/970/1,006 | 9,724 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2020/thumbnail.webp" alt="Croatia — 2020" width="120"> | [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 7,718/1,004/981 | 9,703 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2021/thumbnail.webp" alt="Croatia — 2021" width="120"> | [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 7,816/959/959 | 9,734 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2022/thumbnail.webp" alt="Croatia — 2022" width="120"> | [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 7,781/976/958 | 9,715 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/hr_2024/thumbnail.webp" alt="Croatia — 2024" width="120"> | [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 7,605/973/1,010 | 9,588 stored | [License](https://www.apprrr.hr/prostorni-podaci-servisi/) | [harmonized/hr](https://source.coop/ftw/harmonized-field-data/hr) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/hr_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/ie_2022/thumbnail.webp" alt="Ireland — 2022" width="120"> | [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 13,374/1,653/1,707 | 16,734 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/ie](https://source.coop/ftw/harmonized-field-data/ie) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/ie_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp_2021/thumbnail.webp" alt="Japan — 2021" width="120"> | [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 48,849/6,093/6,074 | 61,000 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp_2022/thumbnail.webp" alt="Japan — 2022" width="120"> | [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 48,799/6,146/6,016 | 60,945 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/jp_2024/thumbnail.webp" alt="Japan — 2024" width="120"> | [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 48,789/6,143/6,011 | 60,927 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/jp](https://source.coop/ftw/harmonized-field-data/jp) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/jp_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lt_2024/thumbnail.webp" alt="Lithuania — 2024" width="120"> | [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 11,297/1,399/1,427 | 14,123 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lt_2025/thumbnail.webp" alt="Lithuania — 2025" width="120"> | [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 11,323/1,388/1,429 | 14,140 stored | [CC-BY-4.0](https://spdx.org/licenses/CC-BY-4.0.html) | [harmonized/lt](https://source.coop/ftw/harmonized-field-data/lt) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lt_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv_2017/thumbnail.webp" alt="Latvia — 2017" width="120"> | [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 10,383/1,308/1,325 | 13,016 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2017/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/lv_2023/thumbnail.webp" alt="Latvia — 2023" width="120"> | [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 10,371/1,310/1,347 | 13,028 stored | [CC-BY-SA-4.0](https://spdx.org/licenses/CC-BY-SA-4.0.html) | [harmonized/lv](https://source.coop/ftw/harmonized-field-data/lv) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/lv_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2018/thumbnail.webp" alt="Netherlands (Crops) — 2018" width="120"> | [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 6,067/796/731 | 7,588 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2019/thumbnail.webp" alt="Netherlands (Crops) — 2019" width="120"> | [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 6,077/741/764 | 7,576 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2020/thumbnail.webp" alt="Netherlands (Crops) — 2020" width="120"> | [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 6,085/745/762 | 7,586 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2021/thumbnail.webp" alt="Netherlands (Crops) — 2021" width="120"> | [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 6,116/722/758 | 7,590 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2022/thumbnail.webp" alt="Netherlands (Crops) — 2022" width="120"> | [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 6,113/719/758 | 7,584 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2024/thumbnail.webp" alt="Netherlands (Crops) — 2024" width="120"> | [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 6,090/735/759 | 7,578 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/nl_2025/thumbnail.webp" alt="Netherlands (Crops) — 2025" width="120"> | [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 6,041/737/796 | 7,568 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/nl](https://source.coop/ftw/harmonized-field-data/nl) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/nl_2025/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si_2019/thumbnail.webp" alt="Slovenia — 2019" width="120"> | [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 3,430/457/413 | 4,300 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si_2020/thumbnail.webp" alt="Slovenia — 2020" width="120"> | [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 3,423/438/421 | 4,282 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si_2021/thumbnail.webp" alt="Slovenia — 2021" width="120"> | [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 3,424/438/424 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si_2022/thumbnail.webp" alt="Slovenia — 2022" width="120"> | [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 3,445/422/419 | 4,286 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/si_2024/thumbnail.webp" alt="Slovenia — 2024" width="120"> | [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si_2024) | 4,291 | 3,431/424/436 | 4,291 stored | [License](https://rkg.gov.si/vstop/) | [harmonized/si](https://source.coop/ftw/harmonized-field-data/si) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/si_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2018/thumbnail.webp" alt="Slovakia — 2018" width="120"> | [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk_2018) | 9,806 | 7,842/962/1,002 | 9,785 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2018/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2019/thumbnail.webp" alt="Slovakia — 2019" width="120"> | [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk_2019) | 9,856 | 7,885/984/987 | 9,835 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2019/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2020/thumbnail.webp" alt="Slovakia — 2020" width="120"> | [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk_2020) | 9,885 | 7,949/969/967 | 9,864 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2020/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2021/thumbnail.webp" alt="Slovakia — 2021" width="120"> | [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk_2021) | 9,875 | 7,904/994/977 | 9,854 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2021/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2022/thumbnail.webp" alt="Slovakia — 2022" width="120"> | [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk_2022) | 9,866 | 7,899/985/982 | 9,845 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2022/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2023/thumbnail.webp" alt="Slovakia — 2023" width="120"> | [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk_2023) | 9,571 | 7,624/946/1,001 | 9,552 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2023/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2024/thumbnail.webp" alt="Slovakia — 2024" width="120"> | [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk_2024) | 9,986 | 7,975/999/1,012 | 9,965 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2024/collection.json) |
| <img src="https://data.source.coop/ftw/benchmark-data/sk_2025/thumbnail.webp" alt="Slovakia — 2025" width="120"> | [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk_2025) | 9,985 | 7,991/975/1,019 | 9,964 stored | [CC0-1.0](https://spdx.org/licenses/CC0-1.0.html) | [harmonized/sk](https://source.coop/ftw/harmonized-field-data/sk) | [browse](https://browser.portolan-sdi.org/#/external/data.source.coop/ftw/benchmark-data/sk_2025/collection.json) |

### What each collection carries

| Collection | Label masks | Sentinel-2 imagery | HCAT crop labels |
| --- | --- | --- | --- |
| [Austria — 2018](https://source.coop/ftw/benchmark-data/at_2018) | 14,493 | 14,493 stored | 14,493 |
| [Austria — 2019](https://source.coop/ftw/benchmark-data/at_2019) | 14,491 | 14,491 stored | 14,491 |
| [Austria — 2020](https://source.coop/ftw/benchmark-data/at_2020) | 14,496 | 14,496 stored | 14,496 |
| [Austria — 2021](https://source.coop/ftw/benchmark-data/at_2021) | 14,506 | 14,506 stored | 14,506 |
| [Austria — 2022](https://source.coop/ftw/benchmark-data/at_2022) | 14,473 | 14,473 stored | 14,473 |
| [Belgium, Flanders — 2018](https://source.coop/ftw/benchmark-data/be_vlg_2018) | 2,939 | 2,939 stored | 2,939 |
| [Belgium, Flanders — 2019](https://source.coop/ftw/benchmark-data/be_vlg_2019) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Flanders — 2020](https://source.coop/ftw/benchmark-data/be_vlg_2020) | 2,941 | 2,941 stored | 2,941 |
| [Belgium, Flanders — 2021](https://source.coop/ftw/benchmark-data/be_vlg_2021) | 2,943 | 2,943 stored | 2,943 |
| [Belgium, Flanders — 2022](https://source.coop/ftw/benchmark-data/be_vlg_2022) | 2,946 | 2,946 stored | 2,946 |
| [Belgium, Flanders — 2023](https://source.coop/ftw/benchmark-data/be_vlg_2023) | 2,948 | 2,948 stored | 2,948 |
| [Belgium, Flanders — 2024](https://source.coop/ftw/benchmark-data/be_vlg_2024) | 2,949 | 2,949 stored | 2,949 |
| [Belgium, Flanders — 2025](https://source.coop/ftw/benchmark-data/be_vlg_2025) | 2,945 | 2,945 stored | 2,945 |
| [Belgium, Wallonia — 2022](https://source.coop/ftw/benchmark-data/be_wal_2022) | 3,607 | 3,602 stored | 3,607 |
| [Bulgaria — 2021](https://source.coop/ftw/benchmark-data/bg_2021) | 18,076 | 18,055 stored | none |
| [Bulgaria — 2022](https://source.coop/ftw/benchmark-data/bg_2022) | 18,123 | 18,102 stored | none |
| [Bulgaria — 2023](https://source.coop/ftw/benchmark-data/bg_2023) | 17,846 | 17,825 stored | none |
| [Bulgaria — 2024](https://source.coop/ftw/benchmark-data/bg_2024) | 18,225 | 18,204 stored | none |
| [Bulgaria — 2025](https://source.coop/ftw/benchmark-data/bg_2025) | 18,292 | 18,271 stored | none |
| [Switzerland, Aargau — 2025](https://source.coop/ftw/benchmark-data/ch_ag_2025) | 346 | 346 stored | 346 |
| [Switzerland, Appenzell Innerrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ai_2025) | 14 | 14 stored | 14 |
| [Switzerland, Appenzell Ausserrhoden — 2025](https://source.coop/ftw/benchmark-data/ch_ar_2025) | 34 | 34 stored | 34 |
| [Switzerland, Bern — 2025](https://source.coop/ftw/benchmark-data/ch_be_2025) | 1,061 | 1,061 stored | 1,061 |
| [Switzerland, Basel-Landschaft — 2025](https://source.coop/ftw/benchmark-data/ch_bl_2025) | 142 | 142 stored | 142 |
| [Switzerland, Fribourg — 2025](https://source.coop/ftw/benchmark-data/ch_fr_2025) | 363 | 363 stored | 363 |
| [Switzerland, Geneva — 2025](https://source.coop/ftw/benchmark-data/ch_ge_2025) | 44 | 44 stored | 44 |
| [Switzerland, Jura — 2025](https://source.coop/ftw/benchmark-data/ch_ju_2025) | 179 | 179 stored | 179 |
| [Switzerland, Luzern — 2025](https://source.coop/ftw/benchmark-data/ch_lu_2025) | 354 | 354 stored | 354 |
| [Switzerland, St. Gallen — 2025](https://source.coop/ftw/benchmark-data/ch_sg_2025) | 339 | 339 stored | 339 |
| [Switzerland, Schaffhausen — 2025](https://source.coop/ftw/benchmark-data/ch_sh_2025) | 44 | 44 stored | 44 |
| [Switzerland, Solothurn — 2025](https://source.coop/ftw/benchmark-data/ch_so_2025) | 193 | 193 stored | 193 |
| [Switzerland, Schwyz — 2025](https://source.coop/ftw/benchmark-data/ch_sz_2025) | 139 | 139 stored | 139 |
| [Switzerland, Thurgau — 2025](https://source.coop/ftw/benchmark-data/ch_tg_2025) | 187 | 187 stored | 187 |
| [Switzerland, Uri — 2025](https://source.coop/ftw/benchmark-data/ch_ur_2025) | 15 | 15 stored | 15 |
| [Switzerland, Valais — 2025](https://source.coop/ftw/benchmark-data/ch_vs_2025) | 145 | 145 stored | 145 |
| [Switzerland, Zug — 2025](https://source.coop/ftw/benchmark-data/ch_zg_2025) | 32 | 32 stored | 32 |
| [Switzerland, Zürich — 2025](https://source.coop/ftw/benchmark-data/ch_zh_2025) | 423 | 423 stored | 423 |
| [Germany, Schleswig-Holstein — 2023](https://source.coop/ftw/benchmark-data/de_sh_2023) | 3,452 | 3,452 stored | none |
| [Denmark — 2018](https://source.coop/ftw/benchmark-data/dk_2018) | 9,629 | 9,629 stored | 9,629 |
| [Denmark — 2019](https://source.coop/ftw/benchmark-data/dk_2019) | 9,624 | 9,624 stored | 9,624 |
| [Denmark — 2020](https://source.coop/ftw/benchmark-data/dk_2020) | 9,654 | 9,654 stored | 9,654 |
| [Denmark — 2021](https://source.coop/ftw/benchmark-data/dk_2021) | 9,647 | 9,647 stored | 9,647 |
| [Denmark — 2022](https://source.coop/ftw/benchmark-data/dk_2022) | 9,640 | 9,640 stored | 9,640 |
| [Denmark — 2024](https://source.coop/ftw/benchmark-data/dk_2024) | 9,672 | 9,672 stored | 9,672 |
| [Denmark — 2025](https://source.coop/ftw/benchmark-data/dk_2025) | 9,639 | 9,639 stored | 9,639 |
| [Lithuania - Eurocrops 2021 — 2021](https://source.coop/ftw/benchmark-data/ec_lt_2021) | 13,468 | 13,468 stored | 13,468 |
| [Estonia — 2017](https://source.coop/ftw/benchmark-data/ee_2017) | 7,745 | 7,745 stored | 7,745 |
| [Estonia — 2018](https://source.coop/ftw/benchmark-data/ee_2018) | 7,765 | 7,765 stored | 7,765 |
| [Estonia — 2019](https://source.coop/ftw/benchmark-data/ee_2019) | 7,787 | 7,787 stored | 7,787 |
| [Estonia — 2020](https://source.coop/ftw/benchmark-data/ee_2020) | 7,807 | 7,807 stored | 7,807 |
| [Estonia — 2021](https://source.coop/ftw/benchmark-data/ee_2021) | 7,853 | 7,853 stored | 7,853 |
| [Estonia — 2022](https://source.coop/ftw/benchmark-data/ee_2022) | 7,871 | 7,871 stored | 7,871 |
| [Estonia — 2023](https://source.coop/ftw/benchmark-data/ee_2023) | 7,606 | 7,606 stored | 7,606 |
| [Estonia — 2024](https://source.coop/ftw/benchmark-data/ee_2024) | 7,562 | 7,562 stored | 7,562 |
| [Spain Balearic Islands — 2024](https://source.coop/ftw/benchmark-data/es_ib_2024) | 837 | 837 stored | none |
| [Spain — 2025](https://source.coop/ftw/benchmark-data/es_po_2025) | 29,795 | 29,795 stored | 29,795 |
| [Croatia — 2018](https://source.coop/ftw/benchmark-data/hr_2018) | 9,704 | 9,704 stored | 9,704 |
| [Croatia — 2019](https://source.coop/ftw/benchmark-data/hr_2019) | 9,724 | 9,724 stored | 9,724 |
| [Croatia — 2020](https://source.coop/ftw/benchmark-data/hr_2020) | 9,703 | 9,703 stored | 9,703 |
| [Croatia — 2021](https://source.coop/ftw/benchmark-data/hr_2021) | 9,734 | 9,734 stored | 9,734 |
| [Croatia — 2022](https://source.coop/ftw/benchmark-data/hr_2022) | 9,715 | 9,715 stored | 9,715 |
| [Croatia — 2024](https://source.coop/ftw/benchmark-data/hr_2024) | 9,588 | 9,588 stored | 9,588 |
| [Ireland — 2022](https://source.coop/ftw/benchmark-data/ie_2022) | 16,734 | 16,734 stored | 16,734 |
| [Japan — 2021](https://source.coop/ftw/benchmark-data/jp_2021) | 61,016 | 61,000 stored | none |
| [Japan — 2022](https://source.coop/ftw/benchmark-data/jp_2022) | 60,961 | 60,945 stored | none |
| [Japan — 2024](https://source.coop/ftw/benchmark-data/jp_2024) | 60,943 | 60,927 stored | none |
| [Lithuania — 2024](https://source.coop/ftw/benchmark-data/lt_2024) | 14,123 | 14,123 stored | 14,123 |
| [Lithuania — 2025](https://source.coop/ftw/benchmark-data/lt_2025) | 14,140 | 14,140 stored | 14,140 |
| [Latvia — 2017](https://source.coop/ftw/benchmark-data/lv_2017) | 13,016 | 13,016 stored | 13,016 |
| [Latvia — 2023](https://source.coop/ftw/benchmark-data/lv_2023) | 13,028 | 13,028 stored | 13,028 |
| [Netherlands (Crops) — 2018](https://source.coop/ftw/benchmark-data/nl_2018) | 7,594 | 7,588 stored | 7,569 |
| [Netherlands (Crops) — 2019](https://source.coop/ftw/benchmark-data/nl_2019) | 7,582 | 7,576 stored | 7,582 |
| [Netherlands (Crops) — 2020](https://source.coop/ftw/benchmark-data/nl_2020) | 7,592 | 7,586 stored | 7,592 |
| [Netherlands (Crops) — 2021](https://source.coop/ftw/benchmark-data/nl_2021) | 7,596 | 7,590 stored | 7,596 |
| [Netherlands (Crops) — 2022](https://source.coop/ftw/benchmark-data/nl_2022) | 7,590 | 7,584 stored | 7,590 |
| [Netherlands (Crops) — 2024](https://source.coop/ftw/benchmark-data/nl_2024) | 7,584 | 7,578 stored | 7,584 |
| [Netherlands (Crops) — 2025](https://source.coop/ftw/benchmark-data/nl_2025) | 7,574 | 7,568 stored | 7,574 |
| [Slovenia — 2019](https://source.coop/ftw/benchmark-data/si_2019) | 4,300 | 4,300 stored | 4,300 |
| [Slovenia — 2020](https://source.coop/ftw/benchmark-data/si_2020) | 4,282 | 4,282 stored | 4,282 |
| [Slovenia — 2021](https://source.coop/ftw/benchmark-data/si_2021) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2022](https://source.coop/ftw/benchmark-data/si_2022) | 4,286 | 4,286 stored | 4,286 |
| [Slovenia — 2024](https://source.coop/ftw/benchmark-data/si_2024) | 4,291 | 4,291 stored | 4,291 |
| [Slovakia — 2018](https://source.coop/ftw/benchmark-data/sk_2018) | 9,806 | 9,785 stored | 9,806 |
| [Slovakia — 2019](https://source.coop/ftw/benchmark-data/sk_2019) | 9,856 | 9,835 stored | 9,856 |
| [Slovakia — 2020](https://source.coop/ftw/benchmark-data/sk_2020) | 9,885 | 9,864 stored | 9,885 |
| [Slovakia — 2021](https://source.coop/ftw/benchmark-data/sk_2021) | 9,875 | 9,854 stored | 9,875 |
| [Slovakia — 2022](https://source.coop/ftw/benchmark-data/sk_2022) | 9,866 | 9,845 stored | 9,866 |
| [Slovakia — 2023](https://source.coop/ftw/benchmark-data/sk_2023) | 9,571 | 9,552 stored | 9,571 |
| [Slovakia — 2024](https://source.coop/ftw/benchmark-data/sk_2024) | 9,986 | 9,965 stored | 9,986 |
| [Slovakia — 2025](https://source.coop/ftw/benchmark-data/sk_2025) | 9,985 | 9,964 stored | 9,985 |

`stored` means four-band GeoTIFFs (red, green, blue, NIR at 10 m) clipped to the chip's mask grid and published with it: the Q1-Q4 Sentinel-2 quarterly cloudless mosaics of the collection's year (and planting/harvest scenes, where a collection has them). `linked` means the chip's imagery items point at whole Sentinel-2 scenes on the source STAC API, for a reader to window. A chip with no imagery still carries its masks and its split — pair it with imagery of your own, on the footprint in `items.parquet`.
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
       assets.q3_image.href             AS q3_image
FROM read_parquet('https://data.source.coop/ftw/benchmark-data/ee_2024/items.parquet')
WHERE "ftw:split" = 'train'
LIMIT 5;
```

Swap `ee_2024` for any collection id in the table above. `assets` is a struct,
so `DESCRIBE SELECT assets.* FROM read_parquet(...)` lists what a given
collection's chips actually carry: where imagery is `linked` rather than
`stored`, its asset is the whole scene, to window yourself.

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
- **Sentinel-2 imagery**, in the collections that have it: the four quarterly
  cloudless mosaics (Q1-Q4) of the collection's own year, each a four-band
  GeoTIFF (red, green, blue, NIR; 10 m) clipped to the chip's mask grid and
  published as a child item alongside the chip. Which collections carry
  imagery, and in what shape, is in the coverage table above.

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
- **Imagery can have gaps.** Where every scene of a quarter was cloudy, its
  mosaic has no data; those pixels are kept as nodata (-32768) rather than the
  chip being dropped, so expect a few missing pixels, most often in Q2. The
  imagery is always from the collection's own year, never a neighbouring one.

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
