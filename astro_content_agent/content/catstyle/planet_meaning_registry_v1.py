"""Short human-language planet meanings for Catstyle captions (Russian)."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

PLANET_MEANINGS_RU: Final[dict[str, str]] = {
    "Sun": (
        "Солнце — ядро «я»: видимость, воля, самоуважение, жизненная сила и то, "
        "как ты хочешь светить (или не светить) сегодня."
    ),
    "Moon": (
        "Луна — эмоции, тело, безопасность, привычки и потребность в опоре; "
        "реагирует быстрее логики."
    ),
    "Mercury": (
        "Меркурий — мысли, слова, новости, договорённости, учёба и скорость "
        "обмена информацией."
    ),
    "Venus": (
        "Венера — ценности, удовольствие, близость, деньги как «что мне приятно», "
        "эстетика и выбор в пользу себя."
    ),
    "Mars": (
        "Марс — импульс, действие, смелость, раздражение и энергия «сделать сейчас», "
        "иногда через конфликт."
    ),
    "Jupiter": (
        "Юпитер — расширение, смысл, вера в возможное, щедрость и риск "
        "перераздуть масштаб."
    ),
    "Saturn": (
        "Сатурн — границы, ответственность, время, структура и цена «по-взрослому»."
    ),
    "Uranus": (
        "Уран — внезапность, свобода, нервная искра, срыв шаблона и потребность "
        "обновить систему."
    ),
    "Neptune": (
        "Нептун — туман, фантазия, эмпатия, растворение границ и риск "
        "путать желание с правдой."
    ),
    "Pluto": (
        "Плутон — глубина, контроль, трансформация, интенсивность и то, "
        "что «не отпускает» без честного разговора с собой."
    ),
}


def planet_meaning_ru(planet: str) -> str | None:
    if not (planet or "").strip():
        return None
    try:
        name = normalize_planet_name(planet)
    except ValueError:
        return None
    return PLANET_MEANINGS_RU.get(name)


def planet_display_ru(planet: str) -> str:
    line = planet_meaning_ru(planet)
    if line and "—" in line:
        return line.split("—", 1)[0].strip()
    return (planet or "").strip() or "Планета"


__all__ = ["PLANET_MEANINGS_RU", "planet_display_ru", "planet_meaning_ru"]
