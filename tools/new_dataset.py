#!/usr/bin/env python3
"""Scaffold a region-year dataset: recipe, class filter and manifest entry.

    uv run python tools/new_dataset.py be_wal_2022
    uv run python tools/new_dataset.py be_wal_2022 --ftwd-checkout ../ftw-dataset-tools

Reads the dataset's row in ``tracking.csv`` and the harmonized source over
HTTPS, then writes:

- ``datasets/<id>.yaml``: the ftwd recipe. ``fields_file`` is the year's own
  parquet (``<hid>/year=<Y>/<hid>-<Y>.parquet``), never ``latest``. The title
  is the harmonized year item's link title; license and producer/licensor
  providers are copied from the harmonized year item where it states them (one
  canton of a multi-source collection), else from the collection, which is the attested
  source. Fields of the World is appended as processor.
- ``datasets/filters/<filter>``: a byte-for-byte copy of ftwd's
  ``configs/filters/<filter>`` at the pinned commit (or from a local checkout
  with ``--ftwd-checkout``). ``tests/test_filters.py`` fails if they drift.
- a ``datasets.yaml`` entry with ``ftw1_name: none`` and the default
  thumbnail framing (``thumbnail_spec``).

Refuses to overwrite an existing recipe unless ``--force``; the manifest entry
is only appended when missing.

Two exceptions, both explicit:

- A dataset in ``DERIVED`` reads ``work/<id>.parquet``, which the named script
  builds from harmonized sources (run it before building). ``source_via`` still
  names the harmonized collection of the row. Its row must name the entry's
  filter, and the providers and attribution of every collection it draws on are
  credited. When their licenses differ the recipe says ``other`` with
  ``license_url: TODO(attest)``, which the manifest gate refuses until someone
  attests the combined terms.
- A row whose ``wall_to_wall`` is ``Presence-only`` gets ``presence_only: true``:
  semantic masks mark unlabelled pixels unknown (3) instead of background, and only
  the semantic masks are built: instance and DECODE masks have no unknown value, so
  they would label unlabelled fields as not-field.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tracking  # noqa: E402
from common import ROOT, STAGING, ftwd_pin, load_manifest  # noqa: E402

HARMONIZED = "https://data.source.coop/ftw/harmonized-field-data"
FTWD_RAW = "https://raw.githubusercontent.com/fieldsoftheworld/ftw-dataset-tools"
FTW_PROVIDER = {
    "name": "Fields of the World",
    "roles": ["processor"],
    "url": "https://fieldsofthe.world",
}
# The framing every new collection starts from. Override per dataset in
# datasets.yaml only after looking at the rendered thumbnail.
DEFAULT_THUMBNAIL = {"style": "outline", "zoom": 13, "rank": 0}
# Datasets whose input is built by a script from harmonized sources, not read as is.
DERIVED = {
    "es_2025": {"script": "tools/merge_es_2025.py", "filter": "es_merged_filter.yaml",
                "sources": ("es", "es_pv")},
    "es_po_2025": {"script": "tools/merge_es_2025.py", "filter": "es_merged_filter.yaml",
                   "sources": ("es",)},
}
PRESENCE_ONLY = "Presence-only"
MASK_TYPES = ["instance", "semantic_2_class", "semantic_3_class", "decode_boundary", "decode_distance"]
# Only these can mark a pixel unknown; the others would call unlabelled fields not-field.
PRESENCE_ONLY_MASK_TYPES = ["semantic_2_class", "semantic_3_class"]


def mask_types(presence_only: bool) -> str:
    """The recipe's ``mask_types`` list, as YAML flow text."""
    return "[" + ", ".join(PRESENCE_ONLY_MASK_TYPES if presence_only else MASK_TYPES) + "]"


def fields_file(dataset_id: str, urls: dict[str, str]) -> str:
    """The recipe's input: the derived file for ``DERIVED`` datasets, else the year parquet."""
    return f"work/{dataset_id}.parquet" if dataset_id in DERIVED else urls["parquet"]


def combined_collection(collections: list[dict]) -> dict:
    """One collection's worth of credits for a dataset drawn from several.

    Providers are listed once each in source order; attributions are joined. The
    first collection's links (item titles) are kept; its license link only when
    every source shares the license, else the license is ``other`` and unattested.
    """
    first = collections[0]
    seen, provs = set(), []
    for c in collections:
        for p in c.get("providers", []):
            if p.get("name") not in seen:
                seen.add(p.get("name"))
                provs.append(p)
    licenses = {c.get("license") for c in collections}
    links = [link for link in first.get("links", []) if link.get("rel") != "license"]
    same = len(licenses) == 1
    if same:
        links += [link for link in first.get("links", []) if link.get("rel") == "license"]
    attributions = [attribution(c) for c in collections]
    return {
        **first,
        "license": first.get("license") if same else "other",
        "providers": provs,
        "attribution": "; ".join(dict.fromkeys(attributions)),
        "links": links,
    }


def _open(url: str):
    # data.source.coop answers 403 to urllib's default Python-urllib User-Agent.
    request = urllib.request.Request(url, headers={"User-Agent": "benchmark-data-catalog"})
    return urllib.request.urlopen(request, timeout=30)


def fetch_json(url: str) -> dict:
    with _open(url) as resp:
        return json.load(resp)


def source_urls(row: dict[str, str]) -> dict[str, str]:
    """The harmonized collection, year item and year parquet for one tracking row."""
    year, stem = row["year"], tracking.source_stem(row)
    base = f"{HARMONIZED}/{row['harmonized_id']}"
    return {
        "collection": f"{base}/collection.json",
        "item": f"{base}/year={year}/{stem}-{year}.json",
        "parquet": f"{base}/year={year}/{stem}-{year}.parquet",
    }


def item_terms(collection: dict, item: dict) -> dict:
    """The collection with the year item's own terms, where the item states them.

    A collection fed by several sources (the cantons of ``ch``) is ``other`` with
    every source's license links and providers; each year item carries just its
    source's license, license link, attribution and providers. A dataset cut
    from one item must carry that item's terms, not the whole collection's.
    """
    props = item.get("properties", {})
    if not props.get("license"):
        return collection
    out = {**collection, "license": props["license"]}
    if props.get("providers"):
        out["providers"] = props["providers"]
    if props.get("attribution"):
        out["attribution"] = props["attribution"]
    item_licenses = [link for link in item.get("links", []) if link.get("rel") == "license"]
    out["links"] = [link for link in collection.get("links", []) if link.get("rel") != "license"] + item_licenses
    return out


def item_title(collection: dict, item_url: str, fallback: str) -> str:
    """The harmonized collection's own title for the item at ``item_url``."""
    suffix = "/".join(item_url.split("/")[-2:])  # year=<Y>/<stem>-<Y>.json
    for link in collection.get("links", []):
        if link.get("rel") == "item" and link.get("href", "").endswith(suffix) and link.get("title"):
            return link["title"]
    return fallback


def providers(collection: dict) -> list[dict]:
    """The source's providers minus its own FTW entry, then FTW as processor."""
    kept = [
        {k: p[k] for k in ("name", "roles", "url") if k in p}
        for p in collection.get("providers", [])
        if p.get("name") != FTW_PROVIDER["name"]
    ]
    return [*kept, FTW_PROVIDER]


def attribution(collection: dict) -> str:
    """The source's attribution, else its producer's name."""
    if collection.get("attribution"):
        return collection["attribution"]
    for p in collection.get("providers", []):
        if "producer" in p.get("roles", []) and p.get("name") != FTW_PROVIDER["name"]:
            return p["name"]
    return "TODO(attest)"


def license_lines(collection: dict) -> str:
    """``license`` (and ``license_url`` for a non-SPDX license) recipe lines.

    The source's ``rel: license`` link is the attested terms; ftwd and the
    manifest gate require it whenever the license is ``other``.
    """
    license_ = collection.get("license") or "TODO(attest)"
    lines = f"  license: {license_}\n"
    if license_ == "other":
        hrefs = [link["href"] for link in collection.get("links", []) if link.get("rel") == "license"]
        lines += f"  license_url: {hrefs[0] if hrefs else 'TODO(attest)'}\n"
    return lines


def thumbnail_spec() -> dict:
    """The default thumbnail framing for a new collection.

    The field outlines at zoom 13 (about 5 km across) on the densest cluster of
    fields: every dataset has them, crop codes or not, and they show the field
    geometry the benchmark is about. The chip-level styles read as coloured
    squares at that size, and ``dominant-crop`` goes flat where one class
    dominates (hr_2024's generic "Arable land").
    """
    return dict(DEFAULT_THUMBNAIL)


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _providers_yaml(items: list[dict]) -> str:
    lines = []
    for p in items:
        lines.append(f"    - name: {_yaml_str(p['name'])}")
        lines.append(f"      roles: [{', '.join(p.get('roles', []))}]")
        if p.get("url"):
            lines.append(f"      url: {p['url']}")
    return "\n".join(lines)


# The imagery modes this release publishes. ``tracking.csv``'s ``imagery`` column
# says what exists for a year; a recipe selects only what exists *and* is released.
# Scenes are left out of this release (the maintainer's call, 2026-11-02): rows
# whose year has no mosaics are ``blocked`` rather than built without imagery.
RELEASE_IMAGERY = ("mosaics",)


def release_modes(row: dict[str, str]) -> tuple[str, ...]:
    """The row's imagery modes this release builds; exits when there are none."""
    modes = tuple(m for m in tracking.imagery_modes(row) if m in RELEASE_IMAGERY)
    if not modes:
        sys.exit(
            f"{row['dataset_id']}: imagery {row['imagery']!r} has none of the released "
            f"modes {list(RELEASE_IMAGERY)}; mark the row blocked"
        )
    return modes


def _imagery_yaml(modes: tuple[str, ...]) -> str:
    """The select/download stage blocks for the row's imagery modes."""
    mode = modes[0] if len(modes) == 1 else f"[{', '.join(modes)}]"
    # Mosaics keep their few-pixel cloud gaps (models should cope with missing
    # data); a scene can miss a chip entirely, so scenes stay at zero.
    nodata_max = "0.0" if "scenes" in modes else "100.0"
    return f"""\
  select_images:
    enabled: true
    imagery_mode: {mode}
    cloud_cover_chip: 2.0
    nodata_max: {nodata_max}
    buffer_days: 14
    num_buffer_expansions: 3
    buffer_expansion_size: 14
  download_images:
    enabled: true
    mode: clip
    workers: 16
    bands: [red, green, blue, nir]
    resolution: 10.0"""


def recipe_text(
    dataset_id: str,
    row: dict[str, str],
    collection: dict,
    urls: dict[str, str],
    version: str,
) -> str:
    """The full ``datasets/<id>.yaml`` text for one region-year."""
    year = int(row["year"])
    title = item_title(collection, urls["item"], f"{row['region']} — {year}")
    name = tracking.filter_file(row)
    filter_line = f"    class_filter: filters/{name}\n" if name else ""
    keywords = ["field-boundaries", "benchmark", tracking.source_stem(row), str(year)]
    presence_only = row.get("wall_to_wall") == PRESENCE_ONLY
    if dataset_id in DERIVED:
        source = (f"Input is derived from harmonized collections by {DERIVED[dataset_id]['script']};\n"
                  f"# run it before building.")
    else:
        source = "Input is one year of the harmonized (fiboa) collection."
    return f"""\
# ftwd recipe for {title}. {source}
# Generated by tools/new_dataset.py from tracking.csv; edit freely afterwards.
# Build with: ftwd run datasets/{dataset_id}.yaml   (tools/build.py wraps this)
version: 1

fields_file: {fields_file(dataset_id, urls)}
source_via: {urls["collection"]}
output_dir: {STAGING.relative_to(ROOT)}/{dataset_id}
name: {dataset_id}
year: {year}

metadata:
  title: {_yaml_str(title)}
  description: >
    Benchmark chips for {row["region"]} cut from the {year} edition of the
    harmonized field boundary collection {row["harmonized_id"]}.
{license_lines(collection)}  version: {version}
  attribution: {_yaml_str(attribution(collection))}
  keywords: [{", ".join(keywords)}]
  providers:
{_providers_yaml(providers(collection))}

stages:
  chips:
    min_coverage: 0.01
    drop_border_chips: true
  splits:
    split_type: block3x3
    split_percents: [80, 10, 10]
    random_seed: 42
  masks:
    mask_types: {mask_types(presence_only)}
    resolution: 10.0
    workers: null
    presence_only: {"true" if presence_only else "false"}
    # Reuse non-empty mask files on rerun so a repeated masks stage only fills gaps.
    skip_existing: true
{filter_line}  stac:
    checksums: false
{_imagery_yaml(release_modes(row))}
"""


def filter_bytes(name: str, checkout: Path | None) -> bytes:
    """ftwd's ``configs/filters/<name>``, from a checkout or the pinned commit."""
    if checkout is not None:
        return (checkout / "configs" / "filters" / name).read_bytes()
    pin = ftwd_pin()
    if pin.kind != "commit":
        sys.exit("ftwd is pinned by version; pass --ftwd-checkout to copy filters")
    with _open(f"{FTWD_RAW}/{pin.value}/configs/filters/{name}") as r:
        return r.read()


def manifest_entry(dataset_id: str, thumb: dict) -> str:
    return (
        f"  {dataset_id}:\n"
        f"    ftw1_name: none\n"
        f"    thumbnail: {{style: {thumb['style']}, zoom: {thumb['zoom']}, rank: {thumb['rank']}}}\n"
    )


def scaffold(dataset_id: str, *, checkout: Path | None = None, force: bool = False) -> Path:
    """Write the recipe, filter and manifest entry for ``dataset_id``."""
    row = tracking.row(dataset_id)
    if row["status"] != "include":
        sys.exit(f"{dataset_id}: tracking.csv status is {row['status']!r}, not 'include'")
    recipe_path = ROOT / "datasets" / f"{dataset_id}.yaml"
    if recipe_path.exists() and not force:
        sys.exit(f"{recipe_path.relative_to(ROOT)} exists (use --force to regenerate it)")

    urls = source_urls(row)
    collection = fetch_json(urls["collection"])
    item = fetch_json(urls["item"])  # fails loudly when the year was never published
    collection = item_terms(collection, item)
    if derived := DERIVED.get(dataset_id):
        if tracking.filter_file(row) != derived["filter"]:
            sys.exit(f"{dataset_id}: tracking.csv filter must be {derived['filter']}, "
                     f"got {tracking.filter_file(row)!r}")
        extra = [fetch_json(f"{HARMONIZED}/{hid}/collection.json")
                 for hid in derived["sources"] if hid != row["harmonized_id"]]
        collection = combined_collection([collection, *extra])
    manifest = load_manifest()
    version = manifest["catalog"]["version"]

    if name := tracking.filter_file(row):
        (ROOT / "datasets" / "filters" / name).write_bytes(filter_bytes(name, checkout))
    recipe_path.write_text(recipe_text(dataset_id, row, collection, urls, version))

    if dataset_id not in manifest["datasets"]:
        with (ROOT / "datasets.yaml").open("a") as f:
            f.write(manifest_entry(dataset_id, thumbnail_spec()))
    return recipe_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dataset_ids", nargs="+", help="region-year ids from tracking.csv")
    parser.add_argument(
        "--ftwd-checkout",
        type=Path,
        default=None,
        help="copy class filters from this ftwd checkout instead of the pinned commit",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing recipe")
    args = parser.parse_args(argv)
    for dataset_id in args.dataset_ids:
        path = scaffold(dataset_id, checkout=args.ftwd_checkout, force=args.force)
        print(f"wrote  {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
