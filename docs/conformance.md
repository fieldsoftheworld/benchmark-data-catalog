# Conformance

`tests/test_conformance.py` runs rashid with an empty accepted set. Every entry
that is ever added there needs a row here: rule, where it fires, why it is
accepted, and the issue tracking its removal.

| Rule | Where | Why accepted | Tracking |
|------|-------|--------------|----------|
| PTL-LNK-006 | `catalog/<id>/chips/<square>/catalog.json`, `rel: item` links only, and only when the gate runs under `CI_LIGHT=1` without a staging tree | Item JSON is bucket-only; CI checks out metadata alone, so the links cannot resolve there. The local overlay run resolves and enforces them. The `ACCEPTED` set stays empty; this is a scoped waiver in `tests/test_conformance.py`. | [#1](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1) |
| PTL-COL-005 | `catalog/<id>/collection.json`, only under `CI_LIGHT=1` without a staging tree | Same cause: the item mirror is registered but CI sees no item JSON. Enforced in the overlay run. | [#1](https://github.com/fieldsoftheworld/benchmark-data-catalog/issues/1) |

## Overlay validation

A committed sub-catalog (`catalog/<id>/chips/<square>/catalog.json`) carries
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
