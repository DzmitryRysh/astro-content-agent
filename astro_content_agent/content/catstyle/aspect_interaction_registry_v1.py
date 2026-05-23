"""Aspect + mode interaction meanings for Catstyle captions."""
from __future__ import annotations

from typing import Final

from astro_content_agent.content.catstyle.aspect_library_v0 import get_aspect_interaction
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.transit_pair_seed_v0 import get_transit_pair_seed, orient_outer_personal

_ASPECT_BASE_RU: Final[dict[str, str]] = {
    "conjunction": "Соединение сливает две темы в один узел — усиление и перегруз одной истории другой.",
    "sextile": "Секстиль даёт мягкий шанс — окно, где можно согласовать разные ритмы без лобового удара.",
    "square": "Квадрат — трение и столкновение: обе силы хотят своё сейчас, компромисс не даётся даром.",
    "trine": "Трин — поток и поддержка: темы двигаются в одном ритме, важно не расслабиться в автопилот.",
    "opposition": "Оппозиция — полюса тянут в разные стороны; баланс виден только если назвать обе стороны вслух.",
}

_MODE_OVERLAY_RU: Final[dict[str, str]] = {
    "tension": "Режим напряжения: день просит честно увидеть давление, а не делать вид, что «и так сойдёт».",
    "flow": "Режим потока: день даёт возможность — важно поймать её коротким действием, не раздув в вечный проект.",
    "compensation": "Режим компенсации: фокус на разрядке и конструктивном ходе, который снимает лишний накал.",
    "mixed": "Смешанный режим: и искра, и усталость — держи один ясный шаг, остальное в очередь.",
}


def aspect_type_meaning_ru(aspect_type: str) -> str:
    return _ASPECT_BASE_RU.get((aspect_type or "").strip().lower(), "Аспект задаёт ритм взаимодействия двух планетарных тем.")


def mode_overlay_ru(mode: str) -> str:
    return _MODE_OVERLAY_RU.get((mode or "").strip().lower(), "")


def pair_specific_interaction_ru(planet_a: str, planet_b: str, aspect_type: str) -> str | None:
    ix = get_aspect_interaction(planet_a, planet_b)
    if ix is not None:
        return f"Пара {ix.planet_a}–{ix.planet_b}: {ix.core_tension}"
    oriented = orient_outer_personal(planet_a, planet_b)
    if oriented is None:
        return None
    seed = get_transit_pair_seed(oriented[0], oriented[1])
    if seed is None:
        return None
    return f"Пара {oriented[0]}–{oriented[1]}: {seed.core_tension}"


def build_aspect_interaction_block(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> str:
    parts: list[str] = [aspect_type_meaning_ru(aspect_type)]
    mo = mode_overlay_ru(mode)
    if mo:
        parts.append(mo)
    pair = pair_specific_interaction_ru(planet_a, planet_b, aspect_type)
    if pair:
        parts.append(pair)
    return " ".join(parts)


__all__ = [
    "aspect_type_meaning_ru",
    "build_aspect_interaction_block",
    "mode_overlay_ru",
    "pair_specific_interaction_ru",
]
