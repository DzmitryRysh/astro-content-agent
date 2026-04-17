from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from astro_content_agent.db.models import Draft

# Weak hook openers that indicate generic, repetitive patterns.
_WEAK_HOOK_PATTERNS = [
    r"^the (stars|planets|cosmos|universe) (are|have|say)",
    r"^mercury (is|goes) retrograde",
    r"^today('s)? energy",
    r"^this (week|month|season)",
    r"^it's (a )?(big|powerful|intense|strong|wild)",
    r"^the (energy|vibe) (today|right now)",
]
_WEAK_HOOK_RE = [re.compile(p, re.IGNORECASE) for p in _WEAK_HOOK_PATTERNS]


@dataclass(frozen=True)
class AntiRepeatContext:
    """Extracts recent hook/CTA/angle patterns from draft history to drive anti-repeat logic.

    Designed to be injected into AI prompt inputs so the model explicitly avoids
    repeating structures that have already been used recently.
    """

    recent_hooks: list[str] = field(default_factory=list)
    recent_ctas: list[str] = field(default_factory=list)
    recent_angles: list[str] = field(default_factory=list)

    @classmethod
    def from_recent_drafts(
        cls,
        db: Session,
        brand_profile_id: str,
        *,
        limit: int = 7,
    ) -> "AntiRepeatContext":
        """Query recent drafts and extract hook/CTA/angle patterns."""
        stmt = (
            select(Draft)
            .where(
                Draft.brand_profile_id == brand_profile_id,
                Draft.draft_type.in_(["post", "reel"]),
            )
            .order_by(Draft.created_at.desc())
            .limit(limit)
        )
        drafts = list(db.execute(stmt).scalars().all())

        hooks: list[str] = []
        ctas: list[str] = []
        angles: list[str] = []

        for d in drafts:
            payload = d.payload or {}
            if h := payload.get("hook"):
                hooks.append(str(h))
            if c := payload.get("cta"):
                ctas.append(str(c))
            meta = payload.get("metadata") or {}
            if a := meta.get("primary_angle") or meta.get("angle"):
                angles.append(str(a))

        return cls(recent_hooks=hooks, recent_ctas=ctas, recent_angles=angles)

    def is_hook_weak(self, hook: str) -> bool:
        """Return True if the hook matches a known weak/generic opener pattern."""
        return any(rx.search(hook) for rx in _WEAK_HOOK_RE)

    def is_hook_repetitive(self, hook: str, *, similarity_words: int = 4) -> bool:
        """Return True if the first N words of *hook* match any recent hook."""
        candidate_words = hook.lower().split()[:similarity_words]
        if not candidate_words:
            return False
        for recent in self.recent_hooks:
            recent_words = recent.lower().split()[:similarity_words]
            if candidate_words == recent_words:
                return True
        return False

    def to_prompt_hint(self) -> str:
        """Format as a human-readable anti-repeat block for prompt injection."""
        parts: list[str] = []
        if self.recent_hooks:
            parts.append("Recently used hook openings (DO NOT repeat these structures):")
            for h in self.recent_hooks[:5]:
                parts.append(f"  - {h[:120]}")
        if self.recent_ctas:
            parts.append("Recently used CTAs (vary these, avoid verbatim repeats):")
            for c in self.recent_ctas[:3]:
                parts.append(f"  - {c[:80]}")
        if self.recent_angles:
            parts.append("Recently used angles (prefer a different primary angle):")
            for a in self.recent_angles[:3]:
                parts.append(f"  - {a[:80]}")
        if not parts:
            return "No recent draft history — fresh slate, all angles are fair game."
        return "\n".join(parts)
