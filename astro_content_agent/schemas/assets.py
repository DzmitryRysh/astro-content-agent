from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AssetResponse(BaseModel):
    id: str
    brand_profile_id: str
    draft_id: str | None
    asset_type: str
    storage_path: str
    public_url: str | None = None
    mime_type: str | None
    width: int | None
    height: int | None
    meta: dict[str, Any] | None

    @classmethod
    def from_orm_model(cls, rec: Any, *, public_url: str | None = None) -> "AssetResponse":
        return cls(
            id=rec.id,
            brand_profile_id=rec.brand_profile_id,
            draft_id=rec.draft_id,
            asset_type=rec.asset_type,
            storage_path=rec.storage_path,
            public_url=public_url,
            mime_type=rec.mime_type,
            width=rec.width,
            height=rec.height,
            meta=rec.meta,
        )
