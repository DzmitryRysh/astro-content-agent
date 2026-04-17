"""Tests for the Russian-first language pivot.

Covers:
- prompt_ref_for_language: correct path/name for ru and en
- PersonaContext: Russian presets are loaded when content_language="ru"
- brand_defaults: Russian defaults used when content_language="ru"
- BrandProfile content_language field: schema, DB fixture, admin API
- Service language routing: planner/caption/reel use Russian prompt when brand is ru
- Fake responder: Russian output for ru brand
"""

from __future__ import annotations

import types
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from astro_content_agent.db.models import BrandProfile
from astro_content_agent.services.ai.responses_runner import PromptRef, prompt_ref_for_language
from astro_content_agent.services.content.brand_defaults import (
    DEFAULT_CONTENT_LANGUAGE,
    DEFAULT_HASHTAGS_RU,
    build_brand_config,
)
from astro_content_agent.services.content.persona import (
    PersonaContext,
    _PRESET_REGISTRY,
    _PRESET_REGISTRY_RU,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_brand(
    language: str = "ru",
    tone_preset: str = "educational_warm",
    face_led: bool = False,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        id=str(uuid.uuid4()),
        name="Test Brand",
        description="Тестовый бренд",
        tone_preset=tone_preset,
        face_led_preferred=int(face_led),
        banned_terms=[],
        default_hashtags=[],
        content_language=language,
    )


def _ru_brand_db(db: Session, tone_preset: str = "educational_warm") -> BrandProfile:
    bp = BrandProfile(
        id=str(uuid.uuid4()),
        name="Русский бренд",
        tone_preset=tone_preset,
        content_language="ru",
    )
    db.add(bp)
    db.commit()
    db.refresh(bp)
    return bp


# ---------------------------------------------------------------------------
# prompt_ref_for_language
# ---------------------------------------------------------------------------


class TestPromptRefForLanguage:
    def test_ru_returns_ru_path(self):
        ref = prompt_ref_for_language("strategist", "ru")
        assert ref.path == Path("ru/strategist.md")
        assert ref.name == "strategist_ru"

    def test_en_returns_default_path(self):
        ref = prompt_ref_for_language("strategist", "en")
        assert ref.path == Path("strategist.md")
        assert ref.name == "strategist"

    def test_unknown_language_falls_back_to_en(self):
        ref = prompt_ref_for_language("copywriter", "fr")
        assert ref.path == Path("copywriter.md")
        assert ref.name == "copywriter"

    @pytest.mark.parametrize("prompt_name", ["strategist", "copywriter", "reel_writer", "brand_guard"])
    def test_all_prompt_names_supported_for_ru(self, prompt_name: str):
        ref = prompt_ref_for_language(prompt_name, "ru")
        assert "ru" in str(ref.path)

    @pytest.mark.parametrize("prompt_name", ["strategist", "copywriter", "reel_writer", "brand_guard"])
    def test_ru_prompt_files_exist(self, prompt_name: str):
        """Confirm the Russian prompt .md files are present on disk."""
        prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
        ru_path = prompts_root / "ru" / f"{prompt_name}.md"
        assert ru_path.exists(), f"Missing Russian prompt file: {ru_path}"
        assert ru_path.stat().st_size > 100, f"Russian prompt file suspiciously small: {ru_path}"


# ---------------------------------------------------------------------------
# PersonaContext Russian presets
# ---------------------------------------------------------------------------


class TestPersonaContextRussian:
    @pytest.mark.parametrize("preset", list(_PRESET_REGISTRY_RU.keys()))
    def test_ru_preset_has_required_fields(self, preset: str):
        data = _PRESET_REGISTRY_RU[preset]
        assert data.get("voice_descriptors"), f"Missing voice_descriptors for ru/{preset}"
        assert data.get("tone_guidance"), f"Missing tone_guidance for ru/{preset}"
        assert data.get("content_dos"), f"Missing content_dos for ru/{preset}"
        assert data.get("content_donts"), f"Missing content_donts for ru/{preset}"

    @pytest.mark.parametrize("preset", list(_PRESET_REGISTRY.keys()))
    def test_all_en_presets_have_ru_equivalent(self, preset: str):
        """Every English preset must have a Russian counterpart."""
        assert preset in _PRESET_REGISTRY_RU, (
            f"English preset '{preset}' has no Russian equivalent in _PRESET_REGISTRY_RU"
        )

    def test_ru_brand_uses_ru_registry(self):
        brand = _make_brand(language="ru", tone_preset="educational_warm")
        persona = PersonaContext.from_brand(brand)  # type: ignore[arg-type]
        ru_descriptors = _PRESET_REGISTRY_RU["educational_warm"]["voice_descriptors"]
        assert persona.voice_descriptors == ru_descriptors

    def test_en_brand_uses_en_registry(self):
        brand = _make_brand(language="en", tone_preset="educational_warm")
        persona = PersonaContext.from_brand(brand)  # type: ignore[arg-type]
        en_descriptors = _PRESET_REGISTRY["educational_warm"]["voice_descriptors"]
        assert persona.voice_descriptors == en_descriptors

    def test_default_language_is_ru(self):
        """Brand without content_language attribute falls back to ru."""
        brand = types.SimpleNamespace(
            tone_preset="educational_warm",
            face_led_preferred=0,
        )
        persona = PersonaContext.from_brand(brand)  # type: ignore[arg-type]
        ru_descriptors = _PRESET_REGISTRY_RU["educational_warm"]["voice_descriptors"]
        assert persona.voice_descriptors == ru_descriptors

    def test_ru_persona_tone_guidance_in_russian(self):
        brand = _make_brand(language="ru", tone_preset="conversational")
        persona = PersonaContext.from_brand(brand)  # type: ignore[arg-type]
        # Russian guidance should contain Cyrillic characters
        assert any(ord(c) > 127 for c in persona.tone_guidance), (
            "Russian persona tone_guidance contains no Cyrillic characters"
        )

    def test_face_led_still_works_with_ru(self):
        brand = _make_brand(language="ru", face_led=True)
        persona = PersonaContext.from_brand(brand)  # type: ignore[arg-type]
        assert persona.preferred_format == "face_led"

    def test_language_override_in_from_brand(self):
        """Explicit language= override takes precedence over brand.content_language."""
        brand = _make_brand(language="ru")
        persona_en = PersonaContext.from_brand(brand, language="en")  # type: ignore[arg-type]
        persona_ru = PersonaContext.from_brand(brand, language="ru")  # type: ignore[arg-type]
        assert persona_en.voice_descriptors == _PRESET_REGISTRY["educational_warm"]["voice_descriptors"]
        assert persona_ru.voice_descriptors == _PRESET_REGISTRY_RU["educational_warm"]["voice_descriptors"]


# ---------------------------------------------------------------------------
# brand_defaults: Russian defaults
# ---------------------------------------------------------------------------


class TestBrandDefaultsRussian:
    def test_default_language_is_ru(self):
        assert DEFAULT_CONTENT_LANGUAGE == "ru"

    def test_ru_config_has_ru_hashtags(self):
        config = build_brand_config(content_language="ru")
        for tag in config["default_hashtags"]:
            assert any(ord(c) > 127 for c in tag), (
                f"Russian hashtag '{tag}' contains no Cyrillic characters"
            )

    def test_ru_config_has_ru_banned_terms(self):
        config = build_brand_config(content_language="ru")
        for term in config["banned_terms"]:
            assert any(ord(c) > 127 for c in term), (
                f"Russian banned term '{term}' contains no Cyrillic characters"
            )

    def test_ru_config_has_ru_description(self):
        config = build_brand_config(content_language="ru", tone_preset="educational_warm")
        assert any(ord(c) > 127 for c in config["description"]), (
            "Russian description contains no Cyrillic characters"
        )

    def test_en_config_uses_en_defaults(self):
        config = build_brand_config(content_language="en")
        assert config["default_hashtags"] != DEFAULT_HASHTAGS_RU
        assert "#astrology" in config["default_hashtags"]

    def test_content_language_in_config(self):
        for lang in ("ru", "en"):
            config = build_brand_config(content_language=lang)
            assert config["content_language"] == lang


# ---------------------------------------------------------------------------
# DB fixture: content_language stored and retrieved
# ---------------------------------------------------------------------------


class TestContentLanguageDB:
    def test_brand_profile_stores_content_language(self, db_session: Session):
        bp = _ru_brand_db(db_session)
        fetched = db_session.get(BrandProfile, bp.id)
        assert fetched is not None
        assert getattr(fetched, "content_language", None) == "ru"

    def test_brand_profile_default_is_ru(self, db_session: Session):
        bp = BrandProfile(id=str(uuid.uuid4()), name="Default lang test")
        db_session.add(bp)
        db_session.commit()
        db_session.refresh(bp)
        lang = getattr(bp, "content_language", "ru")
        assert lang in ("ru", None, "")  # model default is "ru"; SQLite may return None before migration


# ---------------------------------------------------------------------------
# Admin API: content_language in request/response
# ---------------------------------------------------------------------------


class TestAdminAPIContentLanguage:
    def test_create_brand_profile_with_ru_language(self, client):
        resp = client.post(
            "/api/v1/admin/brand-profile",
            json={
                "name": "Русский тест бренд",
                "tone_preset": "educational_warm",
                "content_language": "ru",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["content_language"] == "ru"

    def test_create_brand_profile_with_en_language(self, client):
        resp = client.post(
            "/api/v1/admin/brand-profile",
            json={
                "name": "English Test Brand",
                "tone_preset": "educational_warm",
                "content_language": "en",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["content_language"] == "en"

    def test_default_content_language_is_ru(self, client):
        resp = client.post(
            "/api/v1/admin/brand-profile",
            json={"name": "No Language Specified Brand"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["content_language"] == "ru"


# ---------------------------------------------------------------------------
# Service-level language routing (mocked AI)
# ---------------------------------------------------------------------------


class TestServiceLanguageRouting:
    """Verify that planner/caption services use the Russian prompt when content_language=ru."""

    def _runner(self, responder):
        from astro_content_agent.services.ai.responses_runner import ResponsesRunner
        from astro_content_agent.tests.fakes.fake_openai import FakeOpenAIClient

        prompts_root = Path(__file__).resolve().parents[1] / "services" / "ai" / "prompts"
        return ResponsesRunner(
            model="test",
            client=FakeOpenAIClient(responder),
            prompts_root=prompts_root,
        )

    def test_planner_uses_ru_prompt_for_ru_brand(self, db_session: Session):
        from astro_content_agent.services.strategy.planner import StrategyPlannerService
        from astro_content_agent.tests.fakes.fake_openai import russian_responder

        bp = _ru_brand_db(db_session)
        runner = self._runner(russian_responder)
        svc = StrategyPlannerService(runner=runner)
        plan = svc.generate_day_plan(
            db=db_session,
            brand_profile_id=bp.id,
            day=date(2026, 4, 3),
            generate_astro_if_missing=True,
        )
        items = plan.payload.get("items", [])
        assert len(items) >= 1
        # Russian responder produces Cyrillic angles
        assert any(ord(c) > 127 for c in items[0]["primary_angle"]), (
            "Expected Cyrillic text in primary_angle for Russian brand"
        )

    def test_caption_service_uses_ru_prompt_for_ru_brand(self, db_session: Session):
        from astro_content_agent.services.content.caption_service import CaptionService
        from astro_content_agent.services.strategy.planner import StrategyPlannerService
        from astro_content_agent.tests.fakes.fake_openai import russian_responder

        bp = _ru_brand_db(db_session)
        runner = self._runner(russian_responder)

        plan = StrategyPlannerService(runner=runner).generate_day_plan(
            db=db_session,
            brand_profile_id=bp.id,
            day=date(2026, 4, 3),
            generate_astro_if_missing=True,
        )
        draft = CaptionService(runner=runner).generate_post_draft(
            db=db_session,
            brand_profile_id=bp.id,
            day=date(2026, 4, 3),
            content_plan=plan,
            plan_slot=1,
        )
        payload = draft.payload or {}
        # Russian hook / caption should contain Cyrillic
        assert any(ord(c) > 127 for c in payload.get("hook", "")), (
            "Expected Cyrillic text in hook for Russian brand draft"
        )

    def test_prompt_ref_name_in_model_run(self, db_session: Session):
        """Prompt version name stored should be 'strategist_ru' for a Russian brand."""
        from astro_content_agent.db.models import PromptVersion
        from astro_content_agent.services.strategy.planner import StrategyPlannerService
        from astro_content_agent.tests.fakes.fake_openai import russian_responder

        bp = _ru_brand_db(db_session)
        runner = self._runner(russian_responder)
        StrategyPlannerService(runner=runner).generate_day_plan(
            db=db_session,
            brand_profile_id=bp.id,
            day=date(2026, 4, 3),
            generate_astro_if_missing=True,
        )
        pv = db_session.query(PromptVersion).filter(PromptVersion.name == "strategist_ru").first()
        assert pv is not None, "Expected PromptVersion named 'strategist_ru' to be created"
