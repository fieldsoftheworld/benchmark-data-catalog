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
    write(root / "catalog/roads/collection.json")
    write(root / "catalog/roads/thumbnail.png")
    write(root / "catalog/roads/styles/default.json")
    write(root / "catalog/_assets/logo.svg")
    write(root / "catalog/roads/chips/32UNA/catalog.json")
    write(root / "catalog/roads/chips/32UNA/ftw-1/ftw-1.json")

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
        "a/prefix/roads/collection.json",
        "a/prefix/roads/thumbnail.png",
        "a/prefix/roads/styles/default.json",
        "a/prefix/_assets/logo.svg",
        "a/prefix/roads/chips/32UNA/catalog.json",
        "a/prefix/roads/chips/32UNA/ftw-1/ftw-1.json",
    }
    check(keys == expected, f"upload set wrong.\n  extra:   {keys - expected}"
                            f"\n  missing: {expected - keys}")

    # collect_uploads passes rel through to content_type_for, so an item
    # JSON gets geo+json and its square's catalog.json stays plain json.
    types = {u.key: u.content_type for u in uploads}
    check(
        types["a/prefix/roads/chips/32UNA/ftw-1/ftw-1.json"]
        == "application/geo+json",
        "collect_uploads gives an item JSON geo+json via rel",
    )
    check(
        types["a/prefix/roads/chips/32UNA/catalog.json"] == "application/json",
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
    content_type_for(Path("x.json"), rel=Path("lu/chips/32UNA/ftw-1/sub/x.json"))
    == "application/json",
    "an extra level below the item directory is not an item JSON",
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

    def upload_file(self, local, bucket, key, ExtraArgs):
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

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: publish contract holds")
