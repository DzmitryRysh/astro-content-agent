from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from astro_content_agent.db.models import Asset, Draft
from astro_content_agent.schemas.drafts import PostDraftPayload


@dataclass(frozen=True)
class ContainerParams:
    """Parameters required to create an IG media container."""

    image_url: str
    caption: str


class ContainerBuilder:
    """Translates a draft + asset into IG container creation parameters.

    Args:
        url_resolver: Callable that converts a storage key (``asset.storage_path``)
            into a publicly accessible URL.  Defaults to the identity function
            (returns the key unchanged) for backward compatibility and testing.

            In production, inject ``LocalFileStorage.url`` or an S3-signed-URL
            function so that ``image_url`` in ``ContainerParams`` is always a
            real HTTPS URL that Instagram can fetch.
    """

    SUPPORTED_DRAFT_TYPES = frozenset({"post"})

    def __init__(self, url_resolver: Callable[[str], str] | None = None) -> None:
        self._url_resolver: Callable[[str], str] = url_resolver or (lambda key: key)

    def build(self, *, draft: Draft, asset: Asset) -> ContainerParams:
        if draft.draft_type not in self.SUPPORTED_DRAFT_TYPES:
            raise ValueError(
                f"Publishing not supported for draft_type='{draft.draft_type}' in MVP. "
                "Only 'post' (image) is publishable."
            )
        if asset.mime_type not in (None, "image/png", "image/jpeg", "image/jpg"):
            raise ValueError(f"Unsupported asset mime_type: {asset.mime_type}")

        payload = PostDraftPayload.model_validate(draft.payload or {})
        hashtags_str = " ".join(payload.hashtags) if payload.hashtags else ""
        caption_parts = [payload.caption]
        if payload.cta:
            caption_parts.append(payload.cta)
        if hashtags_str:
            caption_parts.append(hashtags_str)
        caption = "\n\n".join(caption_parts)

        return ContainerParams(
            image_url=self._url_resolver(asset.storage_path),
            caption=caption,
        )
