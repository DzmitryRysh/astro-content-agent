"""Live Astrology Rules — interpretation principles and style DNA.

Distilled from structural study of modern Russian astrology interpretation practice.
Captures the "living vs dead" interpretation philosophy: read signals as mechanisms
and behavioral patterns rather than flattening them into cookbook keywords.

NOT direct author imitation. Principles are paraphrased into our internal prompt language.
Inspired by anti-dogmatic, behaviorally-grounded interpretation methodology.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Core interpretation rules — universal for all presets
# ---------------------------------------------------------------------------

LIVE_ASTROLOGY_RULES_RU: list[str] = [
    "Читай транзит как механизм и поведенческое проявление — не как ключевое слово из справочника",
    "Не своди аспект к одной трактовке: контекст, природа планет и ситуация важнее заученного значения",
    "Называй живой паттерн, который человек узнаёт — не абстрактную доктрину",
    "Гармоничный аспект — окно, поддержка, более лёгкое движение; не гарантия и не 'всё хорошо'",
    "Напряжённый аспект — трение, компенсация, искажение, перегрузка; не катастрофа и не приговор",
    "Соединение — слияние двух принципов; интерпретируй через природу обеих планет, не механически",
    "Деньги — это поведение, обмен, привычка, ёмкость, самооценка; не только цифра в счёте",
    "Не сводить к одному: Венера — не только романтика, 2 дом — не только деньги, Луна — не только настроение",
]

# ---------------------------------------------------------------------------
# Enriched house + planet notes for money / resource interpretation
# ---------------------------------------------------------------------------

BIOASTROLOGY_MONEY_NOTES_RU: dict[str, dict[str, str]] = {
    "2nd_house": {
        "core": (
            "Личный ресурс, заработанный собственным усилием. "
            "То, что человек способен держать, создавать и на что может опираться сам."
        ),
        "not_only": (
            "Не просто 'дом денег'. Это ёмкость принятия, самоценность как основа дохода, "
            "то, чем человек готов обменять своё время и силу."
        ),
        "money_mechanism": (
            "Напряжение во 2 доме — не 'мало денег'. Это искажение в отношении к собственной ценности: "
            "неспособность держать ресурс, зарабатывать своим путём или принимать оплату без вины."
        ),
    },
    "8th_house": {
        "core": (
            "Зависимый, общий, заёмный ресурс. Деньги, которые приходят через связь, "
            "кризис, трансформацию, чужие решения или совместные договорённости."
        ),
        "not_only": (
            "Не только 'наследство' или 'инвестиции'. Это паттерны слияния, зависимости "
            "и доверия в ресурсных отношениях."
        ),
        "money_mechanism": (
            "8 дом в напряжении часто говорит о страхе зависимости, попытке контролировать "
            "общие ресурсы или о заряженных финансовых связях, где деньги переплетены с властью."
        ),
    },
    "10th_house": {
        "core": (
            "Социальная реализация, роль, статус, профессиональное признание. "
            "Деньги как побочный продукт места и вклада в более широкий контекст."
        ),
        "not_only": (
            "Не просто 'карьера'. Это то, как личность монетизирует свой вклад через роль, "
            "репутацию и признание системой."
        ),
        "money_mechanism": (
            "10 дом поддерживает долгосрочную консолидацию дохода через репутацию и профессиональное "
            "позиционирование. Здесь деньги приходят медленно, но держатся."
        ),
    },
    "venus": {
        "core": (
            "Принцип ценности, выбора, вкуса. Как человек отбирает, притягивает и принимает "
            "ресурс — в деньгах и в отношениях."
        ),
        "not_only": (
            "Венера — не только романтика. Это ценообразование, способность принимать оплату, "
            "вкус как критерий выбора, отношение к достаточности."
        ),
        "money_mechanism": (
            "Напряжение к Венере часто проявляется как занижение цены, неловкость в получении, "
            "неспособность сказать 'да' деньгам без вины или самообесценивание под видом скромности."
        ),
    },
    # Resource distortion taxonomy — name the type, not just "money problems"
    "resource_distortion_types": {
        "core": (
            "Нарушения ресурса имеют разные механизмы. Называть тип — точнее, чем 'проблемы с деньгами'."
        ),
        "not_only": (
            "Не просто 'денежный блок'. Это конкретный тип нарушения с конкретным поведением."
        ),
        "money_mechanism": (
            "Четыре паттерна:\n"
            "- Стагнация: страх выпустить деньги, ресурс лежит мёртвым грузом, нет движения\n"
            "- Утечка: страх удержать, деньги уходят быстрее чем приходят, нет ёмкости\n"
            "- Перегорание: импульсивный выброс, покупка из напряжения или для снятия тревоги\n"
            "- Заморозка: контроль через неподвижность, 'ничего не трогать', паралич"
        ),
    },
}

# ---------------------------------------------------------------------------
# Sharp_witty style DNA — contrast-based writing principles
# Injected only for sharp_witty persona context
# ---------------------------------------------------------------------------

SHARP_WITTY_STYLE_DNA_RU: dict[str, Any] = {
    "core_principle": (
        "Пиши как человек, который видит механизм сразу и называет его без лишних слов. "
        "Живое наблюдение — не справочная трактовка. Контраст и точность — не многословие."
    ),
    "do": [
        "Сильный контраст: живое наблюдение vs мёртвая трактовка — всегда выбирай живое",
        "Называй механизм как инсайдер: 'это вот как работает' вместо 'это символизирует'",
        "Используй компактную метафору вместо длинного объяснения",
        "Одна точная неудобная правда сильнее трёх мягких утешений",
        "Сухая ирония как инструмент узнавания — не как насмешка",
        "Деньги как поведение: 'ты сделал скидку, которую не планировал' вместо 'мы недооцениваем себя'",
    ],
    "dont": [
        "Не пиши манифесты и философские рассуждения",
        "Не перегружай иронией — одного острого наблюдения достаточно",
        "Не обобщай до 'многие из нас' — пиши 'ты', 'это', 'вот что происходит'",
        "Не заканчивай обязательным оптимизмом, если он не заработан",
        "Не превращай астрологию в коучинг с астрологической декорацией",
    ],
    "live_vs_dead_examples": [
        {
            "dead": "Венера символизирует любовь, красоту и материальные блага",
            "alive": (
                "Венера — это про то, что ты считаешь достаточным. "
                "Поэтому напряжение к Венере часто звучит как 'я столько не стою'"
            ),
        },
        {
            "dead": "2 дом — дом денег и имущества",
            "alive": (
                "2 дом — не просто деньги. Это ёмкость: что ты способен держать. "
                "Напряжение там — не про сумму на счету, а про ощущение, что тебе нечего предложить"
            ),
        },
        {
            "dead": "Трин Венеры и Юпитера благоприятен для финансовых дел",
            "alive": (
                "Трин Венеры и Юпитера — не 'деньги упадут с неба'. "
                "Это момент, когда просить больше ощущается немного более нормальным, чем обычно"
            ),
        },
        {
            "dead": "Нептун квадрат Луне создаёт неопределённость",
            "alive": (
                "Нептун квадрат Луне — и ты снова не можешь понять, "
                "это реальная потребность или просто тревога. Кошелёк обычно страдает первым"
            ),
        },
    ],
}

# ---------------------------------------------------------------------------
# Anti-dead-astrology safeguards — rules that apply broadly
# ---------------------------------------------------------------------------

ANTI_DEAD_ASTROLOGY_RU: list[str] = [
    "Не сводить Венеру только к романтике — включать ресурсный, вкусовой и ценностный пласт",
    "Не сводить 2 дом только к 'деньгам' — это личный ресурс, самоценность, ёмкость держания",
    "Не называть гармоничный аспект конфликтным по умолчанию",
    "Не писать 'звёзды говорят' или 'астрология учит' — это информация без человека",
    "Не заменять конкретный механизм абстрактным духовным напутствием",
    "Не превращать транзит в инструкцию действия, если инсайт работает без неё",
]


# ---------------------------------------------------------------------------
# LiveAstrologyContext — injectable prompt context builder
# ---------------------------------------------------------------------------

class LiveAstrologyContext:
    """Packages live astrology interpretation rules for prompt injection.

    Injectable into caption / reel generation to prevent flat cookbook
    outputs and strengthen money/resource interpretation depth.
    """

    @staticmethod
    def interpretation_rules_hint() -> str:
        """Return a compact block of interpretation rules for prompt injection."""
        lines = [f"- {r}" for r in LIVE_ASTROLOGY_RULES_RU]
        return "Принципы живой интерпретации (обязательны):\n" + "\n".join(lines)

    @staticmethod
    def money_entity_hints() -> str:
        """Return compact house/planet money notes for depth injection."""
        parts: list[str] = []
        for key, data in BIOASTROLOGY_MONEY_NOTES_RU.items():
            parts.append(f"[{key}] {data['core']} | Денежный механизм: {data['money_mechanism']}")
        return "Расширенные ресурсные контексты:\n" + "\n".join(parts)

    @staticmethod
    def anti_dead_rules_hint() -> str:
        """Return the anti-dead-astrology safeguard list."""
        lines = [f"- {r}" for r in ANTI_DEAD_ASTROLOGY_RU]
        return "Запрещено (мёртвые трактовки):\n" + "\n".join(lines)

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """Return a flat dict for JSON payload injection into AI calls."""
        return {
            "interpretation_rules": LIVE_ASTROLOGY_RULES_RU,
            "money_entity_notes": {
                k: {
                    "core": v["core"],
                    "not_only": v["not_only"],
                    "money_mechanism": v["money_mechanism"],
                }
                for k, v in BIOASTROLOGY_MONEY_NOTES_RU.items()
            },
            "anti_dead_rules": ANTI_DEAD_ASTROLOGY_RU,
            # Sharp_witty contrast DNA — live/dead examples and structural writing principles.
            # The AI uses these to produce mechanism-first, contrast-framed content.
            "sharp_witty_style_dna": {
                "core_principle": SHARP_WITTY_STYLE_DNA_RU["core_principle"],
                "do": SHARP_WITTY_STYLE_DNA_RU["do"],
                "dont": SHARP_WITTY_STYLE_DNA_RU["dont"],
                "live_vs_dead_examples": SHARP_WITTY_STYLE_DNA_RU["live_vs_dead_examples"],
            },
        }


def get_sharp_witty_style_reinforcement_hint() -> str:
    """Compact string hint for injecting sharp_witty style DNA into PersonaContext."""
    core = SHARP_WITTY_STYLE_DNA_RU["core_principle"]
    do_lines = "\n".join(f"  - {r}" for r in SHARP_WITTY_STYLE_DNA_RU["do"])
    dont_lines = "\n".join(f"  - {r}" for r in SHARP_WITTY_STYLE_DNA_RU["dont"])
    examples = "\n".join(
        f"  Мёртво: «{ex['dead']}» → Живо: «{ex['alive']}»"
        for ex in SHARP_WITTY_STYLE_DNA_RU["live_vs_dead_examples"]
    )
    return (
        f"Style DNA (sharp_witty): {core}\n"
        f"Do:\n{do_lines}\n"
        f"Don't:\n{dont_lines}\n"
        f"Live vs dead contrast:\n{examples}"
    )
