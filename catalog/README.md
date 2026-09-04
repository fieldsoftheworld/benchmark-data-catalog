# Fields of the World Benchmark Data

Training and evaluation chips for field boundary delineation models. Each
collection is one country or region: Sentinel-2 imagery for two seasons paired
with instance and semantic label masks on a fixed grid, with train, validation
and test splits assigned per chip.

The chips are cut from the [harmonized field boundary
catalog](https://source.coop/ftw/harmonized-field-data) with
[ftw-dataset-tools](https://github.com/fieldsoftheworld/ftw-dataset-tools). The
recipe for every collection is a config file in the [source
repository](https://github.com/fieldsoftheworld/benchmark-data-catalog), so
each one can be rebuilt.

This is version 2.0 of the benchmark described in [Fields of The World
(2024)](https://arxiv.org/abs/2409.16252). Version 1.0 remains at
[kerner-lab/fields-of-the-world](https://source.coop/kerner-lab/fields-of-the-world).

## Collections

No collections are published yet. The first three (Austria, Slovenia,
Luxembourg) are a reviewer sample and will appear here when built.

## License

Each collection carries the license of its source field boundary data; see the
collection page. The masks and imagery chips derived from them are published
under the same terms as the source. Sentinel-2 data is Copernicus, free and open.

## Contact

Open an [issue](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues).
