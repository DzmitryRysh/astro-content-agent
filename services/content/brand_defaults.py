"""Default brand profile configuration and builder for local development.

Used by the optional seed helper at ``scripts/aca/seed_brand_profile.py`` when
present; run it with the **repository root** (the directory that contains
``main.py``) as the current working directory. The module is importable on its
own so tests do not rely on dynamic script loading.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Per-preset descriptions injected into BrandProfile.description.
# Keyed to match _PRESET_REGISTRY in persona.py so descriptions align with voice.
# ---------------------------------------------------------------------------

TONE_DESCRIPTIONS: dict[str, str] = {
    "educational_warm": (
        "An astrology-inspired lifestyle content brand. Voice: clear, warm, and practical. "
        "We translate complex astrological concepts into grounded, actionable daily guidance. "
        "We speak like a knowledgeable friend — never preachy, never vague."
    ),
    "empowering": (
        "A bold, empowering astrology brand for high-achievers. Voice: direct, confident, energising. "
        "We activate and uplift our audience with short punchy insights. "
        "We give people agency — we don't predict their fate, we help them claim it."
    ),
    "mystical_grounded": (
        "An astrology brand that blends poetic imagery with practical grounding. "
        "Voice: evocative but never vague, mystical but never escapist. "
        "Every poetic moment lands somewhere real and actionable."
    ),
    "conversational": (
        "A casual, authentic astrology account that feels like texting a smart friend. "
        "Voice: friendly, relatable, and direct. We trust our audience to keep up. "
        "We share personal moments and honest takes — polished copy is not our vibe."
    ),
    "sharp_witty": (
        "An astrology account with a sharp eye and dry wit. Voice: observant, intelligent, slightly edgy. "
        "We name patterns fast — money distortions, behavioral loops, avoidance, compensation. "
        "Humor creates recognition, not performance. Astrology stays central. Non-toxic, non-cheesy."
    ),
}

DEFAULT_BRAND_NAME = "Astro Content Co"
DEFAULT_TONE_PRESET = "educational_warm"
DEFAULT_CONTENT_LANGUAGE = "ru"

# Russian-primary defaults: hashtags and banned terms are in Russian
DEFAULT_BANNED_TERMS_RU = [
    "гарантированно", "судьба решила", "обречён", "точно произойдёт",
    "звёзды обещают", "100% сбудется",
]
DEFAULT_BANNED_TERMS_EN = ["guaranteed", "fate", "doomed", "will happen", "definitely will"]

DEFAULT_HASHTAGS_RU = [
    "#астрология",
    "#гороскоп",
    "#астролог",
    "#лунныйкалендарь",
    "#астрологиядлявсех",
    "#деньгиастрология",
    "#финансовоеповедение",
    "#астрологияденег",
]
DEFAULT_HASHTAGS_EN = [
    "#astrology",
    "#dailyastrology",
    "#mindset",
    "#intentionalliving",
    "#spiritualwellness",
]

# Russian-specific brand descriptions per tone preset
TONE_DESCRIPTIONS_RU: dict[str, str] = {
    "educational_warm": (
        "Астрологический бренд о деньгах и финансовом поведении. Голос: понятный, тёплый, практичный. "
        "Мы объясняем, как транзиты влияют на финансовые решения, самооценку и денежные паттерны. "
        "Говорим как умный человек, который знает астрологию и не боится говорить о деньгах прямо."
    ),
    "empowering": (
        "Смелый астрологический бренд для тех, кто берёт деньги под контроль. Голос: прямой, уверенный, заряжающий. "
        "Мы соединяем транзиты с реальными финансовыми решениями — без мистики, без туманности. "
        "Даём людям инструменты для денежных решений, основанные на астрологии."
    ),
    "mystical_grounded": (
        "Астрологический бренд, соединяющий космические циклы с финансовой реальностью. "
        "Голос: образный, но конкретный. Поэтичный, но всегда приземляется в деньгах или решениях. "
        "Каждый образ ведёт к реальному инсайту о деньгах, времени или самооценке."
    ),
    "conversational": (
        "Живой разговорный аккаунт об астрологии и деньгах — как переписка с умной подругой, которая знает оба языка. "
        "Голос: дружелюбный, искренний, прямой. Говорим о транзитах, ценах, страхах и финансовых паттернах без лоска. "
        "Доверяем аудитории — не разжёвываем, не менторствуем."
    ),
    "sharp_witty": (
        "Астрологический аккаунт с острым взглядом и сухим юмором. "
        "Голос: наблюдательный, умный, слегка с иронией — без агрессии, без дешёвого кликбейта. "
        "Называем денежные паттерны точно: занижение цены, страх просить, деньги из тревоги, компенсация через траты. "
        "Астрология — основа. Ирония — инструмент узнавания, не насмешки."
    ),
}


def build_brand_config(
    name: str = DEFAULT_BRAND_NAME,
    tone_preset: str = DEFAULT_TONE_PRESET,
    face_led_preferred: bool = False,
    content_language: str = DEFAULT_CONTENT_LANGUAGE,
) -> dict:
    """Build a brand profile config dict with enriched defaults.

    Returns a dict suitable for passing to ``BrandProfile(**config)`` or the
    ``BrandProfileRepository.create`` method.

    Args:
        name: Brand display name.
        tone_preset: One of the presets registered in ``persona._PRESET_REGISTRY``.
        face_led_preferred: Whether to prefer face-led / talking-head content.
        content_language: Primary output language. ``"ru"`` (default) or ``"en"``.

    Returns:
        Dict with all required BrandProfile fields populated.
    """
    if content_language == "ru":
        description = TONE_DESCRIPTIONS_RU.get(
            tone_preset,
            f"Астрологический контент-бренд (пресет тона: {tone_preset}).",
        )
        banned_terms = list(DEFAULT_BANNED_TERMS_RU)
        hashtags = list(DEFAULT_HASHTAGS_RU)
    else:
        description = TONE_DESCRIPTIONS.get(
            tone_preset,
            f"An astrology content brand using tone preset: {tone_preset}.",
        )
        banned_terms = list(DEFAULT_BANNED_TERMS_EN)
        hashtags = list(DEFAULT_HASHTAGS_EN)

    return {
        "name": name,
        "description": description,
        "tone_preset": tone_preset,
        "banned_terms": banned_terms,
        "default_hashtags": hashtags,
        "face_led_preferred": int(face_led_preferred),
        "content_language": content_language,
    }
