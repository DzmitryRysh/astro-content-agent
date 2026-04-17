"""Tests for the live_astrology_rules knowledge module.

Validates:
- LIVE_ASTROLOGY_RULES_RU is well-formed and contains key anti-generic principles
- BIOASTROLOGY_MONEY_NOTES_RU has all required entities including resource_distortion_types
- SHARP_WITTY_STYLE_DNA_RU has required structure and meaningful content
- ANTI_DEAD_ASTROLOGY_RU covers the main dead-astrology traps
- LiveAstrologyContext.to_dict() returns correct keys and non-empty content
- get_sharp_witty_style_reinforcement_hint() produces a usable string
- PersonaContext integration: sharp_witty gets style_reinforcement_notes; others don't
"""
from __future__ import annotations

import types

import pytest

from astro_content_agent.services.content.live_astrology_rules import (
    ANTI_DEAD_ASTROLOGY_RU,
    BIOASTROLOGY_MONEY_NOTES_RU,
    LIVE_ASTROLOGY_RULES_RU,
    SHARP_WITTY_STYLE_DNA_RU,
    LiveAstrologyContext,
    get_sharp_witty_style_reinforcement_hint,
)
from astro_content_agent.services.content.persona import PersonaContext


# ---------------------------------------------------------------------------
# LIVE_ASTROLOGY_RULES_RU
# ---------------------------------------------------------------------------


class TestLiveAstrologyRules:
    def test_non_empty(self) -> None:
        assert len(LIVE_ASTROLOGY_RULES_RU) >= 6

    def test_contains_mechanism_rule(self) -> None:
        combined = " ".join(LIVE_ASTROLOGY_RULES_RU).lower()
        assert "механизм" in combined or "поведен" in combined

    def test_contains_harmonious_rule(self) -> None:
        combined = " ".join(LIVE_ASTROLOGY_RULES_RU).lower()
        assert "гармоничн" in combined

    def test_contains_tense_rule(self) -> None:
        combined = " ".join(LIVE_ASTROLOGY_RULES_RU).lower()
        assert "напряжённ" in combined or "трение" in combined or "компенсац" in combined

    def test_contains_money_as_behavior_rule(self) -> None:
        combined = " ".join(LIVE_ASTROLOGY_RULES_RU).lower()
        assert "поведен" in combined or "привычк" in combined or "обмен" in combined

    def test_contains_anti_reduction_rule(self) -> None:
        combined = " ".join(LIVE_ASTROLOGY_RULES_RU).lower()
        # Should warn against reducing planets to single meanings
        assert "венер" in combined or "2 дом" in combined or "сводить" in combined or "только" in combined

    def test_all_strings(self) -> None:
        for rule in LIVE_ASTROLOGY_RULES_RU:
            assert isinstance(rule, str) and len(rule) > 10


# ---------------------------------------------------------------------------
# BIOASTROLOGY_MONEY_NOTES_RU
# ---------------------------------------------------------------------------


class TestBioastrologyMoneyNotes:
    def test_required_entities_present(self) -> None:
        required = {"2nd_house", "8th_house", "10th_house", "venus", "resource_distortion_types"}
        assert required.issubset(set(BIOASTROLOGY_MONEY_NOTES_RU.keys()))

    def test_each_entity_has_required_keys(self) -> None:
        for key, data in BIOASTROLOGY_MONEY_NOTES_RU.items():
            assert "core" in data, f"[{key}] missing 'core'"
            assert "not_only" in data, f"[{key}] missing 'not_only'"
            assert "money_mechanism" in data, f"[{key}] missing 'money_mechanism'"

    def test_2nd_house_not_just_money(self) -> None:
        notes = BIOASTROLOGY_MONEY_NOTES_RU["2nd_house"]
        not_only = notes["not_only"].lower()
        assert "не просто" in not_only or "не только" in not_only

    def test_venus_not_just_romance(self) -> None:
        notes = BIOASTROLOGY_MONEY_NOTES_RU["venus"]
        not_only = notes["not_only"].lower()
        assert "романтик" in not_only or "не только" in not_only

    def test_resource_distortion_types_has_four_patterns(self) -> None:
        mechanism = BIOASTROLOGY_MONEY_NOTES_RU["resource_distortion_types"]["money_mechanism"].lower()
        for pattern in ("стагнация", "утечка", "перегорание", "заморозка"):
            assert pattern in mechanism, f"Missing distortion type: {pattern}"

    def test_8th_house_mentions_shared_resource(self) -> None:
        core = BIOASTROLOGY_MONEY_NOTES_RU["8th_house"]["core"].lower()
        assert "общ" in core or "зависим" in core or "заём" in core

    def test_10th_house_mentions_status(self) -> None:
        core = BIOASTROLOGY_MONEY_NOTES_RU["10th_house"]["core"].lower()
        assert "статус" in core or "репутац" in core or "профессиональн" in core


# ---------------------------------------------------------------------------
# SHARP_WITTY_STYLE_DNA_RU
# ---------------------------------------------------------------------------


class TestSharpWittyStyleDna:
    def test_has_required_keys(self) -> None:
        for key in ("core_principle", "do", "dont", "live_vs_dead_examples"):
            assert key in SHARP_WITTY_STYLE_DNA_RU, f"Missing key: {key}"

    def test_do_list_non_empty(self) -> None:
        assert len(SHARP_WITTY_STYLE_DNA_RU["do"]) >= 4

    def test_dont_list_non_empty(self) -> None:
        assert len(SHARP_WITTY_STYLE_DNA_RU["dont"]) >= 3

    def test_live_vs_dead_examples_have_structure(self) -> None:
        for ex in SHARP_WITTY_STYLE_DNA_RU["live_vs_dead_examples"]:
            assert "dead" in ex, "Example missing 'dead' key"
            assert "alive" in ex, "Example missing 'alive' key"

    def test_live_vs_dead_covers_venus(self) -> None:
        dead_texts = " ".join(ex["dead"].lower() for ex in SHARP_WITTY_STYLE_DNA_RU["live_vs_dead_examples"])
        assert "венер" in dead_texts

    def test_live_vs_dead_covers_2nd_house(self) -> None:
        dead_texts = " ".join(ex["dead"].lower() for ex in SHARP_WITTY_STYLE_DNA_RU["live_vs_dead_examples"])
        assert "2 дом" in dead_texts or "второй дом" in dead_texts

    def test_core_principle_is_substantial(self) -> None:
        assert len(SHARP_WITTY_STYLE_DNA_RU["core_principle"]) >= 40


# ---------------------------------------------------------------------------
# ANTI_DEAD_ASTROLOGY_RU
# ---------------------------------------------------------------------------


class TestAntiDeadAstrologyRules:
    def test_non_empty(self) -> None:
        assert len(ANTI_DEAD_ASTROLOGY_RU) >= 5

    def test_covers_venus_reduction(self) -> None:
        combined = " ".join(ANTI_DEAD_ASTROLOGY_RU).lower()
        assert "венер" in combined

    def test_covers_2nd_house_reduction(self) -> None:
        combined = " ".join(ANTI_DEAD_ASTROLOGY_RU).lower()
        assert "2 дом" in combined

    def test_covers_harmonious_aspect_rule(self) -> None:
        combined = " ".join(ANTI_DEAD_ASTROLOGY_RU).lower()
        assert "гармоничн" in combined

    def test_covers_abstract_spiritual_padding(self) -> None:
        combined = " ".join(ANTI_DEAD_ASTROLOGY_RU).lower()
        assert "абстракт" in combined or "духовн" in combined or "механизм" in combined


# ---------------------------------------------------------------------------
# LiveAstrologyContext.to_dict()
# ---------------------------------------------------------------------------


class TestLiveAstrologyContextToDict:
    def test_has_required_keys(self) -> None:
        d = LiveAstrologyContext.to_dict()
        for key in ("interpretation_rules", "money_entity_notes", "anti_dead_rules", "sharp_witty_style_dna"):
            assert key in d, f"Missing key: {key}"

    def test_interpretation_rules_is_list(self) -> None:
        d = LiveAstrologyContext.to_dict()
        assert isinstance(d["interpretation_rules"], list)
        assert len(d["interpretation_rules"]) >= 6

    def test_money_entity_notes_has_all_entities(self) -> None:
        d = LiveAstrologyContext.to_dict()
        notes = d["money_entity_notes"]
        for key in ("2nd_house", "8th_house", "10th_house", "venus", "resource_distortion_types"):
            assert key in notes, f"Missing entity: {key}"

    def test_each_entity_note_has_required_subkeys(self) -> None:
        d = LiveAstrologyContext.to_dict()
        for key, data in d["money_entity_notes"].items():
            for subkey in ("core", "not_only", "money_mechanism"):
                assert subkey in data, f"[{key}] missing subkey: {subkey}"

    def test_sharp_witty_style_dna_has_required_keys(self) -> None:
        d = LiveAstrologyContext.to_dict()
        dna = d["sharp_witty_style_dna"]
        for key in ("core_principle", "do", "dont", "live_vs_dead_examples"):
            assert key in dna, f"sharp_witty_style_dna missing: {key}"

    def test_anti_dead_rules_is_list(self) -> None:
        d = LiveAstrologyContext.to_dict()
        assert isinstance(d["anti_dead_rules"], list)
        assert len(d["anti_dead_rules"]) >= 5

    def test_interpretation_rules_hint_is_string(self) -> None:
        hint = LiveAstrologyContext.interpretation_rules_hint()
        assert isinstance(hint, str)
        assert "Принципы" in hint
        assert len(hint) > 50

    def test_anti_dead_rules_hint_is_string(self) -> None:
        hint = LiveAstrologyContext.anti_dead_rules_hint()
        assert isinstance(hint, str)
        assert "Запрещено" in hint


# ---------------------------------------------------------------------------
# get_sharp_witty_style_reinforcement_hint()
# ---------------------------------------------------------------------------


class TestSharpWittyStyleReinforcementHint:
    def test_returns_string(self) -> None:
        hint = get_sharp_witty_style_reinforcement_hint()
        assert isinstance(hint, str)

    def test_contains_live_vs_dead_markers(self) -> None:
        hint = get_sharp_witty_style_reinforcement_hint()
        assert "Мёртво" in hint or "мёртво" in hint
        assert "Живо" in hint or "живо" in hint

    def test_contains_do_section(self) -> None:
        hint = get_sharp_witty_style_reinforcement_hint()
        assert "Do:" in hint

    def test_contains_dont_section(self) -> None:
        hint = get_sharp_witty_style_reinforcement_hint()
        assert "Don't:" in hint

    def test_substantial_length(self) -> None:
        hint = get_sharp_witty_style_reinforcement_hint()
        assert len(hint) > 200


# ---------------------------------------------------------------------------
# PersonaContext integration
# ---------------------------------------------------------------------------


def _make_brand(tone_preset: str, language: str = "ru") -> types.SimpleNamespace:
    return types.SimpleNamespace(
        tone_preset=tone_preset,
        content_language=language,
        face_led_preferred=False,
        persona_notes=None,
    )


class TestPersonaContextStyleReinforcementIntegration:
    def test_sharp_witty_has_style_reinforcement_notes(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("sharp_witty"))
        assert ctx.style_reinforcement_notes is not None
        assert len(ctx.style_reinforcement_notes) > 100

    def test_educational_warm_has_no_style_reinforcement(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("educational_warm"))
        assert ctx.style_reinforcement_notes is None

    def test_conversational_has_no_style_reinforcement(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("conversational"))
        assert ctx.style_reinforcement_notes is None

    def test_empowering_has_no_style_reinforcement(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("empowering"))
        assert ctx.style_reinforcement_notes is None

    def test_sharp_witty_prompt_hint_contains_style_reinforcement(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("sharp_witty"))
        hint = ctx.to_prompt_hint()
        assert "Style reinforcement" in hint
        assert "live vs dead" in hint.lower() or "Live vs dead" in hint

    def test_educational_warm_prompt_hint_has_no_style_reinforcement(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("educational_warm"))
        hint = ctx.to_prompt_hint()
        assert "Style reinforcement" not in hint

    def test_sharp_witty_english_has_no_style_reinforcement(self) -> None:
        # English sharp_witty preset also gets style_reinforcement_notes now (it has caption_style_notes)
        # but does NOT get style_reinforcement_notes since only RU preset has it
        ctx = PersonaContext.from_brand(_make_brand("sharp_witty", language="en"))
        # EN registry sharp_witty doesn't have style_reinforcement_notes
        assert ctx.style_reinforcement_notes is None

    def test_sharp_witty_still_has_hook_and_caption_notes(self) -> None:
        ctx = PersonaContext.from_brand(_make_brand("sharp_witty"))
        assert ctx.hook_style_notes is not None
        assert ctx.caption_style_notes is not None
        assert ctx.style_reinforcement_notes is not None
