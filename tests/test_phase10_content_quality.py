from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile, ContentPlan, Draft
from astro_content_agent.repositories.drafts import DraftRepository
from astro_content_agent.schemas.drafts import PostDraftPayload, ReelDraftPayload
from astro_content_agent.schemas.strategy import DayPlanItem, DayPlanPayload
from astro_content_agent.services.content.anti_repeat import AntiRepeatContext
from astro_content_agent.services.content.persona import PersonaContext
from astro_content_agent.services.content.pillar_balancer import ContentPillarBalancer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_brand(
    db: Session,
    *,
    tone_preset: str = "educational_warm",
    face_led_preferred: bool = False,
) -> BrandProfile:
    bp = BrandProfile(
        id=str(uuid.uuid4()),
        name="Test Brand",
        tone_preset=tone_preset,
        face_led_preferred=int(face_led_preferred),
    )
    db.add(bp)
    db.commit()
    db.refresh(bp)
    return bp


def _make_draft_with_payload(db: Session, brand_profile_id: str, payload: dict) -> Draft:
    repo = DraftRepository()
    d = repo.create(
        db,
        brand_profile_id=brand_profile_id,
        content_plan_id=None,
        draft_type="post",
        text=payload.get("caption", ""),
        payload=payload,
    )
    db.commit()
    db.refresh(d)
    return d


def _make_content_plan_with_pillars(
    db: Session, brand_profile_id: str, pillars: list[str]
) -> ContentPlan:
    items = [
        {"slot": i + 1, "format": "post", "primary_angle": f"angle {i}", "creative_brief": "brief", "content_pillar": p}
        for i, p in enumerate(pillars)
    ]
    plan = ContentPlan(
        id=str(uuid.uuid4()),
        brand_profile_id=brand_profile_id,
        plan_date="2026-03-20",
        payload={"day": "2026-03-20", "items": items, "notes": []},
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# ---------------------------------------------------------------------------
# PersonaContext
# ---------------------------------------------------------------------------


def _fake_brand(tone_preset: str | None, face_led_preferred: int = 0) -> SimpleNamespace:
    """Return a SimpleNamespace that quacks like a BrandProfile for PersonaContext tests.

    Explicitly uses content_language="en" so these English-first unit tests
    continue to verify the English preset registry (not the Russian registry,
    which is now the system default when content_language is absent).
    """
    return SimpleNamespace(
        tone_preset=tone_preset,
        face_led_preferred=face_led_preferred,
        content_language="en",
    )


def test_persona_context_known_preset() -> None:
    persona = PersonaContext.from_brand(_fake_brand("educational_warm"))  # type: ignore[arg-type]
    assert "clear" in persona.voice_descriptors
    assert "warm" in persona.voice_descriptors
    assert persona.preferred_format is None


def test_persona_context_empowering_preset() -> None:
    persona = PersonaContext.from_brand(_fake_brand("empowering"))  # type: ignore[arg-type]
    assert "bold" in persona.voice_descriptors
    assert "direct" in persona.voice_descriptors


def test_persona_context_unknown_preset_falls_back_to_default() -> None:
    persona = PersonaContext.from_brand(_fake_brand("totally-unknown-preset"))  # type: ignore[arg-type]
    assert "clear" in persona.voice_descriptors
    assert len(persona.content_dos) > 0


def test_persona_context_no_preset_falls_back_to_default() -> None:
    persona = PersonaContext.from_brand(_fake_brand(None))  # type: ignore[arg-type]
    assert persona.preferred_format is None
    assert len(persona.voice_descriptors) > 0


def test_persona_context_face_led_sets_preferred_format() -> None:
    persona = PersonaContext.from_brand(_fake_brand("empowering", face_led_preferred=1))  # type: ignore[arg-type]
    assert persona.preferred_format == "face_led"


def test_persona_context_prompt_hint_contains_voice() -> None:
    persona = PersonaContext.from_brand(_fake_brand("conversational"))  # type: ignore[arg-type]
    hint = persona.to_prompt_hint()
    assert "Voice:" in hint
    assert "Tone guidance:" in hint
    assert "Content DOs:" in hint
    assert "Content DON'Ts:" in hint


def test_persona_context_prompt_hint_mentions_face_led_when_set() -> None:
    persona = PersonaContext.from_brand(_fake_brand("empowering", face_led_preferred=1))  # type: ignore[arg-type]
    hint = persona.to_prompt_hint()
    assert "face_led" in hint or "face-led" in hint


# ---------------------------------------------------------------------------
# AntiRepeatContext
# ---------------------------------------------------------------------------


def test_anti_repeat_empty_history(db_session: Session, brand_profile) -> None:
    ctx = AntiRepeatContext.from_recent_drafts(db_session, brand_profile.id, limit=7)
    assert ctx.recent_hooks == []
    assert ctx.recent_ctas == []
    hint = ctx.to_prompt_hint()
    assert "fresh slate" in hint.lower() or "no recent" in hint.lower()


def test_anti_repeat_extracts_hooks_from_recent_drafts(db_session: Session, brand_profile) -> None:
    _make_draft_with_payload(
        db_session, brand_profile.id,
        {"hook": "The stars are calling you today.", "caption": "...", "cta": "Save this."},
    )
    _make_draft_with_payload(
        db_session, brand_profile.id,
        {"hook": "Your intuition is your compass.", "caption": "...", "cta": "Comment below."},
    )

    ctx = AntiRepeatContext.from_recent_drafts(db_session, brand_profile.id, limit=7)
    assert len(ctx.recent_hooks) == 2
    assert any("stars" in h.lower() for h in ctx.recent_hooks)


def test_anti_repeat_extracts_ctas(db_session: Session, brand_profile) -> None:
    _make_draft_with_payload(
        db_session, brand_profile.id,
        {"hook": "Hook A", "caption": "...", "cta": "Save this for later."},
    )
    ctx = AntiRepeatContext.from_recent_drafts(db_session, brand_profile.id, limit=7)
    assert "Save this for later." in ctx.recent_ctas


def test_anti_repeat_hook_repetition_detection() -> None:
    ctx = AntiRepeatContext(
        recent_hooks=["The stars are aligned today.", "Your energy is powerful."],
        recent_ctas=[],
        recent_angles=[],
    )
    # Same first 4 words → repetitive
    assert ctx.is_hook_repetitive("The stars are aligned right now") is True
    # Different opener → not repetitive
    assert ctx.is_hook_repetitive("If your brain feels loud") is False


def test_anti_repeat_weak_hook_detection() -> None:
    ctx = AntiRepeatContext()
    assert ctx.is_hook_weak("The stars are telling you something important") is True
    assert ctx.is_hook_weak("Mercury is retrograde again") is True
    assert ctx.is_hook_weak("Today's energy is really something") is True
    assert ctx.is_hook_weak("Your bank account called. It wants boundaries.") is False


def test_anti_repeat_prompt_hint_lists_recent_hooks(db_session: Session, brand_profile) -> None:
    _make_draft_with_payload(
        db_session, brand_profile.id,
        {"hook": "The universe is speaking.", "caption": "...", "cta": "Follow."},
    )
    ctx = AntiRepeatContext.from_recent_drafts(db_session, brand_profile.id, limit=7)
    hint = ctx.to_prompt_hint()
    assert "universe" in hint.lower()
    assert "DO NOT repeat" in hint or "AVOID" in hint.upper()


def test_anti_repeat_respects_limit(db_session: Session, brand_profile) -> None:
    for i in range(10):
        _make_draft_with_payload(
            db_session, brand_profile.id,
            {"hook": f"Hook number {i}", "caption": "...", "cta": f"CTA {i}"},
        )
    ctx = AntiRepeatContext.from_recent_drafts(db_session, brand_profile.id, limit=5)
    assert len(ctx.recent_hooks) <= 5


# ---------------------------------------------------------------------------
# ContentPillarBalancer
# ---------------------------------------------------------------------------


def test_pillar_balancer_empty_db_returns_empty_usage(db_session: Session, brand_profile) -> None:
    balancer = ContentPillarBalancer()
    usage = balancer.get_recent_pillar_usage(db_session, brand_profile.id, days=14)
    assert usage == {}


def test_pillar_balancer_counts_recent_pillar_usage(db_session: Session, brand_profile) -> None:
    _make_content_plan_with_pillars(db_session, brand_profile.id, ["Education", "Education", "Motivation"])
    balancer = ContentPillarBalancer()
    usage = balancer.get_recent_pillar_usage(db_session, brand_profile.id, days=14)
    assert usage.get("Education", 0) == 2
    assert usage.get("Motivation", 0) == 1


def test_pillar_balancer_suggests_underused_pillar() -> None:
    balancer = ContentPillarBalancer()
    usage = {"Education": 5, "Motivation": 2, "Ritual": 0}
    result = balancer.get_underused_pillar(["Education", "Motivation", "Ritual"], usage)
    assert result == "Ritual"


def test_pillar_balancer_handles_empty_pillar_list() -> None:
    balancer = ContentPillarBalancer()
    assert balancer.get_underused_pillar([], {}) is None


def test_pillar_balancer_prompt_hint_format() -> None:
    balancer = ContentPillarBalancer()
    usage = {"Education": 3, "Motivation": 1}
    hint = balancer.to_prompt_hint(usage, ["Education", "Motivation", "Ritual"])
    assert "Education" in hint
    assert "Ritual" in hint
    assert "Ritual" in hint  # zero usage → should recommend it


def test_pillar_balancer_prompt_hint_recommends_underused() -> None:
    balancer = ContentPillarBalancer()
    usage = {"Education": 5, "Ritual": 0}
    hint = balancer.to_prompt_hint(usage, ["Education", "Ritual"])
    assert "Ritual" in hint
    assert "prioritis" in hint.lower() or "recommend" in hint.lower()


# ---------------------------------------------------------------------------
# Schema: new fields
# ---------------------------------------------------------------------------


def test_day_plan_item_accepts_new_fields() -> None:
    item = DayPlanItem(
        slot=1,
        format="post",
        primary_angle="empowerment angle",
        creative_brief="Write with confidence",
        content_pillar="Motivation",
        face_led_preference=True,
    )
    assert item.content_pillar == "Motivation"
    assert item.face_led_preference is True


def test_day_plan_item_new_fields_default_to_none() -> None:
    item = DayPlanItem(slot=1, format="reel", primary_angle="angle", creative_brief="brief")
    assert item.content_pillar is None
    assert item.face_led_preference is None


def test_post_draft_payload_accepts_voice_note() -> None:
    p = PostDraftPayload(
        title="T",
        hook="H",
        caption="C",
        cta="CTA",
        voice_note="Warm and direct tone used intentionally.",
    )
    assert p.voice_note == "Warm and direct tone used intentionally."


def test_post_draft_payload_voice_note_optional() -> None:
    p = PostDraftPayload(title="T", hook="H", caption="C", cta="CTA")
    assert p.voice_note is None


def test_reel_draft_payload_requires_hook_0_3s() -> None:
    import pytest
    with pytest.raises(Exception):
        # Missing hook_0_3s should raise validation error
        ReelDraftPayload(
            hook="Full hook line",
            reel_type="talking_head",
            script="Script here",
            cta="Follow",
        )


def test_reel_draft_payload_accepts_hook_0_3s() -> None:
    p = ReelDraftPayload(
        hook_0_3s="Stop what you're doing.",
        hook="Stop what you're doing — this changes everything.",
        reel_type="talking_head",
        script="Here's the insight...",
        cta="Save this.",
    )
    assert p.hook_0_3s == "Stop what you're doing."
    assert p.hook != p.hook_0_3s


# ---------------------------------------------------------------------------
# BrandProfile: face_led_preferred
# ---------------------------------------------------------------------------


def test_brand_profile_face_led_preferred_default(db_session: Session) -> None:
    from astro_content_agent.repositories.brand_profiles import BrandProfileRepository

    repo = BrandProfileRepository()
    bp = repo.create(db_session, name="Default Brand")
    db_session.commit()
    db_session.refresh(bp)
    assert bp.face_led_preferred == 0


def test_brand_profile_face_led_preferred_true(db_session: Session) -> None:
    from astro_content_agent.repositories.brand_profiles import BrandProfileRepository

    repo = BrandProfileRepository()
    bp = repo.create(db_session, name="Face Brand", face_led_preferred=True)
    db_session.commit()
    db_session.refresh(bp)
    assert bp.face_led_preferred == 1


def test_brand_profile_admin_schema_face_led(db_session: Session) -> None:
    """face_led_preferred round-trips through admin schema."""
    from datetime import UTC, datetime
    from astro_content_agent.schemas.admin import BrandProfileResponse

    brand = SimpleNamespace(
        id=str(uuid.uuid4()),
        name="Test",
        description=None,
        tone_preset=None,
        banned_terms=[],
        default_hashtags=[],
        face_led_preferred=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    resp = BrandProfileResponse.from_orm_model(brand)
    assert resp.face_led_preferred is True
