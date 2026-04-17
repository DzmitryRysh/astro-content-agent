from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from astro_content_agent.db.models import BrandProfile
from astro_content_agent.services.content.live_astrology_rules import (
    get_sharp_witty_style_reinforcement_hint,
)

# ---------------------------------------------------------------------------
# VOICE LAYER v1 — FROZEN (2026-04-02)
#
# Approved presets:
#   sharp_witty      — primary branded preset (RU-first, money-aware, pattern-naming)
#   educational_warm — soft baseline (supportive, reflective, gently action-oriented)
#
# Calibration complete across:
#   - caption body voice (mechanism-first, named distortion types, no obligatory soft finale)
#   - post hooks (question/reversal vs statement)
#   - post CTAs (recognition-tied vs reflective/action)
#   - reel hook_0_3s, spoken hook, recognition beat, CTA
#
# Do NOT add new presets or modify style rules without evidence from real
# publishing tests showing a repeated, reproducible failure.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tone preset registries
# Maps tone_preset strings → voice guidance.  Two registries: English ("en")
# and Russian ("ru").  Fall back to "default" when no preset matches.
# ---------------------------------------------------------------------------

_PRESET_REGISTRY: dict[str, dict[str, Any]] = {
    "educational_warm": {
        "voice_descriptors": ["clear", "warm", "accessible", "practical"],
        "tone_guidance": "Explain concepts simply, use relatable examples, avoid jargon. Speak like a knowledgeable friend.",
        "content_dos": [
            "Break down complex astro concepts into digestible takeaways",
            "Use 'you/your' to create direct connection",
            "Lead with a relatable human moment before the astro angle",
        ],
        "content_donts": [
            "Don't use overly mystical or alienating vocabulary",
            "Don't bury the practical application",
        ],
    },
    "empowering": {
        "voice_descriptors": ["bold", "empowering", "direct", "energising"],
        "tone_guidance": "Write to activate and uplift. Short punchy sentences. Strong action verbs. Confidence without arrogance.",
        "content_dos": [
            "Open with a bold claim or challenge",
            "Give the reader agency and direction",
            "End with a call to action that feels exciting, not obligatory",
        ],
        "content_donts": [
            "Don't hedge every sentence with 'maybe' or 'might'",
            "Don't use passive, weak language",
        ],
    },
    "mystical_grounded": {
        "voice_descriptors": ["poetic", "grounded", "trustworthy", "depth"],
        "tone_guidance": "Blend evocative imagery with concrete practical grounding. Poetic but never vague. Mystical but never escapist.",
        "content_dos": [
            "Use sensory or emotional language to set atmosphere",
            "Anchor each poetic moment with a concrete insight or action",
            "Let the astro context feel sacred but approachable",
        ],
        "content_donts": [
            "Don't float in abstraction without landing somewhere real",
            "Don't use clichéd spiritual buzzwords (vibes, manifest, etc.) without subverting them",
        ],
    },
    "conversational": {
        "voice_descriptors": ["friendly", "casual", "authentic", "relatable"],
        "tone_guidance": "Write like you're texting a smart friend who knows astrology. Casual but never careless. Authentic over polished.",
        "content_dos": [
            "Use natural, conversational sentence rhythms",
            "Include a moment of self-disclosure or shared experience",
            "Don't over-explain — trust the reader",
        ],
        "content_donts": [
            "Don't write stiff formal copy",
            "Don't use filler phrases ('At the end of the day…')",
        ],
    },
    "sharp_witty": {
        "voice_descriptors": ["sharp", "witty", "observant", "intelligent", "slightly edgy"],
        "tone_guidance": (
            "Write like someone who notices patterns fast and names them without apology. "
            "Dry, observational humor that creates recognition — not performance. "
            "Astrology-first, money-aware, psychologically sharp. "
            "Name the distortion, the avoidance, the overcompensation — directly but without humiliating the reader."
        ),
        "content_dos": [
            "Open the caption body with the mechanism in sentence one — transit name + exact behavioral pattern, no warm-up",
            "Use concrete behavior over abstract emotion: 'you gave a discount you didn't plan' vs 'we often undervalue ourselves'",
            "One precise uncomfortable observation beats three soft reassurances",
        ],
        "content_donts": [
            "Don't default to a soft therapeutic wrap-up ('that's okay', 'be gentle with yourself') unless genuinely earned",
            "Don't moralize or lecture — observe and name, then leave the reader room to think",
            "Don't use astrology as decoration for coaching, wellness filler, or abstract motivation",
        ],
        "hook_style_notes": (
            "Prefer recognition-first openers: pattern-naming questions, sharp reframes, direct distortion calls. "
            "Examples: 'You underpriced again?' / 'Not modesty. That's Venus-Saturn.' / "
            "'Money responds better to clarity than hustle today.' / "
            "'If you hesitate in money conversations — watch this.'"
        ),
        "caption_style_notes": (
            "Caption body rules for sharp_witty: "
            "1. First paragraph = mechanism, not introduction. 'Neptune square Moon triggers this: you can't tell anxiety from need — and your wallet starts compensating.' "
            "2. No obligatory soft finale. Don't end with 'and that's okay' unless earned by the content. "
            "3. Dry irony welcomed if it creates recognition: 'classic pattern', 'not for the first time', 'familiar?' "
            "4. Money as behavior, not philosophy: 'you made a discount you didn't plan' > 'we often undervalue ourselves'. "
            "5. End with a sharp point or question — not a neutral summary like 'all of this is worth considering'."
        ),
    },
    "default": {
        "voice_descriptors": ["clear", "direct", "thoughtful"],
        "tone_guidance": "Write with clarity and purpose. Prioritise usefulness over aesthetics. Keep the reader the hero of the story.",
        "content_dos": [
            "Lead with the most interesting or useful point",
            "Be specific rather than vague",
            "Give the reader something actionable or memorable",
        ],
        "content_donts": [
            "Don't pad with filler sentences",
            "Don't use fear or urgency manipulation",
        ],
    },
}

# Russian-specific tone preset registry.
# Voice guidance is written for a native Russian-speaking Instagram audience.
_PRESET_REGISTRY_RU: dict[str, dict[str, Any]] = {
    "educational_warm": {
        "voice_descriptors": ["понятный", "тёплый", "астрологически точный", "денежно практичный"],
        "tone_guidance": (
            "Называй транзит или аспект — и сразу переводи на финансовое поведение или ощущение. "
            "Не 'Венера квадрат Сатурну', а 'Венера квадрат Сатурну — и вот почему ты снова занизил цену'. "
            "Читатель должен узнать свой денежный паттерн через астрологию."
        ),
        "content_dos": [
            "Называй конкретный транзит или аспект — и связывай с финансовым поведением или решением",
            "Первый абзац — сразу в суть, без разгона",
            "Чередуй длинные и короткие предложения — это создаёт ритм",
        ],
        "content_donts": [
            "Не убирай астрологию из текста — это не самопомощь, это астрология о деньгах",
            "Не пиши 'в современном мире мы часто сталкиваемся' и похожие обороты",
            "Не заканчивай обобщением — заканчивай точкой или вопросом",
        ],
    },
    "empowering": {
        "voice_descriptors": ["прямой", "заряжающий", "астрологически конкретный", "денежно уверенный"],
        "tone_guidance": (
            "Называй транзит — и давай импульс к конкретному денежному действию или осознанию. "
            "Каждое предложение — действие или точное наблюдение о деньгах. "
            "Читатель должен почувствовать: этот аспект объясняет мой паттерн — и вот что с этим делать."
        ),
        "content_dos": [
            "Открывай транзитом + его конкретным влиянием на деньги, цену или решение",
            "Давай одно действие или инсайт с учётом аспекта",
            "CTA должен звучать как возможность, а не обязанность",
        ],
        "content_donts": [
            "Не хеджируй: 'возможно', 'может быть', 'некоторые из вас'",
            "Не убирай денежный контекст — превращаешь пост в общую астрологию",
            "Не перегружай текст оговорками",
        ],
    },
    "mystical_grounded": {
        "voice_descriptors": ["образный", "глубокий", "астрологически точный", "денежно заземлённый"],
        "tone_guidance": (
            "Используй образный язык — но каждый образ должен приземляться в деньги или решение. "
            "Поэтично, но с конкретным транзитом и финансовым измерением. "
            "Ни один абзац не заканчивается в абстракции без практического заземления."
        ),
        "content_dos": [
            "Один сильный образ — построенный на транзите с выходом в финансовый контекст",
            "После каждого поэтического момента — конкретный вывод о деньгах или решении",
            "Астрология как точный инструмент для понимания денежных циклов",
        ],
        "content_donts": [
            "Не использовать 'вибрации', 'манифестация', 'вселенная послала знак' без переосмысления",
            "Не строить весь пост на метафоре без денежного или практического выхода",
            "Не заканчивать туманным обобщением",
        ],
    },
    "conversational": {
        "voice_descriptors": ["живой", "прямой", "свой", "астрологически грамотный и денежно честный"],
        "tone_guidance": (
            "Пиши как умный человек, который знает астрологию и не боится говорить о деньгах прямо. "
            "Называй транзит легко — как называешь погоду. "
            "Финансовый паттерн называй без стыда и без лоска: 'занизить цену', 'импульсивно вложить', 'бояться просить'."
        ),
        "content_dos": [
            "Называй планету или аспект и сразу — денежный или поведенческий эффект",
            "Вставляй момент узнавания: 'этот транзит всегда про то, когда...'",
            "Короче, чем кажется нужным",
        ],
        "content_donts": [
            "Не пиши 'в конечном счёте', 'по большому счёту', 'безусловно'",
            "Не убирай денежный язык — это не лайфстайл-блог, а астрология о деньгах",
            "Не объясняй шутку и не разжёвывай метафору",
        ],
    },
    "sharp_witty": {
        "voice_descriptors": ["острый", "наблюдательный", "умный", "с иронией", "астрологически точный"],
        "tone_guidance": (
            "Пиши как человек, который видит механизм сразу и называет его без лишних слов. "
            "Живое наблюдение — не справочная трактовка. Называй паттерн напрямую, не через 'символизирует'. "
            "Можно быть ироничным — но не злобным. Наблюдение, а не насмешка. "
            "Называй искажения точно: занижение цены, страх просить, деньги из тревоги, трата как компенсация. "
            "Астрология — основа. Венера — не только романтика: называй её ресурсный пласт. "
            "Не объясняй иронию. Не смягчай острое наблюдение обязательным оптимистичным послесловием."
        ),
        "content_dos": [
            "Первый абзац — механизм напрямую: живое наблюдение, не справочное 'символизирует Х'",
            "Называй конкретное поведение, не абстрактное состояние: 'ты сделал скидку, которую не планировал' вместо 'мы недооцениваем себя'",
            "Используй полный потенциал планеты: Венера — ценообразование, самоценность, ёмкость принятия; 2 дом — что ты способен держать",
        ],
        "content_donts": [
            "Не заканчивай обязательным мягким финалом ('это нормально', 'будь добр к себе') — только если органично вытекает",
            "Не размывай наблюдение широким обобщением: не 'многие из нас', а 'ты', 'это', 'вот что происходит'",
            "Не сводить Венеру к романтике, 2 дом к 'просто деньгам', Луну к настроению — это мёртвые трактовки",
        ],
        "hook_style_notes": (
            "Предпочитай крючки-вопросы, переформулировки и прямые называния паттерна. "
            "Примеры: 'Ты опять занизил?' / 'Это не скромность. Это Венера-Сатурн.' / "
            "'Сегодня деньги лучше реагируют не на суету, а на ясность.' / "
            "'Если ты мнёшься в разговорах о цене — смотри сюда.'"
        ),
        "caption_style_notes": (
            "Структура основного текста для sharp_witty:\n"
            "1. Первый абзац — механизм напрямую, без вступления. "
            "Живое наблюдение, не справочная трактовка. "
            "Пример (мёртво): 'Нептун символизирует туман и иллюзии.' "
            "Пример (живо): 'Нептун квадрат Луне — и ты снова не можешь понять, "
            "это реальная потребность или тревога. Кошелёк обычно страдает первым.'\n"
            "2. Не нужен обязательный мягкий финал. Не заканчивай 'и это нормально' или 'будь добр к себе' "
            "если это не вытекает органично — это educational_warm, не sharp_witty.\n"
            "3. Одна точная неудобная правда > три мягких наблюдения. "
            "Не смягчай, если наблюдение работает само по себе.\n"
            "4. Сухая ирония разрешена и приветствуется, если создаёт узнавание: "
            "'классическая схема', 'не впервые', 'знакомо?', 'это объяснение, которое никто не называет вслух'.\n"
            "5. Деньги как поведение, не философия: "
            "'ты сделал скидку, которую не планировал' > 'многие из нас недооценивают свою ценность'.\n"
            "6. Заканчивай точкой или острым вопросом — не нейтральным выводом типа 'всё это важно учитывать'.\n"
            "7. Транзит → поведенческий паттерн → конкретное проявление → вывод без морализаторства.\n"
            "8. Венера — не только романтика. Называй её ресурсный пласт: ценообразование, самоценность, "
            "способность принимать. 2 дом — не просто 'деньги', а ёмкость: что ты способен держать.\n"
            "9. Не заменять конкретный механизм абстрактным духовным напутствием."
        ),
        "style_reinforcement_notes": get_sharp_witty_style_reinforcement_hint(),
    },
    "default": {
        "voice_descriptors": ["чёткий", "прямой", "без лишнего"],
        "tone_guidance": (
            "Ясно и по существу. Первое предложение — самое важное. "
            "Дай читателю что-то конкретное: действие, вопрос или сдвиг в восприятии. "
            "Ритм важнее объёма."
        ),
        "content_dos": [
            "Начинай с самого острого или полезного момента",
            "Один главный вывод — не пять",
            "Конкретика вместо абстракций",
        ],
        "content_donts": [
            "Не заполняй текст вводными конструкциями",
            "Не используй страх или давление",
            "Не заканчивай обобщением",
        ],
    },
}


@dataclass(frozen=True)
class PersonaContext:
    """Encapsulates brand voice and creator style for prompt injection.

    Built from a ``BrandProfile``; consumed by caption and reel services
    to keep tone, vocabulary, and content patterns consistent across drafts.
    """

    voice_descriptors: list[str]
    tone_guidance: str
    content_dos: list[str]
    content_donts: list[str]
    preferred_format: str | None  # "face_led" | None
    hook_style_notes: str | None = None  # Optional per-preset hook style guidance
    caption_style_notes: str | None = None  # Optional per-preset caption/body guidance
    style_reinforcement_notes: str | None = None  # Live/dead contrast DNA for sharp_witty

    @classmethod
    def from_brand(cls, brand: BrandProfile, language: str | None = None) -> "PersonaContext":
        """Derive persona context from a BrandProfile.

        Args:
            brand: The brand profile ORM model (or SimpleNamespace for testing).
            language: Override the language. If None, reads ``brand.content_language``
                      and falls back to ``"ru"`` (the system default).
        """
        lang = language or getattr(brand, "content_language", "ru") or "ru"
        registry = _PRESET_REGISTRY_RU if lang == "ru" else _PRESET_REGISTRY

        preset_key = (brand.tone_preset or "default").lower().strip()
        preset = registry.get(preset_key, registry["default"])

        # Check face_led_preferred — may not exist on older records
        face_led = getattr(brand, "face_led_preferred", False) or False
        preferred_format = "face_led" if face_led else None

        return cls(
            voice_descriptors=list(preset["voice_descriptors"]),
            tone_guidance=preset["tone_guidance"],
            content_dos=list(preset["content_dos"]),
            content_donts=list(preset["content_donts"]),
            preferred_format=preferred_format,
            hook_style_notes=preset.get("hook_style_notes"),
            caption_style_notes=preset.get("caption_style_notes"),
            style_reinforcement_notes=preset.get("style_reinforcement_notes"),
        )

    def to_prompt_hint(self) -> str:
        """Format as an injected context block for AI prompts."""
        parts = [
            f"Voice: {', '.join(self.voice_descriptors)}.",
            f"Tone guidance: {self.tone_guidance}",
            "Content DOs: " + " | ".join(self.content_dos),
            "Content DON'Ts: " + " | ".join(self.content_donts),
        ]
        if self.preferred_format:
            parts.append(f"Format preference: {self.preferred_format} (face-led content preferred for this brand).")
        if self.hook_style_notes:
            parts.append(f"Hook style notes: {self.hook_style_notes}")
        if self.caption_style_notes:
            parts.append(f"Caption style notes: {self.caption_style_notes}")
        if self.style_reinforcement_notes:
            parts.append(f"Style reinforcement (live vs dead contrast): {self.style_reinforcement_notes}")
        return "\n".join(parts)
