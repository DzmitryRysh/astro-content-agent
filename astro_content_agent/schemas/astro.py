from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AspectPolarity = Literal["harmonious", "tense", "neutral"]

# foreground: suitable as today's content hook (inner-planet involvement or tight orb)
# background: slow outer-planet structural context; real but should not lead the hook
SignalClass = Literal["foreground", "background"]

# Canonical polarity for each standard aspect type.
ASPECT_POLARITY_MAP: dict[str, AspectPolarity] = {
    "sextile": "harmonious",
    "trine": "harmonious",
    "square": "tense",
    "opposition": "tense",
    "conjunct": "neutral",
    "conjunction": "neutral",
}


def aspect_polarity_from_key(signal_key: str) -> AspectPolarity | None:
    """Derive polarity from a signal key string such as 'venus-sextile-mercury'."""
    for aspect, polarity in ASPECT_POLARITY_MAP.items():
        if f"-{aspect}-" in signal_key or signal_key.startswith(f"{aspect}-"):
            return polarity
    return None


class TransitSignal(BaseModel):
    key: str
    headline: str
    summary: str
    intensity: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    recommended_formats: list[str] = Field(default_factory=list)
    content_angles: list[str] = Field(default_factory=list)
    guardrails: dict[str, Any] = Field(default_factory=dict)
    # Aspect polarity: set by the engine; used by prompt layer for correct framing.
    aspect_polarity: AspectPolarity | None = None
    # V1 engine enrichment fields — None for V0 stub signals.
    planet1_sign: str | None = None
    planet2_sign: str | None = None
    orb: float | None = None            # degrees from exact aspect angle
    planet1_retrograde: bool | None = None
    planet2_retrograde: bool | None = None
    # Content classification: foreground = daily hook candidate,
    # background = structural context.  Defaults to "foreground" so that V0
    # stub signals and legacy DB records remain fully backward-compatible.
    signal_class: SignalClass = "foreground"


class AstroDayPayload(BaseModel):
    day: date
    engine_version: str
    generated_at: datetime
    signals: list[TransitSignal]

    @property
    def foreground_signals(self) -> list[TransitSignal]:
        """Signals suitable as daily content hooks (inner planet or tight orb)."""
        return [s for s in self.signals if s.signal_class == "foreground"]

    @property
    def background_signals(self) -> list[TransitSignal]:
        """Structural outer-planet aspects useful as thematic context."""
        return [s for s in self.signals if s.signal_class == "background"]


class AstroCalculateDayRequest(BaseModel):
    brand_profile_id: str
    day: date


class AstroSignalRecordResponse(BaseModel):
    id: str
    brand_profile_id: str
    signal_date: str
    engine_version: str
    payload: AstroDayPayload

    @classmethod
    def from_orm_model(cls, rec: Any) -> "AstroSignalRecordResponse":
        # `rec` is a SQLAlchemy model; keep this tiny and explicit.
        return cls(
            id=rec.id,
            brand_profile_id=rec.brand_profile_id,
            signal_date=rec.signal_date,
            engine_version=rec.engine_version,
            payload=AstroDayPayload.model_validate(rec.payload),
        )

