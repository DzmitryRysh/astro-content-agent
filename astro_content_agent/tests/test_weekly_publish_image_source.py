"""Unit tests for Venus weekly publish CLI image source exclusivity."""
from __future__ import annotations

from pathlib import Path

import pytest

from astro_content_agent.services.content.weekly_publish_image_source import weekly_publish_image_mode


def test_weekly_publish_image_mode_url_only() -> None:
    assert weekly_publish_image_mode(post_image_url="https://x/y.jpg", post_image_storage_key=None, post_image_path=None) == "url"


def test_weekly_publish_image_mode_storage_key_only() -> None:
    assert weekly_publish_image_mode(post_image_url=None, post_image_storage_key="a/b.png", post_image_path=None) == "storage_key"


def test_weekly_publish_image_mode_path_only() -> None:
    assert weekly_publish_image_mode(post_image_url=None, post_image_storage_key=None, post_image_path=Path("z.jpg")) == "path"


def test_weekly_publish_image_mode_none_raises() -> None:
    with pytest.raises(ValueError, match="Missing image source"):
        weekly_publish_image_mode(post_image_url=None, post_image_storage_key=None, post_image_path=None)


def test_weekly_publish_image_mode_url_and_path_raises() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        weekly_publish_image_mode(
            post_image_url="https://x",
            post_image_storage_key=None,
            post_image_path="local.jpg",
        )


def test_weekly_publish_image_mode_path_and_storage_raises() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        weekly_publish_image_mode(
            post_image_url=None,
            post_image_storage_key="k/x.png",
            post_image_path="/tmp/y.jpg",
        )


def test_weekly_publish_image_mode_all_three_raises() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        weekly_publish_image_mode(
            post_image_url="https://x",
            post_image_storage_key="k",
            post_image_path="p",
        )
