"""Zodiac sign meanings for Catstyle caption sign context (Russian)."""
from __future__ import annotations

from typing import Final

SIGN_MEANINGS_RU: Final[dict[str, str]] = {
    "Aries": "Овен — старт, прямота, спешка, телесный импульс «вперёд».",
    "Taurus": (
        "Телец — тело, комфорт, деньги, стабильность и сопротивление резким переменам."
    ),
    "Gemini": (
        "Близнецы — мысли, слова, контакты, новости, движение и переключение внимания."
    ),
    "Cancer": "Рак — дом, забота, память, уязвимость и потребность в безопасной среде.",
    "Leo": (
        "Лев — гордость, видимость, творческое самовыражение и желание быть замеченным."
    ),
    "Virgo": "Дева — порядок, тело как система, практика, критика и мелкие доработки.",
    "Libra": "Весы — баланс, партнёрство, эстетика и торг «красиво vs честно».",
    "Scorpio": (
        "Скорпион — контроль, интенсивность, скрытое давление и трансформация через кризис."
    ),
    "Sagittarius": "Стрелец — горизонт, смысл, риск, путешествие идеи и оптимизм масштаба.",
    "Capricorn": "Козерог — цель, статус, дисциплина, долгий срок и жёсткая рамка.",
    "Aquarius": "Водолей — свобода, будущее, нетипичный ход и отстранённая ясность.",
    "Pisces": "Рыбы — туман, эмпатия, творчество и размытые границы.",
}


def normalize_sign_name(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    for key in SIGN_MEANINGS_RU:
        if key.lower() == s.lower():
            return key
    return None


def sign_meaning_ru(sign: str) -> str | None:
    key = normalize_sign_name(sign)
    if not key:
        return None
    return SIGN_MEANINGS_RU.get(key)


def sign_display_ru(sign: str) -> str:
    line = sign_meaning_ru(sign)
    if line and "—" in line:
        return line.split("—", 1)[0].strip()
    return (sign or "").strip() or "знаке"


def sign_context_line_ru(planet: str, sign: str | None) -> str | None:
    if not sign:
        return None
    body = sign_meaning_ru(sign)
    if not body:
        return None
    from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_display_ru

    pl = planet_display_ru(planet)
    z = sign_display_ru(sign)
    return f"{pl} в {z}: {body}"


__all__ = [
    "SIGN_MEANINGS_RU",
    "normalize_sign_name",
    "sign_context_line_ru",
    "sign_display_ru",
    "sign_meaning_ru",
]
