"""Tests for ContentSampleReviewer.

Covers:
- score_post: money alignment detection, hook strength, composite score
- score_reel: hook_0_3s scoring, planet detection, money signals
- rank_by_score: correct descending order
- group_by_format: posts and reels separated
- group_by_tone: correct grouping
- assign_review_labels: labels assigned to correct top items
- format_comparison_table: non-empty string with expected structure
- format_ranked_summary: non-empty with headers and hooks
- format_tone_comparison: correct tone grouping
- money keyword detection: Russian keywords recognized
- planet name detection: Russian planet names recognized
- hook strength logic: weak patterns caught, strong hooks recognised
"""

from __future__ import annotations

from astro_content_agent.services.content.sample_reviewer import (
    ContentSampleReviewer,
    SampleScore,
    _MONEY_KEYWORDS_RU,
    _PLANET_NAMES_RU,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_payload(
    hook: str = "Венера квадрат Сатурну — и ты снова занизил цену",
    caption: str = "Когда Венера получает квадрат от Сатурна, запускается паттерн занижения цены.",
    cta: str = "Напиши 👇",
) -> dict:
    return {"hook": hook, "caption": caption, "cta": cta, "title": "test", "hashtags": [], "voice_note": None}


def _reel_payload(
    hook_0_3s: str = "Венера встала — ты снова занизил",
    hook: str = "Венера квадрат Сатурну — вот почему ты снова занижаешь цену",
    script: str = "Когда Венера под давлением Сатурна, автоматически запускается паттерн занижения цены.",
) -> dict:
    return {"hook_0_3s": hook_0_3s, "hook": hook, "script": script, "reel_type": "talking_head", "on_screen_text": [], "cta": "Напиши"}


REVIEWER = ContentSampleReviewer()


# ---------------------------------------------------------------------------
# Money signal detection
# ---------------------------------------------------------------------------

class TestMoneySignals:
    def test_money_keyword_detected(self) -> None:
        payload = _post_payload(caption="Деньги утекают быстрее, чем ты успеваешь заработать")
        score = REVIEWER.score_post("t1", payload, "educational_warm")
        assert score.money_alignment in ("high", "medium")

    def test_no_money_in_coaching_text(self) -> None:
        payload = _post_payload(
            hook="Сегодня хорошее время для размышлений",
            caption="Прислушайся к себе и доверяй своей интуиции.",
        )
        score = REVIEWER.score_post("t2", payload, "educational_warm")
        assert score.money_alignment == "low"

    def test_house_reference_detected(self) -> None:
        payload = _post_payload(caption="2 дом показывает способ заработка.")
        score = REVIEWER.score_post("t3", payload, "educational_warm")
        assert score.has_house_reference

    def test_planet_name_detected(self) -> None:
        payload = _post_payload(hook="Марс оппозиция Нептуну")
        score = REVIEWER.score_post("t4", payload, "educational_warm")
        assert score.has_planet_name

    def test_no_planet_in_pure_coaching(self) -> None:
        payload = _post_payload(
            hook="Доверяй себе",
            caption="Слушай своё сердце и делай, что чувствуешь правильным.",
        )
        score = REVIEWER.score_post("t5", payload, "educational_warm")
        assert not score.has_planet_name

    def test_money_angle_phrase_counts_more(self) -> None:
        payload = _post_payload(caption="2 дом показывает: деньги через личный труд.")
        score = REVIEWER.score_post("t6", payload, "educational_warm")
        assert score.money_alignment == "high"


# ---------------------------------------------------------------------------
# Hook strength
# ---------------------------------------------------------------------------

class TestHookStrength:
    def test_weak_generic_hook(self) -> None:
        payload = _post_payload(hook="Сегодня особенная энергия...")
        score = REVIEWER.score_post("h1", payload, "educational_warm")
        assert score.hook_strength == "weak"

    def test_strong_hook_with_planet_and_short(self) -> None:
        payload = _post_payload(hook="Венера квадрат Сатурну — ты снова занизил")
        score = REVIEWER.score_post("h2", payload, "educational_warm")
        assert score.hook_strength == "strong"

    def test_medium_hook_no_specifics(self) -> None:
        payload = _post_payload(hook="Это объясняет твои финансы в этом месяце")
        score = REVIEWER.score_post("h3", payload, "educational_warm")
        # Has money keyword but may be medium; not weak, not strong
        assert score.hook_strength in ("strong", "medium")

    def test_long_hook_not_strong(self) -> None:
        long_hook = "Когда Венера находится в напряжённом аспекте с Сатурном то ты скорее всего снова занижаешь цену"
        payload = _post_payload(hook=long_hook)
        score = REVIEWER.score_post("h4", payload, "educational_warm")
        # >12 words → not strong even with planet + money
        assert score.hook_strength in ("medium", "weak")


# ---------------------------------------------------------------------------
# score_post
# ---------------------------------------------------------------------------

class TestScorePost:
    def test_high_score_money_planet_hook(self) -> None:
        payload = _post_payload()
        score = REVIEWER.score_post("p1", payload, "educational_warm")
        assert score.score >= 7
        assert score.format == "post"
        assert score.tone_preset == "educational_warm"

    def test_low_score_generic_no_money(self) -> None:
        payload = _post_payload(
            hook="Сегодня энергия особенная",
            caption="Прислушайся к себе. Доверяй своей интуиции.",
        )
        score = REVIEWER.score_post("p2", payload, "educational_warm")
        assert score.score <= 3

    def test_caption_word_count_populated(self) -> None:
        caption = "Слово " * 50
        payload = _post_payload(caption=caption)
        score = REVIEWER.score_post("p3", payload, "educational_warm")
        assert score.caption_word_count >= 40

    def test_angle_stored(self) -> None:
        score = REVIEWER.score_post("p4", _post_payload(), "educational_warm", angle="test angle")
        assert score.angle == "test angle"


# ---------------------------------------------------------------------------
# score_reel
# ---------------------------------------------------------------------------

class TestScoreReel:
    def test_reel_scored_from_hook_0_3s(self) -> None:
        payload = _reel_payload()
        score = REVIEWER.score_reel("r1", payload, "empowering")
        assert score.format == "reel"
        assert score.hook == payload["hook_0_3s"]

    def test_reel_falls_back_to_hook(self) -> None:
        payload = _reel_payload(hook_0_3s="")
        score = REVIEWER.score_reel("r2", payload, "empowering")
        assert score.hook == payload["hook"]

    def test_reel_planet_from_script(self) -> None:
        payload = _reel_payload(hook_0_3s="Сегодня важный день", script="Луна квадрат Плутону")
        score = REVIEWER.score_reel("r3", payload, "empowering")
        assert score.has_planet_name

    def test_reel_money_from_script(self) -> None:
        payload = _reel_payload(script="Деньги утекают через страх — это Нептун оппозиция Меркурию")
        score = REVIEWER.score_reel("r4", payload, "empowering")
        assert score.money_alignment in ("high", "medium")


# ---------------------------------------------------------------------------
# rank_by_score
# ---------------------------------------------------------------------------

class TestRankByScore:
    def _make_score(self, score: int, fmt: str = "post", tone: str = "a") -> SampleScore:
        return SampleScore(
            draft_id=f"d{score}",
            format=fmt,
            tone_preset=tone,
            angle="",
            hook="test hook",
            hook_full="test hook",
            hook_strength="medium",
            money_alignment="medium",
            has_planet_name=False,
            has_house_reference=False,
            hook_word_count=3,
            caption_word_count=50,
            instagram_ready=True,
            score=score,
        )

    def test_descending_order(self) -> None:
        scores = [self._make_score(3), self._make_score(8), self._make_score(5)]
        ranked = REVIEWER.rank_by_score(scores)
        assert [s.score for s in ranked] == [8, 5, 3]

    def test_empty_list(self) -> None:
        assert REVIEWER.rank_by_score([]) == []


# ---------------------------------------------------------------------------
# group_by_format
# ---------------------------------------------------------------------------

class TestGroupByFormat:
    def _make_score(self, fmt: str, score: int = 5) -> SampleScore:
        return SampleScore(
            draft_id=fmt,
            format=fmt,
            tone_preset="a",
            angle="",
            hook="x",
            hook_full="x",
            hook_strength="medium",
            money_alignment="medium",
            has_planet_name=False,
            has_house_reference=False,
            hook_word_count=1,
            caption_word_count=10,
            instagram_ready=True,
            score=score,
        )

    def test_posts_and_reels_separated(self) -> None:
        scores = [self._make_score("post"), self._make_score("post"), self._make_score("reel")]
        groups = REVIEWER.group_by_format(scores)
        assert len(groups["post"]) == 2
        assert len(groups["reel"]) == 1

    def test_group_by_tone(self) -> None:
        def _ts(tone: str) -> SampleScore:
            s = self._make_score("post")
            return SampleScore(**{**s.__dict__, "tone_preset": tone})
        scores = [_ts("educational_warm"), _ts("empowering"), _ts("educational_warm")]
        groups = REVIEWER.group_by_tone(scores)
        assert len(groups["educational_warm"]) == 2
        assert len(groups["empowering"]) == 1


# ---------------------------------------------------------------------------
# assign_review_labels
# ---------------------------------------------------------------------------

class TestAssignReviewLabels:
    def _s(self, score: int, fmt: str = "post", money: str = "medium", tone: str = "a") -> SampleScore:
        return SampleScore(
            draft_id=f"d{score}{fmt}",
            format=fmt,
            tone_preset=tone,
            angle="",
            hook="test hook",
            hook_full="test hook",
            hook_strength="strong" if score >= 7 else "medium",
            money_alignment=money,
            has_planet_name=True,
            has_house_reference=False,
            hook_word_count=5,
            caption_word_count=100,
            instagram_ready=True,
            score=score,
        )

    def test_highest_score_labeled(self) -> None:
        scores = [self._s(8), self._s(5), self._s(3)]
        labeled = REVIEWER.assign_review_labels(scores)
        top = next(s for s in labeled if s.score == 8)
        assert any("highest" in lb for lb in top.review_labels)

    def test_most_money_aligned_labeled(self) -> None:
        scores = [self._s(5, money="low"), self._s(6, money="high"), self._s(4, money="medium")]
        labeled = REVIEWER.assign_review_labels(scores)
        money_best = next(s for s in labeled if s.money_alignment == "high")
        assert any("money" in lb for lb in money_best.review_labels)

    def test_best_post_labeled(self) -> None:
        scores = [self._s(8, "post"), self._s(6, "reel"), self._s(4, "post")]
        labeled = REVIEWER.assign_review_labels(scores)
        best_post = next(s for s in labeled if s.format == "post" and s.score == 8)
        assert any("post" in lb for lb in best_post.review_labels)

    def test_best_reel_labeled(self) -> None:
        scores = [self._s(5, "post"), self._s(9, "reel"), self._s(3, "reel")]
        labeled = REVIEWER.assign_review_labels(scores)
        best_reel = next(s for s in labeled if s.format == "reel" and s.score == 9)
        assert any("reel" in lb for lb in best_reel.review_labels)


# ---------------------------------------------------------------------------
# format_* methods
# ---------------------------------------------------------------------------

class TestFormatMethods:
    def _scores(self) -> list[SampleScore]:
        def _s(score: int, fmt: str, tone: str, hook: str) -> SampleScore:
            return SampleScore(
                draft_id=f"d{score}",
                format=fmt,
                tone_preset=tone,
                angle="test angle",
                hook=hook,
                hook_full=hook + " — extended",
                hook_strength="strong" if score >= 7 else "medium",
                money_alignment="high" if score >= 7 else "medium",
                has_planet_name=True,
                has_house_reference=False,
                hook_word_count=5,
                caption_word_count=100,
                instagram_ready=True,
                score=score,
            )

        return [
            _s(8, "post", "educational_warm", "Венера квадрат Сатурну — ты снова занизил цену"),
            _s(6, "post", "empowering", "Марс давит — деньги сгорают"),
            _s(7, "reel", "educational_warm", "Луна к Плутону — страх потерь"),
        ]

    def test_comparison_table_non_empty(self) -> None:
        table = REVIEWER.format_comparison_table(self._scores())
        assert len(table) > 50
        assert "FORMAT" in table or "post" in table.lower()

    def test_comparison_table_empty_returns_msg(self) -> None:
        result = REVIEWER.format_comparison_table([])
        assert "no samples" in result

    def test_ranked_summary_non_empty(self) -> None:
        summary = REVIEWER.format_ranked_summary(self._scores())
        assert "RANKED" in summary
        assert "Венера" in summary

    def test_tone_comparison_non_empty(self) -> None:
        result = REVIEWER.format_tone_comparison(self._scores())
        assert "TONE PRESET" in result or "educational_warm" in result

    def test_tone_comparison_format_filter(self) -> None:
        result = REVIEWER.format_tone_comparison(self._scores(), format_filter="reel")
        assert "REEL" in result.upper() or "educational_warm" in result

    def test_tone_comparison_empty_filter(self) -> None:
        result = REVIEWER.format_tone_comparison(self._scores(), format_filter="carousel")
        assert "no samples" in result


# ---------------------------------------------------------------------------
# Hook naturalization: academic/dry patterns are detected as weak
# ---------------------------------------------------------------------------

class TestHookNaturalizationPatterns:
    """Verify that over-explanatory / academic Russian hook patterns are caught."""

    def _weak(self, hook: str) -> None:
        payload = _post_payload(hook=hook)
        score = REVIEWER.score_post("nat", payload, "educational_warm")
        assert score.hook_strength == "weak", (
            f"Expected 'weak' for academic hook: {hook!r}, got {score.hook_strength!r}"
        )

    def _not_weak(self, hook: str) -> None:
        payload = _post_payload(hook=hook)
        score = REVIEWER.score_post("nat", payload, "educational_warm")
        assert score.hook_strength != "weak", (
            f"Expected not 'weak' for natural hook: {hook!r}, got {score.hook_strength!r}"
        )

    # --- academic/dry hooks that should be rejected ---
    def test_dry_harms_aspect_hook(self) -> None:
        self._weak("Хороший момент для тихих финансовых шагов")

    def test_academic_harmony_hook(self) -> None:
        self._weak("Этот аспект помогает мягко договориться")

    def test_explanatory_harmony_hook(self) -> None:
        self._weak("Когда Венера в гармонии с Меркурием, ценность легче перевести в слова")

    def test_generic_sextile_hook(self) -> None:
        self._weak("Секстиль открывает денежное окно")

    # --- natural hooks that should NOT be caught as weak ---
    def test_natural_harmonious_hook_not_weak(self) -> None:
        self._not_weak("Сегодня легче назвать цену и не сжаться")

    def test_recognition_hook_not_weak(self) -> None:
        self._not_weak("Если ты обычно смягчаешь цену — сегодня это особенно видно")

    def test_terse_reel_hook_not_weak(self) -> None:
        # Recognition-first hooks should not be flagged as weak
        self._not_weak("Ты опять смягчаешь цену?")

    def test_natural_tense_hook_not_weak(self) -> None:
        self._not_weak("Венера квадрат Сатурну — ты снова занизил")

    def test_natural_state_hook_not_weak(self) -> None:
        self._not_weak("Сегодня деньги лучше реагируют не на рывок, а на дисциплину")

    def test_astro_observation_not_weak(self) -> None:
        self._not_weak("Меркурий встал — и ты уже это чувствуешь")


# ---------------------------------------------------------------------------
# Reel hook surgery: advice-first / generic-motivation patterns are rejected
# ---------------------------------------------------------------------------

class TestReelHookSurgery:
    """Verify advice-first and generic-motivation reel openers are caught as weak."""

    def _reel_score(self, hook_0_3s: str) -> object:
        payload = _reel_payload(hook_0_3s=hook_0_3s)
        return REVIEWER.score_reel("rhs", payload, "educational_warm")

    def _is_weak(self, hook_0_3s: str) -> bool:
        score = self._reel_score(hook_0_3s)
        return score.hook_strength == "weak"

    # --- advice-first patterns that should be weak ---
    def test_advice_first_popros(self) -> None:
        assert self._is_weak("Попроси больше. Сейчас это работает")

    def test_generic_motivation_silnee(self) -> None:
        assert self._is_weak("Ты сильнее, чем думаешь")

    def test_generic_vsyo_poluchitsya(self) -> None:
        assert self._is_weak("Всё получится. Верь в себя")

    def test_advice_prosто(self) -> None:
        assert self._is_weak("Просто попроси больше")

    # --- recognition-first patterns that should NOT be weak ---
    def test_recognition_question_not_weak(self) -> None:
        assert not self._is_weak("Ты опять смягчаешь цену?")

    def test_state_contrast_not_weak(self) -> None:
        assert not self._is_weak("Сегодня цену назвать легче, чем обычно")

    def test_redirect_pattern_not_weak(self) -> None:
        assert not self._is_weak("Если ты мнёшься в разговорах о деньгах — смотри")

    def test_distortion_transformation_not_weak(self) -> None:
        assert not self._is_weak("Страх бедности сегодня можно превратить в опору")

    def test_metaphor_contrast_not_weak(self) -> None:
        assert not self._is_weak("Сегодня деньги лучше любят ясность, чем суету")

    def test_reversal_not_weak(self) -> None:
        assert not self._is_weak("Это не скромность. Это Венера-Сатурн")

    def test_tense_naming_not_weak(self) -> None:
        assert not self._is_weak("Деньги уходят быстрее, чем ты успеваешь заработать?")

    def test_curiosity_hook_not_weak(self) -> None:
        assert not self._is_weak("Подожди. Это объясняет прошлую неделю")

