"""Classification for Venus weekly real-publish failures."""
from __future__ import annotations

import httpx
import pytest

from astro_content_agent.services.content.venus_publish_failure import (
    classify_exception,
    classify_message,
    next_publish_attempt_count,
)
from astro_content_agent.services.instagram.publisher import PublisherService


def _http_error(code: int) -> httpx.HTTPStatusError:
    req = httpx.Request("GET", "https://graph.facebook.com/x")
    resp = httpx.Response(code, request=req)
    return httpx.HTTPStatusError("fail", request=req, response=resp)


def test_classify_503_retryable() -> None:
    c = classify_exception(_http_error(503))
    assert c.error_type == "meta_http_transient"
    assert c.publish_retryable is True


def test_classify_400_not_retryable() -> None:
    c = classify_exception(_http_error(400))
    assert c.error_type == "meta_http_client_error"
    assert c.publish_retryable is False


def test_classify_timeout_retryable() -> None:
    c = classify_exception(httpx.ReadTimeout("timeout"))
    assert c.error_type == "network_timeout"
    assert c.publish_retryable is True


def test_classify_draft_not_approved() -> None:
    c = classify_exception(PublisherService.DraftNotApprovedError("not approved"))
    assert c.error_type == "draft_not_approved"
    assert c.publish_retryable is False


def test_classify_message_unknown() -> None:
    c = classify_message("something weird from Meta")
    assert c.error_type == "unknown"
    assert c.publish_retryable is False


def test_next_publish_attempt_count_increments() -> None:
    state: dict = {
        "real_publish": {
            "publish_attempt_count": 2,
        }
    }
    assert next_publish_attempt_count(state) == 3
    assert next_publish_attempt_count({}) == 1


@pytest.mark.parametrize(
    "snippet,expected_type",
    [
        ("OAuthException", "meta_token_invalid"),
        ("access token", "meta_token_invalid"),
        ("image could not be accessed", "meta_media_fetch"),
    ],
)
def test_classify_message_token_and_media(snippet: str, expected_type: str) -> None:
    c = classify_message(snippet + " details here")
    assert c.error_type == expected_type
