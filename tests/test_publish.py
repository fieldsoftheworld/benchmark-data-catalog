#!/usr/bin/env python3
"""The publish contract: only the published directory is ever uploaded.

This is the gate that turns the three-file-category model into an enforced
property. It builds a temp tree holding all three categories, asks the
publisher what it would upload, and asserts set equality — so a leak fails and
a missing file fails too.

No network, no AWS, no credentials.

Run: python3 tests/test_publish.py
"""
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from publish import (  # noqa: E402
    Upload,
    aws_session,
    collect_uploads,
    content_type_for,
    is_unchanged,
    load_config,
    s3_client,
    split_s3_uri,
    unedited_sentinels,
    upload_all,
)

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def write(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# --- what gets uploaded, and what never does ---------------------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # Category 1: tracked and published.
    write(root / "catalog/catalog.json")
    write(root / "catalog/README.md")
    write(root / "catalog/AGENTS.md")
    write(root / "catalog/g/roads/collection.json")
    write(root / "catalog/g/roads/thumbnail.png")
    write(root / "catalog/g/roads/styles/default.json")
    write(root / "catalog/_assets/logo.svg")
    write(root / "catalog/g/roads/chips/32UNA/catalog.json")
    write(root / "catalog/g/roads/chips/32UNA/ftw-1/ftw-1.json")

    # Category 2: tracked, never published.
    write(root / "tools/publish.py")
    write(root / "tests/test_publish.py")
    write(root / "docs/conformance.md")
    write(root / "README.md")
    write(root / "AGENTS.md")
    write(root / "CLAUDE.md")
    write(root / "catalog.publish.yaml")
    write(root / ".github/workflows/ci.yml")

    # Dotfiles inside the published directory are tracked but not uploaded.
    write(root / "catalog/_assets/.gitkeep", "")
    write(root / "catalog/.portolan/state.json")

    config = {
        "write_prefix": "s3://a-bucket/a/prefix",
        "public_base": "https://data.example.org/a/prefix",
        "publish_dir": "catalog",
    }
    uploads = collect_uploads(config, root)
    keys = {u.key for u in uploads}

    expected = {
        "a/prefix/catalog.json",
        "a/prefix/README.md",
        "a/prefix/AGENTS.md",
        "a/prefix/g/roads/collection.json",
        "a/prefix/g/roads/thumbnail.png",
        "a/prefix/g/roads/styles/default.json",
        "a/prefix/_assets/logo.svg",
        "a/prefix/g/roads/chips/32UNA/catalog.json",
        "a/prefix/g/roads/chips/32UNA/ftw-1/ftw-1.json",
    }
    check(keys == expected, f"upload set wrong.\n  extra:   {keys - expected}"
                            f"\n  missing: {expected - keys}")

    # collect_uploads passes rel through to content_type_for, so an item
    # JSON gets geo+json and its square's catalog.json stays plain json.
    types = {u.key: u.content_type for u in uploads}
    check(
        types["a/prefix/g/roads/chips/32UNA/ftw-1/ftw-1.json"]
        == "application/geo+json",
        "collect_uploads gives an item JSON geo+json via rel",
    )
    check(
        types["a/prefix/g/roads/chips/32UNA/catalog.json"] == "application/json",
        "collect_uploads leaves a square's catalog.json as plain json",
    )

    # The bare-prefix case: no prefix at all.
    flat = dict(config, write_prefix="s3://a-bucket")
    check(
        {u.key for u in collect_uploads(flat, root)}
        == {k.removeprefix("a/prefix/") for k in expected},
        "keys are wrong when write_prefix names no prefix",
    )

# --- split_s3_uri ------------------------------------------------------
check(split_s3_uri("s3://b/a/c") == ("b", "a/c"), "plain uri")
check(split_s3_uri("s3://b/a/c/") == ("b", "a/c"), "trailing slash")
check(split_s3_uri("s3://b") == ("b", ""), "bare bucket")
check(split_s3_uri("s3://b/") == ("b", ""), "bare bucket, trailing slash")

# --- content types -----------------------------------------------------
check(content_type_for(Path("a/catalog.json")) == "application/json",
      "plain json")
check(
    content_type_for(Path("a/styles/default.json"))
    == "application/vnd.mapbox.style+json",
    "json under styles/ is a MapLibre style",
)
check(
    content_type_for(Path("a/roads.style.json"))
    == "application/vnd.mapbox.style+json",
    "*.style.json is a MapLibre style",
)
check(
    content_type_for(Path("a/d.parquet")) == "application/vnd.apache.parquet",
    "parquet",
)
check(content_type_for(Path("a/x.unknown")) == "application/octet-stream",
      "unknown suffix falls back")
check(
    content_type_for(Path("a/d.tif"))
    == "image/tiff; application=geotiff; profile=cloud-optimized",
    "a .tif is a cloud-optimized GeoTIFF",
)
check(
    content_type_for(Path("a/d.tiff"))
    == "image/tiff; application=geotiff; profile=cloud-optimized",
    "a .tiff is a cloud-optimized GeoTIFF",
)

# --- content_type_for: item JSON, positional on rel ---------------------
check(
    content_type_for(
        Path("x.json"), rel=Path("lu/chips/32UNA/ftw-1/ftw-1.json")
    )
    == "application/geo+json",
    "an item JSON two levels below the square is geo+json",
)
check(
    content_type_for(
        Path("c.json"),
        rel=Path("lu/chips/32UNA/ftw-1/ftw-1_s2_2023-07/ftw-1_s2_2023-07.json"),
    )
    == "application/geo+json",
    "an item JSON nested deeper below the square is geo+json too",
)
check(
    content_type_for(Path("x.json"), rel=Path("lu/chips/32UNA/catalog.json"))
    == "application/json",
    "a square's catalog.json is plain json, not an item",
)
check(
    content_type_for(Path("x.json"), rel=Path("lu/styles/split.json"))
    == "application/vnd.mapbox.style+json",
    "the styles/ rule still applies when rel is passed",
)
check(
    content_type_for(Path("a/styles/default.json"))
    == "application/vnd.mapbox.style+json",
    "the styles/ rule still applies with no rel at all",
)
check(
    content_type_for(Path("x.json"), rel=Path("lu/collection.json"))
    == "application/json",
    "no chips segment at all is plain json",
)

# --- change detection --------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    local = write(Path(tmp) / "f.json", "hello")
    digest = hashlib.md5(b"hello").hexdigest()  # noqa: S324
    upload = Upload(local, "k", "application/json")

    check(is_unchanged(upload, {"k": (5, digest)}), "identical bytes")
    check(is_unchanged(upload, {"k": (5, f'"{digest}"')}), "quoted etag")
    check(not is_unchanged(upload, {}), "absent key")
    check(not is_unchanged(upload, {"other": (5, digest)}), "key mismatch")
    check(not is_unchanged(upload, {"k": (5, "0" * 32)}), "etag differs")
    check(not is_unchanged(upload, {"k": (9, digest)}), "size differs")
    check(is_unchanged(upload, {"k": (5, "abc-2")}), "multipart: size only")

# --- the sentinel guard ------------------------------------------------
check(
    unedited_sentinels({
        "write_prefix": "s3://EXAMPLE-BUCKET/EXAMPLE-PREFIX",
        "public_base": "https://example.invalid/EXAMPLE-PREFIX",
    }) != [],
    "an unedited config is refused",
)
check(
    unedited_sentinels({
        "write_prefix": "s3://real/prefix",
        "public_base": "https://data.example.org/prefix",
    }) == [],
    "an edited config is accepted",
)

# --- the parallel upload pool ------------------------------------------
# A fake session stands in for boto3, so this stays offline and has no
# credentials. It records every call and fails one chosen key.
class FakeClient:
    def __init__(self, calls: list, fail_key: str | None) -> None:
        self.calls = calls
        self.fail_key = fail_key

    def upload_file(self, local, bucket, key, ExtraArgs, Config=None):
        if key == self.fail_key:
            raise RuntimeError("boom")
        self.calls.append((local, bucket, key, ExtraArgs["ContentType"]))


class FakeSession:
    def __init__(self, fail_key: str | None = None) -> None:
        self.calls: list = []
        self.clients = 0
        self.fail_key = fail_key
        self.client_kwargs: dict = {}

    def client(self, name, **kwargs):
        self.clients += 1
        self.client_kwargs = kwargs
        return FakeClient(self.calls, self.fail_key)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    batch = [
        Upload(write(root / f"f{i}.json"), f"p/f{i}.json", "application/json")
        for i in range(50)
    ]

    session = FakeSession()
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        failed = upload_all(session, "a-bucket", batch)
    check(failed == [], "no failures")
    check(
        {c[2] for c in session.calls} == {u.key for u in batch},
        "every object is uploaded exactly once",
    )
    # Progress is batched, not one line per object.
    check(
        len(out.getvalue().splitlines()) < len(batch),
        "progress does not print one line per object",
    )
    check(
        {c[3] for c in session.calls} == {"application/json"},
        "the content type reaches upload_file",
    )
    check(
        {c[1] for c in session.calls} == {"a-bucket"},
        "the bucket reaches upload_file",
    )

    # One bad object names itself and does not stop the other uploads.
    session = FakeSession(fail_key="p/f7.json")
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        failed = upload_all(session, "a-bucket", batch)
    check(failed == ["p/f7.json"], f"the failed key is named, got {failed}")
    check(len(session.calls) == len(batch) - 1, "one failure stops nothing")
    check("p/f7.json" in err.getvalue(), "the failed key goes to stderr")

# --- the AWS session ---------------------------------------------------
# boto3 is not a dependency of this template, so this part is skipped when
# boto3 is absent. CI runs without it. A fixture AWS config keeps the check
# off the developer's own profiles.
if importlib.util.find_spec("boto3") is None:
    print("note: boto3 is not installed; skipping the aws_session checks")
else:
    with tempfile.TemporaryDirectory() as tmp:
        conf = write(
            Path(tmp) / "aws-config",
            "[default]\nregion = us-east-1\n\n"
            "[profile a-profile]\nregion = eu-west-1\n",
        )
        os.environ["AWS_CONFIG_FILE"] = str(conf)
        os.environ.pop("AWS_PROFILE", None)

        named = aws_session({"profile": "a-profile", "region": "us-west-2"})
        check(named.profile_name == "a-profile", "profile reaches the session")
        check(named.region_name == "us-west-2", "region reaches the session")

        inherited = aws_session({"profile": "a-profile"})
        check(
            inherited.region_name == "eu-west-1",
            "no region means the region of the profile",
        )

        bare = aws_session({})
        check(bare.profile_name == "default", "no profile means the default")

        empty = aws_session({"profile": "", "region": ""})
        check(empty.profile_name == "default", "an empty profile is no profile")

# --- endpoint support ------------------------------------------------------
cfg = load_config()
check(cfg.get("endpoint_url") == "https://data.source.coop", "endpoint_url is read from catalog.publish.yaml")
check(cfg.get("profile") == "source-coop", "profile is read from catalog.publish.yaml")
check(unedited_sentinels(cfg) == [], "no template sentinels survive in catalog.publish.yaml")

# endpoint_url in the config is not enough on its own; it has to reach
# session.client(...). s3_client is the one place every client in this
# script is built, so cover it directly first.
with_endpoint = FakeSession()
s3_client(with_endpoint, endpoint_url="https://data.source.coop")
check(
    with_endpoint.client_kwargs.get("endpoint_url") == "https://data.source.coop",
    "s3_client passes endpoint_url to session.client when one is set",
)

without_endpoint = FakeSession()
s3_client(without_endpoint)
check(
    without_endpoint.client_kwargs.get("endpoint_url") is None,
    "s3_client passes no endpoint_url when none is configured",
)

# End to end: upload_all is the code path main() drives with the loaded
# config's endpoint_url (`upload_all(session, bucket, changed,
# config.get("endpoint_url"))`). Confirm it reaches session.client(...) from
# the actual value load_config() reads out of catalog.publish.yaml.
end_to_end_session = FakeSession()
one_upload = [Upload(Path("unused.json"), "k", "application/json")]
out, err = io.StringIO(), io.StringIO()
with redirect_stdout(out), redirect_stderr(err):
    upload_all(end_to_end_session, "a-bucket", one_upload, cfg["endpoint_url"])
check(
    end_to_end_session.client_kwargs.get("endpoint_url") == cfg["endpoint_url"],
    "upload_all passes the configured endpoint_url through to session.client",
)

# --- a collection is published only once its data is in the bucket ------------
from publish import pending_data  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    write(root / "catalog/aa/aa_2024/collection.json")
    write(root / "catalog/bb/bb_2024/collection.json")
    a = write(root / "staging/aa_2024/items.parquet", "aaaa")
    write(root / "staging/bb_2024/items.parquet", "bbbb")
    write(root / "staging/bb_2024/chips/x/c_q1_image_s2.tif", "tif")
    write(root / "staging/cc_2024/items.parquet", "not catalogued, not checked")
    cfg = {"write_prefix": "s3://bkt/pre", "public_base": "https://x", "publish_dir": "catalog",
           "data_dir": "staging"}
    a_md5 = hashlib.md5(a.read_bytes()).hexdigest()
    listing = {"pre/aa/aa_2024/items.parquet": (4, a_md5)}
    check(pending_data(cfg, listing, root) == {"bb_2024": 2}, "bb_2024's two files are pending")
    listing["pre/bb/bb_2024/items.parquet"] = (4, hashlib.md5(b"bbbb").hexdigest())
    listing["pre/bb/bb_2024/chips/x/c_q1_image_s2.tif"] = (3, hashlib.md5(b"tif").hexdigest())
    check(pending_data(cfg, listing, root) == {}, "everything uploaded: nothing pending")
    write(root / "catalog/dd/dd_2024/collection.json")  # no staging: must already be in the bucket
    check(pending_data(cfg, listing, root) == {"dd_2024": 1}, "no staging and no mirror: pending")
    listing["pre/dd/dd_2024/items.parquet"] = (1, "x")
    check(pending_data(cfg, listing, root) == {}, "staging pruned after upload: fine")

from publish import collections_to_check, split_pending  # noqa: E402


def uploaded(listing: dict, upload: Upload) -> None:
    """Put ``upload`` in the bucket listing, byte for byte."""
    data = upload.local.read_bytes()
    listing[upload.key] = (len(data), hashlib.md5(data).hexdigest())


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = {"write_prefix": "s3://bkt/pre", "public_base": "https://x", "publish_dir": "catalog",
           "data_dir": "staging"}

    def up(rel: str, body: str = "{}") -> Upload:
        return Upload(write(root / "catalog" / rel, body), f"pre/{rel}", "application/json")

    root_json = up("catalog.json")
    aa = up("aa/aa_2024/collection.json")
    bb_chip = up("bb/bb_2024/chips/x/c.json")
    asset = up("_assets/logo.json")
    uploads = [root_json, aa, bb_chip, asset]
    listing: dict = {}
    for u in uploads:
        uploaded(listing, u)
    check(collections_to_check(uploads, listing, cfg, root) == set(),
          "nothing differs from the bucket: no collections to check")
    write(root / "catalog/bb/bb_2024/chips/x/c.json", '{"new": 1}')
    write(root / "catalog/_assets/logo.json", '{"new": 1}')
    check(collections_to_check(uploads, listing, cfg, root) == {"bb_2024"},
          "the dataset folders (<source>/<id>/) that differ are checked")
    write(root / "catalog/catalog.json", '{"new": 1}')
    check(collections_to_check(uploads, listing, cfg, root) is None,
          "a changed root file checks every collection: root tables come from staging")
    write(root / "catalog/catalog.json", "{}")
    readme = up("README.md", "# old")
    uploaded(listing, readme)
    write(root / "catalog/README.md", "# new row")
    check(collections_to_check([*uploads, readme], listing, cfg, root) is None,
          "a changed root README checks every collection too")

    # split_pending, the check main() runs: aa_2024 is rebuilding in staging while
    # bb_2024 (fully uploaded) is what this publish changes.
    write(root / "catalog/bb/bb_2024/collection.json")
    write(root / "catalog/catalog.json", "{}")
    write(root / "catalog/_assets/logo.json", "{}")
    bb_data = write(root / "staging/bb_2024/items.parquet", "bbbb")
    listing["pre/bb/bb_2024/items.parquet"] = (4, hashlib.md5(bb_data.read_bytes()).hexdigest())
    write(root / "staging/aa_2024/items.parquet", "rebuilt")
    blocking, other = split_pending(uploads, listing, cfg, root)
    check(blocking == {} and other == {"aa_2024": 1},
          f"aa_2024's rebuild does not block bb_2024's publish but is reported, got {blocking}, {other}")
    write(root / "catalog/catalog.json", '{"new": 2}')
    blocking, other = split_pending(uploads, listing, cfg, root)
    check(blocking == {"aa_2024": 1} and other == {},
          f"a root change publishes aa_2024's staged row, so it blocks, got {blocking}, {other}")
    write(root / "catalog/catalog.json", "{}")
    write(root / "catalog/aa/aa_2024/collection.json", '{"rebuilt": 1}')
    blocking, other = split_pending(uploads, listing, cfg, root)
    check(blocking == {"aa_2024": 1}, f"aa_2024's own catalog changes: it blocks, got {blocking}")

# --- --only narrows the walk, the listing and the data check ------------------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = {"write_prefix": "s3://bkt/pre", "public_base": "https://x", "publish_dir": "catalog",
           "data_dir": "staging"}
    write(root / "catalog/catalog.json")
    write(root / "catalog/aa/aa_2024/collection.json")
    write(root / "catalog/aa/aa_2024/chips/x/catalog.json")
    write(root / "catalog/aa/catalog.json")
    write(root / "catalog/aa/README.md")
    write(root / "catalog/aa/aa_2023/collection.json")
    write(root / "catalog/bb/catalog.json")
    write(root / "catalog/bb/bb_2024/collection.json")
    write(root / "staging/bb_2024/items.parquet", "not uploaded")
    keys = {u.key for u in collect_uploads(cfg, root, only={"aa_2024"})}
    check(keys == {"pre/aa/aa_2024/collection.json", "pre/aa/aa_2024/chips/x/catalog.json",
                   "pre/aa/catalog.json", "pre/aa/README.md"},
          f"--only publishes that dataset's folder and its group's own files, no root file and "
          f"no sibling, got {sorted(keys)}")
    check(pending_data(cfg, {"pre/aa/aa_2024/items.parquet": (1, "x")}, root, only={"aa_2024"}) == {},
          "--only leaves other datasets' pending data out of the check")
    check(pending_data(cfg, {}, root, only={"bb_2024"}) == {"bb_2024": 1},
          "--only still blocks the named dataset until its data is uploaded")

# --- a new source group brings the root files; otherwise they stay out ------------
from publish import missing_data, new_groups, root_uploads  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = {"write_prefix": "s3://bkt/pre", "public_base": "https://x", "publish_dir": "catalog",
           "data_dir": "staging"}
    write(root / "catalog/catalog.json")
    write(root / "catalog/README.md")
    write(root / "catalog/aa/catalog.json")
    write(root / "catalog/aa/aa_2024/collection.json")
    check(new_groups({"aa_2024"}, {}, cfg, root) == {"aa"},
          "a group whose catalog.json the bucket lacks is new")
    check(new_groups({"aa_2024"}, {"pre/aa/catalog.json": (1, "x")}, cfg, root) == set(),
          "a group already in the bucket is not new, so the root files stay out")
    check({u.key for u in root_uploads(cfg, root)} == {"pre/catalog.json", "pre/README.md"},
          "root_uploads is exactly the files directly under publish_dir")
    from publish import collect_uploads, plan_root_files  # noqa: E402
    group_only = collect_uploads(cfg, root, only={"aa_2024"})
    planned, why = plan_root_files(group_only, {"aa_2024"}, {}, cfg, root)
    check("pre/catalog.json" in {u.key for u in planned} and why,
          "--only on a new group adds the root files")
    planned, why = plan_root_files(group_only, {"aa_2024"}, {}, cfg, root, no_root=True)
    check({u.key for u in planned} == {"pre/aa/catalog.json", "pre/aa/aa_2024/collection.json"}
          and why is None,
          f"--no-root keeps root files out even for a new group, group files still go: {planned}")
    planned, why = plan_root_files(collect_uploads(cfg, root), None, {}, cfg, root, no_root=True)
    check(not {"pre/catalog.json", "pre/README.md"} & {u.key for u in planned} and why,
          "--no-root drops the root files from a full publish too")

# --- a moved collection is not published before its data is at the new keys -------
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    cfg = {"write_prefix": "s3://bkt/pre", "public_base": "https://x", "publish_dir": "catalog",
           "data_dir": "staging"}
    collection = {"type": "Collection", "id": "aa_2024",
                  "assets": {"chips": {"href": "./aa_2024_chips.parquet"},
                             "thumbnail": {"href": "./thumbnail.webp"},
                             "license": {"href": "https://example.org/terms"}},
                  "links": [{"rel": "pmtiles", "href": "./chips.pmtiles"},
                            {"rel": "root", "href": "../../catalog.json"}]}
    coll = write(root / "catalog/aa/aa_2024/collection.json", json.dumps(collection))
    write(root / "catalog/aa/aa_2024/thumbnail.webp", "git owns it")
    up_coll = Upload(coll, "pre/aa/aa_2024/collection.json", "application/json")
    check(missing_data([up_coll], {}, cfg, root) == {"aa_2024": ["aa_2024_chips.parquet", "chips.pmtiles"]},
          f"data neither staged nor at the new key is missing: {missing_data([up_coll], {}, cfg, root)}")
    write(root / "staging/aa_2024/aa_2024_chips.parquet", "staged")
    listing = {"pre/aa/aa_2024/chips.pmtiles": (1, "x"), "pre/aa_2024/chips.pmtiles": (1, "old")}
    check(missing_data([up_coll], listing, cfg, root) == {},
          "staged data, or data already copied to the new key, is enough")
    check(missing_data([up_coll], {"pre/aa_2024/chips.pmtiles": (1, "x")}, cfg, root)
          == {"aa_2024": ["chips.pmtiles"]},
          "data still only at the old flat key does not count")
    uploaded(listing, up_coll)
    (root / "staging/aa_2024/aa_2024_chips.parquet").unlink()
    check(missing_data([up_coll], listing, cfg, root) == {},
          "a collection this publish leaves unchanged is not checked")

# --- retry and transfer settings for the data proxy ----------------------------
if importlib.util.find_spec("botocore") is not None:
    from publish import MULTIPART_CHUNK_BYTES, RETRY_MAX_ATTEMPTS, _retry_config, _transfer_config

    _cfg = _retry_config()
    check(_cfg is not None and _cfg.retries == {"max_attempts": RETRY_MAX_ATTEMPTS, "mode": "standard"}, "S3 clients use the standard retry mode with more attempts")
    from publish import _client_config

    _pc = _client_config(retry=True, pool_size=32)
    check(_pc.max_pool_connections == 32 and _pc.retries["mode"] == "standard", "the listing client gets a pool for every worker and keeps the retries")
    check(_client_config(retry=False, pool_size=None) is None, "a default client gets no Config")
    _tc = _transfer_config()
    check(_tc is not None and _tc.multipart_chunksize == MULTIPART_CHUNK_BYTES, "uploads use large multipart chunks")

# --- the parallel bucket listing -----------------------------------------
# A fake S3 answers list_objects_v2 with Prefix, Delimiter and 2-key pages, so
# the walk is checked against a plain flat listing of the same keys.
import threading as _threading  # noqa: E402

import publish as _publish  # noqa: E402


class FakeLister:
    def __init__(self, keys, fail_prefix=None, page_size=2, failures=None):
        self.keys = sorted(keys)
        self.fail_prefix = fail_prefix
        self.failures = failures  # None: fail every time
        self.page_size = page_size
        self.requests = []
        self.lock = _threading.Lock()

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return self

    def paginate(self, Bucket, Prefix, Delimiter=None):
        with self.lock:
            self.requests.append((Prefix, Delimiter))
        if self.fail_prefix is not None and Prefix.startswith(self.fail_prefix):
            with self.lock:
                fail = self.failures is None or self.failures > 0
                if self.failures:
                    self.failures -= 1
            if fail:
                raise RuntimeError("520")
        contents, folders = [], []
        for key in self.keys:
            if not key.startswith(Prefix):
                continue
            rest = key[len(Prefix):]
            if Delimiter and Delimiter in rest:
                folder = Prefix + rest.split(Delimiter)[0] + Delimiter
                if folder not in folders:
                    folders.append(folder)
            else:
                contents.append({"Key": key, "Size": len(key), "ETag": f'"{key}"'})
        entries = [("c", c) for c in contents] + [("p", f) for f in folders]
        for i in range(0, max(len(entries), 1), self.page_size):
            chunk = entries[i:i + self.page_size]
            yield {
                "Contents": [c for kind, c in chunk if kind == "c"],
                "CommonPrefixes": [{"Prefix": f} for kind, f in chunk if kind == "p"],
            }


_keys = [
    "bd/catalog.json",
    "bd/README.md",
    "bd/aa/catalog.json",
    "bd/aa/aa_2024/collection.json",
    "bd/aa/aa_2024/items.parquet",
    "bd/bb/bb_2025/collection.json",
    "bd-other/unrelated.txt",
    "elsewhere/x.json",
]
for tile in ("30SVH", "31TBF"):
    for chip in range(3):
        for f in ("image_s2.tif", "mask.tif"):
            _keys.append(f"bd/aa/aa_2024/chips/{tile}/ftw-{tile}{chip}/{f}")
_keys.append("bd/bb/bb_2025/chips/32ULU/ftw-32ULU0/mask.tif")
# A dataset still at the old flat key during the move: never walked, never split.
_old = [f"bd/zz_2020/chips/30SVH/ftw-30SVH{c}/mask.tif" for c in range(3)] + ["bd/zz_2020/collection.json"]
_expected = {k: (len(k), f'"{k}"') for k in _keys if k.startswith("bd/")}

_listing_root = Path(tempfile.mkdtemp())
for _rel in ("aa/aa_2024", "bb/bb_2025"):
    write(_listing_root / "catalog" / _rel / "collection.json")
_cfg = {"publish_dir": "catalog"}

_saved = (_publish.aws_session, _publish.s3_client, _publish.LIST_RETRY_SECONDS)
_publish.LIST_RETRY_SECONDS = 0
try:
    _publish.aws_session = lambda config: None
    _lister = FakeLister(_keys + _old)
    _publish.s3_client = lambda session, endpoint_url=None, **kw: _lister
    _out = io.StringIO()
    with redirect_stdout(_out):
        _index = _publish.remote_index("b", "bd", _cfg, root=_listing_root)
    check(_index == _expected, "the walk finds every key under the root and the source groups, nothing else")
    _flat = [p for p, d in _lister.requests if d is None]
    check(
        sorted(_flat) == ["bd/aa/aa_2024/chips/30SVH/", "bd/aa/aa_2024/chips/31TBF/",
                          "bd/bb/bb_2025/chips/32ULU/"],
        f"folders are split down to the tile and listed flat there, got {sorted(_flat)}",
    )
    check(
        not any(p.count("/") > 5 for p, _ in _lister.requests),
        "single chip folders are not listed one by one",
    )
    check(
        not any(p.startswith("bd/zz_2020/") for p, _ in _lister.requests),
        "a top-level folder that is not a source group (an old flat dataset) is never walked",
    )

    _lister = FakeLister(_keys)
    with redirect_stdout(_out):
        _only = _publish.remote_index("b", "bd", _cfg, only={"aa_2024"}, root=_listing_root)
    check(
        _only == {k: v for k, v in _expected.items()
                  if k.startswith("bd/aa/aa_2024/") or k in ("bd/catalog.json", "bd/README.md", "bd/aa/catalog.json")},
        f"only= lists those datasets' folders, their group's files and the root files, got {sorted(_only)}",
    )
    check(
        all(p.startswith("bd/aa/aa_2024/") or (p in ("bd/", "bd/aa/") and d == "/")
            for p, d in _lister.requests),
        f"only= walks nothing else, and the root and group only one level: {_lister.requests}",
    )
    _flat = sorted(p for p, d in _lister.requests if d is None)
    check(
        _flat == ["bd/aa/aa_2024/chips/30SVH/", "bd/aa/aa_2024/chips/31TBF/"],
        f"only= splits to the same tile depth, got {_flat}",
    )

    _lister = FakeLister(_keys + ["bd/chips.parquet"])
    with redirect_stdout(_out):
        _root_file = _publish.remote_index("b", "bd", _cfg, only={"aa_2024", "chips.parquet"},
                                           root=_listing_root)
    check("bd/chips.parquet" in _root_file and "bd/aa/aa_2024/items.parquet" in _root_file,
          "only= naming a root file (upload_data --only chips.parquet) lists the root level")

    _lister = FakeLister(_keys, fail_prefix="bd/aa/aa_2024/chips/31TBF/")
    _out = io.StringIO()
    with redirect_stdout(_out):
        _failed = _publish.remote_index("b", "bd", _cfg, root=_listing_root)
    check(_failed == {}, "one failed request fails the whole listing, never a partial index")
    check("could not list" in _out.getvalue(), "a failed listing says so")

    check(
        sum(p == "bd/aa/aa_2024/chips/31TBF/" for p, _ in _lister.requests) == _publish.LIST_ATTEMPTS,
        "a failing folder is tried LIST_ATTEMPTS times before the listing gives up",
    )

    _lister = FakeLister(_keys, fail_prefix="bd/aa/aa_2024/chips/31TBF/", failures=2)
    with redirect_stdout(io.StringIO()):
        _retried = _publish.remote_index("b", "bd", _cfg, root=_listing_root)
    check(_retried == _expected, "a folder that fails twice and then answers is listed in full")

    _lister = FakeLister([])
    with redirect_stdout(io.StringIO()):
        check(_publish.remote_index("b", "bd", _cfg, root=_listing_root) == {}, "an empty bucket lists as empty")
finally:
    _publish.aws_session, _publish.s3_client, _publish.LIST_RETRY_SECONDS = _saved

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: publish contract holds")
