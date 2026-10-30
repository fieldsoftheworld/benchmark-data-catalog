#!/usr/bin/env python3
"""Class filters copied from ftwd have not drifted from the pinned commit.

ftw-dataset-tools' ``configs/filters/`` is the source of truth for class
filters. ``tools/new_dataset.py`` copies one into ``datasets/filters/``
byte for byte; this gate fetches each copy's original at the ftwd pin and
fails on any difference, so a filter fix lands in ftwd and reaches here by
moving the pin and re-copying, never by a local edit.

Files with no counterpart in ftwd (``at.yaml``, written before filters moved
there) are skipped with a note. Offline, the gate notes and skips rather
than failing.

Run: python3 tests/test_filters.py
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from common import ftwd_pin  # noqa: E402
from new_dataset import FTWD_RAW  # noqa: E402

errors: list[str] = []
pin = ftwd_pin()
if pin.kind != "commit":
    print(f"skip   ftwd is pinned by version {pin.value}; filters are checked by commit only")
    raise SystemExit(0)

for path in sorted((ROOT / "datasets" / "filters").glob("*.yaml")):
    url = f"{FTWD_RAW}/{pin.value}/configs/filters/{path.name}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            upstream = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"note   {path.name}: not in ftwd@{pin.value[:8]}, skipped")
            continue
        raise
    except urllib.error.URLError as exc:
        print(f"skip   offline ({exc.reason}); filter drift not checked")
        raise SystemExit(0) from None
    if path.read_bytes() != upstream:
        errors.append(
            f"datasets/filters/{path.name} differs from ftwd@{pin.value[:8]}; fix it in ftwd, "
            "move the pin, and re-run tools/new_dataset.py --force"
        )

if errors:
    for e in errors:
        print(f"error  {e}")
    raise SystemExit(1)
print("ok     filters match ftwd")
