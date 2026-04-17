"""Editorial Use Checklist v1 — human memo from WeeklyVenusPackage + on-disk drafts.

Reads markdown drafts produced by ``generate_weekly_venus_drafts`` (same ``## Section`` layout).
Uses simple heuristics only — no LLM, no astrology recomputation.

Output: ``venus_editorial_checklist_<week_start>.md`` in the week folder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from astro_content_agent.services.content.venus_weekly_selector import WeeklyVenusPackage

_ORGANIC = ("сохрани", "подпис", "коммент", "напиши", "директ", "возвращайся", "узнал", "узнаёш")
_FORBIDDEN = ("money compass", "2-й дом", "2 дом", "10-й дом", "10 дом", "твоя венера", "личн")


def _extract_section(markdown: str, header: str) -> str | None:
    esc = re.escape(header)
    m = re.search(rf"(?ms)^## {esc}\s*\n(?P<body>.+?)(?=^## |\Z)", markdown)
    if not m:
        return None
    body = m.group("body").strip()
    return body or None


def _load_post_draft(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    md = path.read_text(encoding="utf-8")
    hook = _extract_section(md, "Hook") or ""
    caption = _extract_section(md, "Caption") or ""
    cta = _extract_section(md, "CTA") or ""
    return {"hook": hook.strip(), "caption": caption.strip(), "cta": cta.strip()}


def _load_reel_draft(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    md = path.read_text(encoding="utf-8")
    h0 = _extract_section(md, "hook_0_3s") or ""
    hook = _extract_section(md, "Spoken hook") or ""
    script = _extract_section(md, "Script") or ""
    cta = _extract_section(md, "CTA") or ""
    return {
        "hook_0_3s": h0.strip(),
        "hook": hook.strip(),
        "script": script.strip(),
        "cta": cta.strip(),
    }


def _load_support_draft(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    md = path.read_text(encoding="utf-8")
    lead = _extract_section(md, "Lead") or ""
    body = _extract_section(md, "Body") or ""
    cta = _extract_section(md, "CTA") or ""
    return {"lead": lead.strip(), "body": body.strip(), "cta": cta.strip()}


def _prev_week_post_hook(weekly_root: Path, week_start: date) -> str | None:
    prev = week_start - timedelta(days=7)
    p = weekly_root / prev.isoformat() / f"venus_weekly_post_{prev.isoformat()}.md"
    d = _load_post_draft(p)
    return d["hook"] if d else None


def _text_lower(s: str) -> str:
    return s.lower()


def _organic_cta_ok(text: str) -> bool:
    lo = _text_lower(text)
    return any(k in lo for k in _ORGANIC)


def _forbidden_in_text(text: str) -> bool:
    lo = _text_lower(text)
    return any(k in lo for k in _FORBIDDEN)


def _hook_strong_post(hook: str) -> bool:
    t = hook.strip()
    return 12 <= len(t) <= 220


def _hook_strong_reel(h0: str) -> bool:
    t = h0.strip()
    if len(t) < 8:
        return False
    words = t.split()
    return len(words) <= 10 and len(t) <= 90


def _compensation_clear(caption_or_script: str) -> bool:
    """Heuristic: list-like structure or explicit compensation wording."""
    if not caption_or_script:
        return False
    lines = [ln.strip() for ln in caption_or_script.splitlines() if ln.strip()]
    bulletish = sum(1 for ln in lines if ln.startswith(("-", "—", "•", "*"))) >= 2
    keywords = ("компенс", "что помогает", "что сейчас полезно", "микро", "практик")
    lo = _text_lower(caption_or_script)
    return bulletish or any(k in lo for k in keywords)


def _first_words_key(s: str, n: int = 6) -> tuple[str, ...]:
    return tuple(_text_lower(s).split()[:n])


def _too_similar_to_prior(current_hook: str, prior: str | None) -> bool:
    if not prior or not current_hook:
        return False
    a = _first_words_key(current_hook, 5)
    b = _first_words_key(prior, 5)
    if a and a == b:
        return True
    cur = current_hook.strip().lower()[:60]
    prv = prior.strip().lower()[:60]
    return bool(cur) and cur == prv


def _stack_readable_reel(script: str) -> bool:
    return 40 <= len(script) <= 2500


def _publish_order_lines(pkg: WeeklyVenusPackage) -> tuple[str, str]:
    if not pkg.overlay_active or pkg.overlay_mode == "climate_only":
        order = "1) Пост → 2) Рилс → 3) Support (опционально)"
        why = (
            "Климат-only: пост задаёт узнаваемый фон и утечку; рилс даёт быстрый хук; "
            "support — лёгкое усиление без перегруза."
        )
    elif pkg.overlay_mode == "friction":
        order = "1) Рилс → 2) Пост → 3) Support (опционально)"
        why = "Трение/аспект — сильнее сначала дать узнавание в коротком формате, затем разбор в посте."
    else:
        order = "1) Пост → 2) Рилс → 3) Support (опционально)"
        why = (
            "Оверлей opportunity: сначала контекст и «окно» в посте, затем динамика в рилсе."
        )
    return order, why


def _verdict(
    *,
    post_forbidden: bool,
    reel_forbidden: bool,
    post_weak: bool,
    reel_weak: bool,
    post_similar: bool,
    reel_similar: bool,
    reel_loaded: bool,
) -> tuple[str, str]:
    if post_forbidden or reel_forbidden:
        return "hold_and_rewrite", "В тексте или CTA есть запрещённые формулировки — править до чистого органического режима."
    if not reel_loaded:
        return "publish_with_light_edits", "Файл рилса не найден — догенерировать или принять только пост/support."
    if post_weak and reel_weak:
        return "hold_and_rewrite", "И пост, и рилс выглядят слабо по зацепкам — лучше переписать с новым входом."
    if post_similar and reel_similar:
        return "publish_with_light_edits", "Зацепки всё ещё близки к прошлой неделе — лёгкая ручная дифференциация."
    if not post_weak and not reel_weak and not post_similar and not reel_similar:
        return "publish_now", "Эвристики зелёные — можно выкладывать после быстрого глазного просмотра."
    return "publish_with_light_edits", "Точечно проверить отмеченные пункты и при необходимости поджать формулировки."


@dataclass(frozen=True)
class ChecklistPaths:
    checklist_path: Path


def render_editorial_checklist_markdown(
    *,
    pkg: WeeklyVenusPackage,
    week_dir: Path,
    weekly_venus_root: Path | None = None,
) -> str:
    """Build checklist markdown. Raises ``FileNotFoundError`` if post draft is missing."""
    ws = pkg.week_start.isoformat()
    post_path = week_dir / f"venus_weekly_post_{ws}.md"
    reel_path = week_dir / f"venus_weekly_reel_{ws}.md"
    sup_path = week_dir / f"venus_weekly_support_{ws}.md"

    post = _load_post_draft(post_path)
    if post is None:
        raise FileNotFoundError(f"missing post draft: {post_path}")

    reel = _load_reel_draft(reel_path)
    support = _load_support_draft(sup_path) if sup_path.is_file() else None

    root = weekly_venus_root or week_dir.parent
    prior_hook = _prev_week_post_hook(root, pkg.week_start)

    post_hook_ok = _hook_strong_post(post["hook"])
    post_similar = _too_similar_to_prior(post["hook"], prior_hook)
    post_comp = _compensation_clear(post["caption"])
    post_body = post["caption"] + " " + post["cta"]
    post_organic = _organic_cta_ok(post["cta"]) or _organic_cta_ok(post["caption"])
    post_forbid = _forbidden_in_text(post_body)
    post_manual = (not post_hook_ok) or post_similar or (not post_comp) or (not post_organic) or post_forbid
    post_notes: list[str] = []
    if not post_hook_ok:
        post_notes.append("Зацепка короткая/длинная — проверь ударность.")
    if post_similar:
        post_notes.append("Близко к зацепке прошлой недели — смени вход или образ.")
    if not post_comp:
        post_notes.append("Слабо виден список/блок компенсации — усилить по weekly pack.")
    if not post_organic:
        post_notes.append("CTA: нет явного органического призыва (сохрани/коммент/подписка).")
    if post_forbid:
        post_notes.append("Убрать запрещённые упоминания (приложение / натальные дома в CTA).")

    reel_notes: list[str] = []
    reel_loaded = reel is not None
    reel_hook_ok = False
    reel_stack = False
    reel_comp = False
    reel_organic = False
    reel_forbid = False
    reel_similar = False
    reel_manual = not reel_loaded
    if reel:
        reel_hook_ok = _hook_strong_reel(reel["hook_0_3s"])
        reel_stack = _stack_readable_reel(reel["script"])
        reel_comp = _compensation_clear(reel["script"])
        rb = reel["script"] + " " + reel["cta"]
        reel_organic = _organic_cta_ok(reel["cta"]) or _organic_cta_ok(reel["script"])
        reel_forbid = _forbidden_in_text(rb)
        reel_similar = _too_similar_to_prior(reel["hook_0_3s"], prior_hook)
        reel_manual = (
            (not reel_hook_ok)
            or (not reel_stack)
            or (not reel_comp)
            or (not reel_organic)
            or reel_forbid
            or reel_similar
        )
        if not reel_hook_ok:
            reel_notes.append("hook_0_3s: слишком длинно/пусто для первых секунд.")
        if not reel_stack:
            reel_notes.append("Сценарий кажется слишком коротким или перегруженным — проверить ритм.")
        if not reel_comp:
            reel_notes.append("Compensation beat слабо выделен.")
        if not reel_organic:
            reel_notes.append("CTA рилса — добавить органический призыв.")
        if reel_forbid:
            reel_notes.append("Убрать запрещённые формулировки.")
        if reel_similar:
            reel_notes.append("0–3с близко к прошлой неделе — освежить.")
    else:
        reel_notes.append("Файл рилса не найден — сгенерируй черновик.")

    # Support
    sup_worth = False
    sup_why = "Файл support не создан (угол support в пакете короткий или черновик не писали)."
    sup_format = "—"
    sup_notes: list[str] = []
    if support:
        body_len = len(support["body"])
        if body_len >= 80:
            sup_worth = True
            sup_why = "Текст достаточно плотный для вторичного выхода."
            sup_format = "stories или одна карточка карусели (короткий lead + body)."
        else:
            sup_why = "Текст короткий — можно оставить как internal note или дописать вручную."
            sup_notes.append("Расширить на 2–3 предложения с одним действием, если публикуешь.")
    elif sup_path.is_file():
        sup_why = "Файл есть, но не распарсился."

    order, why_order = _publish_order_lines(pkg)
    verdict_key, verdict_expl = _verdict(
        post_forbidden=post_forbid,
        reel_forbidden=reel_forbid,
        post_weak=not post_hook_ok,
        reel_weak=not reel_hook_ok,
        post_similar=post_similar,
        reel_similar=reel_similar,
        reel_loaded=reel_loaded,
    )

    overlay_line = (
        f"да — `{pkg.overlay_pair}` ({pkg.overlay_mode})"
        if pkg.overlay_active and pkg.overlay_pair
        else f"нет — {pkg.overlay_mode}"
    )

    def yn(b: bool) -> str:
        return "да" if b else "нет"

    lines: list[str] = [
        "# Venus editorial checklist",
        "",
        "## Week",
        "",
        f"- **Диапазон:** {pkg.week_start.isoformat()} → {pkg.week_end.isoformat()}",
        f"- **Климат Венеры:** {pkg.venus_sign} — {_one_line(pkg.climate_title)}",
        f"- **Оверлей:** {overlay_line}",
        "",
        "## Publish order",
        "",
        f"- **Порядок:** {order}",
        f"- **Почему:** {why_order}",
        "",
        "## Post check",
        "",
        f"- **Зацепка сильная?** {yn(post_hook_ok)}",
        f"- **Слишком похоже на прошлую неделю?** {yn(post_similar)}",
        f"- **Компенсация читается?** {yn(post_comp)}",
        f"- **CTA органический?** {yn(post_organic and not post_forbid)}",
        f"- **Нужна ручная правка?** {yn(post_manual)}",
        "- **Заметки редактора:**",
    ]
    lines.extend([f"  - {n}" for n in post_notes] if post_notes else ["  - —"])
    lines.extend(
        [
            "",
            "## Reel check",
            "",
            f"- **hook_0_3s сильный?** {yn(reel_hook_ok)}",
            f"- **Стек читается?** {yn(reel_stack)}",
            f"- **Compensation beat ясен?** {yn(reel_comp)}",
            f"- **CTA органический?** {yn(reel_organic and not reel_forbid)}",
            f"- **Нужна ручная правка?** {yn(reel_manual)}",
            "- **Заметки редактора:**",
        ]
    )
    lines.extend([f"  - {n}" for n in reel_notes] if reel_notes else ["  - —"])
    lines.extend(
        [
            "",
            "## Support check",
            "",
            f"- **Стоит постить?** {yn(sup_worth)}",
            f"- **Если нет — почему:** {sup_why}",
            f"- **Если да — формат:** {sup_format}",
            f"- **Заметки:** {'; '.join(sup_notes) if sup_notes else '—'}",
            "",
            "## Final weekly recommendation",
            "",
            f"- **Вердикт:** `{verdict_key}`",
            f"- **Пояснение:** {verdict_expl}",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _one_line(s: str, max_len: int = 100) -> str:
    s = s.strip()
    return s if len(s) <= max_len else s[: max_len - 1].rstrip() + "…"


def write_editorial_checklist(
    pkg: WeeklyVenusPackage,
    week_dir: Path,
    *,
    weekly_venus_root: Path | None = None,
) -> Path:
    """Write ``venus_editorial_checklist_<week_start>.md`` into *week_dir*."""
    md = render_editorial_checklist_markdown(
        pkg=pkg, week_dir=week_dir, weekly_venus_root=weekly_venus_root
    )
    out = week_dir / f"venus_editorial_checklist_{pkg.week_start.isoformat()}.md"
    out.write_text(md, encoding="utf-8")
    return out
