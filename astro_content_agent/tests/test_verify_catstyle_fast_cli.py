"""Tests for scripts/aca/verify_catstyle_fast.py helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_cli():
    repo = Path(__file__).resolve().parents[2]
    aca = str(repo / "scripts" / "aca")
    if aca not in sys.path:
        sys.path.insert(0, aca)
    p = repo / "scripts" / "aca" / "verify_catstyle_fast.py"
    spec = importlib.util.spec_from_file_location("_verify_catstyle_fast_cli", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_scan_diff_for_secrets_detects_token() -> None:
    mod = _load_cli()
    openai_key = "OPENAI" + "_API_KEY"
    fake_secret = "sk" + "-fake-token"
    diff = f"+{openai_key}={fake_secret}\n"
    assert mod.scan_diff_for_secrets(diff) == [openai_key]


def test_scan_diff_for_secrets_clean() -> None:
    mod = _load_cli()
    assert mod.scan_diff_for_secrets("+planet_a = Mercury\n") == []


def test_scan_diff_for_secrets_ignores_removed_and_context_lines() -> None:
    mod = _load_cli()
    openai_key = "OPENAI" + "_API_KEY"
    sk_proj = "sk" + "-proj" + "-fake-token"
    diff = (
        f" context line {openai_key}=old\n"
        f"-{openai_key}=old-value\n"
        f"-{sk_proj}-old-removed\n"
        "+++ b/example.py\n"
    )
    assert mod.scan_diff_for_secrets(diff) == []


def test_scan_diff_for_secrets_detects_only_added_lines() -> None:
    mod = _load_cli()
    openai_key = "OPENAI" + "_API_KEY"
    insta_token = "INSTAGRAM" + "_ACCESS_TOKEN"
    diff = (
        f"-{openai_key}=old-value\n"
        "+safe = True\n"
        f"+{insta_token}=added-token\n"
    )
    assert mod.scan_diff_for_secrets(diff) == [insta_token]


def test_scan_diff_for_media_warnings_detects_png_path() -> None:
    mod = _load_cli()
    diff = "diff --git a/references/cat.png b/references/cat.png\n"
    warnings = mod.scan_diff_for_media_warnings(diff)
    assert warnings


def test_scan_diff_for_media_warnings_ignores_unrelated() -> None:
    mod = _load_cli()
    diff = "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n"
    assert mod.scan_diff_for_media_warnings(diff) == []
