"""Catstyle v1 — deterministic local Instagram-oriented post package from image job manifests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


POST_PACKAGE_VERSION = "catstyle-post-package-v1"


def load_catstyle_image_generation_manifest(manifest_path: Path | str) -> dict[str, Any]:
    """Load ``image_generation_jobs.json`` (v0) as a plain dict."""
    p = Path(manifest_path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Manifest not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object.")
    return data


def _sorted_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        jobs,
        key=lambda j: (
            int(j.get("prompt_index") or 0),
            int(j.get("variant_index") or 0),
            str(j.get("job_id") or ""),
        ),
    )


def _aspect_summary(selected: dict[str, Any] | None) -> str | None:
    if not selected:
        return None
    pa = selected.get("planet_a")
    pb = selected.get("planet_b")
    asp = selected.get("aspect_type")
    mode = selected.get("mode_recommendation")
    score = selected.get("total_score")
    parts = [str(x) for x in (pa, asp, pb) if x is not None and str(x).strip()]
    head = " ".join(parts) if parts else "Catstyle aspect"
    tail_bits: list[str] = []
    if mode:
        tail_bits.append(f"режим: {mode}")
    if score is not None:
        tail_bits.append(f"score={score}")
    if tail_bits:
        return f"{head} ({', '.join(tail_bits)})"
    return head


def _infer_shot_mode(manifest: dict[str, Any], jobs: list[dict[str, Any]]) -> str | None:
    top = manifest.get("shot_mode")
    if isinstance(top, str) and top.strip():
        return top.strip()
    if any(str(j.get("shot_role") or "").strip() for j in jobs):
        return "hero_pair"
    return "standard"


def _is_jupiter_mars_tension_pack(selected: dict[str, Any] | None, jobs: list[dict[str, Any]]) -> bool:
    def check(pa: str | None, pb: str | None, asp: str | None, mode: str | None) -> bool:
        if not pa or not pb:
            return False
        a, b = pa.lower(), pb.lower()
        planets = {a, b} == {"jupiter", "mars"}
        aspect = (asp or "").lower()
        mode_l = (mode or "").lower()
        aspect_hard = aspect in ("square", "opposition")
        mode_tension = mode_l == "tension"
        return planets and (aspect_hard or mode_tension)

    if selected and check(
        str(selected.get("planet_a") or "") or None,
        str(selected.get("planet_b") or "") or None,
        str(selected.get("aspect_type") or "") or None,
        str(selected.get("mode_recommendation") or "") or None,
    ):
        return True
    for j in jobs[:1]:
        if check(
            str(j.get("planet_a") or "") or None,
            str(j.get("planet_b") or "") or None,
            str(j.get("aspect_type") or "") or None,
            str(j.get("mode") or "") or None,
        ):
            return True
    return False


def _ru_jupiter_mars_square() -> tuple[str, str, str, str, str]:
    hook = (
        "Юпитер vs Марс: масштаб против удара. "
        "Идея уже развернула паруса, а ты уже несёшься таранить берег."
    )
    caption = (
        "Космический спектакль на тему «квадрата»: Юпитер тянет «расширим смысл и горизонт», "
        "Марс орёт «прямо сейчас и железом». Это не обязательно драма ради драмы — "
        "это конфликт между стратегией масштаба и импульсом атаки. "
        "Острота в том, что вдохновение легко превратить в случайный налёт без координат. "
        "Сарказм бесплатный, разбор полётов — тоже; билет обратно бережёт только дисциплина."
    )
    carousel = (
        "Слайд 1 — Обложка: два планетных кота в напряжении, без текста на арте.\n"
        "Слайд 2 — Марс: «удари сейчас» — импульс, жар, телега впереди лошади.\n"
        "Слайд 3 — Юпитер: «подожди смысл» — масштаб, смысл, не разметать усилие по щелям.\n"
        "Слайд 4 — Вывод: смелость да, хаос как доказательство крутости — нет."
    )
    compensation = (
        "Компенсация (если чувствуешь жар квадрата):\n"
        "• одно действие — без меню из десяти пунктов;\n"
        "• один измеримый результат — чтобы не «я старался», а «готово»;\n"
        "• не доказывай себя через хаос и эффектность;\n"
        "• направь жару в спорт, в фокусную работу или в стратегию с ясным шагом."
    )
    checklist = (
        "Чеклист перед постом:\n"
        "☐ Выбрал одно действие на сегодня.\n"
        "☐ Сформулировал один измеримый результат.\n"
        "☐ Отделил импульс от «докажу-что-я-могу-сломать».\n"
        "☐ Дал энергии канал: спорт / глубокая работа / план на 3 шага."
    )
    return hook, caption, carousel, compensation, checklist


def _ru_generic(pa: str | None, pb: str | None, asp: str | None) -> tuple[str, str, str, str, str]:
    label = " / ".join(str(x) for x in (pa, asp, pb) if x) or "Catstyle"
    hook = (
        f"Аспект дня ({label}): космическое совещание закончилось, "
        f"а Земля всё равно просит конкретику."
    )
    caption = (
        f"Пакет Catstyle для ручной сборки поста. Смотри на пару и тип аспекта как на метафору ритма: "
        f"где хочется действовать, где — расширять, где — тормозить. "
        f"Без морализаторства: просто якорь для подписи и карусели."
    )
    carousel = (
        "Слайд 1 — Обложка: ключевой кадр без текста на арте.\n"
        "Слайд 2 — Контекст аспекта коротко и по делу.\n"
        "Слайд 3 — Второй ракурс / деталь из промпт-пака.\n"
        "Слайд 4 — Мягкий вывод: что сохранить из этого дня."
    )
    compensation = (
        "Компенсация:\n"
        "• одно действие;\n"
        "• один проверяемый результат;\n"
        "• не разгонять тревогу скоростью;\n"
        "• энергию — в телесный режим или спокойную задачу."
    )
    checklist = (
        "Чеклист:\n"
        "☐ Совпадает ли картинка с аспектом и тоном профиля?\n"
        "☐ Есть ли один явный посыл, без перегруза?\n"
        "☐ Карусель читается без текста на слайдах?\n"
        "☐ Дисклеймер/юмор на месте по правилам канала?"
    )
    return hook, caption, carousel, compensation, checklist


def _collect_generated_paths(
    jobs: list[dict[str, Any]],
    gen_dir: Path | None,
) -> tuple[list[str], str | None]:
    """Return ordered resolved paths and deterministic primary recommendation."""
    if gen_dir is None or not gen_dir.is_dir():
        return [], None
    resolved: list[tuple[dict[str, Any], str]] = []
    for job in jobs:
        name = job.get("suggested_output_name")
        if not name:
            continue
        p = gen_dir / Path(str(name)).name
        if p.is_file():
            resolved.append((job, str(p.resolve())))
    if not resolved:
        return [], None

    paths = [rp for _, rp in resolved]
    hero = next((rp for j, rp in resolved if str(j.get("shot_role") or "") == "hero_poster"), None)
    primary = hero if hero else resolved[0][1]
    return paths, primary


class CatstylePostPackage(BaseModel):
    """Ready-to-review Instagram post package (local files only)."""

    version: str = POST_PACKAGE_VERSION
    date: str
    aspect_summary: str | None = None
    editorial_profile: str
    world_template: str | None = None
    scene_template: str | None = None
    render_style_profile: str | None = None
    shot_mode: str | None = None
    style_reference_image_path: str | None = None
    image_jobs_summary: list[dict[str, Any]] = Field(default_factory=list)
    generated_image_paths: list[str] = Field(default_factory=list)
    recommended_primary_image: str | None = None
    hook: str
    caption: str
    carousel_slide_text: str
    compensation: str
    checklist: str
    source_manifest_path: str


def build_catstyle_post_package(
    manifest_path: Path | str,
    *,
    generated_images_dir: Path | str | None = None,
) -> CatstylePostPackage:
    mp = Path(manifest_path).expanduser().resolve()
    raw = load_catstyle_image_generation_manifest(mp)

    date = str(raw.get("date") or "").strip()
    if not date:
        raise ValueError("Manifest missing required field: date")

    editorial_profile = str(raw.get("editorial_profile") or "balanced").strip() or "balanced"
    selected = raw.get("selected_candidate") if isinstance(raw.get("selected_candidate"), dict) else None
    jobs_raw = raw.get("jobs")
    jobs_list = jobs_raw if isinstance(jobs_raw, list) else []
    jobs = _sorted_jobs([j for j in jobs_list if isinstance(j, dict)])

    gen_path = None
    if generated_images_dir is not None:
        gen_path = Path(generated_images_dir).expanduser().resolve()

    aspect_summary = _aspect_summary(selected)
    shot_mode = _infer_shot_mode(raw, jobs)

    def _key_opt(gen):
        k = next(gen, None)
        return k if k else None

    wt = _key_opt(str(j.get("world_template_key", "")).strip() for j in jobs if str(j.get("world_template_key", "")).strip())
    st = _key_opt(str(j.get("scene_template_key", "")).strip() for j in jobs if str(j.get("scene_template_key", "")).strip())
    rsp = _key_opt(
        str(j.get("render_style_profile_key", "")).strip()
        for j in jobs
        if str(j.get("render_style_profile_key", "")).strip()
    )

    style_ref = _key_opt(
        str(j.get("style_reference_image_path", "")).strip()
        for j in jobs
        if str(j.get("style_reference_image_path", "")).strip()
    )
    image_jobs_summary = [
        {
            "job_id": j.get("job_id"),
            "prompt_index": j.get("prompt_index"),
            "variant_index": j.get("variant_index"),
            "suggested_output_name": j.get("suggested_output_name"),
            "shot_role": j.get("shot_role"),
            "status": j.get("status"),
            "planet_a": j.get("planet_a"),
            "planet_b": j.get("planet_b"),
            "aspect_type": j.get("aspect_type"),
            "mode": j.get("mode"),
        }
        for j in jobs
    ]

    gen_paths, primary = _collect_generated_paths(jobs, gen_path)

    pa_g = str(selected.get("planet_a")) if selected else None
    pb_g = str(selected.get("planet_b")) if selected else None
    asp_g = str(selected.get("aspect_type")) if selected else None
    if _is_jupiter_mars_tension_pack(selected, jobs):
        hook, caption, carousel, compensation, checklist = _ru_jupiter_mars_square()
    else:
        hook, caption, carousel, compensation, checklist = _ru_generic(pa_g, pb_g, asp_g)

    # Prefer first job carousel_idea as EN snippet hint only when generic? User asked deterministic Russian — keep Russian carousel.
    # Optionally append job carousel as metadata line in markdown only.

    return CatstylePostPackage(
        date=date,
        aspect_summary=aspect_summary,
        editorial_profile=editorial_profile,
        world_template=wt,
        scene_template=st,
        render_style_profile=rsp,
        shot_mode=shot_mode,
        style_reference_image_path=style_ref,
        image_jobs_summary=image_jobs_summary,
        generated_image_paths=gen_paths,
        recommended_primary_image=primary,
        hook=hook,
        caption=caption,
        carousel_slide_text=carousel,
        compensation=compensation,
        checklist=checklist,
        source_manifest_path=str(mp),
    )


def render_catstyle_post_package_markdown(pkg: CatstylePostPackage) -> str:
    """Human-readable Markdown summary."""
    lines = [
        f"# Catstyle post package — {pkg.date}",
        "",
        f"- **Manifest:** `{pkg.source_manifest_path}`",
        f"- **Editorial profile:** {pkg.editorial_profile}",
        f"- **Aspect summary:** {pkg.aspect_summary or '_(none)_'}",
        f"- **World template:** {pkg.world_template or '_(none)_'}",
        f"- **Scene template:** {pkg.scene_template or '_(none)_'}",
        f"- **Render style profile:** {pkg.render_style_profile or '_(none)_'}",
        f"- **Shot mode:** {pkg.shot_mode or '_(none)_'}",
        f"- **Style reference image:** {pkg.style_reference_image_path or '_(none)_'}",
        f"- **Recommended primary image:** {pkg.recommended_primary_image or '_(not found on disk)_'}",
        "",
        "## Generated image paths",
    ]
    if pkg.generated_image_paths:
        for p in pkg.generated_image_paths:
            lines.append(f"- `{p}`")
    else:
        lines.append("- _(none — pass `--generated-images-dir` after execution)_")
    lines.extend(
        [
            "",
            "## Image jobs",
            "",
            "```json",
            json.dumps(pkg.image_jobs_summary, indent=2, ensure_ascii=False),
            "```",
            "",
            "## Hook",
            "",
            pkg.hook,
            "",
            "## Caption",
            "",
            pkg.caption,
            "",
            "## Carousel (text)",
            "",
            pkg.carousel_slide_text,
            "",
            "## Compensation",
            "",
            pkg.compensation,
            "",
            "## Checklist",
            "",
            pkg.checklist,
            "",
        ]
    )
    return "\n".join(lines)


def write_catstyle_post_package(
    pkg: CatstylePostPackage,
    output_dir: Path | str,
    *,
    overwrite: bool = False,
) -> list[str]:
    """Write ``post_package.json``, Markdown, and split text fields. Returns basenames written."""
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    targets = {
        "post_package.json": json.dumps(pkg.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        "post_package.md": render_catstyle_post_package_markdown(pkg).rstrip("\n") + "\n",
        "caption.txt": pkg.caption + "\n",
        "hook.txt": pkg.hook + "\n",
        "compensation.txt": pkg.compensation + "\n",
        "checklist.txt": pkg.checklist + "\n",
    }

    written: list[str] = []
    for name, body in targets.items():
        dest = out / name
        if dest.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file (use --overwrite): {dest}")
        dest.write_text(body, encoding="utf-8")
        written.append(name)
    return written


__all__ = [
    "POST_PACKAGE_VERSION",
    "CatstylePostPackage",
    "build_catstyle_post_package",
    "load_catstyle_image_generation_manifest",
    "render_catstyle_post_package_markdown",
    "write_catstyle_post_package",
]
