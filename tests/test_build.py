#!/usr/bin/env python3
"""The ftwd build wrapper: argv construction, recipe checks, and the pin gate.

``tools/build.py`` wraps ``ftwd run datasets/<id>.yaml``. This gate exercises
``command()`` directly (pure argv construction, no subprocess involved) and
the two validation helpers through the ``SystemExit`` message they raise, the
same way ``tests/test_upload_data.py`` checks ``data_root()``. No subprocess
is run here at all -- the real invocation is exercised by hand with
``uv run python tools/build.py lu --dry-run``.

Run: python3 tests/test_build.py
"""
import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
from common import Pin  # noqa: E402

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def exit_message(call) -> str:
    """Run a call that must exit, and return the message it exits with."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            call()
    except SystemExit as exc:
        return str(exc.code)
    return ""


# --- command() builds the ftwd argv, in the documented flag order --------
import sys
from pathlib import Path as _P

_FTWD = str(_P(sys.executable).with_name("ftwd"))
check(
    build.command("lu") == [_FTWD, "run", "datasets/lu.yaml"],
    "the plain command runs this interpreter's own ftwd, not one from PATH",
)
check(
    build.command("lu", from_="select_images")
    == [_FTWD, "run", "datasets/lu.yaml", "--from", "select_images"],
    "--from select_images passes through",
)
check(
    build.command("lu", through="stac")
    == [_FTWD, "run", "datasets/lu.yaml", "--through", "stac"],
    "--through stac passes through",
)
check(
    build.command("lu", only="masks")
    == [_FTWD, "run", "datasets/lu.yaml", "--only", "masks"],
    "--only masks passes through",
)
check(
    build.command("lu", dry_run=True)
    == [_FTWD, "run", "datasets/lu.yaml", "--dry-run"],
    "--dry-run is appended",
)

# --- the recipe check: exists, name == id, and published in datasets.yaml -
message = exit_message(lambda: build._check_recipe("no-such-dataset"))
check("datasets.yaml" in message, f"an unknown dataset id names datasets.yaml: {message!r}")

# lu is a real, published recipe whose name field is "lu".
recipe = build._check_recipe("lu")
check(recipe["name"] == "lu", "a real, published recipe passes the check")

# --- the pin check: match, mismatch, missing install, and the override ---
real_ftwd_pin, real_installed_ftwd = build.ftwd_pin, build.installed_ftwd
try:
    build.ftwd_pin = lambda: Pin("commit", "aaaaaaa1111")
    build.installed_ftwd = lambda: Pin("commit", "bbbbbbb2222")

    message = exit_message(lambda: build._check_pin(allow_unpinned=False))
    check("aaaaaaa1111" in message, f"the mismatch message names the pinned commit: {message!r}")
    check(
        "bbbbbbb2222" in message, f"the mismatch message names the installed commit: {message!r}"
    )

    warned = io.StringIO()
    with redirect_stderr(warned):
        build._check_pin(allow_unpinned=True)  # must not raise
    check(
        "aaaaaaa1111" in warned.getvalue() and "bbbbbbb2222" in warned.getvalue(),
        "--allow-unpinned warns loudly with both commits instead of exiting",
    )

    build.installed_ftwd = lambda: None
    message = exit_message(lambda: build._check_pin(allow_unpinned=False))
    check(
        "aaaaaaa1111" in message and "not installed" in message,
        f"no installed ftwd still names the pin: {message!r}",
    )

    build.ftwd_pin = lambda: Pin("commit", "aaaaaaa1111")
    build.installed_ftwd = lambda: Pin("commit", "aaaaaaa1111999")
    build._check_pin(allow_unpinned=False)  # a matching (prefix) pin does not exit
finally:
    build.ftwd_pin, build.installed_ftwd = real_ftwd_pin, real_installed_ftwd

# --- the ftwd process runs from the repository root --------------------
# The recipe path is relative (datasets/<id>.yaml), so the subprocess must
# run with cwd=ROOT regardless of where build.py was invoked from.
_recorded: dict = {}


class _FakeResult:
    returncode = 0


def _fake_run(cmd, **kwargs):
    _recorded["cmd"] = cmd
    _recorded["kwargs"] = kwargs
    return _FakeResult()


_real_run = build.subprocess.run
build.subprocess.run = _fake_run
try:
    with redirect_stdout(io.StringIO()):
        build.main(["lu", "--dry-run", "--allow-unpinned"])
finally:
    build.subprocess.run = _real_run
check(_recorded.get("kwargs", {}).get("cwd") == build.ROOT, "ftwd runs with cwd=ROOT")
check(_recorded.get("cmd", [None])[0] == _FTWD, "the recorded command is this interpreter's ftwd")
# Isolate from whatever PROJ_LIB/PROJ_DATA/GDAL_DATA the ambient shell
# happens to carry (a conda env on PATH, say), so the note is checked against
# a known, controlled set: PROJ_LIB present, the other two absent.
_proj_env_names = ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA")
_saved_proj_env = {key: os.environ.pop(key, None) for key in _proj_env_names}
os.environ["PROJ_LIB"] = "/nonexistent/proj"
_note_out = io.StringIO()
try:
    with redirect_stdout(_note_out):
        _env = build.subprocess_env()
finally:
    for key, value in _saved_proj_env.items():
        os.environ.pop(key, None)
        if value is not None:
            os.environ[key] = value
check("PROJ_LIB" not in _env and "GDAL_DATA" not in _env, "inherited PROJ/GDAL data paths are dropped")
_note_message = _note_out.getvalue()
check(
    "PROJ_LIB" in _note_message and "GDAL_DATA" not in _note_message and "PROJ_DATA" not in _note_message,
    f"a note names exactly the variable(s) actually dropped, got {_note_message!r}",
)
check(
    bool(_recorded.get("kwargs", {}).get("env", {}).get("SSL_CERT_FILE"))
    or bool(os.environ.get("SSL_CERT_DIR")),
    "ftwd runs with a CA bundle configured (certifi when the env has none)",
)

if errors:
    print("\n".join(f"error  {e}" for e in errors))
    raise SystemExit(1)
print("OK: build.py argv construction, recipe check and pin gate hold")
