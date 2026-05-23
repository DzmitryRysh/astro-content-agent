"""Structured compensation guidance for Catstyle post copy (pair + aspect + mode)."""
from __future__ import annotations

from typing import Final

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name

CAPTION_COMPENSATION_MARKER = "Практический шаг:"


class CatstyleCompensationEntry(BaseModel):
    """Book-aligned relief actions for a specific Catstyle aspect configuration."""

    registry_key: str
    planet_a: str
    planet_b: str
    aspect_type: str
    mode: str
    primary_action: str = Field(
        ...,
        description="One concrete step the audience can do today.",
    )
    why_it_helps: str = Field(
        ...,
        description="One short line: why this step relieves the aspect pressure.",
    )
    compensation_actions: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="Short bullet actions for the compensation package field.",
    )
    pressure_phrasing: str | None = Field(
        default=None,
        description="Optional: how the aspect pressure shows up in plain language.",
    )
    relieve_phrasing: str | None = Field(
        default=None,
        description="Optional: how to relieve / work with this aspect.",
    )


def _safe_planet_name(name: str) -> str | None:
    raw = (name or "").strip()
    if not raw:
        return None
    try:
        return normalize_planet_name(raw)
    except ValueError:
        return None


def _pair_key(planet_a: str, planet_b: str) -> frozenset[str] | None:
    a = _safe_planet_name(planet_a)
    b = _safe_planet_name(planet_b)
    if not a or not b:
        return None
    return frozenset({a, b})


def _entry(
    *,
    registry_key: str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    primary_action: str,
    why_it_helps: str,
    compensation_actions: list[str],
    pressure_phrasing: str | None = None,
    relieve_phrasing: str | None = None,
) -> CatstyleCompensationEntry:
    return CatstyleCompensationEntry(
        registry_key=registry_key,
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
        mode=mode,
        primary_action=primary_action,
        why_it_helps=why_it_helps,
        compensation_actions=compensation_actions,
        pressure_phrasing=pressure_phrasing,
        relieve_phrasing=relieve_phrasing,
    )


CATSTYLE_COMPENSATION_STARTER_REGISTRY: Final[tuple[CatstyleCompensationEntry, ...]] = (
    _entry(
        registry_key="mercury_jupiter_sextile_flow_v1",
        planet_a="Mercury",
        planet_b="Jupiter",
        aspect_type="sextile",
        mode="flow",
        pressure_phrasing="Юпитер раздувает смысл быстрее, чем Меркурий успевает проверить факты — легко уехать в «гениальную идею без релиза».",
        relieve_phrasing="Секстиль любит короткую дистанцию: одна гипотеза, один критерий, один таймер.",
        primary_action="запиши одну гипотезу в три строки и поставь таймер на 20 минут проверки",
        why_it_helps="так ты ловишь шанс секстиля без недели «я только думаю» и без меню из десяти задач",
        compensation_actions=[
            "одна гипотеза — один критерий «да/нет/переформулировать»",
            "один таймер 20 минут — потом решение, не новый ресёрч",
            "не покупай себе неделю исследований вместо одного пинка в реальность",
            "если лезет «я гений, мир не готов» — переведи энергию в текст, схему или короткий звонок",
        ],
    ),
    _entry(
        registry_key="sun_uranus_conjunction_tension_v1",
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="conjunction",
        mode="tension",
        pressure_phrasing="Солнце хочет цельную роль, Уран рвёт сценарий — соблазн сжечь всё ради одного вдоха свободы.",
        relieve_phrasing="Компенсация — один осознанный эксперимент, а не десять хаотичных разрывов.",
        primary_action="измени одну вещь по правилу: что именно, зачем, и как проверишь результат через 24 часа",
        why_it_helps="так бунт получает инженерный план, а не фейерверк из биографии",
        compensation_actions=[
            "одно изменение — один критерий «стало легче/яснее?»",
            "не сжигай рабочее ради мгновенного эффекта свободы",
            "дай бунту канал: проект, формат, правило эксперимента",
            "запиши, что именно освобождаешь и зачем — до действия, не после",
        ],
    ),
    _entry(
        registry_key="mars_pluto_square_tension_v1",
        planet_a="Mars",
        planet_b="Pluto",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Марс тянет ударить сейчас, Плутон — удержать всю подковёрную механику; сила без точки легко становится шумом.",
        relieve_phrasing="Компенсация — одно контролируемое действие с ясным «готово», не серия ударов «для эффекта».",
        primary_action="выбери одно измеримое действие на сегодня и отложи всё, что звучит как «докажу мощь разрушением»",
        why_it_helps="так жар уходит в фокус, а не в статусный снос без критерия",
        compensation_actions=[
            "не доказывай силу через уничтожение — одна контрольная точка",
            "один измеримый шаг вместо серии «для эффекта»",
            "переведи жару в работу, тело или стратегию с критерием «готово»",
            "если лезет «сломаю ради статуса» — смени канал до охлаждения",
        ],
    ),
    _entry(
        registry_key="moon_saturn_square_tension_v1",
        planet_a="Moon",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Луна просит опору и честное «мне больно», Сатурн требует рамок — легко заморозить чувства в самокритику.",
        relieve_phrasing="Компенсация — назвать потребность и дать ей одну маленькую взрослую форму.",
        primary_action="назови одну реальную потребность вслух (или в заметке) и сделай одно маленькое взрослое действие на 15 минут",
        why_it_helps="так чувство получает форму, а дисциплина перестаёт звучать как экзамен без человеческого голоса",
        compensation_actions=[
            "не наказывай себя за чувства, даже если они мешают графику",
            "одна потребность — без стыда и без оправданий",
            "одно маленькое взрослое действие на сегодня",
            "базовый режим для тела: сон / еда / пауза — не как награда, а как опора",
        ],
    ),
    _entry(
        registry_key="neptune_moon_conjunction_tension_v1",
        planet_a="Neptune",
        planet_b="Moon",
        aspect_type="conjunction",
        mode="tension",
        pressure_phrasing="Нептун размывает контуры, Луна ищет безопасность — туман легко принять за интуицию без проверки.",
        relieve_phrasing="Компенсация — мягкая граница и заземление, без отмены чувствительности.",
        primary_action="запиши одну границу «да / пока нет / уточню завтра» и сделай одно телесное заземление (вода, еда, прогулка 10 минут)",
        why_it_helps="так ты сохраняешь эмпатию, но не растворяешься в чужом тумане",
        compensation_actions=[
            "не принимай туман за окончательную правду — одна проверка фактами",
            "одна мягкая граница без театра и без шантажа себе",
            "заземление в теле перед большими выводами",
            "отложи крупные решения, пока сон/еда/ритм не восстановлены",
        ],
    ),
    _entry(
        registry_key="venus_pluto_opposition_tension_v1",
        planet_a="Venus",
        planet_b="Pluto",
        aspect_type="opposition",
        mode="tension",
        pressure_phrasing=(
            "Магнитизм под давлением: Венера тянет к контакту и красоте без перегруза, "
            "Плутон — к правде, глубине и полному рычагу."
        ),
        relieve_phrasing="Компенсация — честная граница и заземление притяжения, без театра.",
        primary_action="сформулируй одну честную границу без шантажа себе и проверь цену входа",
        why_it_helps="так интенсивность не подменяет самооценку, а притяжение остаётся выбором",
        compensation_actions=[
            "не обменивай самооценку на интенсивность «это судьба»",
            "одна честная граница — без театра",
            "переведи притяжение в творчество, тело или спокойный разговор по фактам",
            "если лезет одержимость проверкой — верни фокус на одно действие",
        ],
    ),
    _entry(
        registry_key="mercury_neptune_square_tension_v1",
        planet_a="Mercury",
        planet_b="Neptune",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Меркурий хочет фактов, Нептун туманит контуры — обещания легко становятся акварелью без проверки.",
        relieve_phrasing="Компенсация — письменная фиксация и один прямой вопрос.",
        primary_action="запиши ключевое письменно и задай один прямой вопрос вместо намёков",
        why_it_helps="так ты сохраняешь образ и интуицию, но не строишь день на непроверяемом",
        compensation_actions=[
            "запиши ключевое письменно, не доверяй «я помню»",
            "проверь факты до вывода",
            "отложи крупные заключения, пока туман не спадёт",
            "задай один прямой вопрос вместо трёх намёков",
        ],
    ),
    _entry(
        registry_key="sun_uranus_square_tension_v1",
        planet_a="Sun",
        planet_b="Uranus",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Солнце хочет цельную роль, Уран рвёт сценарий — соблазн сжечь всё ради одного вдоха свободы.",
        relieve_phrasing="Компенсация — одно осознанное изменение с планом, не фейерверк из биографии.",
        primary_action="измени одну вещь по правилу: что, зачем, и как проверишь результат через 24 часа",
        why_it_helps="так бунт получает канал, а не хаотичный снос рабочего",
        compensation_actions=[
            "измени одну вещь сознательно, а не десять в панике",
            "не сжигай всю сцену ради одного вдоха свободы",
            "дай бунту канал: проект, формат, правило эксперимента",
            "зафиксируй, что именно освобождаешь и зачем",
        ],
    ),
    _entry(
        registry_key="jupiter_saturn_square_tension_v1",
        planet_a="Jupiter",
        planet_b="Saturn",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Юпитер тянет масштаб, Сатурн требует доказательств — качели между оптимизмом и параличом.",
        relieve_phrasing="Компенсация — один измеримый шаг и один дедлайн.",
        primary_action="сократи мечту до одного измеримого шага и назначь один дедлайн с критерием результата",
        why_it_helps="так рост переживает встречу с таблицей задач, а не остаётся лозунгом",
        compensation_actions=[
            "сократи мечту до одного измеримого следующего шага",
            "поставь одну чёткую границу ресурсов",
            "назначь один дедлайн и критерий результата",
            "без фальшивого оптимизма и без паралича страхом",
        ],
    ),
    _entry(
        registry_key="venus_mars_square_tension_v1",
        planet_a="Venus",
        planet_b="Mars",
        aspect_type="square",
        mode="tension",
        pressure_phrasing="Венера тянет к контакту и красоте, Марс — к скорости и жару; химия легко маскирует хаос.",
        relieve_phrasing="Компенсация — замедлить один импульс и назвать запрос словами.",
        primary_action="замедли один «срочно» импульс и сформулируй один честный запрос",
        why_it_helps="так притяжение не превращается в пассивную агрессию или разнос сцены",
        compensation_actions=[
            "не путай химию с разрешением устраивать хаос",
            "замедли один импульс перед действием",
            "сформулируй один честный запрос вместо пассивной агрессии",
            "переведи жар в движение, спорт или творческое действие",
        ],
    ),
)


def resolve_catstyle_compensation(
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    *,
    registry: tuple[CatstyleCompensationEntry, ...] | None = None,
) -> CatstyleCompensationEntry | None:
    """Return pair-specific compensation when registry matches (order-insensitive planets)."""
    pair = _pair_key(planet_a, planet_b)
    asp = (aspect_type or "").strip().lower()
    mo = (mode or "").strip().lower()
    if pair is None or not asp or not mo:
        return None
    rows = registry if registry is not None else CATSTYLE_COMPENSATION_STARTER_REGISTRY
    for row in rows:
        if _pair_key(row.planet_a, row.planet_b) != pair:
            continue
        if row.aspect_type.strip().lower() != asp:
            continue
        if row.mode.strip().lower() != mo:
            continue
        return row
    return None


__all__ = [
    "CAPTION_COMPENSATION_MARKER",
    "CATSTYLE_COMPENSATION_STARTER_REGISTRY",
    "CatstyleCompensationEntry",
    "resolve_catstyle_compensation",
]
