"""Venus Aspect Overlay — composition logic for Venus Sign Climate + Venus aspect.

When Venus is part of an active transit aspect AND a Venus Sign Climate is registered,
this overlay provides explicit generation directives that tell the LLM *how* to combine:

  - venus_sign_climate_context  (background: collective money/value/comfort style)
  - aspect_behavior_cards_context  (trigger: what Venus aspect is doing right now)

This is NOT a new astrology engine and does NOT generate content itself.
It produces structured context injected as ``venus_aspect_overlay_context`` into the
prompt payload alongside the two existing context objects.

Design principles:
- Additive only — existing contexts remain unchanged
- Minimal: one module, one dataclass, one context builder
- Deterministic: all logic is derived from already-computed contexts, no new IO
- Curated for known Venus pairs; generic fallback for unknown combinations

Extension: add entries to ``_CURATED_PATTERNS`` and ``_HOOK_SUGGESTIONS`` for new pairs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _involves_venus(pair_key: str) -> bool:
    """True when the canonical pair key names Venus as one of the two planets."""
    return "venus" in pair_key.split("_")


def _overlay_mode(polarity: str | None) -> str:
    if polarity == "harmonious":
        return "opportunity"
    return "friction"   # tense or ambiguous conjunction both default to friction


def _hook_priority(mode: str) -> str:
    """Aspect leads the hook for friction; climate leads for opportunity."""
    return "aspect_first" if mode == "friction" else "climate_first"


def _compensation_priority(mode: str) -> str:
    """Friction → weave both layers; opportunity → aspect card alone is enough."""
    return "both_layers" if mode == "friction" else "aspect_card"


# ---------------------------------------------------------------------------
# Curated combined patterns (sign × pair_key → interaction bullets)
# ---------------------------------------------------------------------------
#
# Each tuple describes how the Venus climate is *modified* by the aspect.
# Format: 3–4 short bullets (Russian), concrete, sharp, no generic astrology.
# These are generation hints — the LLM adapts them, not quotes them.
#
# Key format: (sign_name, canonical_pair_key)  e.g. ("Taurus", "pluto_venus")
# ---------------------------------------------------------------------------

_CURATED_PATTERNS: dict[tuple[str, str], tuple[str, ...]] = {
    # ── Taurus combos ──────────────────────────────────────────────────────
    ("Taurus", "pluto_venus"): (
        "удержание превращается в одержимость владением, а не в стабильность",
        "накопление становится невозможностью отпустить даже то, что уже не работает",
        "стремление к безопасности смещается в контроль и собственничество",
        "сенсорная ценность — что приятно держать в руках — уходит в зацикленность на обладании",
    ),
    ("Taurus", "mars_venus"): (
        "медленный накопительный инстинкт сталкивается с импульсом немедленного действия",
        "желание стабильности под давлением Марса превращается в раздражение от «слишком медленно»",
        "каждое финансовое решение становится полем напряжения: подождать или взять сейчас",
        "Марс не даёт удержать тот темп, на котором Телец чувствует себя в безопасности",
    ),

    # ── Gemini combos ──────────────────────────────────────────────────────
    ("Gemini", "mars_venus"): (
        "варианты и гибкость превращаются в соревновательное рассеивание под давлением желания",
        "любопытство переходит в нетерпение — импульсивные денежные решения из конкуренции",
        "обмен и движение приобретают привкус спора: кто быстрее, кто интереснее, кто больше",
        "гибкость рассыпается в несколько одновременно открытых и незакрытых фронтов",
    ),
    ("Gemini", "pluto_venus"): (
        "лёгкость движения встречает глубинный контроль — и начинаются скрытые игры в переговорах",
        "интерес к вариантам становится одержимостью одним — но под маской гибкости",
        "обмен теряет нейтральность: кто владеет информацией, тот управляет ситуацией",
        "рассеивание заменяется фиксацией, которую сложно заметить снаружи",
    ),

    # ── Cancer combos ──────────────────────────────────────────────────────
    ("Cancer", "mars_venus"): (
        "потребность в финансовой безопасности сталкивается с агрессивным импульсом желания",
        "эмоциональные траты усиливаются: «мне это нужно сейчас» становится острее и быстрее",
        "тревога вокруг денег приобретает активный, защитный, почти боевой характер",
        "накопительный инстинкт и импульс к немедленной трате работают одновременно и против друг друга",
    ),
    ("Cancer", "pluto_venus"): (
        "деньги как лекарство от страха приобретают оттенок контроля и скрытой власти",
        "накопление перестаёт быть безопасностью — становится попыткой не быть уязвимым",
        "эмоциональные траты уступают место тихому, но интенсивному удержанию",
        "страх потери обостряется до уровня, где даже разумные расходы кажутся угрозой",
    ),

    # ── Leo combos ─────────────────────────────────────────────────────────
    ("Leo", "pluto_venus"): (
        "желание статуса и признания обостряется до компульсии быть замеченным любой ценой",
        "траты на образ и видимость теряют меру: цена признания незаметно перестаёт быть важной",
        "щедрость превращается в инструмент влияния — «я даю, значит, я веду»",
        "страх потерять статус становится сильнее ценности самого статуса",
    ),
    ("Leo", "mars_venus"): (
        "порывистые траты на образ и роскошь становятся ещё более импульсивными",
        "конкуренция за видимость активируется: «кто круче» вместо «что нужно»",
        "щедрость из лидерства превращается в щедрость из соперничества",
        "финансовые решения принимаются быстрее, ярче и дороже, чем требует ситуация",
    ),

    # ── Virgo combos ───────────────────────────────────────────────────────
    ("Virgo", "pluto_venus"): (
        "расчётливость становится одержимостью контролем: каждая цифра должна быть правильной",
        "экономность превращается в жёсткую самоцель, а не инструмент",
        "прагматизм с Плутоном — это уже не «разумно», а «не могу иначе»",
        "дисциплина накопления уходит в скрытый страх потерять контроль над каждым рублём",
    ),
    ("Virgo", "mars_venus"): (
        "потребность в анализе сталкивается с Марсом, который требует решения сейчас",
        "расчётливость трещит под напором импульса: «считать» vs «брать» в постоянном конфликте",
        "оптимизация под давлением Марса становится раздражением на всё «недостаточно идеальное»",
        "гиперанализ обостряется — или, наоборот, рвётся под импульсом в противоположную сторону",
    ),

    # ── Libra combos ───────────────────────────────────────────────────────
    ("Libra", "pluto_venus"): (
        "стремление к гармонии превращается в скрытую силовую динамику в деньгах и партнёрстве",
        "баланс перестаёт быть нейтральным: кто-то контролирует, кто-то подстраивается",
        "красота и эстетика становятся инструментом влияния, а не просто ценностью",
        "нерешительность в тратах усиливается: за каждым выбором — чья-то власть или зависимость",
    ),
    ("Libra", "mars_venus"): (
        "стремление к балансу рвётся под агрессивным желанием и конкуренцией",
        "нерешительность в тратах превращается в раздражение: «почему я всё ещё не выбрал»",
        "гармоничный денежный стиль конфликтует с Марсом, который хочет победить, а не договориться",
        "компромисс становится невозможным — и тогда либо уступают полностью, либо действуют резко",
    ),

    # ── Scorpio combos ─────────────────────────────────────────────────────
    ("Scorpio", "pluto_venus"): (
        "жажда обладания и контроля удваивается — Плутон усиливает то, что и так было интенсивным",
        "хроническая неудовлетворённость обостряется: чем больше есть, тем острее ощущение нехватки",
        "скрытые движения денег становятся ещё непрозрачнее — для себя в том числе",
        "компульсивный слив из накопленного напряжения становится очень вероятным",
    ),
    ("Scorpio", "mars_venus"): (
        "контроль встречает импульс — и Скорпион либо сжимается сильнее, либо срывается",
        "жажда обладания плюс Марс — это желание, которое трудно не реализовать сразу",
        "скрытые денежные решения принимаются под импульсом и потом труднее признать",
        "конкуренция за ресурс становится острой: соперничество, подозрительность, закрытость",
    ),

    # ── Sagittarius combos ─────────────────────────────────────────────────
    ("Sagittarius", "mars_venus"): (
        "лёгкое расставание с деньгами под Марсом становится совсем лёгким — до ущерба",
        "импульс к масштабу ускоряется: «хочу большого — беру сейчас» без расчёта",
        "щедрость приобретает соревновательный привкус: кто щедрее, кто живёт крупнее",
        "деньги уходят быстро, красиво и с ощущением правоты — а потом возникает вопрос «зачем»",
    ),
    ("Sagittarius", "pluto_venus"): (
        "стремление к свободе через деньги встречает Плутона с контролем — и начинается внутренний конфликт",
        "масштаб и экспансия приобретают одержимость: «я должен сделать это большим» без остановок",
        "трата на опыт перестаёт быть свободой — становится компульсией к следующему большому шагу",
        "философия «деньги придут» сталкивается с трансформирующим давлением Плутона",
    ),

    # ── Capricorn combos ───────────────────────────────────────────────────
    ("Capricorn", "pluto_venus"): (
        "страх бедности обостряется до компульсии: копить любой ценой, никогда не достаточно",
        "труд как ценность превращается в труд как единственно допустимую форму существования",
        "контроль над деньгами становится одержимостью — даже при объективном достатке",
        "способность пользоваться накопленным блокируется полностью: деньги есть, но «нельзя»",
    ),
    ("Capricorn", "mars_venus"): (
        "медленное, структурированное накопление встречает Марс, который требует действия сейчас",
        "страх ошибки обостряется: Марс давит на решение, Козерог тормозит — максимальное напряжение",
        "дисциплина и импульс в прямом столкновении: ни один не побеждает без потерь",
        "деньги зарабатываются через труд, но Марс хочет всё сразу — и это не про Козерога",
    ),

    # ── Aquarius combos ────────────────────────────────────────────────────
    ("Aquarius", "mars_venus"): (
        "антиматериализм слетает мгновенно, когда Марс приносит острое желание",
        "непоследовательность в расходах становится резкой: от принципиальной экономии к крупному импульсу",
        "конкуренция идей выходит наружу — «это важнее, и я готов за это заплатить немедленно»",
        "свобода от денег как принцип рушится под конкретным и сильным желанием",
    ),
    ("Aquarius", "pluto_venus"): (
        "независимость как ценность встречает Плутона — и становится идеологическим контролем",
        "антиматериализм приобретает одержимость: «я никогда не буду таким как все» любой ценой",
        "нестандартные траты становятся компульсивными — под маской принципиальности",
        "скрытые денежные решения принимаются из позиции идеи, а не реальной ситуации",
    ),

    # ── Pisces combos ──────────────────────────────────────────────────────
    ("Pisces", "mars_venus"): (
        "денежная интуиция смешивается с Марсом — сложно отличить чуйку от нетерпеливого желания",
        "траты «по наитию» приобретают скорость и агрессивность, которой обычно нет",
        "ослабленный контроль плюс Марс: деньги уходят очень быстро и ещё менее осознанно",
        "внутренний сигнал может оказаться импульсом, а не интуицией — нужна пауза перед «надо»",
    ),
    ("Pisces", "pluto_venus"): (
        "интуиция на деньги смешивается с Плутоном — появляются скрытые страхи и одержимости",
        "ослабленный контроль становится полным растворением в чужой воле или влиянии",
        "параллельная реальность с деньгами углубляется: Плутон добавляет скрытые слои",
        "чуйка превращается в тревожную фиксацию: ощущение, что деньги — это что-то опасное",
    ),
}


def _get_combined_pattern(sign: str, pair_key: str) -> tuple[str, ...]:
    """Return curated pattern, falling back to a generic dynamic description."""
    curated = _CURATED_PATTERNS.get((sign, pair_key))
    if curated:
        return curated
    # Generic fallback — names the dynamic without specific bullets
    planets = pair_key.split("_")
    other = next((p for p in planets if p != "venus"), "аспектная планета")
    return (
        f"текущий климат Венеры в знаке {sign} получает дополнительное напряжение через аспект",
        f"основная утечка этого климата усиливается через {other}",
        "обращай внимание на то, как желания и ценности искажаются под аспектом",
    )


# ---------------------------------------------------------------------------
# Curated hook suggestions for key sign × aspect combinations
# ---------------------------------------------------------------------------

_HOOK_SUGGESTIONS: dict[tuple[str, str], str] = {
    ("Taurus",      "pluto_venus"):    "Накопление подушки vs одержимость запасом: ты копишь смысл — или уже не отпускаешь ни копейки?",
    ("Taurus",      "mars_venus"):     "Стабильность vs скорость — кто сейчас побеждает в твоих деньгах?",
    ("Gemini",      "mars_venus"):     "Это движение к деньгам — или бегство от одного варианта к другому под давлением?",
    ("Gemini",      "pluto_venus"):    "В этом обмене кто на самом деле контролирует информацию и ресурс?",
    ("Cancer",      "mars_venus"):     "Это финансовая защита — или тревожная покупка в режиме страха?",
    ("Cancer",      "pluto_venus"):    "Ты копишь безопасность — или строишь неприступную крепость из страха?",
    ("Leo",         "pluto_venus"):    "Ты платишь за признание — или уже за страх его потерять?",
    ("Leo",         "mars_venus"):     "Это щедрость — или соревнование за то, кто живёт ярче?",
    ("Virgo",       "pluto_venus"):    "Ты контролируешь деньги — или деньги контролируют каждую твою мысль?",
    ("Virgo",       "mars_venus"):     "Это анализ — или Марс уже требует решения, пока ты считаешь?",
    ("Libra",       "pluto_venus"):    "В этом балансе кто на самом деле управляет ресурсом?",
    ("Libra",       "mars_venus"):     "Это поиск гармонии — или ты просто не можешь больше ждать?",
    ("Scorpio",     "pluto_venus"):    "Деньги как власть — или власть над собой через отказ от денег?",
    ("Scorpio",     "mars_venus"):     "Контроль — или всё-таки срыв? Скорпион + Марс делают выбор сложным.",
    ("Sagittarius", "mars_venus"):     "Это инвестиция в масштаб — или Марс просто торопит без плана?",
    ("Sagittarius", "pluto_venus"):    "Ты расширяешь горизонт — или Плутон превратил это в одержимость?",
    ("Capricorn",   "pluto_venus"):    "Ты контролируешь деньги — или страх бедности управляет тобой?",
    ("Capricorn",   "mars_venus"):     "Марс требует действия. Козерог требует уверенности. Чья очередь?",
    ("Aquarius",    "mars_venus"):     "Это принцип — или просто дорогой импульс в режиме идеи?",
    ("Aquarius",    "pluto_venus"):    "Антиматериализм — это свобода или новый способ всё контролировать?",
    ("Pisces",      "mars_venus"):     "Это чуйка говорит «надо» — или Марс торопит без причины?",
    ("Pisces",      "pluto_venus"):    "Интуиция на деньги — или Плутон уже добавил к ней страх?",
}


def _get_hook_suggestion(sign: str, pair_key: str) -> str:
    return _HOOK_SUGGESTIONS.get(
        (sign, pair_key),
        "Что текущий аспект Венеры делает с денежным климатом этого знака?",
    )


# ---------------------------------------------------------------------------
# Overlay record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VenusAspectOverlay:
    """Structured composition directives for Venus climate + Venus aspect generation.

    When ``active`` is True, the LLM should use this overlay to combine the two
    existing context objects rather than treating them as independent.
    When ``active`` is False, each context is used independently per normal rules.
    """

    active: bool
    overlay_mode: str            # "friction" | "opportunity" | "no_overlay"
    venus_sign: str | None
    aspect_key: str | None       # canonical pair key, e.g. "mars_venus", "pluto_venus"
    aspect_polarity: str | None  # "tense" | "harmonious" | None

    # Ready-to-use distilled phrases (Russian) derived from existing context objects
    climate_background: str      # 1–2 sentences: what the Venus climate normally creates
    aspect_trigger: str          # 1 sentence: what the Venus aspect injects into the climate

    # Core overlay output: how the two layers interact
    combined_pattern: tuple[str, ...]  # 3–4 bullets describing the interaction

    # Generation directives
    hook_priority: str            # "aspect_first" | "climate_first"
    compensation_priority: str    # "aspect_card" | "both_layers"
    instagram_hook_suggestion: str  # ready-to-adapt hook phrasing

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def no_overlay(cls) -> "VenusAspectOverlay":
        return cls(
            active=False,
            overlay_mode="no_overlay",
            venus_sign=None,
            aspect_key=None,
            aspect_polarity=None,
            climate_background="",
            aspect_trigger="",
            combined_pattern=(),
            hook_priority="climate_first",
            compensation_priority="aspect_card",
            instagram_hook_suggestion="",
        )


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

@dataclass
class VenusAspectOverlayContext:
    """Derived overlay context computed from already-resolved climate and cards contexts.

    Injected as ``venus_aspect_overlay_context`` in the prompt payload alongside
    ``venus_sign_climate_context`` and ``aspect_behavior_cards_context``.
    """

    overlay: VenusAspectOverlay

    def to_dict(self) -> dict[str, Any]:
        return {"overlay": self.overlay.to_dict()}

    @classmethod
    def from_contexts(
        cls,
        climate_ctx: VenusSignClimateContext,
        cards_ctx: AspectBehaviorCardsContext,
    ) -> "VenusAspectOverlayContext":
        """Build overlay from already-derived climate and cards contexts.

        Returns a no-overlay context if:
        - No Venus Sign Climate is registered for the current sign, OR
        - No matched aspect card involves Venus as one of the planets.
        """
        if not climate_ctx.has_climate or climate_ctx.climate is None:
            return cls(overlay=VenusAspectOverlay.no_overlay())

        # Find the first (strongest) Venus-involving match
        venus_match: dict[str, Any] | None = None
        for m in cards_ctx.matches:
            if _involves_venus(m["pair_key"]):
                venus_match = m
                break

        if venus_match is None:
            return cls(overlay=VenusAspectOverlay.no_overlay())

        climate = climate_ctx.climate
        pair_key: str = venus_match["pair_key"]
        polarity: str | None = venus_match.get("aspect_polarity")
        card_data: dict[str, Any] = venus_match.get("card", {})

        mode = _overlay_mode(polarity)
        sign: str = climate_ctx.sign or "Unknown"

        # Distil climate background: first sentence of money_style
        climate_bg_raw = climate.money_style.strip()
        first_period = climate_bg_raw.find(".")
        climate_bg = (
            climate_bg_raw[: first_period + 1].strip()
            if first_period != -1
            else climate_bg_raw[:120]
        )

        # Distil aspect trigger: first clause of core_tension
        core_tension: str = card_data.get("core_tension", "")
        first_break = min(
            (core_tension.find(sep) for sep in (";", ".", ",") if core_tension.find(sep) != -1),
            default=len(core_tension),
        )
        aspect_trigger = core_tension[:first_break].strip().rstrip(",;")

        overlay = VenusAspectOverlay(
            active=True,
            overlay_mode=mode,
            venus_sign=sign,
            aspect_key=pair_key,
            aspect_polarity=polarity,
            climate_background=climate_bg,
            aspect_trigger=aspect_trigger,
            combined_pattern=_get_combined_pattern(sign, pair_key),
            hook_priority=_hook_priority(mode),
            compensation_priority=_compensation_priority(mode),
            instagram_hook_suggestion=_get_hook_suggestion(sign, pair_key),
        )
        return cls(overlay=overlay)
