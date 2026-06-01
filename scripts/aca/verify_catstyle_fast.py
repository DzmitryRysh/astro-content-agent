#!/usr/bin/env python3
"""Fast Catstyle verification: targeted pytest + git diff hygiene (stdlib only)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PYTEST_TARGETS: tuple[str, ...] = (
    "astro_content_agent/tests/test_catstyle_caption_generator.py",
    "astro_content_agent/tests/test_catstyle_caption_opening_guard_v1.py",
    "astro_content_agent/tests/test_catstyle_aspect_source_truth_v1.py",
    "astro_content_agent/tests/test_catstyle_compensation_registry_v1.py",
    "astro_content_agent/tests/test_catstyle_sky_weather_stack_v1.py",
    "astro_content_agent/tests/test_catstyle_daily_agent_summary.py",
    "astro_content_agent/tests/test_catstyle_art_direction.py",
    "astro_content_agent/tests/test_catstyle_global_quality_lock_v1.py",
    "astro_content_agent/tests/test_catstyle_prompt_generator.py",
    "astro_content_agent/tests/test_catstyle_render_style_profiles_v1.py",
)

SECRET_TOKENS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "INSTAGRAM_ACCESS_TOKEN",
    "CLOUDINARY_API_SECRET",
    "sk-proj",
    "IGA",
    "CLOUDINARY_API_KEY",
    "API_SECRET",
)

MEDIA_WARN_SUBSTRINGS: tuple[str, ...] = (
    "references",
    "png",
    "approved_references",
    ".png",
)


def _run(
    args: list[str],
    *,
    cwd: Path,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def scan_diff_for_secrets(diff_text: str, tokens: tuple[str, ...] = SECRET_TOKENS) -> list[str]:
    """Return secret token names found in added diff lines only."""
    hits: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        for tok in tokens:
            if tok in line and tok not in seen:
                hits.append(tok)
                seen.add(tok)
    return hits


def scan_diff_for_media_warnings(
    diff_text: str,
    patterns: tuple[str, ...] = MEDIA_WARN_SUBSTRINGS,
) -> list[str]:
    """Return warning labels for diff paths/lines touching media or references."""
    warnings: list[str] = []
    seen: set[str] = set()
    for line in diff_text.splitlines():
        if not (line.startswith("+++") or line.startswith("---") or line.startswith("diff --git")):
            continue
        low = line.lower()
        for pat in patterns:
            if pat in low:
                label = f"{pat!r} in: {line.strip()}"
                if label not in seen:
                    warnings.append(label)
                    seen.add(label)
    return warnings


def run_pytest(repo_root: Path) -> tuple[bool, str]:
    args = [sys.executable, "-m", "pytest", "-q", *PYTEST_TARGETS]
    code, out, err = _run(args, cwd=repo_root)
    combined = (out + err).strip()
    return code == 0, combined


def git_diff(repo_root: Path) -> str:
    code, out, err = _run(["git", "diff"], cwd=repo_root)
    if code not in (0, 1):
        return (out + err).strip()
    return out


def git_status_short(repo_root: Path) -> str:
    code, out, err = _run(["git", "status", "--short"], cwd=repo_root)
    text = (out + err).strip()
    return text if code == 0 else f"(git status failed, exit {code})\n{text}"


def main() -> int:
    repo = REPO_ROOT
    print("Catstyle fast verify")
    print(f"  repo: {repo}")
    print()

    pytest_ok, pytest_log = run_pytest(repo)
    print("--- pytest (targeted) ---")
    print(pytest_log or "(no output)")
    print(f"pytest: {'PASS' if pytest_ok else 'FAIL'}")
    print()

    diff = git_diff(repo)
    secret_hits = scan_diff_for_secrets(diff)
    secrets_ok = not secret_hits
    print("--- secret check (git diff) ---")
    if secrets_ok:
        print("secret check: PASS (no forbidden tokens in diff)")
    else:
        print("secret check: FAIL")
        for tok in secret_hits:
            print(f"  - found: {tok}")
    print()

    media_warnings = scan_diff_for_media_warnings(diff)
    print("--- media/reference warning (git diff) ---")
    if media_warnings:
        print("media/reference: WARN")
        for w in media_warnings:
            print(f"  - {w}")
    else:
        print("media/reference: OK (no matching paths in diff)")
    print()

    status = git_status_short(repo)
    print("--- git status --short ---")
    print(status or "(clean)")
    print()

    print("=== summary ===")
    print(f"  pytest:              {'PASS' if pytest_ok else 'FAIL'}")
    print(f"  secret check:        {'PASS' if secrets_ok else 'FAIL'}")
    print(f"  media/reference:     {'WARN' if media_warnings else 'OK'}")
    print()

    if pytest_ok and secrets_ok:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
