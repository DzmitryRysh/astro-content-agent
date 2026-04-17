"""Phase 10.5 tests: brand calibration, quality reporter, and seed helpers.

Covers:
- DraftQualityReporter: hook assessment, post/reel report building, formatting
- build_brand_config: tone_preset defaults, face_led_preferred, descriptions
- PersonaContext: all registered tone presets resolve correctly
- face_led_preferred flows through PersonaContext
- Seed config uses a recognized tone preset
"""

from __future__ import annotations

import types

import pytest

from astro_content_agent.services.content.brand_defaults import (
    DEFAULT_TONE_PRESET,
    TONE_DESCRIPTIONS,
    build_brand_config,
)
from astro_content_agent.services.content.persona import PersonaContext, _PRESET_REGISTRY
from astro_content_agent.services.content.quality_reporter import (
    DraftQualityReporter,
    HookQualityReport,
    PostDraftReport,
    ReelDraftReport,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_brand(tone_preset: str = "educational_warm", face_led: bool = False, language: str = "en"):
    """Return a SimpleNamespace that satisfies PersonaContext.from_brand.

    Defaults to content_language="en" so these English-registry tests remain
    stable after the Russian-first language pivot.
    """
    return types.SimpleNamespace(
        id="bp-test",
        name="Test Brand",
        description="Test description",
        tone_preset=tone_preset,
        face_led_preferred=int(face_led),
        banned_terms=[],
        default_hashtags=[],
        content_language=language,
    )


# ---------------------------------------------------------------------------
# DraftQualityReporter — HookQualityReport
# ---------------------------------------------------------------------------

class TestHookAssessment:
    def setup_method(self):
        self.reporter = DraftQualityReporter()

    def test_good_hook_passes(self):
        report = self.reporter.assess_hook(
            "Your birth chart is a blueprint — not a prison", recent_hooks=[]
        )
        assert report.passed is True
        assert report.verdict == "OK"

    def test_weak_hook_flagged(self):
        report = self.reporter.assess_hook("The stars are speaking today", recent_hooks=[])
        assert report.is_weak is True
        assert "WEAK" in report.verdict

    def test_weak_hook_mercury_retrograde(self):
        report = self.reporter.assess_hook("Mercury is retrograde and that means...", recent_hooks=[])
        assert report.is_weak is True

    def test_repetitive_hook_flagged(self):
        recent = ["Your birth chart reveals your pattern"]
        report = self.reporter.assess_hook("Your birth chart reveals something", recent_hooks=recent)
        assert report.is_repetitive is True
        assert "REPETITIVE" in report.verdict

    def test_unique_hook_not_flagged_as_repetitive(self):
        recent = ["Mars is activating your ambition zone"]
        report = self.reporter.assess_hook("The moon is shifting your emotional landscape", recent_hooks=recent)
        assert report.is_repetitive is False

    def test_empty_recent_hooks_no_false_positive(self):
        report = self.reporter.assess_hook("Stop. This transit changes everything.", recent_hooks=[])
        assert report.is_repetitive is False

    def test_both_weak_and_repetitive_reported(self):
        # First 4 words must match exactly for is_repetitive; also matches weak pattern
        recent = ["Today's energy is calling you to slow down"]
        report = self.reporter.assess_hook(
            "Today's energy is calling for stillness", recent_hooks=recent
        )
        assert report.is_weak is True      # matches ^today('s)? energy
        assert report.is_repetitive is True  # first 4 words: "today's energy is calling"
        assert "WEAK" in report.verdict
        assert "REPETITIVE" in report.verdict


# ---------------------------------------------------------------------------
# DraftQualityReporter — PostDraftReport
# ---------------------------------------------------------------------------

class TestPostDraftReport:
    def setup_method(self):
        self.reporter = DraftQualityReporter()

    def _payload(self, hook: str = "Something powerful just shifted") -> dict:
        return {
            "title": "Mars Direct: Your Energy Returns",
            "hook": hook,
            "caption": "Full caption text here. " * 5,
            "cta": "Save this for when you need the reminder.",
            "hashtags": ["#astrology", "#mars", "#mindset"],
            "voice_note": "Warm and direct; no hedging.",
        }

    def test_returns_post_draft_report_type(self):
        report = self.reporter.assess_post_draft("d-1", self._payload())
        assert isinstance(report, PostDraftReport)

    def test_fields_populated(self):
        p = self._payload()
        report = self.reporter.assess_post_draft("d-1", p)
        assert report.draft_id == "d-1"
        assert report.title == p["title"]
        assert report.hook == p["hook"]
        assert report.cta == p["cta"]
        assert report.hashtags == p["hashtags"]
        assert report.voice_note == "Warm and direct; no hedging."

    def test_hook_quality_attached(self):
        report = self.reporter.assess_post_draft("d-1", self._payload())
        assert isinstance(report.hook_quality, HookQualityReport)

    def test_missing_fields_dont_raise(self):
        report = self.reporter.assess_post_draft("d-1", {})
        assert report.title == ""
        assert report.hook == ""
        assert report.hashtags == []
        assert report.voice_note is None

    def test_format_post_report_contains_key_sections(self):
        report = self.reporter.assess_post_draft("d-1", self._payload())
        text = self.reporter.format_post_report(report)
        assert "POST DRAFT" in text
        assert "Hook" in text
        assert "Hook QA" in text
        assert "CTA" in text


# ---------------------------------------------------------------------------
# DraftQualityReporter — ReelDraftReport
# ---------------------------------------------------------------------------

class TestReelDraftReport:
    def setup_method(self):
        self.reporter = DraftQualityReporter()

    def _payload(self, hook_0_3s: str = "Wait — this changes everything.") -> dict:
        return {
            "hook_0_3s": hook_0_3s,
            "hook": "Wait — this Mars transit changes everything about your drive.",
            "reel_type": "talking_head",
            "script": "Full reel script goes here.",
            "on_screen_text": ["Mars Direct", "Energy Returns", "Take Action"],
            "cta": "Follow for daily transit updates.",
        }

    def test_returns_reel_draft_report_type(self):
        report = self.reporter.assess_reel_draft("d-2", self._payload())
        assert isinstance(report, ReelDraftReport)

    def test_fields_populated(self):
        p = self._payload()
        report = self.reporter.assess_reel_draft("d-2", p)
        assert report.hook_0_3s == p["hook_0_3s"]
        assert report.hook == p["hook"]
        assert report.reel_type == "talking_head"
        assert report.on_screen_text == p["on_screen_text"]
        assert report.cta == p["cta"]

    def test_hook_0_3s_used_for_quality_check(self):
        # hook_0_3s matches a weak pattern but full hook does not
        p = self._payload(hook_0_3s="The stars are speaking today")
        report = self.reporter.assess_reel_draft("d-2", p)
        assert report.hook_quality.is_weak is True

    def test_fallback_to_hook_when_no_hook_0_3s(self):
        p = {
            "hook": "Today's energy is heavy and charged",  # matches ^today('s)? energy
            "reel_type": "voiceover",
            "script": "...",
            "on_screen_text": [],
            "cta": "...",
        }
        report = self.reporter.assess_reel_draft("d-2", p)
        # Falls back to hook — which matches a weak pattern
        assert report.hook_quality.is_weak is True

    def test_format_reel_report_contains_key_sections(self):
        report = self.reporter.assess_reel_draft("d-2", self._payload())
        text = self.reporter.format_reel_report(report)
        assert "REEL DRAFT" in text
        assert "Hook 0-3s" in text
        assert "Hook QA" in text
        assert "Type" in text


# ---------------------------------------------------------------------------
# Seed helper: build_brand_config (imported from brand_defaults module)
# ---------------------------------------------------------------------------

class TestBuildBrandConfig:
    def test_build_brand_config_importable(self):
        # build_brand_config is a first-class module function, not a script helper
        assert callable(build_brand_config)

    def test_default_tone_preset_is_recognized(self):
        config = build_brand_config()
        assert config["tone_preset"] in _PRESET_REGISTRY, (
            f"Default tone_preset '{config['tone_preset']}' not in PersonaContext registry."
        )

    def test_default_tone_preset_constant(self):
        assert DEFAULT_TONE_PRESET in _PRESET_REGISTRY

    def test_all_seeded_tone_presets_are_recognized(self):
        """Every preset in TONE_DESCRIPTIONS must map to a PersonaContext preset."""
        for preset in TONE_DESCRIPTIONS:
            assert preset in _PRESET_REGISTRY, (
                f"Seed tone_preset '{preset}' not recognised by PersonaContext registry."
            )

    def test_face_led_true_sets_flag(self):
        config = build_brand_config(face_led_preferred=True)
        assert config["face_led_preferred"] == 1

    def test_face_led_false_default(self):
        config = build_brand_config()
        assert config["face_led_preferred"] == 0

    def test_description_non_empty_for_all_presets(self):
        for preset in _PRESET_REGISTRY:
            if preset == "default":
                continue
            config = build_brand_config(tone_preset=preset)
            assert config["description"], f"Empty description for preset '{preset}'"

    def test_custom_name_propagates(self):
        config = build_brand_config(name="My Custom Brand")
        assert config["name"] == "My Custom Brand"

    def test_banned_terms_present(self):
        config = build_brand_config()
        assert isinstance(config["banned_terms"], list)
        assert len(config["banned_terms"]) > 0

    def test_default_hashtags_present(self):
        config = build_brand_config()
        assert isinstance(config["default_hashtags"], list)
        assert len(config["default_hashtags"]) > 0


# ---------------------------------------------------------------------------
# PersonaContext: all presets resolve without error
# ---------------------------------------------------------------------------

class TestPersonaContextPresets:
    @pytest.mark.parametrize("preset", list(_PRESET_REGISTRY.keys()))
    def test_preset_resolves(self, preset: str):
        bp = _make_brand(tone_preset=preset)
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        assert len(persona.voice_descriptors) > 0
        assert len(persona.tone_guidance) > 0

    def test_unknown_preset_falls_back_to_default(self):
        bp = _make_brand(tone_preset="nonexistent_preset_xyz")
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        default_preset = _PRESET_REGISTRY["default"]
        assert persona.voice_descriptors == default_preset["voice_descriptors"]

    def test_face_led_preferred_true_sets_format(self):
        bp = _make_brand(face_led=True)
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        assert persona.preferred_format == "face_led"

    def test_face_led_preferred_false_format_none(self):
        bp = _make_brand(face_led=False)
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        assert persona.preferred_format is None

    def test_face_led_included_in_prompt_hint(self):
        bp = _make_brand(face_led=True)
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        hint = persona.to_prompt_hint()
        assert "face-led" in hint.lower() or "face_led" in hint.lower()

    def test_no_face_led_prompt_hint_omits_format(self):
        bp = _make_brand(face_led=False)
        persona = PersonaContext.from_brand(bp)  # type: ignore[arg-type]
        hint = persona.to_prompt_hint()
        assert "face-led" not in hint.lower()
