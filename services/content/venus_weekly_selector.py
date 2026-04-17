"""Venus Weekly Trend Selector — editorial selection layer on top of Venus Sign Climate
and Venus Aspect Overlay.

This is NOT a new astrology engine.
It is an editorial tool that scans a 7-day window and produces a structured
content brief: one main post angle, one main reel angle, one support angle.

Usage:
    package = VenusWeeklySelector.select_for_week(
        start_date=date(2026, 4, 13),
        astro_days=[...],   # optional list of AstroDayPayload for the week
    )

The package contains:
- ready-to-use context objects (climate_ctx, overlay_ctx) for generation
- editorial angles (post / reel / support) as concrete prompt hints
- scoring rationale (for editorial review / ops logs)

Design notes:
- Uses ephemeris for Venus sign (always available)
- Uses provided AstroDayPayload signals for overlay detection (optional)
- When no signals → climate-only package
- When multiple Venus overlays → picks highest-scoring one
- Scoring heuristic: curated pattern > intensity > tight orb > friction
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from astro_content_agent.astro.ephemeris import compute_positions
from astro_content_agent.schemas.astro import AstroDayPayload
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.venus_aspect_overlay import (
    VenusAspectOverlayContext,
    _CURATED_PATTERNS,
)
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext


# ---------------------------------------------------------------------------
# Hook-family taxonomy
# ---------------------------------------------------------------------------
# Maps (sign, pair_key | None) → editorial hook family label.
# These describe the *category* of hooks that will work best, not a single hook.

_HOOK_FAMILY: dict[tuple[str, str | None], str] = {
    # Overlay-driven families
    ("Taurus",      "pluto_venus"):    "владение_vs_ценность",
    ("Taurus",      "mars_venus"):     "стабильность_vs_импульс",
    ("Gemini",      "mars_venus"):     "движение_vs_рассеивание",
    ("Gemini",      "pluto_venus"):    "гибкость_vs_скрытый_контроль",
    ("Cancer",      "mars_venus"):     "защита_vs_тревожная_покупка",
    ("Cancer",      "pluto_venus"):    "безопасность_vs_крепость_из_страха",
    ("Leo",         "pluto_venus"):    "признание_vs_одержимость_статусом",
    ("Leo",         "mars_venus"):     "щедрость_vs_соревнование",
    ("Virgo",       "pluto_venus"):    "контроль_vs_одержимость_точностью",
    ("Virgo",       "mars_venus"):     "анализ_vs_давление_решить_сейчас",
    ("Libra",       "pluto_venus"):    "баланс_vs_силовая_динамика",
    ("Libra",       "mars_venus"):     "гармония_vs_нетерпение",
    ("Scorpio",     "pluto_venus"):    "обладание_vs_власть_над_ресурсом",
    ("Scorpio",     "mars_venus"):     "контроль_vs_срыв",
    ("Sagittarius", "mars_venus"):     "масштаб_vs_импульсная_трата",
    ("Sagittarius", "pluto_venus"):    "расширение_vs_одержимость",
    ("Capricorn",   "pluto_venus"):    "труд_vs_страх_бедности",
    ("Capricorn",   "mars_venus"):     "дисциплина_vs_давление_действовать",
    ("Aquarius",    "mars_venus"):     "принцип_vs_дорогой_импульс",
    ("Aquarius",    "pluto_venus"):    "независимость_vs_идеологический_контроль",
    ("Pisces",      "mars_venus"):     "чуйка_vs_нетерпение",
    ("Pisces",      "pluto_venus"):    "интуиция_vs_страх",
    # Climate-only families (no overlay)
    ("Aries",       None):            "желание_и_скорость",
    ("Taurus",      None):            "накопление_и_инерция",
    ("Gemini",      None):            "движение_и_рассеивание",
    ("Cancer",      None):            "безопасность_и_тревога",
    ("Leo",         None):            "статус_и_порыв",
    ("Virgo",       None):            "расчёт_и_заморозка",
    ("Libra",       None):            "гармония_и_нерешительность",
    ("Scorpio",     None):            "контроль_и_компульсия",
    ("Sagittarius", None):            "масштаб_и_прожигание",
    ("Capricorn",   None):            "труд_и_страх_успеха",
    ("Aquarius",    None):            "идея_и_непоследовательность",
    ("Pisces",      None):            "наитие_и_утечка",
}


def _hook_family(sign: str, pair_key: str | None) -> str:
    return _HOOK_FAMILY.get((sign, pair_key), f"денежный_климат_{sign.lower()}")


# ---------------------------------------------------------------------------
# Compensation focus
# ---------------------------------------------------------------------------

_COMPENSATION_FOCUS: dict[tuple[str, str | None], str] = {
    ("Taurus",      "pluto_venus"):    "честная цена без торга из тревоги; плотная реальная ценность, а не контроль",
    ("Taurus",      "mars_venus"):     "спокойный темп + осознанное решение; комфорт как выбор, не как укрытие",
    ("Gemini",      "mars_venus"):     "один приоритет за раз; ритм вместо скорости; завершённые циклы",
    ("Gemini",      "pluto_venus"):    "прозрачность в переговорах; фокус вместо многоканальности",
    ("Cancer",      "mars_venus"):     "разделить «защита» и «тревожная трата»; конкретная подушка vs эмоциональный расход",
    ("Cancer",      "pluto_venus"):    "накопление с планом использования; ресурс как свобода, а не крепость",
    ("Leo",         "pluto_venus"):    "трата на актив, а не на признание; образ как стратегия, не как компульсия",
    ("Leo",         "mars_venus"):     "щедрость из силы, а не из соревнования; ценовой барьер без порыва",
    ("Virgo",       "pluto_venus"):    "анализ с дедлайном; эффективность без бесконечной оптимизации",
    ("Virgo",       "mars_venus"):     "решение в срок; действие без идеальных условий",
    ("Libra",       "pluto_venus"):    "честная цена в отношениях; баланс без подчинения",
    ("Libra",       "mars_venus"):     "один выбор сейчас; гармония не за счёт своей позиции",
    ("Scorpio",     "pluto_venus"):    "инвестиция, а не владение; трансформация через форму",
    ("Scorpio",     "mars_venus"):     "импульс в стратегию; контроль с горизонтом",
    ("Sagittarius", "mars_venus"):     "один масштабный проект; бюджетированная амбиция",
    ("Sagittarius", "pluto_venus"):    "экспансия с контейнером; рост по форме",
    ("Capricorn",   "pluto_venus"):    "разрешение пользоваться накопленным; структура не как клетка",
    ("Capricorn",   "mars_venus"):     "действие без идеальных условий; дисциплина + движение",
    ("Aquarius",    "mars_venus"):     "бюджет для нестандартного; система для свободы",
    ("Aquarius",    "pluto_venus"):    "принцип с практикой; независимость без идеологии",
    ("Pisces",      "mars_venus"):     "пауза перед «надо»; отделить чуйку от импульса",
    ("Pisces",      "pluto_venus"):    "структура для интуиции; финансовый учёт без убийства чувства",
}

_CLIMATE_COMPENSATION_FOCUS: dict[str, str] = {
    "Aries":       "пауза перед покупкой; осознанная скорость, не хаотичный импульс",
    "Taurus":      "плотная реальная ценность без инерции; накопление с точкой использования",
    "Gemini":      "один финансовый приоритет; завершённый цикл важнее нового начала",
    "Cancer":      "отдельная подушка безопасности; не путать защиту и тревожную трату",
    "Leo":         "трата на актив, а не на образ; ценовой барьер из достоинства",
    "Virgo":       "анализ с дедлайном; прагматизм не в ущерб росту",
    "Libra":       "один честный выбор без компромисса ценой самой позиции",
    "Scorpio":     "прозрачность перед собой; инвестиционный инстинкт без компульсии",
    "Sagittarius": "бюджетированная амбиция; один масштабный шаг вместо десяти",
    "Capricorn":   "разрешение пользоваться накопленным; структура как инструмент, не как клетка",
    "Aquarius":    "система для нестандартного; бюджет не убивает принцип",
    "Pisces":      "финансовый учёт без жёсткости; форма для интуиции",
}


def _compensation_focus(sign: str, pair_key: str | None) -> str:
    if pair_key:
        return _COMPENSATION_FOCUS.get((sign, pair_key), _CLIMATE_COMPENSATION_FOCUS.get(sign, ""))
    return _CLIMATE_COMPENSATION_FOCUS.get(sign, "")


# ---------------------------------------------------------------------------
# Overlay scoring
# ---------------------------------------------------------------------------

@dataclass
class _ScoredOverlay:
    """Internal scoring record — one per Venus-involving signal found in the week."""
    day: date
    overlay_ctx: VenusAspectOverlayContext
    intensity: float
    orb: float
    score: float
    has_curated_pattern: bool
    signal_key: str


def _score_overlay(
    day: date,
    overlay_ctx: VenusAspectOverlayContext,
    signal_intensity: float,
    signal_orb: float,
    signal_key: str,
) -> _ScoredOverlay:
    """Score a single Venus overlay match.

    Factors (in rough priority order):
    1. Curated pattern exists (+1.0) — known sign×pair combination; will produce richer content
    2. Friction mode (+0.5) — sharper hooks, more content-worthy
    3. Intensity (+0 to +0.5) — stronger signal = more notable
    4. Tight orb (+0 to +0.3) — orb ≤ 1° = right at exact; orb > 5° = weak
    """
    ov = overlay_ctx.overlay
    pair_key = ov.aspect_key or ""
    sign = ov.venus_sign or ""

    has_curated = (sign, pair_key) in _CURATED_PATTERNS

    score = (
        (1.0 if has_curated else 0.0)
        + (0.5 if ov.overlay_mode == "friction" else 0.0)
        + min(0.5, signal_intensity * 0.5)
        + max(0.0, (5.0 - signal_orb) / 5.0) * 0.3
    )

    return _ScoredOverlay(
        day=day,
        overlay_ctx=overlay_ctx,
        intensity=signal_intensity,
        orb=signal_orb,
        score=score,
        has_curated_pattern=has_curated,
        signal_key=signal_key,
    )


# ---------------------------------------------------------------------------
# Editorial angle builders
# ---------------------------------------------------------------------------

def _post_angle(
    climate_ctx: VenusSignClimateContext,
    best: _ScoredOverlay | None,
) -> str:
    """Derive the main post angle as a concrete editorial directive."""
    climate = climate_ctx.climate
    if not climate:
        return "Текущий денежный климат Венеры — фоновое поведение и паттерн недели."
    if best and best.overlay_ctx.overlay.active:
        ov = best.overlay_ctx.overlay
        pattern = ov.combined_pattern[0] if ov.combined_pattern else ""
        leak = climate.likely_leak[0] if climate.likely_leak else ""
        return (
            f"Глубокое объяснение: {pattern}. "
            f"Показать, как это искажение проявляется в реальных деньгах: {leak}. "
            f"Завершить компенсационным блоком."
        )
    # Climate-only
    leak = climate.likely_leak[0] if climate.likely_leak else ""
    money = climate.money_style.split(".")[0].strip()
    return (
        f"Паттерн недели: {money}. "
        f"Назвать главную утечку этого климата: {leak}. "
        f"Показать, где сила и где ловушка."
    )


def _reel_angle(
    climate_ctx: VenusSignClimateContext,
    best: _ScoredOverlay | None,
) -> str:
    """Derive the main reel angle as a concrete editorial directive."""
    climate = climate_ctx.climate
    if best and best.overlay_ctx.overlay.active:
        hook_sug = best.overlay_ctx.overlay.instagram_hook_suggestion
        mode = best.overlay_ctx.overlay.overlay_mode
        return (
            f"Быстрый рилс: открыть через «{hook_sug}». "
            f"Recognition beat — {mode} pattern. "
            f"Короткий compensation beat. CTA: сохрани/напиши."
        )
    if climate:
        hook = climate.instagram_hook_angles[0] if climate.instagram_hook_angles else ""
        return (
            f"Климатный рилс: зацепка «{hook}». "
            f"Назвать pattern этого знака. Компенсация коротко. CTA органический."
        )
    return "Рилс по текущему климату Венеры: recognition + compensation."


def _support_angle(
    climate_ctx: VenusSignClimateContext,
    best: _ScoredOverlay | None,
) -> str:
    """Derive the lighter support/stories angle."""
    climate = climate_ctx.climate
    if best and best.overlay_ctx.overlay.active:
        ov = best.overlay_ctx.overlay
        if ov.overlay_mode == "friction" and climate:
            leak = climate.likely_leak[1] if len(climate.likely_leak) > 1 else climate.likely_leak[0] if climate.likely_leak else ""
            return f"Сторис / карточка: «Утечка недели» — {leak}. Один конкретный совет."
        if climate:
            strength = climate.likely_strength[0] if climate.likely_strength else ""
            return f"Сторис / карточка: «Возможность недели» — {strength}. Коротко и конкретно."
    if climate:
        strength = climate.likely_strength[0] if climate.likely_strength else ""
        return f"Напоминание о силе климата: {strength}."
    return "Лёгкое напоминание о текущем денежном климате."


# ---------------------------------------------------------------------------
# Weekly Venus Package
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WeeklyVenusPackage:
    """Editorial content brief for the strongest Venus-related Instagram content
    in a 7-day window.

    Contains both the structured editorial picks (angles, hooks, compensation) and
    the ready-to-use context objects that can be passed directly to content generation.
    """

    # Week window
    week_start: date
    week_end: date

    # Venus climate
    venus_sign: str
    climate_title: str
    climate_ctx: VenusSignClimateContext

    # Best overlay (None if no Venus aspect active this week)
    overlay_ctx: VenusAspectOverlayContext | None
    overlay_active: bool
    overlay_mode: str           # "friction" | "opportunity" | "climate_only"
    overlay_pair: str | None    # e.g. "pluto_venus" | "mars_venus" | None
    best_day: date | None       # day with highest-scoring overlay signal

    # Editorial picks
    primary_post_angle: str
    primary_reel_angle: str
    support_angle: str
    hook_family: str
    compensation_focus: str

    # Scoring context (for ops / editorial review)
    scored_overlays: tuple[dict[str, Any], ...]   # all candidates, sorted by score
    selection_rationale: str
    editorial_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Replace non-serialisable context objects with their dicts
        d["climate_ctx"] = self.climate_ctx.to_dict()
        d["overlay_ctx"] = self.overlay_ctx.to_dict() if self.overlay_ctx else None
        d["week_start"] = self.week_start.isoformat()
        d["week_end"] = self.week_end.isoformat()
        d["best_day"] = self.best_day.isoformat() if self.best_day else None
        return d


# ---------------------------------------------------------------------------
# Selector
# ---------------------------------------------------------------------------

class VenusWeeklySelector:
    """Editorial selector that produces one WeeklyVenusPackage per 7-day window.

    The selector:
    1. Uses ephemeris to find Venus sign for each day of the week
    2. Scans provided AstroDayPayload objects for active Venus aspect overlays
    3. Scores each overlay candidate using a simple editorial heuristic
    4. Returns the best overlay (or climate-only if none found)
    5. Derives editorial angles and hook family from the winning combination

    Scoring heuristic (descending priority):
    - Curated pattern exists for (sign, pair) in _CURATED_PATTERNS (+1.0)
    - Friction mode overlay (+0.5)
    - Signal intensity × 0.5 (up to +0.5)
    - Tight orb: (5 - orb) / 5 × 0.3 (up to +0.3)

    Maximum score: 2.3 (curated + friction + intensity=1.0 + orb=0)
    Climate-only baseline: 0.0 (always valid fallback)
    """

    @classmethod
    def select_for_week(
        cls,
        start_date: date,
        astro_days: list[AstroDayPayload] | None = None,
    ) -> WeeklyVenusPackage:
        """Build the weekly editorial package.

        Args:
            start_date: First day of the 7-day window.
            astro_days: Optional list of pre-computed AstroDayPayload objects for
                        the week.  When None, the package is climate-only (no overlay
                        analysis, since signal data is unavailable).

        Returns:
            WeeklyVenusPackage — structured editorial brief.
        """
        week_end = start_date + timedelta(days=6)

        # Step 1 — determine dominant Venus sign for the week using ephemeris
        venus_sign, retrograde = cls._dominant_venus_sign(start_date)
        climate_ctx = VenusSignClimateContext.from_sign(venus_sign, retrograde=retrograde)
        climate = climate_ctx.climate
        climate_title = climate.climate_title if climate else f"Венера в {venus_sign}"

        # Step 2 — scan provided astro_days for Venus overlays
        candidates: list[_ScoredOverlay] = []

        if astro_days:
            for astro_day in astro_days:
                cards_ctx = AspectBehaviorCardsContext.from_astro_day(astro_day)
                day_climate_ctx = VenusSignClimateContext.from_sign(venus_sign, retrograde=retrograde)
                overlay_ctx = VenusAspectOverlayContext.from_contexts(day_climate_ctx, cards_ctx)

                if not overlay_ctx.overlay.active:
                    continue

                # Pick the best Venus-involving signal from this day's matches
                for m in cards_ctx.matches:
                    from astro_content_agent.services.content.venus_aspect_overlay import _involves_venus
                    if not _involves_venus(m["pair_key"]):
                        continue
                    scored = _score_overlay(
                        day=astro_day.day,
                        overlay_ctx=overlay_ctx,
                        signal_intensity=m.get("intensity", 0.5),
                        signal_orb=m.get("orb", 3.0),
                        signal_key=m.get("signal_key", ""),
                    )
                    candidates.append(scored)
                    break  # one per day is enough

        # Step 3 — sort candidates by score (highest first)
        candidates.sort(key=lambda c: c.score, reverse=True)

        # Step 4 — pick winner
        best: _ScoredOverlay | None = candidates[0] if candidates else None

        # Step 5 — build package fields
        if best:
            overlay_ctx_out = best.overlay_ctx
            overlay_mode = best.overlay_ctx.overlay.overlay_mode
            overlay_pair = best.overlay_ctx.overlay.aspect_key
            best_day_out = best.day
            rationale = cls._build_rationale(best, candidates[1:])
            editorial_notes = cls._build_notes(best, climate_ctx, retrograde)
        else:
            overlay_ctx_out = None
            overlay_mode = "climate_only"
            overlay_pair = None
            best_day_out = None
            rationale = (
                f"Активных аспектов к Венере на этой неделе не обнаружено. "
                f"Контент строится на климате знака: {venus_sign}."
            )
            editorial_notes = cls._build_climate_notes(climate_ctx, retrograde)

        scored_dicts = tuple(
            {
                "day": c.day.isoformat(),
                "signal_key": c.signal_key,
                "pair_key": c.overlay_ctx.overlay.aspect_key,
                "mode": c.overlay_ctx.overlay.overlay_mode,
                "intensity": round(c.intensity, 3),
                "orb": round(c.orb, 3),
                "score": round(c.score, 3),
                "has_curated_pattern": c.has_curated_pattern,
            }
            for c in candidates
        )

        return WeeklyVenusPackage(
            week_start=start_date,
            week_end=week_end,
            venus_sign=venus_sign,
            climate_title=climate_title,
            climate_ctx=climate_ctx,
            overlay_ctx=overlay_ctx_out,
            overlay_active=best is not None,
            overlay_mode=overlay_mode,
            overlay_pair=overlay_pair,
            best_day=best_day_out,
            primary_post_angle=_post_angle(climate_ctx, best),
            primary_reel_angle=_reel_angle(climate_ctx, best),
            support_angle=_support_angle(climate_ctx, best),
            hook_family=_hook_family(venus_sign, overlay_pair),
            compensation_focus=_compensation_focus(venus_sign, overlay_pair),
            scored_overlays=scored_dicts,
            selection_rationale=rationale,
            editorial_notes=editorial_notes,
        )

    # ---------------------------------------------------------------------------
    # Internal builders
    # ---------------------------------------------------------------------------

    @staticmethod
    def _dominant_venus_sign(start_date: date) -> tuple[str, bool]:
        """Return (sign, retrograde) for Venus at midweek (day 3 of the window).

        Midweek is the most representative day — avoids sign-change edge cases
        that can occur on the first or last day of the window.
        """
        midweek = start_date + timedelta(days=3)
        positions = compute_positions(midweek)
        venus = positions["Venus"]
        return venus.sign, venus.retrograde

    @staticmethod
    def _build_rationale(
        best: _ScoredOverlay,
        runners_up: list[_ScoredOverlay],
    ) -> str:
        ov = best.overlay_ctx.overlay
        lines: list[str] = [
            f"Выбран оверлей: {ov.aspect_key} ({ov.overlay_mode}) в знаке {ov.venus_sign}.",
            f"  Оценка: {best.score:.2f} "
            f"(паттерн в таблице: {best.has_curated_pattern}, "
            f"интенсивность: {best.intensity:.2f}, орб: {best.orb:.1f}°)",
            f"  Сигнал: {best.signal_key}  |  день: {best.day}",
        ]
        if runners_up:
            lines.append("Альтернативы (отклонены по очкам):")
            for r in runners_up[:3]:
                rv = r.overlay_ctx.overlay
                lines.append(
                    f"  - {rv.aspect_key} / {rv.overlay_mode} "
                    f"| score={r.score:.2f} | день={r.day}"
                )
        else:
            lines.append("Других кандидатов на этой неделе нет.")
        return "\n".join(lines)

    @staticmethod
    def _build_notes(
        best: _ScoredOverlay,
        climate_ctx: VenusSignClimateContext,
        retrograde: bool,
    ) -> tuple[str, ...]:
        ov = best.overlay_ctx.overlay
        climate = climate_ctx.climate
        notes: list[str] = [
            f"Основной сигнал недели: {ov.aspect_key} в знаке {ov.venus_sign} "
            f"({'ретроградная Венера — добавь осторожность' if retrograde else 'прямой ход'}).",
        ]
        if ov.combined_pattern:
            notes.append(f"Паттерн наложения: {ov.combined_pattern[0]}")
        if climate:
            notes.append(f"Климатный контекст: {climate.money_style[:100]}...")
        if ov.overlay_mode == "friction":
            notes.append(
                "Режим: friction — используй острые зацепки; "
                "compensation block обязателен в посте."
            )
        else:
            notes.append(
                "Режим: opportunity — климат ведёт; "
                "аспект как открытие/усиление."
            )
        notes.append(f"Хук-семья: {_hook_family(ov.venus_sign or '', ov.aspect_key)}")
        return tuple(notes)

    @staticmethod
    def _build_climate_notes(
        climate_ctx: VenusSignClimateContext,
        retrograde: bool,
    ) -> tuple[str, ...]:
        climate = climate_ctx.climate
        notes: list[str] = []
        if retrograde:
            notes.append(
                "Венера ретроградная — подчёркивай тему пересмотра ценностей, "
                "возврата к старым паттернам, переоценки."
            )
        if climate:
            notes.append(
                f"Климат без оверлея: {climate.climate_title}. "
                f"Сила: {climate.likely_strength[0] if climate.likely_strength else '—'}."
            )
            notes.append(
                f"Главная утечка: {climate.likely_leak[0] if climate.likely_leak else '—'}."
            )
        return tuple(notes)
