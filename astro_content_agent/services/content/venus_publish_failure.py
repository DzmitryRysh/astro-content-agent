"""Classify Venus weekly real-publish failures for explicit retry vs fix-first behavior.

``PublisherService`` may perform bounded ``media_publish`` retries for Meta
code ``9007`` / subcode ``2207027`` (container not ready) before surfacing a
failure; this module classifies the final exception / error string for operator
judgment and state artifacts. There is no additional automatic retry loop at
the Venus weekly orchestration layer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from astro_content_agent.services.instagram.publisher import PublisherService
from astro_content_agent.services.instagram.client import MetaAPIError


@dataclass(frozen=True)
class PublishFailureClassification:
    """How to interpret a failure for the next *manual* publish attempt."""

    error_type: str
    publish_retryable: bool
    message: str


def classify_exception(exc: BaseException) -> PublishFailureClassification:
    """Best-effort classification from an exception raised during publish."""
    msg = str(exc).strip() or type(exc).__name__

    if isinstance(exc, PublisherService.DraftNotApprovedError):
        return PublishFailureClassification(
            error_type="draft_not_approved",
            publish_retryable=False,
            message=msg,
        )
    if isinstance(exc, PublisherService.DraftNotFoundError):
        return PublishFailureClassification(
            error_type="draft_not_found",
            publish_retryable=False,
            message=msg,
        )
    if isinstance(exc, PublisherService.AccountNotFoundError):
        return PublishFailureClassification(
            error_type="missing_instagram_account",
            publish_retryable=False,
            message=msg,
        )

    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout)):
        return PublishFailureClassification(
            error_type="network_timeout",
            publish_retryable=True,
            message=msg,
        )
    if isinstance(exc, (httpx.ConnectError, httpx.RemoteProtocolError, httpx.NetworkError)):
        return PublishFailureClassification(
            error_type="network_error",
            publish_retryable=True,
            message=msg,
        )

    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code in (429, 500, 502, 503, 504):
            return PublishFailureClassification(
                error_type="meta_http_transient",
                publish_retryable=True,
                message=f"HTTP {code}: {msg}",
            )
        if code == 401 or code == 403:
            return PublishFailureClassification(
                error_type="meta_auth_forbidden",
                publish_retryable=False,
                message=f"HTTP {code}: {msg}",
            )
        if 400 <= code < 500:
            return PublishFailureClassification(
                error_type="meta_http_client_error",
                publish_retryable=False,
                message=f"HTTP {code}: {msg}",
            )
        return PublishFailureClassification(
            error_type="meta_http_error",
            publish_retryable=code >= 500,
            message=f"HTTP {code}: {msg}",
        )
    if isinstance(exc, MetaAPIError):
        if exc.meta_error_code == 9007:
            try:
                sub = int(exc.meta_error_subcode) if exc.meta_error_subcode is not None else None
            except (TypeError, ValueError):
                sub = None
            if sub == 2207027:
                return PublishFailureClassification(
                    error_type="meta_container_not_ready",
                    publish_retryable=True,
                    message=str(exc),
                )
        code = int(exc.status_code)
        if code in (429, 500, 502, 503, 504):
            return PublishFailureClassification(
                error_type="meta_http_transient",
                publish_retryable=True,
                message=str(exc),
            )
        if code in (401, 403):
            return PublishFailureClassification(
                error_type="meta_auth_forbidden",
                publish_retryable=False,
                message=str(exc),
            )
        if 400 <= code < 500:
            return PublishFailureClassification(
                error_type="meta_http_client_error",
                publish_retryable=False,
                message=str(exc),
            )
        return PublishFailureClassification(
            error_type="meta_http_error",
            publish_retryable=code >= 500,
            message=str(exc),
        )

    if isinstance(exc, ValueError):
        low = msg.lower()
        if "no assets" in low or "draft not found" in low or "must be approved" in low:
            return PublishFailureClassification(
                error_type="publisher_validation",
                publish_retryable=False,
                message=msg,
            )
        if "unsupported" in low and "mime" in low:
            return PublishFailureClassification(
                error_type="invalid_media_payload",
                publish_retryable=False,
                message=msg,
            )
        if "not found on disk" in low or "storage key" in low:
            return PublishFailureClassification(
                error_type="missing_media_asset",
                publish_retryable=False,
                message=msg,
            )
        if "handoff has no post" in low:
            return PublishFailureClassification(
                error_type="invalid_handoff_payload",
                publish_retryable=False,
                message=msg,
            )
        if "unexpected ig response" in low:
            return PublishFailureClassification(
                error_type="meta_response_validation",
                publish_retryable=False,
                message=msg,
            )

    low = msg.lower()
    if "oauth" in low or "access token" in low or "invalid token" in low or "session has been invalidated" in low:
        return PublishFailureClassification(
            error_type="meta_token_invalid",
            publish_retryable=False,
            message=msg,
        )
    if "image" in low and ("download" in low or "could not be accessed" in low or "url" in low):
        return PublishFailureClassification(
            error_type="meta_media_fetch",
            publish_retryable=True,
            message=msg,
        )
    if re.search(r"\b5\d\d\b", msg):
        return PublishFailureClassification(
            error_type="meta_transient_hint",
            publish_retryable=True,
            message=msg,
        )

    return PublishFailureClassification(
        error_type="unknown",
        publish_retryable=False,
        message=msg,
    )


def classify_message(message: str | None) -> PublishFailureClassification:
    """Classify when only the publisher error string is available (no exception type)."""
    if not message:
        return PublishFailureClassification(
            error_type="unknown",
            publish_retryable=False,
            message="(empty error)",
        )
    return classify_exception(RuntimeError(message))


def classify_publish_result_meta(
    *,
    error: str | None,
    meta_error: dict | None,
) -> PublishFailureClassification:
    """Classify a failed ``PublishResult`` using structured Meta fields when present."""
    if meta_error and isinstance(meta_error, dict):
        raw_code = meta_error.get("meta_error_code")
        raw_sub = meta_error.get("meta_error_subcode")
        try:
            c = int(raw_code) if raw_code is not None else None
            s = int(raw_sub) if raw_sub is not None else None
        except (TypeError, ValueError):
            c, s = None, None
        st_raw = meta_error.get("meta_status_code")
        try:
            st = int(st_raw) if st_raw is not None else 400
        except (TypeError, ValueError):
            st = 400
        url = meta_error.get("meta_url")
        body = meta_error.get("meta_error_body")
        j = meta_error.get("meta_error_json")
        syn = MetaAPIError(
            status_code=st,
            url=str(url) if isinstance(url, str) else "https://graph.instagram.com/<redacted>",
            response_text=str(body) if body is not None else "",
            response_json=j if isinstance(j, (dict, list)) else None,
            meta_error_code=c,
            meta_error_subcode=s,
            meta_error_type=meta_error.get("meta_error_type") if isinstance(meta_error.get("meta_error_type"), str) else None,
            meta_error_message=meta_error.get("meta_error_message")
            if isinstance(meta_error.get("meta_error_message"), str)
            else None,
        )
        return classify_exception(syn)
    return classify_message(error or "")


def next_publish_attempt_count(state: dict[str, Any]) -> int:
    """1-based attempt index for the next run (counts prior recorded outcomes)."""
    rp = state.get("real_publish")
    if not isinstance(rp, dict):
        return 1
    prev = rp.get("publish_attempt_count")
    try:
        n = int(prev) if prev is not None else 0
    except (TypeError, ValueError):
        n = 0
    return max(1, n + 1)


__all__ = [
    "PublishFailureClassification",
    "classify_exception",
    "classify_message",
    "classify_publish_result_meta",
    "next_publish_attempt_count",
]
