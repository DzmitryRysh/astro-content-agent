"""LLM + fallback Catstyle caption generation from structured context."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from astro_content_agent.content.catstyle.compensation_registry_v1 import (
    CAPTION_COMPENSATION_MARKER,
    resolve_catstyle_compensation,
)
from astro_content_agent.content.catstyle.planet_meaning_registry_v1 import planet_display_ru
from astro_content_agent.content.catstyle.sign_meaning_registry_v1 import sign_display_ru
from astro_content_agent.core.config import get_settings
from astro_content_agent.services.ai.client import OpenAIClientFactory
from astro_content_agent.services.ai.responses_runner import make_strict_schema
from astro_content_agent.services.content.catstyle_caption_context import (
    CatstyleCaptionContext,
    caption_banned_phrases,
    context_to_llm_payload,
)
from astro_content_agent.services.content.catstyle_caption_planet_policy import use_sign_in_public_caption
from astro_content_agent.services.content.catstyle_caption_polish import polish_caption_for_package
from astro_content_agent.services.content.catstyle_compensation_copy import (
    format_compensation_package_block,
)

_PROMPTS_ROOT = Path(__file__).resolve().parents[1] / "ai" / "prompts"
_CAPTION_INSTRUCTIONS_PATH = _PROMPTS_ROOT / "ru" / "catstyle_caption_writer.md"


class CatstyleCaptionLLMOutput(BaseModel):
    hook: str = Field(..., min_length=1)
    caption: str = Field(..., min_length=1)
    compensation: str = Field(default="")


@dataclass(frozen=True)
class CatstyleCaptionResult:
    hook: str
    caption: str
    compensation: str
    source: str  # "llm" | "fallback"


class CatstyleCaptionGenerator(Protocol):
    def generate(self, ctx: CatstyleCaptionContext) -> CatstyleCaptionResult: ...


def _load_instructions() -> str:
    return _CAPTION_INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _sanitize_text(text: str) -> str:
    out = (text or "").strip()
    low = out.lower()
    for banned in caption_banned_phrases():
        if banned in low:
            out = re.sub(re.escape(banned), "", out, flags=re.IGNORECASE)
    lines = [" ".join(line.split()) for line in out.splitlines()]
    return "\n".join(lines).strip()


def _validate_output(data: CatstyleCaptionLLMOutput) -> CatstyleCaptionLLMOutput:
    cap = _sanitize_text(data.caption)
    hook = _sanitize_text(data.hook) or cap.split("\n\n")[0][:200]
    comp = _sanitize_text(data.compensation)
    if len(cap) < 200:
        raise ValueError("caption too short after sanitization")
    return CatstyleCaptionLLMOutput(hook=hook, caption=cap, compensation=comp)


def build_fallback_caption(ctx: CatstyleCaptionContext) -> CatstyleCaptionResult:
    """Deterministic caption when LLM is unavailable (same structure as LLM target)."""
    asp_ru = {
        "conjunction": "соединение",
        "sextile": "секстиль",
        "square": "квадрат",
        "opposition": "оппозиция",
        "trine": "трин",
    }.get(ctx.aspect_type.lower(), ctx.aspect_type)

    pa_label = planet_display_ru(ctx.planet_a)
    pb_label = planet_display_ru(ctx.planet_b)
    sign_a = (
        f" ({sign_display_ru(ctx.planet_a_sign)})"
        if ctx.planet_a_sign and use_sign_in_public_caption(ctx.planet_a)
        else ""
    )
    sign_b = (
        f" ({sign_display_ru(ctx.planet_b_sign)})"
        if ctx.planet_b_sign and use_sign_in_public_caption(ctx.planet_b)
        else ""
    )

    p1 = ctx.planet_a_sign_context or ctx.planet_a_meaning
    p2 = ctx.planet_b_sign_context or ctx.planet_b_meaning

    feel = (
        "Сегодня обе темы звучат громче обычного — тело и нервы могут реагировать быстрее, "
        "чем успеваешь всё назвать словами."
    )
    if ctx.mode.lower() == "flow":
        feel = (
            "Сегодня есть ощущение короткого окна — если поймать его, день может дать облегчение; "
            "если проморгать, останется только «ну, было красиво в голове»."
        )

    risk = ctx.pressure_phrasing or (
        "Риск — разогнать тему в тревогу или в спор «кто прав», вместо одного ясного шага."
    )

    action = ctx.compensation_primary_action or (
        "выбери один маленький шаг на сегодня и зафиксируй критерий «стало легче или яснее?»"
    )
    why = ctx.compensation_why or "так ты переводишь аспект в опору, а не в бесконечное прокручивание."

    comp_entry = resolve_catstyle_compensation(ctx.planet_a, ctx.planet_b, ctx.aspect_type, ctx.mode)
    comp_block = ctx.compensation_guidance or (
        format_compensation_package_block(comp_entry)
        if comp_entry
        else "Как снять давление:\n• один конкретный шаг;\n• один проверяемый результат к вечеру."
    )

    paragraphs = [
        f"**{pa_label}{sign_a}** — {p1}",
        f"**{pb_label}{sign_b}** — {p2}",
        f"В **{asp_ru}** ({ctx.mode}) эти две силы встречаются так: {ctx.aspect_interaction}",
        feel,
        f"**Точка давления:** {risk}",
        f"**Компенсация:** {comp_block.split(chr(10))[0] if comp_block else 'сними накал одним ясным действием.'}",
        f"{CAPTION_COMPENSATION_MARKER} {action}.\nЗачем это работает: {why}",
    ]
    caption = "\n\n".join(paragraphs)
    hook = (
        f"{pa_label} и {pb_label}, {asp_ru}: "
        f"день не про «красивую теорию», а про один честный шаг."
    )
    polished = polish_caption_for_package(_sanitize_text(caption), ctx)
    return CatstyleCaptionResult(
        hook=hook,
        caption=polished,
        compensation=_sanitize_text(comp_block),
        source="fallback",
    )


def _responses_json_schema() -> dict[str, Any]:
    schema = make_strict_schema(CatstyleCaptionLLMOutput.model_json_schema())
    return {
        "type": "json_schema",
        "name": "catstyle_caption",
        "schema": schema,
        "strict": True,
    }


def _llm_caption_enabled(use_llm: bool | None) -> bool:
    if use_llm is not None:
        return use_llm
    return os.getenv("CATSTYLE_USE_LLM_CAPTION", "").strip().lower() in ("1", "true", "yes")


class OpenAICatstyleCaptionGenerator:
    """OpenAI Responses API caption writer (no DB logging)."""

    def __init__(self, *, client: Any | None = None, model: str | None = None) -> None:
        self._client = client
        self._model_override = model

    def _client_or_create(self) -> Any:
        if self._client is not None:
            return self._client
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return OpenAIClientFactory(api_key=settings.openai_api_key).create()

    def generate(self, ctx: CatstyleCaptionContext) -> CatstyleCaptionResult:
        client = self._client_or_create()
        settings = get_settings()
        model = (self._model_override or settings.openai_model).strip()
        instructions = _load_instructions()
        payload = context_to_llm_payload(ctx)
        resp = client.responses.create(
            model=model,
            instructions=instructions,
            input=json.dumps({"caption_context": payload}, ensure_ascii=False),
            text={"format": _responses_json_schema()},
            temperature=0.55,
            max_output_tokens=1800,
        )
        raw = resp.output_text
        data = json.loads(raw)
        parsed = _validate_output(CatstyleCaptionLLMOutput.model_validate(data))
        comp = parsed.compensation.strip()
        if not comp and ctx.compensation_guidance:
            comp = ctx.compensation_guidance.strip()
        cap = polish_caption_for_package(parsed.caption.strip(), ctx)
        return CatstyleCaptionResult(
            hook=parsed.hook.strip(),
            caption=cap,
            compensation=comp,
            source="llm",
        )


def generate_catstyle_caption(
    ctx: CatstyleCaptionContext,
    *,
    generator: CatstyleCaptionGenerator | None = None,
    use_llm: bool | None = None,
) -> CatstyleCaptionResult:
    """
    Generate caption via LLM when enabled and configured; otherwise structured fallback.
    """
    if not _llm_caption_enabled(use_llm):
        return build_fallback_caption(ctx)
    gen = generator
    if gen is None:
        settings = get_settings()
        if settings.openai_api_key:
            try:
                gen = OpenAICatstyleCaptionGenerator()
            except ValueError:
                gen = None
        if gen is None:
            return build_fallback_caption(ctx)
    try:
        return gen.generate(ctx)
    except Exception:
        return build_fallback_caption(ctx)


__all__ = [
    "CatstyleCaptionLLMOutput",
    "CatstyleCaptionGenerator",
    "CatstyleCaptionResult",
    "OpenAICatstyleCaptionGenerator",
    "build_fallback_caption",
    "generate_catstyle_caption",
]
