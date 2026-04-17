"""Money Astrology Knowledge Layer v1 + v2.

Core knowledge module connecting astro signals to money-psychology content.

v1 Provides:
- Planet-to-money-distortion mappings
- Planet-to-exchange-type mappings
- Earning channel descriptions
- House interpretations (2nd, 8th)
- MoneyAstrologyContext: derives structured prompt hints from astro day signals

v2 Adds:
- VENUS_MONEY_BEHAVIOR: sign-based unconscious money interaction patterns
- MONEY_FROM_EFFORT: 2nd house cusp sign earning styles
- PLANET_FUNCTIONS: core planetary function descriptions
- HOUSE_ENERGY_SUMMARIES: house life-sphere descriptions
- get_save_or_spend_strategy(): farmer vs predator logic from 2nd house sign
- interpret_2nd_house_ruler(): formula engine for money route interpretation
- MoneyKnowledgeBase: static v2 knowledge aggregator for prompt injection
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from astro_content_agent.schemas.astro import AstroDayPayload

# ---------------------------------------------------------------------------
# Planet money archetypes and distortions
# ---------------------------------------------------------------------------

PLANET_MONEY_PROFILES: dict[str, dict[str, str]] = {
    "moon": {
        "archetype": "survival, safety, basic support, everyday money",
        "distortion": "fear of poverty, chronic money anxiety, 'never enough' loop, emotional spending",
        "healthy": "stable rhythmic income, everyday sufficiency, calm relationship with the basics",
        "content_hook": "когда Луна активирует страх бедности или эмоциональные траты",
    },
    "sun": {
        "archetype": "joy, creativity, self-expression, authorial income",
        "distortion": "self-worth fused with money, income as validation, 'if I earn less — I am less'",
        "healthy": "earning through authentic self-expression, money as byproduct of visibility",
        "content_hook": "когда деньги становятся мерилом ценности личности",
    },
    "mercury": {
        "archetype": "communication, information, trade, negotiation",
        "distortion": "scattered money attention, fragmented earning streams, communication errors in money deals",
        "healthy": "clear contracts, precise negotiations, information monetised cleanly",
        "content_hook": "когда размытость в переговорах или договорённостях стоит денег",
    },
    "venus": {
        "archetype": "resources, sufficiency, pleasure, ability to receive and assimilate",
        "distortion": "inability to receive, underpricing self, confusion about adequacy, 'I don't deserve more'",
        "healthy": "clear sense of own worth, receives easily, knows what is enough",
        "content_hook": "когда напряжение к Венере ведёт к занижению цены или неспособности принять",
    },
    "mars": {
        "archetype": "action, initiative, effort, earning through body/drive",
        "distortion": "impulsive spending, rushing financial decisions, risky moves from urgency",
        "healthy": "direct action toward income, confident pursuit of opportunities",
        "content_hook": "когда давление Марса создаёт импульсивные финансовые решения",
    },
    "jupiter": {
        "archetype": "expansion, abundance, growth, excess",
        "distortion": "overspending, grandiosity, 'big money fantasy', overlooking practical limits",
        "healthy": "well-timed expansion, generosity without depletion, strategic growth",
        "content_hook": "когда оптимизм Юпитера переходит черту и деньги уходят быстрее, чем приходят",
    },
    "saturn": {
        "archetype": "structure, discipline, delayed reward, financial reality",
        "distortion": "fear-based freezing, scarcity mindset, over-control, inability to invest in self",
        "healthy": "financial discipline, long-term planning, realistic budgeting, earned stability",
        "content_hook": "когда Сатурн создаёт не дисциплину, а паралич вокруг денег",
    },
    "uranus": {
        "archetype": "disruption, innovation, sudden change, non-standard income",
        "distortion": "financial instability, money leaks, chaos in income, erratic earning",
        "healthy": "flexible income streams, innovation monetised, freedom in earning model",
        "content_hook": "когда транзит Урана создаёт непредсказуемость в доходах или утечки",
    },
    "neptune": {
        "archetype": "fog, intuition, dissolution, hidden channels",
        "distortion": "money fog, financial illusions, idealization of opportunities, self-deception in numbers",
        "healthy": "intuitive timing, earning through art/healing/invisible work, spiritual clarity about enough",
        "content_hook": "когда Нептун размывает финансовую картину и решения принимаются в тумане",
    },
    "pluto": {
        "archetype": "power, transformation, extremes, shared resources",
        "distortion": "greed, control issues, all-or-nothing resource logic, power dynamics around money",
        "healthy": "deep financial transformation, mastery of shared resources, strategic leverage",
        "content_hook": "когда Плутон поднимает тему власти, контроля или крайностей в деньгах",
    },
}

# ---------------------------------------------------------------------------
# What people exchange for money (resource types)
# ---------------------------------------------------------------------------

EXCHANGE_TYPES: dict[str, str] = {
    "mars": "action, initiative, physical effort, direct pursuit",
    "venus": "beauty, aesthetics, pleasure, materiality, relatability",
    "mercury": "communication, information, data, negotiation, writing",
    "moon": "care, nurturance, safety, emotional holding, family support",
    "sun": "creativity, authorship, leadership, personal charisma",
    "mercury+virgo": "service, mastery, routine, precision, health",
    "venus+libra": "partnership, consulting, mediation, facilitation",
    "pluto+scorpio": "transformation, crisis navigation, investment, research",
    "jupiter+sagittarius": "teaching, expertise, foreign contexts, philosophy",
    "saturn+capricorn": "structure, status, career management, institutional authority",
    "uranus+aquarius": "innovation, technology, collective intelligence, disruption",
    "neptune+pisces": "intuition, artistic work, spiritual guidance, hidden channels",
}

# ---------------------------------------------------------------------------
# House money interpretations (2nd and 8th)
# ---------------------------------------------------------------------------

HOUSE_MONEY_PROFILES: dict[str, dict[str, str]] = {
    "2nd": {
        "theme": "personal earned money, own labor, real tangible resources",
        "questions": [
            "чем человек реально зарабатывает (не должен, а реально)",
            "что он считает своим ресурсом",
            "насколько он верит, что его труд стоит денег",
        ],
        "content_angle": "2 дом показывает способ заработка и отношение к собственному ресурсу",
    },
    "8th": {
        "theme": "shared money, business money, investments, risk, other people's resources",
        "questions": [
            "готов ли человек к совместным деньгам и их условиям",
            "как он переживает финансовый риск",
            "что происходит в инвестиционных или партнёрских деньгах",
        ],
        "content_angle": "8 дом — деньги через партнёрство, трансформацию, инвестиции и чужой ресурс",
    },
}

# ---------------------------------------------------------------------------
# Earning channels (money can come through...)
# ---------------------------------------------------------------------------

EARNING_CHANNELS: dict[str, str] = {
    "body_initiative": "тело, инициатива, прямые действия (Марс, 1 дом)",
    "beauty_materiality": "красота, эстетика, материальность (Венера, 2 дом)",
    "communication_info": "коммуникация, информация, тексты (Меркурий, 3 дом)",
    "care_family": "забота, семья, безопасность (Луна, 4 дом)",
    "creativity_authorship": "творчество, авторство, самовыражение (Солнце, 5 дом)",
    "service_mastery": "сервис, рутина, мастерство (Меркурий+Дева, 6 дом)",
    "partnership_consulting": "партнёрство, консультирование, посредничество (Венера+Весы, 7 дом)",
    "transformation_investment": "кризис, трансформация, инвестиции (Плутон, 8 дом)",
    "teaching_expertise": "обучение, экспертиза, зарубежные темы (Юпитер, 9 дом)",
    "structure_career": "карьера, статус, институциональная власть (Сатурн, 10 дом)",
    "innovation_collective": "инновации, IT, коллективная работа (Уран, 11 дом)",
    "hidden_spiritual": "скрытое, удалённое, художественное, духовное (Нептун, 12 дом)",
}

# ---------------------------------------------------------------------------
# Money problem framing (NOT just "low income")
# ---------------------------------------------------------------------------

MONEY_PROBLEM_TYPES: list[str] = [
    "неспособность принять ресурс (деньги предлагают, но человек отказывается или уменьшает)",
    "неспособность удержать (деньги приходят, но быстро утекают)",
    "страх денег (избегание финансовых разговоров, цифр, решений)",
    "хроническое перерасходование (импульсивность, компенсация через трату)",
    "путаница в ценности (непонимание, сколько стоит труд, время, ресурс)",
    "несоответствие между человеком и способом заработка",
    "внутреннее искажение (Венера под давлением, конфликты 2 дома)",
    "деньги как мерило ценности личности (Солнце + финансовая самооценка)",
    "деньги как тревога выживания (Луна + базовая безопасность)",
]

# ---------------------------------------------------------------------------
# The 6-step content formula
# ---------------------------------------------------------------------------

MONEY_CONTENT_FORMULA = """\
Формула денежного контента (6 шагов):
1. Астро-фактор — какой транзит или аспект работает
2. Денежный механизм — что именно происходит с деньгами/ресурсом
3. Внутреннее ощущение — как это переживается изнутри
4. Поведенческое проявление — что человек делает (или не делает) из-за этого
5. Риск/искажение — где здесь ловушка или типичная ошибка
6. Практика/гармонизация — что конкретно можно сделать прямо сейчас\
"""

# ---------------------------------------------------------------------------
# Known planet names for signal key parsing
# ---------------------------------------------------------------------------

_PLANET_NAMES: frozenset[str] = frozenset(
    ["moon", "sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
)

# ---------------------------------------------------------------------------
# Aspect polarity framing rules
# ---------------------------------------------------------------------------

ASPECT_POLARITY_FRAMING: dict[str, dict] = {
    "harmonious": {
        "aspects_ru": ["трин", "секстиль"],
        "core_nature_ru": (
            "Гармоничный аспект — это окно, поддержка, лёгкость. "
            "Энергии двух планет работают вместе, а не против друг друга."
        ),
        "money_framing_ru": (
            "В денежном контексте: момент, когда что-то даётся легче — "
            "назвать цену, договориться, принять ресурс, сделать финансовый шаг."
        ),
        "hook_style_ru": (
            "Зацепка строится как открытие, возможность или облегчение. "
            "Не 'ты снова ошибаешься', а 'сейчас легче, чем обычно'."
        ),
        "framing_words_ru": [
            "окно возможности", "хороший момент", "легче", "поддержка",
            "открывается путь", "ресурс", "плавный", "без напряжения",
            "можно", "даётся легче", "мягко и точно",
        ],
        "shadow_note_ru": (
            "Тень гармоничных аспектов (вторичная нота, не главный фрейм): "
            "инертность, 'слишком легко — значит не серьёзно', риск упустить момент."
        ),
        "hook_examples_ru": [
            "Венера в секстиле к Меркурию: хороший момент, чтобы спокойно назвать свою цену",
            "Когда Венера в гармонии с Меркурием, ценность легче перевести в слова",
            "Трин Венеры и Юпитера — окно, когда просить больше ощущается естественно",
            "Этот аспект помогает мягко, но точно договориться о деньгах",
            "Луна в трине к Венере: сейчас легче отпустить страх и принять предложение",
        ],
        "avoid_ru": [
            "Не фреймируй гармоничный аспект как конфликт или напряжение",
            "Не используй 'ты снова занижаешь' — это язык для квадрата/оппозиции",
            "Не пиши 'давление', 'напряжение', 'страх' как основной тон",
            "Тень — только как вторичная нота, никогда не главный фрейм",
        ],
    },
    "tense": {
        "aspects_ru": ["квадрат", "оппозиция"],
        "core_nature_ru": (
            "Напряжённый аспект — это трение, конфликт, давление. "
            "Две планеты тянут в разные стороны или создают внутреннее противоречие."
        ),
        "money_framing_ru": (
            "В денежном контексте: момент искажения, ловушки, внутреннего конфликта — "
            "занизить цену, вложить из страха, импульсивная трата, денежная тревога."
        ),
        "hook_style_ru": (
            "Зацепка строится как распознавание боли, паттерна или ловушки. "
            "'Ты снова занизил', 'страх управляет кошельком', 'деньги утекают'."
        ),
        "framing_words_ru": [
            "напряжение", "трение", "конфликт", "давление", "искажение",
            "ловушка", "страх", "снова", "противоречие", "тянет в разные стороны",
            "внутренний конфликт", "вынужденный выбор",
        ],
        "shadow_note_ru": None,
        "hook_examples_ru": [
            "Квадрат Марса к Венере может подталкивать к импульсивным тратам",
            "Оппозиция Луны и Сатурна часто обостряет страх нехватки",
            "Венера квадрат Сатурну — и ты снова занизил цену. Не случайно",
            "При квадрате к денежным показателям легче принять решение из тревоги",
        ],
        "avoid_ru": [
            "Не фреймируй как «всё хорошо» или «возможность» — это конфликт",
            "Не смягчай тон там, где есть реальное напряжение",
        ],
    },
    "neutral": {
        "aspects_ru": ["соединение"],
        "core_nature_ru": (
            "Соединение — слияние, усиление, концентрация. "
            "Ни хорошо, ни плохо — зависит от планет и контекста."
        ),
        "money_framing_ru": (
            "В денежном контексте: усиление темы той планеты. "
            "Луна соединяется с Сатурном → страх; с Юпитером → оптимизм в деньгах."
        ),
        "hook_style_ru": (
            "Интерпретируй по природе планет. Проверь: какие планеты соединяются? "
            "Если Сатурн/Плутон/Нептун — может быть тяжело. "
            "Если Юпитер/Венера/Солнце — может быть ресурсно."
        ),
        "framing_words_ru": [
            "слияние", "усиление", "концентрация", "фокус", "объединение",
        ],
        "shadow_note_ru": None,
        "hook_examples_ru": [
            "Луна соединяется с Сатурном — и денежная тревога сегодня острее обычного",
            "Венера соединяется с Юпитером: момент, когда желание принимать ресурс усилено",
        ],
        "avoid_ru": [
            "Не присваивай автоматически положительный или отрицательный тон — смотри на планеты",
        ],
    },
}


def extract_planets_from_signal_key(key: str) -> list[str]:
    """Extract planet names from a signal key like 'venus_square_saturn'.

    Returns a deduplicated list of lowercase planet names found in the key.

    >>> extract_planets_from_signal_key("venus_square_saturn")
    ['venus', 'saturn']
    >>> extract_planets_from_signal_key("mercury_retrograde")
    ['mercury']
    >>> extract_planets_from_signal_key("moon_trine_jupiter")
    ['moon', 'jupiter']
    """
    tokens = re.split(r"[_\-\s]+", key.lower())
    seen: list[str] = []
    for token in tokens:
        if token in _PLANET_NAMES and token not in seen:
            seen.append(token)
    return seen


# ---------------------------------------------------------------------------
# MoneyAstrologyContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MoneyAstrologyContext:
    """Structured money-astrology context derived from today's astro signals.

    Provides a ``to_prompt_hint()`` method that injects all relevant
    money-framework knowledge into AI generation prompts.
    """

    planets_in_play: list[str]
    active_distortions: list[str]
    active_archetypes: list[str]
    active_hooks: list[str]
    problem_types: list[str] = field(default_factory=list)
    # Mapping of signal_key -> polarity ("harmonious"/"tense"/"neutral"/None)
    aspect_polarities: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_astro_day(cls, astro_day: "AstroDayPayload") -> "MoneyAstrologyContext":
        """Derive money context from an AstroDayPayload.

        Extracts planets from signal keys, then looks up their money profiles.
        Also collects aspect_polarity from each signal.
        """
        planets: list[str] = []
        aspect_polarities: dict[str, str] = {}

        for signal in astro_day.signals:
            for planet in extract_planets_from_signal_key(signal.key):
                if planet not in planets:
                    planets.append(planet)
            if signal.aspect_polarity:
                aspect_polarities[signal.key] = signal.aspect_polarity

        distortions: list[str] = []
        archetypes: list[str] = []
        hooks: list[str] = []

        for planet in planets:
            profile = PLANET_MONEY_PROFILES.get(planet)
            if profile:
                distortions.append(f"{planet.capitalize()}: {profile['distortion']}")
                archetypes.append(f"{planet.capitalize()}: {profile['archetype']}")
                hooks.append(profile["content_hook"])

        # Include a representative sample of problem types (always useful)
        problem_sample = MONEY_PROBLEM_TYPES[:4]

        return cls(
            planets_in_play=planets,
            active_distortions=distortions,
            active_archetypes=archetypes,
            active_hooks=hooks,
            problem_types=problem_sample,
            aspect_polarities=aspect_polarities,
        )

    def to_prompt_hint(self) -> str:
        """Format as an injectable context block for AI prompts."""
        if not self.planets_in_play:
            return ""

        parts: list[str] = [
            "=== MONEY ASTROLOGY CONTEXT ===",
            f"Планеты в игре: {', '.join(p.capitalize() for p in self.planets_in_play)}",
            "",
            "Денежные архетипы активных планет:",
        ]
        for arch in self.active_archetypes:
            parts.append(f"  • {arch}")

        parts += [
            "",
            "Возможные искажения (денежные):",
        ]
        for dist in self.active_distortions:
            parts.append(f"  • {dist}")

        parts += [
            "",
            "Контентные крючки:",
        ]
        for hook in self.active_hooks:
            parts.append(f"  • {hook}")

        parts += [
            "",
            "Типы денежных проблем (не только 'мало доходов'):",
        ]
        for pt in self.problem_types:
            parts.append(f"  • {pt}")

        parts += [
            "",
            MONEY_CONTENT_FORMULA,
            "",
            "2 дом (личные деньги, свой труд):",
            f"  {HOUSE_MONEY_PROFILES['2nd']['content_angle']}",
            "8 дом (партнёрские деньги, инвестиции):",
            f"  {HOUSE_MONEY_PROFILES['8th']['content_angle']}",
            "=== END MONEY CONTEXT ===",
        ]

        return "\n".join(parts)

    def to_dict(self) -> dict:
        """Return as a plain dict for JSON serialization into prompt payloads."""
        # Build a compact aspect framing hint based on what's in today's signals
        framing_hints: dict[str, dict] = {}
        for key, polarity in self.aspect_polarities.items():
            framing = ASPECT_POLARITY_FRAMING.get(polarity, {})
            framing_hints[key] = {
                "polarity": polarity,
                "core_nature_ru": framing.get("core_nature_ru", ""),
                "money_framing_ru": framing.get("money_framing_ru", ""),
                "hook_style_ru": framing.get("hook_style_ru", ""),
                "framing_words_ru": framing.get("framing_words_ru", [])[:5],
                "avoid_ru": framing.get("avoid_ru", []),
            }

        return {
            "planets_in_play": self.planets_in_play,
            "active_archetypes": self.active_archetypes,
            "active_distortions": self.active_distortions,
            "active_hooks": self.active_hooks,
            "problem_types": self.problem_types,
            "content_formula": MONEY_CONTENT_FORMULA,
            "house_2_angle": HOUSE_MONEY_PROFILES["2nd"]["content_angle"],
            "house_8_angle": HOUSE_MONEY_PROFILES["8th"]["content_angle"],
            "aspect_polarities": self.aspect_polarities,
            "aspect_framing_hints": framing_hints,
        }


# ===========================================================================
# v2 Knowledge Layer
# ===========================================================================
VENUS_MONEY_BEHAVIOR: dict[str, dict[str, str]] = {
    "aries": {
        "unconscious_pattern": "хочу — беру, деньги сразу в движение и действие",
        "spending_style": "импульсивное, быстрое, не накопительное",
        "risk": "деньги сгорают в руках — сложно удержать даже большие суммы",
        "content_hook": "при Венере в Овне деньги быстро уходят туда, где интересно",
    },
    "taurus": {
        "unconscious_pattern": "последовательные желания, накопление, стабильность",
        "spending_style": "планомерное, качественное, с удовольствием от владения",
        "risk": "избыточная осторожность может превратиться в страх тратить вообще",
        "content_hook": "Венера в Тельце хочет держать ресурс — и это одновременно сила и ограничение",
    },
    "gemini": {
        "unconscious_pattern": "множественные лёгкие желания, деньги на общение и новизну",
        "spending_style": "разнообразное, частое, на контакты и информацию",
        "risk": "распылённость: деньги уходят в мелкие удовольствия без структуры",
        "content_hook": "Венера в Близнецах тратит на слова, встречи и новизну",
    },
    "cancer": {
        "unconscious_pattern": "деньги как безопасность и комфорт близких",
        "spending_style": "на дом, семью, уют — эмоциональные траты возможны",
        "risk": "тревожные траты ради ощущения безопасности, а не из реальной потребности",
        "content_hook": "при Венере в Раке деньги часто тратятся ради ощущения надёжности",
    },
    "leo": {
        "unconscious_pattern": "роскошь, статус, красота, траты ради самовыражения",
        "spending_style": "щедрое, статусное, на удовольствие и впечатление",
        "risk": "импульсные траты для поддержания образа или настроения",
        "content_hook": "Венера во Льве тратит щедро — иногда из желания блистать, а не из нужды",
    },
    "virgo": {
        "unconscious_pattern": "практичность, полезность, умеренность",
        "spending_style": "рациональное, планомерное, ориентированное на качество",
        "risk": "избыточный анализ тормозит принятие финансовых решений",
        "content_hook": "Венера в Деве хочет, чтобы каждая трата была оправдана — это и сила, и ловушка",
    },
    "libra": {
        "unconscious_pattern": "красота, гармония, деньги на отношения и эстетику",
        "spending_style": "на красивое, на совместное, на подарки и согласие",
        "risk": "избегание финансовых конфликтов, сложно говорить о деньгах прямо",
        "content_hook": "Венера в Весах тратит ради гармонии — и это может стоить дорого",
    },
    "scorpio": {
        "unconscious_pattern": "всё или ничего, глубокий контроль или полное отстранение",
        "spending_style": "стратегическое или трансформационное — склонно к крайностям",
        "risk": "страх потери может заморозить ресурс или привести к контролирующему поведению",
        "content_hook": "Венера в Скорпионе управляет деньгами через контроль или трансформацию",
    },
    "sagittarius": {
        "unconscious_pattern": "деньги на рост, развитие, путешествия, смыслы",
        "spending_style": "щедрое, без накопления, деньги как ресурс для расширения",
        "risk": "излишний оптимизм: 'всегда будет ещё', сложно с планированием",
        "content_hook": "Венера в Стрельце живёт в логике 'деньги приходят и уходят — главное движение'",
    },
    "capricorn": {
        "unconscious_pattern": "накопление, страх бедности, убеждение что деньги даются только тяжёлым трудом",
        "spending_style": "консервативное, планомерное, без лишних трат",
        "risk": "установка 'я не заслуживаю большего без работы' тормозит рост",
        "content_hook": "Венера в Козероге: когда экономия превращается в ограничивающее убеждение",
    },
    "aquarius": {
        "unconscious_pattern": "нестандартные финансовые решения, независимость от денег",
        "spending_style": "нерегулярное, на инновации, коллективные проекты, свободу",
        "risk": "непредсказуемость доходов и расходов, сложность с накоплением",
        "content_hook": "Венера в Водолее: деньги как инструмент свободы, а не безопасности",
    },
    "pisces": {
        "unconscious_pattern": "интуиция вокруг денег, но слабый контроль, параллельная реальность",
        "spending_style": "на ощущения, творчество, интуитивные порывы",
        "risk": "размытая картина финансов — сложно видеть реальные цифры",
        "content_hook": "Венера в Рыбах: когда финансовая картина становится туманной",
    },
}

# Sign element classification (for save-vs-spend strategy)
SIGN_ELEMENTS: dict[str, str] = {
    "aries": "fire", "taurus": "earth", "gemini": "air", "cancer": "water",
    "leo": "fire", "virgo": "earth", "libra": "air", "scorpio": "water",
    "sagittarius": "fire", "capricorn": "earth", "aquarius": "air", "pisces": "water",
}

# Scorpio gets a mixed override because of its Pluto co-rulership and 8th house intensity
_SAVE_OR_SPEND_OVERRIDES: dict[str, str] = {"scorpio": "mixed"}

STRATEGY_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "farmer": {
        "label": "фермер",
        "logic": "деньги растут через накопление, планирование, экономию, использование своих средств",
        "strength": "стабильность, надёжная база, медленный но устойчивый рост",
        "risk": "пропустить момент расширения, слишком долго удерживать ресурс без движения",
        "content_hook": "твоя стратегия — растить деньги через сохранение и накопление, не через скорость",
    },
    "predator": {
        "label": "хищник",
        "logic": "деньги растут через движение, новые связи, реинвестирование, скорость оборота",
        "strength": "быстрый рост через действие, масштабирование, использование чужого ресурса",
        "risk": "нестабильность без базы, деньги гуляют — сложно с накоплением",
        "content_hook": "твоя стратегия — растить деньги через движение и оборот, не через удержание",
    },
    "mixed": {
        "label": "смешанный",
        "logic": "сочетание накопления и активного использования ресурса — зависит от контекста",
        "strength": "гибкость между двумя стратегиями",
        "risk": "неопределённость, может пытаться использовать обе стратегии одновременно",
        "content_hook": "твоя стратегия не однозначна — важен контекст: когда копить, а когда пускать в оборот",
    },
}

# How money comes through personal effort (2nd house cusp sign)
MONEY_FROM_EFFORT: dict[str, dict[str, str]] = {
    "aries": {
        "style": "инициатива и скорость",
        "phrase": "Деньги приходят к тебе через инициативу и быстрые первые шаги",
        "grows_when": "ты первым занимаешь поле и действуешь без промедления",
    },
    "taurus": {
        "style": "последовательность и надёжность",
        "phrase": "Деньги приходят к тебе через последовательность и стабильное качество",
        "grows_when": "ты строишь медленно, но основательно, без резких перемен",
    },
    "gemini": {
        "style": "коммуникация и связи",
        "phrase": "Деньги приходят к тебе через общение, информацию и контакты",
        "grows_when": "ты в движении, говоришь, обмениваешься, соединяешь людей",
    },
    "cancer": {
        "style": "забота и защита",
        "phrase": "Деньги приходят к тебе через заботу, создание безопасности и отклик на потребности других",
        "grows_when": "ты создаёшь пространство доверия и надёжности",
    },
    "leo": {
        "style": "авторство и творчество",
        "phrase": "Деньги приходят к тебе через авторство, уникальность и личную подачу",
        "grows_when": "ты выражаешь себя и позволяешь себе быть заметным",
    },
    "virgo": {
        "style": "порядок, польза, детали",
        "phrase": "Деньги приходят к тебе через мастерство, точность и практическую пользу",
        "grows_when": "ты делаешь работу лучше, чем нужно, и создаёшь ощутимый результат",
    },
    "libra": {
        "style": "партнёрство и баланс",
        "phrase": "Деньги приходят к тебе через партнёрство, консультирование и создание гармонии",
        "grows_when": "ты строишь качественные отношения и работаешь для другого",
    },
    "scorpio": {
        "style": "трансформация и глубина",
        "phrase": "Деньги приходят к тебе через кризисные точки, исследование скрытого и управление чужим ресурсом",
        "grows_when": "ты работаешь с тем, что другие боятся трогать",
    },
    "sagittarius": {
        "style": "смысл и экспертиза",
        "phrase": "Деньги приходят к тебе через обучение, экспертизу, расширение и зарубежные связи",
        "grows_when": "ты делишься знанием и выходишь за привычные рамки",
    },
    "capricorn": {
        "style": "структура и репутация",
        "phrase": "Деньги приходят к тебе через профессиональный статус, ответственность и долгосрочную репутацию",
        "grows_when": "ты берёшь ответственность за систему и строишь карьеру последовательно",
    },
    "aquarius": {
        "style": "инновация и коллектив",
        "phrase": "Деньги приходят к тебе через нестандартные решения, технологии и коллективную работу",
        "grows_when": "ты выходишь за рамки и предлагаешь то, чего ещё нет",
    },
    "pisces": {
        "style": "интуиция и творчество",
        "phrase": "Деньги приходят к тебе через творчество, интуицию, скрытые каналы и работу с тонким",
        "grows_when": "ты доверяешь своему ощущению и работаешь в творческом или духовном пространстве",
    },
}

# Planet core functions (for formula engine)
PLANET_FUNCTIONS: dict[str, str] = {
    "sun": "сиять, творить, вести, выражать уникальность, занимать место",
    "moon": "заботиться, чувствовать, создавать безопасность, откликаться на потребности",
    "mercury": "коммуницировать, собирать и передавать информацию, учить, писать, считать, посредничать",
    "venus": "создавать красоту и гармонию, строить отношения, наслаждаться, выбирать ценное",
    "mars": "действовать быстро, инициировать, преодолевать, конкурировать, применять силу/страсть",
    "jupiter": "расширять, обучать, наставлять, вдохновлять, давать смысл, искать масштаб",
    "saturn": "структурировать, дисциплинировать, планировать долгосрочно, нести ответственность",
    "uranus": "новаторствовать, ломать паттерны, двигаться быстро, сохранять независимость",
    "neptune": "тонко чувствовать, вдохновлять, растворять границы, создавать через видение",
    "pluto": "трансформировать, проходить через кризис, влиять, управлять ресурсами, исследовать скрытое",
}

# House energy summaries (for formula engine)
HOUSE_ENERGY_SUMMARIES: dict[int, str] = {
    1: "тело, внешность, личное действие, начало",
    2: "деньги, таланты, ценности, личные ресурсы",
    3: "коммуникация, контакты, поездки, обучение",
    4: "дом, семья, корни, недвижимость",
    5: "творчество, дети, хобби, красота, радость",
    6: "рабочая рутина, здоровье, сервис, медицина",
    7: "партнёры, клиенты, консультации, выступление перед другими",
    8: "чужие деньги, риск, кризис, трансформация",
    9: "заграница, высшее образование, идеология, право, смыслы",
    10: "карьера, статус, руководство, профессиональная система",
    11: "коллективы, будущее, технологии, соцсети, IT",
    12: "скрытое, психология, медицина, закрытые организации, творчество",
}


def get_save_or_spend_strategy(second_house_sign: str) -> str:
    """Derive farmer/predator/mixed money strategy from 2nd house cusp sign.

    >>> get_save_or_spend_strategy("taurus")
    'farmer'
    >>> get_save_or_spend_strategy("aries")
    'predator'
    >>> get_save_or_spend_strategy("scorpio")
    'mixed'
    """
    sign = second_house_sign.lower().strip()
    if sign in _SAVE_OR_SPEND_OVERRIDES:
        return _SAVE_OR_SPEND_OVERRIDES[sign]
    element = SIGN_ELEMENTS.get(sign)
    if element in ("earth", "water"):
        return "farmer"
    if element in ("fire", "air"):
        return "predator"
    return "mixed"


# Russian planet name translations
_PLANET_NAMES_RU: dict[str, str] = {
    "sun": "Солнце",
    "moon": "Луна",
    "mercury": "Меркурий",
    "venus": "Венера",
    "mars": "Марс",
    "jupiter": "Юпитер",
    "saturn": "Сатурн",
    "uranus": "Уран",
    "neptune": "Нептун",
    "pluto": "Плутон",
}


def interpret_2nd_house_ruler(ruler_planet: str, ruler_house: int) -> str:
    """Generate a money route interpretation from the formula engine.

    Uses the ruler of the 2nd house and the house it occupies to derive
    the earning route and implementation sphere.

    >>> result = interpret_2nd_house_ruler("venus", 7)
    >>> "Венера" in result and "7" in result
    True
    """
    planet_func = PLANET_FUNCTIONS.get(ruler_planet.lower(), ruler_planet)
    house_energy = HOUSE_ENERGY_SUMMARIES.get(ruler_house, f"{ruler_house} дом")
    planet_ru = _PLANET_NAMES_RU.get(ruler_planet.lower(), ruler_planet.capitalize())
    return (
        f"Управитель 2 дома — {planet_ru}. "
        f"Функция: {planet_func}. "
        f"Стоит в {ruler_house} доме ({house_energy}). "
        f"Денежный маршрут: реализовать функцию {planet_ru} в сфере {ruler_house} дома — "
        f"именно там деньги реализуются наиболее органично."
    )


class MoneyKnowledgeBase:
    """Static v2 money-astrology knowledge aggregator for prompt injection.

    Unlike MoneyAstrologyContext (which is derived from daily transit signals),
    MoneyKnowledgeBase provides timeless knowledge structures — Venus by sign patterns,
    earning styles, formula engine templates, and career/10th house money angles.

    Inject alongside MoneyAstrologyContext to give the AI model full vocabulary
    for educational and natal-chart-style money content.
    """

    CAREER_MONEY_ANGLES: list[str] = [
        "10 дом закрепляет доход через профессиональный статус и долгосрочную репутацию",
        "карьерный маршрут — это способ превратить экспертизу в стабильный предсказуемый доход",
        "когда 10 дом активирован транзитом — это момент для переосмысления денежного статуса",
        "транзит по 10 дому нередко совпадает с изменением уровня дохода или признания",
    ]

    CONTENT_ANGLE_TEMPLATES: list[str] = [
        "Почему деньги держатся только до определённой суммы — и что за этим стоит",
        "Что Венера говорит о твоём бессознательном стиле трат",
        "Ты растишь деньги как фермер или как хищник?",
        "Через какое качество к тебе реально приходят деньги",
        "Почему 2 дом показывает не просто доход, а способ заработка",
        "Как 10 дом закрепляет доход через карьеру и репутацию",
        "Что мешает тебе удерживать ресурс: страх, хаос или крайности?",
        "Как управитель 2 дома показывает твой денежный маршрут",
        "Когда экономия — это сила, а когда — ограничивающее убеждение",
        "Почему деньги не задерживаются даже при хорошем доходе",
    ]

    @classmethod
    def to_dict(cls) -> dict:
        """Return compact v2 knowledge as a plain dict for payload injection."""
        venus_sample = {
            sign: {
                "risk": profile["risk"],
                "content_hook": profile["content_hook"],
            }
            for sign, profile in VENUS_MONEY_BEHAVIOR.items()
        }
        effort_sample = {
            sign: {
                "style": profile["style"],
                "phrase": profile["phrase"],
            }
            for sign, profile in MONEY_FROM_EFFORT.items()
        }
        return {
            "venus_money_patterns": venus_sample,
            "save_or_spend_strategies": {
                s: STRATEGY_DESCRIPTIONS[get_save_or_spend_strategy(s)]["content_hook"]
                for s in SIGN_ELEMENTS
            },
            "earning_effort_styles": effort_sample,
            "career_money_angles": cls.CAREER_MONEY_ANGLES,
            "content_angle_templates": cls.CONTENT_ANGLE_TEMPLATES,
            "formula_engine_example": interpret_2nd_house_ruler("venus", 7),
            "planet_functions": PLANET_FUNCTIONS,
            "house_energy_summaries": {str(k): v for k, v in HOUSE_ENERGY_SUMMARIES.items()},
        }

    @classmethod
    def to_prompt_hints(cls) -> str:
        """Format compact v2 knowledge as an injectable string for AI prompts."""
        lines = [
            "=== MONEY KNOWLEDGE v2 ===",
            "",
            "## Шаблоны денежных углов (используй как основу для primary_angle):",
        ]
        for tpl in cls.CONTENT_ANGLE_TEMPLATES[:6]:
            lines.append(f"  • {tpl}")

        lines += [
            "",
            "## Венера по знаку — бессознательный стиль трат:",
        ]
        for sign, profile in list(VENUS_MONEY_BEHAVIOR.items())[:4]:
            lines.append(f"  • {sign.capitalize()}: {profile['content_hook']}")
        lines.append("  (все 12 знаков в money_knowledge_v2.venus_money_patterns)")

        lines += [
            "",
            "## Фермер vs хищник (стратегия 2 дома по элементу знака):",
            f"  Земля/Вода → {STRATEGY_DESCRIPTIONS['farmer']['label']}: {STRATEGY_DESCRIPTIONS['farmer']['logic']}",
            f"  Огонь/Воздух → {STRATEGY_DESCRIPTIONS['predator']['label']}: {STRATEGY_DESCRIPTIONS['predator']['logic']}",
            "",
            "## Денежный маршрут (формула управителя 2 дома):",
            "  Управитель 2 дома в [X] доме = моя денежная функция реализуется в сфере [X] дома.",
            "  Пример: " + interpret_2nd_house_ruler("venus", 7),
            "",
            "## Карьера и доход (10 дом):",
        ]
        for angle in cls.CAREER_MONEY_ANGLES[:2]:
            lines.append(f"  • {angle}")

        lines.append("=== END MONEY KNOWLEDGE v2 ===")
        return "\n".join(lines)
