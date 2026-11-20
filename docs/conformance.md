# Conformance

`tests/test_conformance.py` runs rashid with an empty accepted set. Every entry
that is ever added there needs a row here: rule, where it fires, why it is
accepted, and the issue tracking its removal.

| Rule | Where | Why accepted | Tracking |
|------|-------|--------------|----------|
| PTL-LNK-006 | `catalog/<source>/<id>/chips/<square>/catalog.json`, `rel: item` links only, and only when the gate runs under `CI_LIGHT=1` without a staging tree | Item JSON is bucket-only; CI checks out metadata alone, so the links cannot resolve there. The local overlay run resolves and enforces them. The `ACCEPTED` set stays empty; this is a scoped waiver in `tests/test_conformance.py`. | [#1](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1) |
| PTL-COL-005 | `catalog/<source>/<id>/collection.json`, only under `CI_LIGHT=1` without a staging tree | Same cause: the item mirror is registered but CI sees no item JSON. Enforced in the overlay run. | [#1](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1) |

## Overlay validation

A committed sub-catalog (`catalog/<source>/<id>/chips/<square>/catalog.json`) carries
`rel: item` links to item JSON that lives only in
`staging/<id>/chips/<square>/<item>/` — ftwd writes it there and it is never
committed (data, uploaded by `tools/upload_data.py`). Validating `catalog/`
alone can neither resolve those links nor check the items themselves.

So once a dataset has been built and its item tree exists on disk,
`tests/test_conformance.py` (rashid) and `tests/test_stac_valid.py`
(stac-check) both run against a temporary copy of `catalog/` with the
matching staging item JSON copied on top, built by `tests/overlay.py`'s
`overlay_tree` — copies, not symlinks, so a validator that treats symlinks
specially sees the same bytes a real checkout would. Only JSON is copied;
rasters and every other data file under an item directory are left out.

Without a built item tree — CI (`CI_LIGHT=1`, no `staging/` checked out) and
the skeleton before any dataset exists — there is nothing to overlay, and both
gates run against `catalog/` unchanged. `tests/test_links.py` covers that gap
locally and in CI: it resolves a `rel: item` link or other data-suffixed href
against `staging/` when present, and under `CI_LIGHT=1` skips (counts, does
not fail on) one still missing after that, since CI never checks out the data
those hrefs point at.

## Portolan v0.3.0 migration (2026-11-20)

Migrated the declared schema URI from v0.1.2 to v0.3.0 everywhere it is
declared (root catalog, every `catalog/<source>/catalog.json`, every
`collection.json`, and every chip sub-catalog that already declared one —
`common.canonicalize_portolan_schema`), filled every missing
`table:columns` and asset `description` (PORTO-FMT-077/078/079,
PORTO-CORE-088), and stamped `updated` on every group catalog
(PORTO-CORE-057, PTL-PRO-003 — these had never carried one). None of this
needed a spec/rashid disagreement entry in the table above; two gaps are
worth recording instead, since neither is a rashid finding to accept or
waive:

- **PORTO-CORE-006** ("every catalog and collection MUST declare the
  versioned Portolan schema URI") reads as covering every STAC `Catalog`
  object, including `catalog/<source>/<id>/chips/<square>/catalog.json`.
  Whether one of these declares the extension at all varies by the ftwd
  version that built the collection (verified: every one of `fi`'s chip
  sub-catalogs declares none; every one of `wri_trazo_ml`'s does). rashid
  0.4.0 reports no finding either way — it does not check the Portolan
  extension is declared at that level of the tree. This repository does not
  add a declaration to a sub-catalog that never had one; it only
  canonicalizes an existing one to v0.3.0 (`canonicalize_portolan_schema`).
  Filed as a question for rashid/the spec to clarify; not tracked as an
  issue yet, since it changes nothing a reader of this catalog can observe
  today.
- **PORTO-CORE-028** (assets SHOULD carry `file:size`/`file:checksum`) is met
  for `thumbnail.webp` and `styles/*.json` (committed bytes; see
  `fill_local_checksums`) but not for any `*.parquet` or `*.pmtiles` data
  asset, across every collection — computing a checksum needs the actual
  bytes, which are bucket-only and were never fetched to build this
  migration (a bulk download, out of scope for a metadata-only pass). See
  the "Requires data work" section of the v0.3 migration PR.

## stac-check exemption

`tests/test_stac_valid.py` exempts one known stac-check failure: stac-validator
hardcodes the JSON Schema 2020-12 dialect and ignores the `$schema` a schema
declares. The Portolan profile schema is draft-07 and uses draft-07's tuple
form of `items` in `valid_bbox`; under 2020-12 that keyword takes a single
schema, so stac-validator hands a list to code expecting an object and raises
`'list' object has no attribute 'get'`. The schema itself is correct draft-07
and rashid validates it cleanly, so nothing on the Portolan side is wrong.
Tracked upstream at https://github.com/stac-utils/stac-check/issues/159.

The exemption is narrow — that exact message, and only when the failing
schema is a Portolan profile schema — and self-expiring: the gate installs
stac-check unpinned and fails once the crash stops happening on an object it
can reach (a Collection or Feature that declares a Portolan extension), since
that means the next stac-check release fixed the dialect handling and the
exemption has outlived its bug. When that happens, delete the exemption from
`tests/test_stac_valid.py` and this section together.
