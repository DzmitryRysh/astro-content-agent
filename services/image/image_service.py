from __future__ import annotations

import io
from datetime import UTC, datetime

from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from astro_content_agent.db.models import Asset, Draft
from astro_content_agent.repositories.assets import AssetRepository
from astro_content_agent.services.media.storage import StorageBackend


class ImageGenerationService:
    """Placeholder image generator — Phase 4/8 stub.

    Produces a solid-colour 1080x1080 PNG with the draft type and ID overlaid.
    Uses a ``StorageBackend`` so the storage layer is decoupled from image
    generation; swap the backend instance for S3/GCS without touching this class.

    Swap the generation logic with a real DALL-E / Flux / Stable Diffusion
    call in a later phase.
    """

    def generate_placeholder(
        self,
        *,
        db: Session,
        draft: Draft,
        storage: StorageBackend,
    ) -> Asset:
        """Generate a placeholder PNG and persist it as an Asset record.

        The ``storage_path`` stored on the returned Asset is the *relative key*
        (e.g. ``{brand_id}/{draft_id}/placeholder.png``), NOT an absolute path.
        This keeps the design storage-backend-agnostic.
        """
        key = f"{draft.brand_profile_id}/{draft.id}/placeholder.png"

        img = Image.new("RGB", (1080, 1080), color=(100, 70, 150))
        draw = ImageDraw.Draw(img)
        draw.text((60, 490), f"[ {draft.draft_type.upper()} DRAFT ]", fill=(255, 255, 255))
        draw.text((60, 530), f"id: {draft.id[:16]}...", fill=(200, 200, 200))

        buf = io.BytesIO()
        img.save(buf, "PNG")
        storage_key = storage.save(key, buf.getvalue(), content_type="image/png")

        repo = AssetRepository()
        asset = repo.create(
            db,
            brand_profile_id=draft.brand_profile_id,
            draft_id=draft.id,
            asset_type="image",
            storage_path=storage_key,
            mime_type="image/png",
            width=1080,
            height=1080,
            meta={
                "generated_at": datetime.now(UTC).isoformat(),
                "kind": "placeholder",
            },
        )
        db.commit()
        db.refresh(asset)
        return asset
