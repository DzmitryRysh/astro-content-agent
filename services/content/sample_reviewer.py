"""Content sample reviewer for local QA and prompt calibration.

Provides scoring, ranking, and comparison of multiple generated drafts
without requiring AI calls. Used by the batch calibration script.

Key concepts:
- ``SampleScore`` — a scored representation of one generated draft
- ``ContentSampleReviewer`` — scores drafts and formats comparison views
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from astro_content_agent.services.content.anti_repeat import AntiRepeatContext

# ---------------------------------------------------------------------------
# Keyword signals for money alignment detection
# ---------------------------------------------------------------------------

_MONEY_KEYWORDS_RU: frozenset[str] = frozenset([
    "деньги", "денег", "деньгам", "доход", "дохода", "доходам",
    "заработок", "заработка", "зарабатыв", "зарабатывает", "заработать",
    "цена", "цены", "цену", "ценообразован",
    "ресурс", "ресурсы", "ресурса",
    "трат", "траты", "трату", "тратит", "тратить",
    "кошелёк", "кошелька", "кошельке",
    "финанс", "финансов", "финансы", "финансовый", "финансовых",
    "бюджет", "бюджета",
    "стоимость", "стоимости",
    "платит", "плату", "платить",
    "прибыль", "прибыли",
    "накоплен", "накопления", "накопить",
    "вложен", "вложения", "вложить", "инвестиц",
    "утекают", "утечка", "утечки",
    "задерживаются", "держатся",
    "зарплата", "зарплаты",
    "стоит", "стою", "стоишь",
])

_MONEY_ANGLE_PHRASES: tuple[str, ...] = (
    "2 дом", "8 дом", "10 дом",
    "способ заработка", "денежный маршрут",
    "фермер", "хищник",
    "способность принять", "удержать ресурс",
    "занижаешь цену", "занижает цену",
    "страх бедности", "денежная тревога",
    "бессознательный стиль",
    "через что приходят деньги",
)

_PLANET_NAMES_RU: frozenset[str] = frozenset([
    "венера", "сатурн", "марс", "нептун", "юпитер",
    "плутон", "луна", "уран", "меркурий", "солнце",
])

_HOUSE_PATTERN = re.compile(r"\b([1-9]|1[0-2])\s*дом\b", re.IGNORECASE)

# Russian-specific weak hook patterns (generic, low-tension openers)
_WEAK_HOOK_PATTERNS_RU: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in [
        r"^сегодня (особенная|мощная|сильная|интересная) энерги",
        r"^сегодня хорош",
        r"^это (особое|важное|особенное) время",
        r"^в эти дни",
        r"^вселенная (говорит|хочет|посылает)",
        r"^энергия (сегодня|сейчас|недели|месяца)",
        r"^прислушайся к себе",
        r"^доверяй своей интуиции",
        r"^сегодня важный день",
        # Over-explanatory / academic openings
        r"^хороший момент для тихих",
        r"^этот аспект помогает мягко",
        r"^когда [а-яё]+ в гармонии с [а-яё]+,\s+(ценность|способность|умение) легче",
        r"^(этот|данный) аспект (создаёт|открывает|даёт) (момент|окно|возможность)",
        r"^секстиль (открывает|создаёт) денежн",
        # Advice-first reel patterns (no felt context, no recognition)
        r"^попроси больше\.",
        r"^сделай (это|шаг|запрос)",
        r"^просто (попроси|скажи|называй)",
        r"^иди и (попроси|скажи|сделай)",
        r"^ты (сильнее|умнее|лучше), чем думаешь",
        r"^ты можешь (больше|лучше|это)",
        # Generic motivation without astrology
        r"^всё (получится|будет хорошо|изменится)",
        r"^верь в себя",
        r"^ты справишься",
    ]
)

# ---------------------------------------------------------------------------
# SampleScore
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SampleScore:
    """Scored representation of one generated draft for comparison."""

    draft_id: str
    format: str  # "post" | "reel"
    tone_preset: str
    angle: str  # primary_angle from plan item, or empty
    hook: str   # post hook or reel hook_0_3s
    hook_full: str  # full hook sentence (post hook or reel hook)

    # Scored dimensions
    hook_strength: Literal["strong", "medium", "weak"]
    money_alignment: Literal["high", "medium", "low"]
    has_planet_name: bool
    has_house_reference: bool
    hook_word_count: int
    caption_word_count: int
    instagram_ready: bool

    # Composite score 0–10
    score: int

    # Labels applied during ranking (mutable-friendly via list)
    review_labels: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ContentSampleReviewer
# ---------------------------------------------------------------------------


class ContentSampleReviewer:
    """Scores, ranks, and formats comparison views for generated draft batches.

    Does not call any external services — all analysis is string-based.
    Designed for use in local calibration scripts and tests.
    """

    # ------------------------------------------------------------------
    # Scoring primitives
    # ------------------------------------------------------------------

    @staticmethod
    def _count_money_signals(text: str) -> int:
        """Count money keyword hits in a text block (case-insensitive)."""
        lower = text.lower()
        count = 0
        for kw in _MONEY_KEYWORDS_RU:
            if kw in lower:
                count += 1
        for phrase in _MONEY_ANGLE_PHRASES:
            if phrase.lower() in lower:
                count += 2  # phrase hits count more
        return count

    @staticmethod
    def _has_planet(text: str) -> bool:
        lower = text.lower()
        return any(planet in lower for planet in _PLANET_NAMES_RU)

    @staticmethod
    def _has_house_ref(text: str) -> bool:
        return bool(_HOUSE_PATTERN.search(text))

    @staticmethod
    def _hook_word_count(hook: str) -> int:
        return len(hook.split())

    @staticmethod
    def _money_alignment(money_score: int) -> Literal["high", "medium", "low"]:
        if money_score >= 3:
            return "high"
        if money_score >= 1:
            return "medium"
        return "low"

    @staticmethod
    def _hook_strength(
        hook: str,
        recent_hooks: list[str],
        word_count: int,
    ) -> Literal["strong", "medium", "weak"]:
        ctx = AntiRepeatContext(recent_hooks=recent_hooks)
        # Check English weak patterns via anti-repeat
        if ctx.is_hook_weak(hook):
            return "weak"
        # Check Russian-specific weak patterns
        if any(rx.search(hook) for rx in _WEAK_HOOK_PATTERNS_RU):
            return "weak"
        # Strong: short + specific (planet or money keyword present)
        has_specifics = (
            any(p in hook.lower() for p in _PLANET_NAMES_RU)
            or any(kw in hook.lower() for kw in _MONEY_KEYWORDS_RU)
        )
        if word_count <= 12 and has_specifics:
            return "strong"
        return "medium"

    @staticmethod
    def _instagram_ready(hook: str, word_count: int) -> bool:
        """Simple Instagram-readiness heuristic."""
        return (
            word_count <= 15
            and not hook.startswith("В данный")
            and not hook.startswith("Итак")
            and len(hook) >= 10
        )

    def _composite_score(
        self,
        hook_strength: str,
        money_alignment: str,
        has_planet: bool,
        has_house: bool,
        instagram_ready: bool,
        word_count: int,
    ) -> int:
        score = 0
        # Hook quality: 0-4 pts
        score += {"strong": 4, "medium": 2, "weak": 0}[hook_strength]
        # Money alignment: 0-3 pts
        score += {"high": 3, "medium": 1, "low": 0}[money_alignment]
        # Astrology specificity: 0-2 pts
        score += 1 if has_planet else 0
        score += 1 if has_house else 0
        # Instagram-ready: 0-1 pt
        score += 1 if instagram_ready else 0
        return min(score, 10)

    # ------------------------------------------------------------------
    # Public scoring API
    # ------------------------------------------------------------------

    def score_post(
        self,
        draft_id: str,
        payload: dict,
        tone_preset: str,
        angle: str = "",
        recent_hooks: list[str] | None = None,
    ) -> SampleScore:
        """Score a post draft payload."""
        hook = payload.get("hook", "")
        caption = payload.get("caption", "")
        body = f"{hook} {caption}"

        wc = self._hook_word_count(hook)
        money = self._count_money_signals(body)
        alignment = self._money_alignment(money)
        planet = self._has_planet(body)
        house = self._has_house_ref(body)
        strength = self._hook_strength(hook, recent_hooks or [], wc)
        ig_ready = self._instagram_ready(hook, wc)
        score = self._composite_score(strength, alignment, planet, house, ig_ready, wc)

        return SampleScore(
            draft_id=draft_id,
            format="post",
            tone_preset=tone_preset,
            angle=angle,
            hook=hook,
            hook_full=hook,
            hook_strength=strength,
            money_alignment=alignment,
            has_planet_name=planet,
            has_house_reference=house,
            hook_word_count=wc,
            caption_word_count=len(caption.split()),
            instagram_ready=ig_ready,
            score=score,
        )

    def score_reel(
        self,
        draft_id: str,
        payload: dict,
        tone_preset: str,
        angle: str = "",
        recent_hooks: list[str] | None = None,
    ) -> SampleScore:
        """Score a reel draft payload."""
        hook_0_3s = payload.get("hook_0_3s", "")
        hook_full = payload.get("hook", "")
        script = payload.get("script", "")
        body = f"{hook_0_3s} {hook_full} {script}"
        display_hook = hook_0_3s or hook_full

        wc = self._hook_word_count(display_hook)
        money = self._count_money_signals(body)
        alignment = self._money_alignment(money)
        planet = self._has_planet(body)
        house = self._has_house_ref(body)
        strength = self._hook_strength(display_hook, recent_hooks or [], wc)
        ig_ready = self._instagram_ready(display_hook, wc)
        score = self._composite_score(strength, alignment, planet, house, ig_ready, wc)

        return SampleScore(
            draft_id=draft_id,
            format="reel",
            tone_preset=tone_preset,
            angle=angle,
            hook=display_hook,
            hook_full=hook_full,
            hook_strength=strength,
            money_alignment=alignment,
            has_planet_name=planet,
            has_house_reference=house,
            hook_word_count=wc,
            caption_word_count=len(script.split()),
            instagram_ready=ig_ready,
            score=score,
        )

    # ------------------------------------------------------------------
    # Grouping and ranking
    # ------------------------------------------------------------------

    def rank_by_score(self, scores: list[SampleScore]) -> list[SampleScore]:
        """Return scores sorted highest-first by composite score."""
        return sorted(scores, key=lambda s: s.score, reverse=True)

    def group_by_format(self, scores: list[SampleScore]) -> dict[str, list[SampleScore]]:
        """Group scores by format ('post' / 'reel')."""
        groups: dict[str, list[SampleScore]] = {}
        for s in scores:
            groups.setdefault(s.format, []).append(s)
        return groups

    def group_by_tone(self, scores: list[SampleScore]) -> dict[str, list[SampleScore]]:
        """Group scores by tone_preset."""
        groups: dict[str, list[SampleScore]] = {}
        for s in scores:
            groups.setdefault(s.tone_preset, []).append(s)
        return groups

    def assign_review_labels(self, scores: list[SampleScore]) -> list[SampleScore]:
        """Assign human-readable review labels to top scorers in each category.

        Returns new SampleScore objects with labels filled in (original list unchanged).
        """
        if not scores:
            return scores

        labeled = [s for s in scores]  # shallow copy list; SampleScore is frozen

        def _top(key_fn, label: str) -> None:
            ranked = sorted(labeled, key=key_fn, reverse=True)
            best = ranked[0]
            idx = labeled.index(best)
            existing = list(labeled[idx].review_labels)
            if label not in existing:
                existing.append(label)
                labeled[idx] = SampleScore(**{
                    **best.__dict__,
                    "review_labels": existing,
                })

        _top(lambda s: s.score, "★ highest overall score")
        posts = [s for s in labeled if s.format == "post"]
        reels = [s for s in labeled if s.format == "reel"]
        if posts:
            best_post = max(posts, key=lambda s: s.score)
            idx = labeled.index(best_post)
            existing = list(labeled[idx].review_labels)
            if "best post hook" not in existing:
                existing.append("best post hook")
            labeled[idx] = SampleScore(**{**best_post.__dict__, "review_labels": existing})
        if reels:
            best_reel = max(reels, key=lambda s: s.score)
            idx = labeled.index(best_reel)
            existing = list(labeled[idx].review_labels)
            if "best reel opening" not in existing:
                existing.append("best reel opening")
            labeled[idx] = SampleScore(**{**best_reel.__dict__, "review_labels": existing})

        # Most money-aligned
        most_money = max(labeled, key=lambda s: (s.money_alignment == "high", s.score))
        idx = labeled.index(most_money)
        existing = list(labeled[idx].review_labels)
        if "most money-aligned" not in existing:
            existing.append("most money-aligned")
        labeled[idx] = SampleScore(**{**most_money.__dict__, "review_labels": existing})

        return labeled

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_comparison_table(self, scores: list[SampleScore]) -> str:
        """Format a compact comparison table for all scores."""
        if not scores:
            return "(no samples to compare)"

        lines = [
            "",
            f"{'#':<3} {'FORMAT':<6} {'TONE':<22} {'HOOK STR':<8} {'MONEY':<7} {'PLANET':<7} {'SCORE':<6} HOOK",
            "-" * 100,
        ]
        ranked = self.rank_by_score(scores)
        for i, s in enumerate(ranked, 1):
            planet_flag = "✓" if s.has_planet_name else "·"
            labels = f"  [{', '.join(s.review_labels)}]" if s.review_labels else ""
            hook_truncated = s.hook[:60] + ("…" if len(s.hook) > 60 else "")
            lines.append(
                f"{i:<3} {s.format:<6} {s.tone_preset:<22} "
                f"{s.hook_strength:<8} {s.money_alignment:<7} {planet_flag:<7} "
                f"{s.score:<6} {hook_truncated}{labels}"
            )
        return "\n".join(lines)

    def format_ranked_summary(self, scores: list[SampleScore], show_full_hook: bool = True) -> str:
        """Format a detailed ranked summary with full hook text."""
        if not scores:
            return "(no samples to compare)"

        labeled = self.assign_review_labels(scores)
        ranked = self.rank_by_score(labeled)

        lines = ["\n" + "=" * 70, "  RANKED CONTENT SAMPLES", "=" * 70]
        for i, s in enumerate(ranked, 1):
            label_str = ("  [" + " | ".join(s.review_labels) + "]") if s.review_labels else ""
            lines += [
                f"\n#{i}  {s.format.upper()}  score={s.score}/10  "
                f"tone={s.tone_preset}  hook={s.hook_strength}  money={s.money_alignment}{label_str}",
                f"   Planet: {'YES' if s.has_planet_name else 'no'}  "
                f"House ref: {'YES' if s.has_house_reference else 'no'}  "
                f"Hook words: {s.hook_word_count}",
            ]
            if show_full_hook:
                lines.append(f"   Hook   : {s.hook}")
                if s.hook_full and s.hook_full != s.hook:
                    lines.append(f"   Full   : {s.hook_full[:120]}")
            if s.angle:
                lines.append(f"   Angle  : {s.angle}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def format_tone_comparison(
        self, scores: list[SampleScore], format_filter: str | None = None
    ) -> str:
        """Format a side-by-side hook comparison grouped by tone preset."""
        filtered = [s for s in scores if format_filter is None or s.format == format_filter]
        if not filtered:
            return f"(no samples for format={format_filter!r})"

        by_tone = self.group_by_tone(filtered)
        lines = [
            "\n" + "=" * 70,
            f"  HOOK COMPARISON BY TONE PRESET  "
            f"({'all formats' if format_filter is None else format_filter.upper()})",
            "=" * 70,
        ]
        for tone, tone_scores in sorted(by_tone.items()):
            best = max(tone_scores, key=lambda s: s.score)
            lines += [
                f"\nTone: {tone}  (best score: {best.score}/10, "
                f"money={best.money_alignment}, hook={best.hook_strength})",
                f"  Hook    : {best.hook}",
            ]
            if best.hook_full and best.hook_full != best.hook:
                lines.append(f"  Full    : {best.hook_full[:100]}")
            lines.append(f"  Planet  : {'YES' if best.has_planet_name else 'no'}  "
                         f"House: {'YES' if best.has_house_reference else 'no'}")
        lines.append("")
        return "\n".join(lines)
