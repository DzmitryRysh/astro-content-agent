"""Tests for repo-root ``.env`` loading and publish target resolution."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from astro_content_agent.core.repo_env import load_repo_dotenv_if_present, resolve_publish_target_ids


@pytest.fixture(autouse=True)
def _clear_aca_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACA_BRAND_PROFILE_ID", raising=False)
    monkeypatch.delenv("ACA_INSTAGRAM_ACCOUNT_ID", raising=False)


def test_load_repo_dotenv_sets_aca_ids_from_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bp = str(uuid.uuid4())
    ig = str(uuid.uuid4())
    (tmp_path / ".env").write_text(
        f"ACA_BRAND_PROFILE_ID={bp}\nACA_INSTAGRAM_ACCOUNT_ID={ig}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert load_repo_dotenv_if_present(tmp_path) is True
    assert os.environ.get("ACA_BRAND_PROFILE_ID") == bp
    assert os.environ.get("ACA_INSTAGRAM_ACCOUNT_ID") == ig


def test_resolve_publish_target_ids_reads_aca_from_env_after_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bp = str(uuid.uuid4())
    ig = str(uuid.uuid4())
    (tmp_path / ".env").write_text(
        f"ACA_BRAND_PROFILE_ID={bp}\nACA_INSTAGRAM_ACCOUNT_ID={ig}\n",
        encoding="utf-8",
    )
    assert load_repo_dotenv_if_present(tmp_path) is True
    out_bp, out_ig = resolve_publish_target_ids(cli_brand_profile_id=None, cli_instagram_account_id=None)
    assert out_bp == bp
    assert out_ig == ig


def test_resolve_publish_target_ids_cli_overrides_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_bp = str(uuid.uuid4())
    cli_bp = str(uuid.uuid4())
    ig = str(uuid.uuid4())
    (tmp_path / ".env").write_text(
        f"ACA_BRAND_PROFILE_ID={env_bp}\nACA_INSTAGRAM_ACCOUNT_ID={ig}\n",
        encoding="utf-8",
    )
    assert load_repo_dotenv_if_present(tmp_path) is True
    out_bp, out_ig = resolve_publish_target_ids(
        cli_brand_profile_id=cli_bp,
        cli_instagram_account_id=None,
    )
    assert out_bp == cli_bp
    assert out_ig == ig


def test_load_repo_dotenv_override_false_keeps_existing_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pre = str(uuid.uuid4())
    from_file = str(uuid.uuid4())
    monkeypatch.setenv("ACA_BRAND_PROFILE_ID", pre)
    (tmp_path / ".env").write_text(f"ACA_BRAND_PROFILE_ID={from_file}\n", encoding="utf-8")
    assert load_repo_dotenv_if_present(tmp_path, override=False) is True
    assert os.environ.get("ACA_BRAND_PROFILE_ID") == pre


def test_load_repo_dotenv_missing_file_is_noop(tmp_path: Path) -> None:
    empty = tmp_path / "no_dotenv_here"
    empty.mkdir()
    assert load_repo_dotenv_if_present(empty) is False


def test_load_repo_dotenv_does_not_print_secrets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
    (tmp_path / ".env").write_text(
        "ACA_BRAND_PROFILE_ID=x\nINSTAGRAM_ACCESS_TOKEN=topsecretvalue123\n",
        encoding="utf-8",
    )
    assert load_repo_dotenv_if_present(tmp_path) is True
    captured = capsys.readouterr()
    assert "topsecretvalue123" not in captured.out
    assert "topsecretvalue123" not in captured.err
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
