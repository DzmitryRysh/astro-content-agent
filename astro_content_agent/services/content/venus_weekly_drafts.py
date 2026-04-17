"""Weekly Venus draft generation — post + reel (+ optional support) from WeeklyVenusPackage.

Uses ``ResponsesRunner`` + existing Russian prompts (copywriter / reel_writer).
Injects ``weekly_venus_draft_context`` for editorial angles and file-based anti-repeat
against the **previous calendar week** folder under the same ``weekly_venus`` root.

Does not change AstroEngineV1, climate, overlay, selector, or review artifact modules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from astro_content_agent.astro.engine import AstroEngineV1, EngineInput
from astro_content_agent.schemas.astro import AstroDayPayload
from astro_content_agent.schemas.drafts import PostDraftPayload, ReelDraftPayload
from astro_content_agent.services.ai.responses_runner import PromptRef, ResponsesRunner, prompt_ref_for_language
from astro_content_agent.services.content.aspect_behavior_cards import AspectBehaviorCardsContext
from astro_content_agent.services.content.live_astrology_rules import LiveAstrologyContext
from astro_content_agent.services.content.money_astrology import MoneyAstrologyContext, MoneyKnowledgeBase
from astro_content_agent.services.content.persona import PersonaContext
from astro_content_agent.services.content.venus_aspect_overlay import VenusAspectOverlayContext
from astro_content_agent.services.content.venus_sign_climate import VenusSignClimateContext
from astro_content_agent.services.content.venus_weekly_selector import WeeklyVenusPackage


# ---------------------------------------------------------------------------
# Previous-week snapshot (file-based, no DB)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreviousWeekSnapshot:
    """Signals read from ``weekly_venus/<prev_week>/`` when those files exist."""

    week_folder: Path
    venus_sign: str | None
    hook_family: str | None
    post_hook: str | None
    reel_hook_0_3s: str | None


def _parse_md_section(markdown: str, header: str) -> str | None:
    """Return body under ``## {header}`` until the next ``## `` heading or EOF."""
    esc = re.escape(header)
    m = re.search(rf"(?ms)^## {esc}\s*\n(?P<body>.+?)(?=^## |\Z)", markdown)
    if not m:
        return None
    body = m.group("body").strip()
    return body or None


def _parse_review_sign_and_hook_family(review_md: str) -> tuple[str | None, str | None]:
    sign = None
    m_sign = re.search(r"(?m)^- \*\*Знак:\*\* (\w+)", review_md)
    if m_sign:
        sign = m_sign.group(1).strip()
    fam = None
    m_f = re.search(r"- \*\*Hook family:\*\* `([^`]+)`", review_md)
    if m_f:
        fam = m_f.group(1).strip()
    return sign, fam


def load_previous_week_snapshot(weekly_venus_root: Path, week_start: date) -> PreviousWeekSnapshot | None:
    """Load prior week artifacts if ``weekly_venus/<week_start - 7d>/`` exists."""
    prev = week_start - timedelta(days=7)
    folder = weekly_venus_root / prev.isoformat()
    if not folder.is_dir():
        return None

    review_path = folder / f"venus_weekly_review_{prev.isoformat()}.md"
    post_path = folder / f"venus_weekly_post_{prev.isoformat()}.md"
    reel_path = folder / f"venus_weekly_reel_{prev.isoformat()}.md"

    sign, fam = None, None
    if review_path.is_file():
        sign, fam = _parse_review_sign_and_hook_family(review_path.read_text(encoding="utf-8"))

    post_hook = None
    if post_path.is_file():
        post_hook = _parse_md_section(post_path.read_text(encoding="utf-8"), "Hook")

    reel_h = None
    if reel_path.is_file():
        reel_h = _parse_md_section(reel_path.read_text(encoding="utf-8"), "hook_0_3s")

    if sign is None and fam is None and post_hook is None and reel_h is None:
        return None

    return PreviousWeekSnapshot(
        week_folder=folder,
        venus_sign=sign,
        hook_family=fam,
        post_hook=post_hook,
        reel_hook_0_3s=reel_h,
    )


def build_anti_repeat_instruction(
    pkg: WeeklyVenusPackage,
    prev: PreviousWeekSnapshot | None,
) -> tuple[str, str | None, list[str]]:
    """Return (anti_repeat_note, forced_hook_angle_ru, adjustment_log).

    ``forced_hook_angle_ru`` — when set, model should lean on this climate angle
    instead of defaulting to ``instagram_hook_angles[0]``.
    """
    log: list[str] = []
    if prev is None:
        return "", None, log

    parts: list[str] = []
    forced: str | None = None
    climate = pkg.climate_ctx.climate
    angles: tuple[str, ...] = climate.instagram_hook_angles if climate else ()

    same_sign = prev.venus_sign and prev.venus_sign == pkg.venus_sign
    same_family = (
        prev.hook_family
        and prev.hook_family == pkg.hook_family
    )

    if same_sign and same_family and angles:
        forced = angles[1] if len(angles) > 1 else angles[0]
        log.append("same_sign_same_hook_family→forced_secondary_angle")
        parts.append(
            f"**Анти-повтор (недельный):** прошлая неделя была тот же транзитный знак Венеры "
            f"({pkg.venus_sign}) и та же hook-семья (`{pkg.hook_family}`). "
            f"НЕ повторяй прошлую неделю как «ещё один такой же пост». "
            f"ОБЯЗАТЕЛЬНО возьми **другой вход**: опора — `forced_hook_angle_ru` "
            f"(второй/третий угол климата), другая утечка из likely_leak, другой тон зацепки."
        )
    elif same_sign and not pkg.overlay_active:
        log.append("same_sign_climate_only→vary_leak_entry")
        parts.append(
            f"**Анти-повтор:** знак Венеры тот же ({pkg.venus_sign}), что на прошлой неделе. "
            f"Смени точку входа: начни со **второй или третьей** типичной утечки климата, "
            f"не с той же формулировки, что в прошлом мемо."
        )

    if prev.post_hook and len(prev.post_hook) > 12:
        snippet = prev.post_hook.replace("\n", " ").strip()[:160]
        parts.append(
            f"**Запрещённый ориентир (прошлый пост):** не копируй этот зачин и не перефразируй его "
            f"один-в-один: «{snippet}» — нужен новый ритм и новая картинка."
        )
        log.append("blocked_prev_post_hook_snippet")

    if prev.reel_hook_0_3s and len(prev.reel_hook_0_3s) > 8:
        rs = prev.reel_hook_0_3s.replace("\n", " ").strip()[:120]
        parts.append(
            f"**Прошлый рилс 0–3с:** не повторяй эту формулировку: «{rs}»."
        )
        log.append("blocked_prev_reel_hook")

    return "\n\n".join(parts), forced, log


def _reference_astro_day(pkg: WeeklyVenusPackage, brand_id: str) -> AstroDayPayload:
    """Representative day for money_astrology + aspect cards (best overlay day or midweek)."""
    ref = pkg.best_day or (pkg.week_start + timedelta(days=3))
    return AstroEngineV1().generate_day(EngineInput(brand_profile_id=brand_id, day=ref))


def _overlay_dict(pkg: WeeklyVenusPackage, cards_ctx: AspectBehaviorCardsContext) -> dict[str, Any]:
    if pkg.overlay_ctx is not None:
        return pkg.overlay_ctx.to_dict()
    return VenusAspectOverlayContext.from_contexts(pkg.climate_ctx, cards_ctx).to_dict()


def build_weekly_venus_input_payload(
    *,
    pkg: WeeklyVenusPackage,
    brand: Any,
    astro_day: AstroDayPayload,
    draft_role: str,
    anti_repeat_note: str,
    forced_hook_angle_ru: str | None,
    anti_repeat_log: list[str],
) -> dict[str, Any]:
    language = getattr(brand, "content_language", "ru") or "ru"
    persona = PersonaContext.from_brand(brand, language=language)
    cards_ctx = AspectBehaviorCardsContext.from_astro_day(astro_day)
    climate = pkg.climate_ctx.climate
    angles = list(climate.instagram_hook_angles) if climate else []

    weekly_ctx: dict[str, Any] = {
        "source": "weekly_venus_drafts_v1",
        "draft_role": draft_role,
        "week_start": pkg.week_start.isoformat(),
        "week_end": pkg.week_end.isoformat(),
        "primary_post_angle": pkg.primary_post_angle,
        "primary_reel_angle": pkg.primary_reel_angle,
        "support_angle": pkg.support_angle,
        "hook_family": pkg.hook_family,
        "compensation_focus": pkg.compensation_focus,
        "instagram_hook_angles": angles,
        "forced_hook_angle_ru": forced_hook_angle_ru,
        "anti_repeat_note": anti_repeat_note,
        "anti_repeat_adjustments": anti_repeat_log,
    }

    return {
        "brand_profile": {
            "id": getattr(brand, "id", "weekly-venus"),
            "name": getattr(brand, "name", "Weekly Venus"),
            "description": getattr(brand, "description", ""),
            "tone_preset": getattr(brand, "tone_preset", "sharp_witty"),
            "banned_terms": list(getattr(brand, "banned_terms", []) or []),
            "default_hashtags": list(getattr(brand, "default_hashtags", []) or []),
            "face_led_preferred": bool(getattr(brand, "face_led_preferred", False)),
            "content_language": language,
        },
        "astro_day": astro_day.model_dump(mode="json"),
        "plan_item": None,
        "persona_context": persona.to_prompt_hint(),
        "anti_repeat_context": "",
        "money_astrology_context": MoneyAstrologyContext.from_astro_day(astro_day).to_dict(),
        "money_knowledge_v2": MoneyKnowledgeBase.to_dict(),
        "live_astrology_context": LiveAstrologyContext.to_dict(),
        "aspect_behavior_cards_context": cards_ctx.to_dict(),
        "venus_sign_climate_context": pkg.climate_ctx.to_dict(),
        "venus_aspect_overlay_context": _overlay_dict(pkg, cards_ctx),
        "weekly_venus_draft_context": weekly_ctx,
    }


def _write_post_md(
    path: Path,
    *,
    week_start: date,
    week_end: date,
    anti_repeat_note: str,
    log: list[str],
    payload: PostDraftPayload,
) -> None:
    lines = [
        f"# Venus weekly — post draft",
        f"",
        f"<!-- week: {week_start.isoformat()} → {week_end.isoformat()} -->",
        f"",
        f"## Anti-repeat",
        f"{anti_repeat_note or 'none'}",
        f"",
        f"## Adjustments",
        f"{', '.join(log) if log else 'none'}",
        f"",
        f"## Hook",
        payload.hook,
        f"",
        f"## Caption",
        payload.caption,
        f"",
        f"## CTA",
        payload.cta,
        f"",
        f"## Hashtags",
        "\n".join(f"- {h}" for h in payload.hashtags) if payload.hashtags else "-",
        f"",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_reel_md(
    path: Path,
    *,
    week_start: date,
    week_end: date,
    anti_repeat_note: str,
    log: list[str],
    payload: ReelDraftPayload,
) -> None:
    lines = [
        f"# Venus weekly — reel draft",
        f"",
        f"<!-- week: {week_start.isoformat()} → {week_end.isoformat()} -->",
        f"",
        f"## Anti-repeat",
        f"{anti_repeat_note or 'none'}",
        f"",
        f"## Adjustments",
        f"{', '.join(log) if log else 'none'}",
        f"",
        f"## hook_0_3s",
        payload.hook_0_3s,
        f"",
        f"## Spoken hook",
        payload.hook,
        f"",
        f"## Script",
        payload.script,
        f"",
        f"## CTA",
        payload.cta,
        f"",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_support_md(path: Path, *, week_start: date, week_end: date, payload: PostDraftPayload) -> None:
    lines = [
        "# Venus weekly — support (stories / carousel note)",
        "",
        f"<!-- week: {week_start.isoformat()} → {week_end.isoformat()} -->",
        "",
        "## Lead",
        payload.hook,
        "",
        "## Body",
        payload.caption,
        "",
        "## CTA",
        payload.cta,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def support_angle_is_meaningful(support_angle: str, *, min_len: int = 36) -> bool:
    return len(support_angle.strip()) >= min_len


@dataclass(frozen=True)
class WeeklyVenusDraftResult:
    post_path: Path
    reel_path: Path
    support_path: Path | None
    anti_repeat_note: str
    anti_repeat_log: tuple[str, ...]
    forced_hook_angle_ru: str | None


def generate_weekly_venus_drafts(
    *,
    db: Session,
    runner: ResponsesRunner,
    brand: Any,
    pkg: WeeklyVenusPackage,
    output_dir: Path,
    brand_id: str = "weekly-workflow",
    weekly_venus_root: Path | None = None,
) -> WeeklyVenusDraftResult:
    """Generate post + reel markdown (+ optional support) under *output_dir*.

    *weekly_venus_root* — parent of per-week folders (for previous-week scan);
    defaults to *output_dir.parent* when *output_dir* ends with
    ``<weekly_root>/<YYYY-MM-DD>/`` (for example ``scripts/aca/weekly_venus/<date>/``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    root = weekly_venus_root or output_dir.parent

    prev = load_previous_week_snapshot(root, pkg.week_start)
    anti_note, forced_hook, log_list = build_anti_repeat_instruction(pkg, prev)
    log = list(log_list)

    astro_day = _reference_astro_day(pkg, brand_id)
    ws = pkg.week_start.isoformat()

    # --- Post
    post_payload_in = build_weekly_venus_input_payload(
        pkg=pkg,
        brand=brand,
        astro_day=astro_day,
        draft_role="main_post",
        anti_repeat_note=anti_note,
        forced_hook_angle_ru=forced_hook,
        anti_repeat_log=log,
    )
    post_payload = runner.run_json(
        db=db,
        prompt_ref=prompt_ref_for_language("copywriter", getattr(brand, "content_language", "ru") or "ru"),
        schema=PostDraftPayload,
        input_payload=post_payload_in,
        max_output_tokens=1400,
        metadata={"kind": "weekly_venus_post", "week_start": ws},
    )
    post_path = output_dir / f"venus_weekly_post_{ws}.md"
    _write_post_md(
        post_path,
        week_start=pkg.week_start,
        week_end=pkg.week_end,
        anti_repeat_note=anti_note,
        log=log,
        payload=post_payload,
    )

    # --- Reel
    reel_payload_in = build_weekly_venus_input_payload(
        pkg=pkg,
        brand=brand,
        astro_day=astro_day,
        draft_role="main_reel",
        anti_repeat_note=anti_note,
        forced_hook_angle_ru=forced_hook,
        anti_repeat_log=log,
    )
    reel_payload = runner.run_json(
        db=db,
        prompt_ref=prompt_ref_for_language("reel_writer", getattr(brand, "content_language", "ru") or "ru"),
        schema=ReelDraftPayload,
        input_payload=reel_payload_in,
        max_output_tokens=1200,
        metadata={"kind": "weekly_venus_reel", "week_start": ws},
    )
    reel_path = output_dir / f"venus_weekly_reel_{ws}.md"
    _write_reel_md(
        reel_path,
        week_start=pkg.week_start,
        week_end=pkg.week_end,
        anti_repeat_note=anti_note,
        log=log,
        payload=reel_payload,
    )

    # --- Support (optional)
    support_path: Path | None = None
    if support_angle_is_meaningful(pkg.support_angle):
        sup_ctx = dict(post_payload_in["weekly_venus_draft_context"])
        sup_ctx["draft_role"] = "support_stories"
        sup_ctx["primary_post_angle"] = pkg.support_angle
        sup_in = {**post_payload_in, "weekly_venus_draft_context": sup_ctx}
        sup_payload = runner.run_json(
            db=db,
            prompt_ref=prompt_ref_for_language("copywriter", getattr(brand, "content_language", "ru") or "ru"),
            schema=PostDraftPayload,
            input_payload=sup_in,
            max_output_tokens=700,
            temperature=0.35,
            metadata={"kind": "weekly_venus_support", "week_start": ws},
        )
        support_path = output_dir / f"venus_weekly_support_{ws}.md"
        _write_support_md(support_path, week_start=pkg.week_start, week_end=pkg.week_end, payload=sup_payload)

    return WeeklyVenusDraftResult(
        post_path=post_path,
        reel_path=reel_path,
        support_path=support_path,
        anti_repeat_note=anti_note,
        anti_repeat_log=tuple(log),
        forced_hook_angle_ru=forced_hook,
    )
