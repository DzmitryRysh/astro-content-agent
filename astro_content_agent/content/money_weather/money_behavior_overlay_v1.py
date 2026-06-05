"""Money / financial behavior overlay v1 — aspect → money-weather copy for Catstyle captions.

Philosophy:
- Financial weather / behavioral climate, not deterministic predictions.
- No investment advice; compensation actions are reflective and organizational.
- Sky shows climate; Money Compass shows personal financial nervous system.
"""
from __future__ import annotations

import re
from typing import Final

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_display_ru

CONTENT_ANGLE_MONEY: Final[str] = "money"
CAPTION_OVERLAY_MONEY_WEATHER: Final[str] = "money_weather"

_PLANET_ORDER: Final[tuple[str, ...]] = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

_ASPECT_ALIASES: Final[dict[str, str]] = {
    "opposite": "opposition",
    "opp": "opposition",
    "sq": "square",
}

_GLOBAL_FORBIDDEN_CLAIMS: Final[tuple[str, ...]] = (
    "you will earn",
    "you will lose",
    "you will get rich",
    "buy now",
    "sell now",
    "invest now",
    "trade now",
    "guaranteed profit",
    "guaranteed return",
)

_GLOBAL_SAFETY_NOTES: Final[tuple[str, ...]] = (
    "Не инвестиционный совет. Только поведенческий и организационный фокус.",
    "Аспект описывает климат поля, не предсказывает личный финансовый исход.",
    "Действия — про паузу, ясность и самонаблюдение, не про сделки на рынке.",
)

_DETERMINISTIC_CLAIM_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\byou will (earn|lose|make|get rich)\b", re.I),
    re.compile(r"\b(buy|sell|invest|trade) now\b", re.I),
    re.compile(r"\bты (заработаешь|потеряешь|разбогатеешь)\b", re.I),
    re.compile(r"\b(покупай|продавай|инвестируй|торгуй) (сейчас|немедленно)\b", re.I),
    re.compile(r"\bгарантированн(ая|ый) (прибыль|доход)\b", re.I),
)

_MONEY_PLANET_LINE_RU: Final[dict[str, str]] = {
    "Sun": "Солнце — видимость, лидерство, самоуважение и то, как ты проявляешь авторитет в деньгах и статусе.",
    "Moon": "Луна — эмоциональная безопасность, потребности, привычки и семейные денежные сценарии.",
    "Mercury": "Меркурий — цифры, договорённости, формулировки, сроки и логика сделок.",
    "Venus": "Венера говорит о ценности, выборе, желании, цене и получении.",
    "Mars": "Марс — импульс, действие, скорость и нервная реакция «сделать сейчас».",
    "Jupiter": "Юпитер — рост, масштаб, вера в расширение и риск перераздуть обязательства.",
    "Saturn": "Сатурн — границы, ограничения, структура, цена и внутренние запреты.",
    "Uranus": "Уран — внезапность, срыв шаблона и нервная искра «всё менять сразу».",
    "Neptune": "Нептун — туман, идеализация, размытые ожидания и красивые слова без условий.",
    "Pluto": "Плутон добавляет контроль, власть, зависимость, страх потери и большие ставки.",
}


class MoneyBehaviorOverlay(BaseModel):
    """Structured money-weather overlay for one aspect configuration."""

    aspect_key: str
    money_theme: str
    financial_behavior_pattern: str
    shadow_risk: str
    resource_pattern: str
    compensation_action: str
    business_angle: str
    personal_money_question: str
    money_compass_cta: str
    safety_notes: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    is_curated: bool = True
    money_theme_ru: str | None = None
    financial_behavior_pattern_ru: str | None = None
    shadow_risk_ru: str | None = None
    compensation_action_ru: str | None = None
    personal_money_question_ru: str | None = None


def normalize_aspect_type(aspect_type: str) -> str:
    raw = (aspect_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _ASPECT_ALIASES.get(raw, raw)


def build_aspect_key(planet_a: str, planet_b: str, aspect_type: str) -> str:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = normalize_aspect_type(aspect_type)
    order = {name: idx for idx, name in enumerate(_PLANET_ORDER)}
    first, second = sorted((pa, pb), key=lambda p: order[p])
    return f"{first.lower()}_{asp}_{second.lower()}"


def is_money_content_angle(content_angle: str | None) -> bool:
    return (content_angle or "").strip().lower() in (CONTENT_ANGLE_MONEY, CAPTION_OVERLAY_MONEY_WEATHER)


def _overlay(
    *,
    aspect_key: str,
    money_theme: str,
    financial_behavior_pattern: str,
    shadow_risk: str,
    resource_pattern: str,
    compensation_action: str,
    business_angle: str,
    personal_money_question: str,
    money_compass_cta: str,
    money_theme_ru: str,
    financial_behavior_pattern_ru: str,
    shadow_risk_ru: str,
    compensation_action_ru: str,
    personal_money_question_ru: str,
    forbidden_claims: list[str] | None = None,
) -> MoneyBehaviorOverlay:
    return MoneyBehaviorOverlay(
        aspect_key=aspect_key,
        money_theme=money_theme,
        financial_behavior_pattern=financial_behavior_pattern,
        shadow_risk=shadow_risk,
        resource_pattern=resource_pattern,
        compensation_action=compensation_action,
        business_angle=business_angle,
        personal_money_question=personal_money_question,
        money_compass_cta=money_compass_cta,
        money_theme_ru=money_theme_ru,
        financial_behavior_pattern_ru=financial_behavior_pattern_ru,
        shadow_risk_ru=shadow_risk_ru,
        compensation_action_ru=compensation_action_ru,
        personal_money_question_ru=personal_money_question_ru,
        safety_notes=list(_GLOBAL_SAFETY_NOTES),
        forbidden_claims=list(forbidden_claims or _GLOBAL_FORBIDDEN_CLAIMS),
        is_curated=True,
    )


_CURATED_OVERLAYS: Final[dict[str, MoneyBehaviorOverlay]] = {
    "venus_opposition_pluto": _overlay(
        aspect_key="venus_opposition_pluto",
        money_theme="value versus control",
        financial_behavior_pattern=(
            "money, pricing, desire, self-worth, and receiving meet pressure from power, "
            "control, dependency, and fear of loss"
        ),
        shadow_risk="pricing, buying, selling, or negotiating from fear rather than value",
        resource_pattern=(
            "ability to transform desire into business power, premium positioning, and added value"
        ),
        compensation_action=(
            "pause before financial decisions and name the real fear behind the desire"
        ),
        business_angle="pricing power, client dependency, negotiation leverage, premium offers, shared resources",
        personal_money_question="Who is controlling your price: your value or your fear of losing the deal?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, где твоя финансовая нервная система "
            "реагирует через контроль, зависимость или занижение ценности."
        ),
        money_theme_ru="ценность и контроль; желание и власть; цена и страх потери",
        financial_behavior_pattern_ru=(
            "страх потерять клиента, зависимость от одобрения/денег/статуса, навязчивое желание, "
            "контроль через деньги, ценообразование из страха, притяжение к большим ресурсам"
        ),
        shadow_risk_ru=(
            "цена, покупка, продажа или переговоры из страха, а не из ценности"
        ),
        compensation_action_ru=(
            "замедли перед финансовым решением и назови реальный страх за желанием; "
            "отдели желание от стратегии, не веди переговоры из паники"
        ),
        personal_money_question_ru=(
            "Кто управляет твоей ценой: твоя ценность или страх потерять сделку?"
        ),
    ),
    "venus_square_saturn": _overlay(
        aspect_key="venus_square_saturn",
        money_theme="value versus restriction; price versus guilt; receiving versus inner prohibition",
        financial_behavior_pattern=(
            "undervaluing, discounting, guilt around pleasure, fear of charging more, "
            "fear that clients will leave"
        ),
        shadow_risk="lowering price before anyone objects — guilt dressed as strategy",
        resource_pattern="disciplined value architecture: minimum price, clear deliverable, adult boundaries",
        compensation_action=(
            "name your minimum price, write the value you provide, "
            "do not lower price before the client objects"
        ),
        business_angle="pricing floors, scope discipline, client retention without self-discount",
        personal_money_question="Where does guilt set your price before the market does?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, где твою ценность блокируют "
            "страх, вина или старые денежные правила."
        ),
        money_theme_ru="ценность и ограничение; цена и вина; получение и внутренний запрет",
        financial_behavior_pattern_ru=(
            "занижение цены, скидки «на всякий случай», вина за удовольствие, "
            "страх поднять цену, страх, что клиенты уйдут"
        ),
        shadow_risk_ru="снижение цены до возражения клиента — вина, переодетая в стратегию",
        compensation_action_ru=(
            "назови минимальную цену, выпиши ценность, которую даёшь; "
            "не снижай цену, пока клиент сам не возразил"
        ),
        personal_money_question_ru="Где вина выставляет цену раньше рынка?",
    ),
    "mars_square_uranus": _overlay(
        aspect_key="mars_square_uranus",
        money_theme="impulse versus disruption; action versus nervous system shock",
        financial_behavior_pattern=(
            "sudden spending, sudden quitting, sudden launch, risky impulsive decisions, "
            "financial rebellion, «I need to change everything now»"
        ),
        shadow_risk="strategic courage confused with nervous-system discharge",
        resource_pattern="controlled experiments — one bold move with a safety rail",
        compensation_action=(
            "reduce scale, wait 24 hours, choose one controlled experiment "
            "instead of burning everything down"
        ),
        business_angle="launch timing, burn rate, impulsive pivots, team shock, offer whiplash",
        personal_money_question="Is this a real business move — or your nervous system asking for a reset?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass помогает отделить стратегическую смелость "
            "от разрядки нервной системы."
        ),
        money_theme_ru="импульс и срыв; действие и шок нервной системы",
        financial_behavior_pattern_ru=(
            "внезапные траты, резкий уход, внезапный запуск, рискованные импульсивные решения, "
            "финансовый бунт, «надо всё сменить прямо сейчас»"
        ),
        shadow_risk_ru="стратегическая смелость путается с разрядкой нервной системы",
        compensation_action_ru=(
            "уменьши масштаб, подожди 24 часа, выбери один контролируемый эксперимент "
            "вместо «сжечь всё»"
        ),
        personal_money_question_ru="Это деловой ход — или нервная система просит перезагрузку?",
    ),
    "mercury_square_neptune": _overlay(
        aspect_key="mercury_square_neptune",
        money_theme="numbers versus fog; contracts versus assumptions; logic versus idealization",
        financial_behavior_pattern=(
            "unclear agreements, vague promises, fuzzy pricing, missed details, "
            "believing beautiful words without terms"
        ),
        shadow_risk="signing on vibe instead of terms — fog feels like trust",
        resource_pattern="clarity as revenue protection: written scope, numbers, deadlines",
        compensation_action=(
            "write it down, check numbers, confirm deadlines, payment terms, scope, and expectations"
        ),
        business_angle="contracts, invoices, scope creep, verbal yes / written no",
        personal_money_question="What did you assume because the conversation felt good?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass помогает превратить финансовый туман "
            "в ясность решения."
        ),
        money_theme_ru="цифры и туман; договор и допущения; логика и идеализация",
        financial_behavior_pattern_ru=(
            "размытые соглашения, расплывчатые обещания, нечёткая цена, "
            "упущенные детали, вера красивым словам без условий"
        ),
        shadow_risk_ru="подписать на вайбе вместо условий — туман ощущается как доверие",
        compensation_action_ru=(
            "зафиксируй письменно, проверь цифры, подтверди сроки, оплату, объём и ожидания"
        ),
        personal_money_question_ru="Что ты допустил, потому что разговор звучал приятно?",
    ),
    "jupiter_square_saturn": _overlay(
        aspect_key="jupiter_square_saturn",
        money_theme="growth versus structure; expansion versus limits",
        financial_behavior_pattern=(
            "wanting to scale without infrastructure, overcommitting, fear of growth, "
            "conservative delay, unstable business expansion"
        ),
        shadow_risk="expensive overreach — or freezing growth out of scarcity reflex",
        resource_pattern="minimum viable expansion that the current system can actually carry",
        compensation_action=(
            "define minimum viable expansion, list constraints, "
            "choose one growth step that the system can support"
        ),
        business_angle="hiring timing, capacity, runway, offer expansion, operational debt",
        personal_money_question="Is this growth — or overload wearing a vision costume?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass помогает найти линию между реальным ростом "
            "и дорогим перераздутием."
        ),
        money_theme_ru="рост и структура; расширение и пределы",
        financial_behavior_pattern_ru=(
            "желание масштабироваться без инфраструктуры, перегруз обязательствами, "
            "страх роста, консервативная задержка, нестабильное расширение бизнеса"
        ),
        shadow_risk_ru="дорогое перераздутие — или заморозка роста из рефлекса дефицита",
        compensation_action_ru=(
            "определи минимально жизнеспособное расширение, выпиши ограничения, "
            "выбери один шаг роста, который система выдержит"
        ),
        personal_money_question_ru="Это рост — или перегруз в костюме видения?",
    ),
    "sun_square_pluto": _overlay(
        aspect_key="sun_square_pluto",
        money_theme="visibility versus power; leadership versus control",
        financial_behavior_pattern=(
            "fear of being seen, power struggles, control around brand/status/money, "
            "underplaying authority or forcing dominance"
        ),
        shadow_risk="performing power instead of holding clean authority",
        resource_pattern="leadership that names the real power move without ego panic",
        compensation_action=(
            "act from clean authority, not ego panic; name the real power move and the real fear"
        ),
        business_angle="personal brand, pricing authority, status games, control in partnerships",
        personal_money_question="Are you hiding — or forcing dominance to feel safe?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, как твоя видимость и доход "
            "реагируют на давление."
        ),
        money_theme_ru="видимость и власть; лидерство и контроль",
        financial_behavior_pattern_ru=(
            "страх быть видимым, борьба за власть, контроль вокруг бренда/статуса/денег, "
            "приуменьшение авторитета или давление доминированием"
        ),
        shadow_risk_ru="демонстрация силы вместо чистого авторитета",
        compensation_action_ru=(
            "действуй из чистого авторитета, не из паники эго; назови реальный силовой ход и реальный страх"
        ),
        personal_money_question_ru="Ты прячешься — или давишь доминированием, чтобы почувствовать безопасность?",
    ),
    "moon_square_saturn": _overlay(
        aspect_key="moon_square_saturn",
        money_theme="security versus scarcity; emotional need versus restriction",
        financial_behavior_pattern=(
            "hoarding, fear spending, emotional shutdown, family money scripts, "
            "guilt around needs, survival-mode budgeting"
        ),
        shadow_risk="real budget limits fused with inherited fear — safety becomes freeze",
        resource_pattern="one stabilizing action that separates need from old scarcity story",
        compensation_action=(
            "separate real budget limits from inherited fear; choose one stabilizing action"
        ),
        business_angle="cash buffer, owner draw, family pressure, emotional spending freeze",
        personal_money_question="What is actual scarcity — and what is an old family script?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, где твоя система финансовой "
            "безопасности тебя перестраховывает."
        ),
        money_theme_ru="безопасность и дефицит; эмоциональная потребность и ограничение",
        financial_behavior_pattern_ru=(
            "накопительство, страх тратить, эмоциональное закрытие, семейные денежные сценарии, "
            "вина вокруг потребностей, бюджет в режиме выживания"
        ),
        shadow_risk_ru="реальные лимиты бюджета сливаются с унаследованным страхом — безопасность превращается в заморозку",
        compensation_action_ru=(
            "отдели реальные лимиты бюджета от унаследованного страха; выбери одно стабилизирующее действие"
        ),
        personal_money_question_ru="Что здесь реальный дефицит — а что старый семейный сценарий?",
    ),
    "venus_square_pluto": _overlay(
        aspect_key="venus_square_pluto",
        money_theme="desire/value under pressure from control",
        financial_behavior_pattern=(
            "intense buying, pricing anxiety, jealousy, dependency, "
            "hidden power games around money"
        ),
        shadow_risk="desire becomes leverage — money turns into emotional control hook",
        resource_pattern="value-based action after slowing the intensity spike",
        compensation_action="slow down desire, identify the control hook, choose value-based action",
        business_angle="client dependency, premium tension, negotiation power games, hidden stakes",
        personal_money_question="Who holds the lever — value, or the fear of losing the hook?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, где деньги становятся "
            "эмоциональным рычагом."
        ),
        money_theme_ru="желание и ценность под давлением контроля",
        financial_behavior_pattern_ru=(
            "интенсивные покупки, тревога вокруг цены, ревность, зависимость, "
            "скрытые силовые игры вокруг денег"
        ),
        shadow_risk_ru="желание становится рычагом — деньги превращаются в эмоциональный крючок",
        compensation_action_ru=(
            "замедли желание, найди крючок контроля, выбери действие из ценности"
        ),
        personal_money_question_ru="Кто держит рычаг — ценность или страх потерять крючок?",
    ),
}


def _generic_overlay(planet_a: str, planet_b: str, aspect_type: str) -> MoneyBehaviorOverlay:
    key = build_aspect_key(planet_a, planet_b, aspect_type)
    pa = planet_display_ru(planet_a)
    pb = planet_display_ru(planet_b)
    asp = normalize_aspect_type(aspect_type)
    return MoneyBehaviorOverlay(
        aspect_key=key,
        money_theme="financial weather — pattern in the field",
        financial_behavior_pattern=(
            f"{pa}–{pb} ({asp}) may activate money-related tension: pricing, timing, "
            "self-worth, control, or clarity — as behavioral climate, not fate."
        ),
        shadow_risk="reacting from panic, guilt, or fog instead of named value and terms",
        resource_pattern="pause, name the pattern, choose one reflective organizational step",
        compensation_action="замедли, назови цену или границу письменно, проверь одно число или условие",
        business_angle="pricing, agreements, cash rhythm, decision timing",
        personal_money_question="What is the nervous-system story behind this money moment?",
        money_compass_cta=(
            "Небо показывает климат. Money Compass показывает, где твоя финансовая нервная система "
            "реагирует на это давление — лично для тебя."
        ),
        safety_notes=list(_GLOBAL_SAFETY_NOTES),
        forbidden_claims=list(_GLOBAL_FORBIDDEN_CLAIMS),
        is_curated=False,
    )


def resolve_money_behavior_overlay(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
) -> MoneyBehaviorOverlay:
    """Return curated overlay when known; otherwise a safe generic money-weather overlay."""
    key = build_aspect_key(planet_a, planet_b, aspect_type)
    curated = _CURATED_OVERLAYS.get(key)
    if curated is not None:
        return curated
    return _generic_overlay(planet_a, planet_b, aspect_type)


def _aspect_label_ru(planet_a: str, planet_b: str, aspect_type: str) -> str:
    pa = planet_display_ru(planet_a)
    pb = planet_display_ru(planet_b)
    asp = normalize_aspect_type(aspect_type)
    asp_ru = {
        "opposition": "оппозиция",
        "square": "квадрат",
        "conjunction": "соединение",
        "trine": "трин",
        "sextile": "секстиль",
    }.get(asp, asp)
    return f"{pa}–{pb} ({asp_ru})"


def _money_planet_explanation_ru(planet_a: str, planet_b: str) -> str:
    try:
        pa = normalize_planet_name(planet_a)
        pb = normalize_planet_name(planet_b)
    except ValueError:
        return "Две планетарные темы встречаются в одном финансовом климате."
    line_a = _MONEY_PLANET_LINE_RU.get(pa, f"{planet_display_ru(pa)} — планетарная тема в деньгах.")
    line_b = _MONEY_PLANET_LINE_RU.get(pb, f"{planet_display_ru(pb)} — планетарная тема в деньгах.")
    return f"{line_a} {line_b}"


def build_money_weather_caption_ru(
    overlay: MoneyBehaviorOverlay,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
) -> str:
    """Deterministic Russian money-weather caption (six-block structure)."""
    pair_label = _aspect_label_ru(planet_a, planet_b, aspect_type)
    theme_ru = overlay.money_theme_ru or overlay.money_theme.replace(" versus ", " и ")
    behavior_ru = overlay.financial_behavior_pattern_ru or overlay.financial_behavior_pattern
    risk_ru = overlay.shadow_risk_ru or overlay.shadow_risk
    comp_ru = overlay.compensation_action_ru or overlay.compensation_action
    question_ru = overlay.personal_money_question_ru or overlay.personal_money_question

    hook = (
        f"Если деньги ощущаются не как цифры, а как контроль, страх, желание или давление — "
        f"посмотри на {pair_label}."
    )
    if overlay.aspect_key == "venus_opposition_pluto":
        hook = (
            "Если деньги ощущаются не как цифры, а как контроль, страх, желание или давление — "
            "посмотри на Венеру–Плутон."
        )

    explanation = _money_planet_explanation_ru(planet_a, planet_b)

    behavior = (
        f"В финансах это **может ощущаться** так: {behavior_ru}. "
        f"Тема дня: **{theme_ru}**."
    )
    risk = (
        f"**Риск:** {risk_ru}. "
        "Речь не о запрете желания — есть риск принять денежное решение из страха, а не из ценности."
    )
    compensation = f"**Компенсация:** {comp_ru}."
    cta = overlay.money_compass_cta.strip()
    if not cta.lower().startswith("небо"):
        cta = f"Небо показывает климат. {cta}"

    question = f"*{question_ru}*"
    return "\n\n".join([hook, explanation, behavior, risk, compensation, question, cta])


def validate_money_caption_safety(text: str) -> list[str]:
    """Return matched forbidden deterministic / trading-advice patterns (empty if clean)."""
    hits: list[str] = []
    for pattern in _DETERMINISTIC_CLAIM_PATTERNS:
        if pattern.search(text or ""):
            hits.append(pattern.pattern)
    low = (text or "").lower()
    for phrase in _GLOBAL_FORBIDDEN_CLAIMS:
        if phrase in low:
            hits.append(phrase)
    return hits


def inject_money_overlay_into_caption(
    caption: str,
    overlay: MoneyBehaviorOverlay,
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
) -> str:
    """Append or replace with full money-weather caption when integrating into an existing draft."""
    money_block = build_money_weather_caption_ru(overlay, planet_a, planet_b, aspect_type)
    base = (caption or "").strip()
    if not base:
        return money_block
    return f"{base}\n\n---\n\n{money_block}"


def overlay_to_context_dict(overlay: MoneyBehaviorOverlay) -> dict[str, object]:
    return overlay.model_dump()


__all__ = [
    "CAPTION_OVERLAY_MONEY_WEATHER",
    "CONTENT_ANGLE_MONEY",
    "MoneyBehaviorOverlay",
    "build_aspect_key",
    "build_money_weather_caption_ru",
    "inject_money_overlay_into_caption",
    "is_money_content_angle",
    "normalize_aspect_type",
    "overlay_to_context_dict",
    "resolve_money_behavior_overlay",
    "validate_money_caption_safety",
]
