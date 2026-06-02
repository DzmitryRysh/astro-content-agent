"""Catstyle approved per-planet character reference registry and prompt helpers (v1)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.catstyle_aspect_staging_locks_v1 import (
    REFERENCE_ROLE_DECLARATION_MARKER,
    build_reference_role_declaration_block,
)
from astro_content_agent.content.catstyle.catstyle_planet_reference_identity_lock_v1 import (
    PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER,
    build_planet_reference_identity_hardlock_layer,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.content.catstyle.models import CatstylePromptPack


APPROVED_PLANET_REFERENCE_LOCK_MARKER: str = "[CATSTYLE PLANET REFERENCE OVERRIDE v2]"

APPROVED_PLANET_REFERENCE_LOCK_BODY: str = (
    "Approved per-planet image references are the primary visual source of truth for character appearance. "
    "For registered planets, attached planet references override old text canon. "
    "Preserve referenced face style, body proportions, silhouette, planetary body material, palette, aura, "
    "costume logic, and main accessories. "
    "Old planet canon is symbolic only and must not force old costumes, old props, old face types, "
    "old body proportions, old color palettes, old cute/noir/fighter archetypes, or old pair-scene clichés. "
    "Aspect choreography may change pose/action, but must not replace referenced character identity. "
    "Render living planet-cat bodies first; costume/props second."
)

_SYMBOLIC_CANON_STUB = (
    "[SYMBOLIC CANON ONLY — secondary to approved planet reference]: "
    "Use attached reference for visual identity; text canon is symbolic/semantic guidance only."
)

_OLD_VISUAL_CANON_PHRASES: tuple[str, ...] = (
    "Stoic pinstripe round cat",
    "Plush rose-cheek round cat",
    "rose stem + short pearls",
    "rose stem, one short pearl strand",
    "wide-brim hat, blank wristwatch, ruler, skeleton key",
    "wide-brim hat and ring-hoop belt",
    "pinstripe suit silhouette with wide-brim hat",
)

_OLD_CHOREO_VISUAL_MARKERS: tuple[str, ...] = (
    "moon may hold, brace, swing, or strike with pillow energy",
    "saturn may use chain/control as saturnian restraint",
)

_OLD_PAIR_STORY_MARKERS: tuple[str, ...] = (
    "business meeting",
    "deadline-heavy business",
    "pleasure under audit",
    "design studio collaboration",
    "design studio teamwork",
    "architecture models",
    "architecture sketch",
    "fashion sketches",
    "fashion collab",
    "jewelry or watch layout",
    "watch layout",
    "moodboard",
    "blank contract",
    "fabric bolt",
    "mannequin",
    "clipboard tallies",
    "pleasure units",
    "real-estate tabletop",
    "co-sketch a watch face",
    "joint jewelry layout",
)

PLANET_REF_IDENTITY_PRESERVE: str = (
    "preserve approved planet reference identity; symbolic canon remains secondary"
)

_CANON_PRESERVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"preserve\s+\[CANON v1 base\]\s*\+\s*\[IDENTITY MARKERS v1\]",
            re.IGNORECASE,
        ),
        PLANET_REF_IDENTITY_PRESERVE,
    ),
    (
        re.compile(
            r"preserve the full \[CANON v1 base\].*?\[IDENTITY MARKERS v1\]",
            re.IGNORECASE | re.DOTALL,
        ),
        PLANET_REF_IDENTITY_PRESERVE,
    ),
    (
        re.compile(
            r"preserve this entire marker block alongside \[CANON v1 base\]",
            re.IGNORECASE,
        ),
        PLANET_REF_IDENTITY_PRESERVE,
    ),
)

_OLD_PAIR_SCENE_VISUAL_MARKERS: tuple[str, ...] = (
    "pinstripe and hat slides a blank contract",
    "saturn cat in pinstripe and hat",
    "venus cat with single rose and moodboard",
    "single rose and moodboard",
    "slides a blank contract across",
    "clipboard tallies 'pleasure units'",
)

_CANON_V1_BLOCK_RE = re.compile(
    r"(\w+) planet-cat \[CANON v1 base\]:.*?"
    r"(?=\s+\w+ planet-cat \[CANON v1 base\]:|\s+\[PLANET CANON v1|\s+Aspect type:|\s+\[CATSTYLE|\s+\[WORLD|\s+\[SCENE|\s+\[RENDER|\s+\[SHOT|\s+Scene beat:|\Z)",
    re.IGNORECASE | re.DOTALL,
)

_PLANET_CANON_V1_BLOCK_RE = re.compile(
    r"\[PLANET CANON v1 - [^\]]+\]:.*?(?=\s+\[PLANET CANON v1|\s+Aspect type:|\s+\[CATSTYLE|\s+Scene beat:|\Z)",
    re.IGNORECASE | re.DOTALL,
)

CG_MATERIAL_FINISH_HARDLOCK_BLOCK: str = (
    "[CG MATERIAL FINISH HARDLOCK v2] "
    "Final image must read as polished premium CG key art / 2.5D-3D hybrid game splash art. "
    "Use crisp surface modeling, clean specular highlights, glossy/translucent material separation, "
    "volumetric rim light, cinematic depth, sharp silhouette edges, high-resolution 3D-render-like polish. "
    "Reject dry painted fantasy illustration, matte brush strokes, watercolor, gouache, storybook softness, "
    "painterly canvas texture, hand-painted poster dryness, muddy airbrush, sketch texture. "
    "Planet-cat bodies must have luminous material surfaces, not ordinary fur painted with brush texture."
)


def build_approved_planet_reference_lock_block(
    planet_a: str,
    planet_b: str,
    planet_references_meta: dict[str, Any],
) -> str:
    """Build planet reference lock block with planet-specific guardrails."""
    pa_norm = normalize_planet_name(planet_a)
    pb_norm = normalize_planet_name(planet_b)
    pa_row = planet_references_meta.get("planet_a") if isinstance(planet_references_meta.get("planet_a"), dict) else {}
    pb_row = planet_references_meta.get("planet_b") if isinstance(planet_references_meta.get("planet_b"), dict) else {}
    extras: list[str] = []
    if pa_row.get("used") and pa_norm.lower() == "venus":
        extras.append(
            "Venus must not revert to generic cute rose cat if a Venus planet reference is attached."
        )
    if pb_row.get("used") and pb_norm.lower() == "venus":
        extras.append(
            "Venus must not revert to generic cute rose cat if a Venus planet reference is attached."
        )
    if pa_row.get("used") and pa_norm.lower() == "saturn":
        extras.append(
            "Saturn must not soften into generic dark boss cat if a Saturn planet reference is attached."
        )
    if pb_row.get("used") and pb_norm.lower() == "saturn":
        extras.append(
            "Saturn must not soften into generic dark boss cat if a Saturn planet reference is attached."
        )
    body = APPROVED_PLANET_REFERENCE_LOCK_BODY
    if extras:
        body = f"{body} {' '.join(dict.fromkeys(extras))}"
    return f"{APPROVED_PLANET_REFERENCE_LOCK_MARKER} {body}"


def _planet_ref_used(meta: dict[str, Any], slot: str) -> bool:
    row = meta.get(slot) if isinstance(meta.get(slot), dict) else {}
    return bool(row.get("used") and row.get("image_path"))


def sanitize_scene_beat_for_planet_refs(scene: str, *, refs_active: bool) -> str:
    """Replace hardcoded visual pair-scene clichés when planet refs are authoritative."""
    if not refs_active:
        return scene
    low = str(scene or "").lower()
    if any(marker in low for marker in _OLD_PAIR_SCENE_VISUAL_MARKERS):
        return (
            "Aspect choreography: symbolic tension and negotiation — preserve approved planet-reference "
            "identity for both characters; staging may change pose/action but not costumes, props, or "
            "face/body from image refs."
        )
    return scene


def _story_line_is_leaky(text: str) -> bool:
    low = str(text or "").lower()
    return any(m in low for m in _OLD_PAIR_STORY_MARKERS)


def neutral_aspect_choreography_for_pair(
    planet_a: str,
    planet_b: str,
    aspect_type: str | None = None,
) -> tuple[str, str] | None:
    """Neutral story fields for pairs whose legacy text canon leaks visual clichés."""
    pa = normalize_planet_name(planet_a).lower()
    pb = normalize_planet_name(planet_b).lower()
    if {pa, pb} != {"saturn", "venus"}:
        return None
    core = (
        "Beauty, value, pleasure, attraction, and desire meet time, boundary, gravity, pressure, and consequence. "
        "Show visual tension through spatial pressure, gravity fields, chain/boundary motifs, and Venusian "
        "glow/value-field resisting compression."
    )
    constructive = (
        "Aspect choreography may reshape pose and staging, but must preserve approved planet-reference identity. "
        "Do not force old costumes, props, business-meeting jokes, contract scenes, or fashion-studio staging."
    )
    return core, constructive


def sanitize_core_tension_and_constructive_for_planet_refs(
    core_tension: str,
    constructive_channel: str,
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str | None = None,
    refs_active: bool,
) -> tuple[str, str]:
    """Rewrite leaky pair story lines when approved planet references are authoritative."""
    if not refs_active:
        return core_tension, constructive_channel
    leaky = _story_line_is_leaky(core_tension) or _story_line_is_leaky(constructive_channel)
    if not leaky:
        return core_tension, constructive_channel
    neutral = neutral_aspect_choreography_for_pair(planet_a, planet_b, aspect_type)
    if neutral:
        return neutral
    generic_core = (
        "Symbolic aspect tension — preserve approved planet-reference identity; "
        "express pressure and negotiation without legacy prop-specific staging."
    )
    generic_cons = (
        "Neutral aspect choreography only — no forced costumes, props, business-meeting jokes, "
        "contract scenes, or fashion-studio staging."
    )
    return generic_core, generic_cons


def sanitize_visual_metaphor_for_planet_refs(
    visual_metaphor: str,
    *,
    planet_a: str,
    planet_b: str,
    refs_active: bool,
) -> str:
    if not refs_active or not _story_line_is_leaky(visual_metaphor):
        return visual_metaphor
    neutral = neutral_aspect_choreography_for_pair(planet_a, planet_b)
    if neutral:
        return neutral[0]
    return (
        "Symbolic spatial tension between the two planet-cats — preserve approved references; "
        "no legacy prop staging."
    )


def _replace_canon_preserve_phrases(out: str) -> str:
    for pattern, replacement in _CANON_PRESERVE_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


def _rewrite_prompt_story_sections(
    out: str,
    *,
    planet_a: str,
    planet_b: str,
    aspect_type: str | None = None,
) -> str:
    if not _story_line_is_leaky(out):
        return out
    neutral = neutral_aspect_choreography_for_pair(planet_a, planet_b, aspect_type)
    if neutral:
        core, cons = neutral
    else:
        core = (
            "Symbolic aspect tension — preserve approved planet-reference identity; "
            "express pressure and negotiation without legacy prop-specific staging."
        )
        cons = (
            "Neutral aspect choreography only — no forced costumes, props, business-meeting jokes, "
            "contract scenes, or fashion-studio staging."
        )
    out = re.sub(
        r"Story tension \(cartoon metaphor\):\s*.*?(?=\s+Constructive undertone available:)",
        f"Story tension (cartoon metaphor): {core} ",
        out,
        flags=re.IGNORECASE | re.DOTALL,
    )
    out = re.sub(
        r"Constructive undertone available:\s*.*?(?=\s+Visual metaphor:|\s+\[CATSTYLE|\s+\[PREMIUM|\Z)",
        f"Constructive undertone available: {cons} ",
        out,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return out


def sanitize_prompt_for_planet_reference_override(
    prompt: str,
    *,
    planet_a: str | None = None,
    planet_b: str | None = None,
    aspect_type: str | None = None,
) -> str:
    """Demote old text canon and strip hardcoded visual clichés when planet refs are active."""
    out = str(prompt or "")

    def _replace_canon_block(match: re.Match[str]) -> str:
        planet = match.group(1)
        return f"{planet} planet-cat {_SYMBOLIC_CANON_STUB}"

    out = _CANON_V1_BLOCK_RE.sub(_replace_canon_block, out)
    out = _PLANET_CANON_V1_BLOCK_RE.sub("", out)

    low = out.lower()
    for phrase in _OLD_VISUAL_CANON_PHRASES:
        idx = low.find(phrase.lower())
        while idx >= 0:
            out = out[:idx] + out[idx + len(phrase) :]
            low = out.lower()
            idx = low.find(phrase.lower())

    for phrase in _OLD_CHOREO_VISUAL_MARKERS:
        idx = low.find(phrase.lower())
        while idx >= 0:
            out = out[:idx] + out[idx + len(phrase) :]
            low = out.lower()
            idx = low.find(phrase.lower())

    scene_match = re.search(r"Scene beat:\s*[^.]+\.", out, flags=re.IGNORECASE)
    if scene_match:
        scene_text = scene_match.group(0)
        if any(m in scene_text.lower() for m in _OLD_PAIR_SCENE_VISUAL_MARKERS):
            replacement = (
                "Scene beat: Aspect choreography — symbolic tension only; follow approved planet references "
                "for character appearance."
            )
            out = out[: scene_match.start()] + replacement + out[scene_match.end() :]

    out = _replace_canon_preserve_phrases(out)
    if planet_a and planet_b:
        out = _rewrite_prompt_story_sections(
            out, planet_a=planet_a, planet_b=planet_b, aspect_type=aspect_type
        )

    low = out.lower()
    for phrase in _OLD_PAIR_STORY_MARKERS:
        idx = low.find(phrase.lower())
        while idx >= 0:
            out = out[:idx] + out[idx + len(phrase) :]
            low = out.lower()
            idx = low.find(phrase.lower())

    return " ".join(out.split())


def append_planet_reference_override_at_end(
    prompt: str,
    lock_block: str,
    *,
    render_style_key: str | None = None,
) -> str:
    """Append override + optional CG hardlock near the end of the prompt."""
    out = str(prompt or "").rstrip()
    if APPROVED_PLANET_REFERENCE_LOCK_MARKER not in out:
        out = f"{out} {lock_block.strip()}"
    if render_style_key == "premium_cg_keyart_v1" and "[CG MATERIAL FINISH HARDLOCK v2]" not in out:
        out = f"{out} {CG_MATERIAL_FINISH_HARDLOCK_BLOCK}"
    return out.strip()


def _ensure_planet_ref_support_blocks(
    prompt: str,
    ref_decl: str,
    *,
    planet_a: str,
    planet_b: str,
    planet_references_meta: dict[str, Any],
) -> str:
    """Ensure identity hardlock, reference-role, and body-material blocks exist before override append."""
    out = str(prompt or "")
    identity = build_planet_reference_identity_hardlock_layer(
        planet_a, planet_b, planet_references_meta
    )
    if identity and PLANET_REFERENCE_IDENTITY_HARDLOCK_MARKER not in out:
        out = f"{out} {identity}".strip()
    if ref_decl and REFERENCE_ROLE_DECLARATION_MARKER not in out:
        out = f"{out} {ref_decl}".strip()
    return out


def inject_approved_planet_reference_lock_block(
    prompt: str,
    block: str,
    *,
    render_style_key: str | None = None,
    planet_a: str | None = None,
    planet_b: str | None = None,
    aspect_type: str | None = None,
) -> str:
    """Sanitize and append planet override blocks near prompt end."""
    sanitized = sanitize_prompt_for_planet_reference_override(
        prompt,
        planet_a=planet_a,
        planet_b=planet_b,
        aspect_type=aspect_type,
    )
    return append_planet_reference_override_at_end(
        sanitized, block, render_style_key=render_style_key
    )


def apply_approved_planet_reference_lock_to_prompt_pack(
    pack: CatstylePromptPack,
    planet_a: str,
    planet_b: str,
    planet_references_meta: dict[str, Any],
    *,
    render_style_key: str | None = None,
    aspect_type: str | None = None,
) -> CatstylePromptPack:
    """Sanitize prompts and inject planet reference override blocks."""
    if not planet_references_active_for_job(planet_references_meta):
        return pack
    block = build_approved_planet_reference_lock_block(planet_a, planet_b, planet_references_meta)
    ref_decl = build_reference_role_declaration_block(
        planet_a, planet_b, planet_refs_active=True
    )
    data = pack.model_dump(mode="json")
    prompts = [str(p) for p in (data.get("image_prompts") or [])]
    if prompts:
        data["image_prompts"] = [
            inject_approved_planet_reference_lock_block(
                _ensure_planet_ref_support_blocks(
                    p,
                    ref_decl,
                    planet_a=planet_a,
                    planet_b=planet_b,
                    planet_references_meta=planet_references_meta,
                ),
                block,
                render_style_key=render_style_key,
                planet_a=planet_a,
                planet_b=planet_b,
                aspect_type=aspect_type,
            )
            for p in prompts
        ]
    full_block = block
    if render_style_key == "premium_cg_keyart_v1":
        full_block = f"{block} {CG_MATERIAL_FINISH_HARDLOCK_BLOCK}"
    data["planet_reference_assist"] = {
        "planet_a": planet_references_meta.get("planet_a"),
        "planet_b": planet_references_meta.get("planet_b"),
        "any_used": planet_references_meta.get("any_used"),
        "prompt_block": full_block,
    }
    return CatstylePromptPack.model_validate(data)


def build_job_reference_images(
    *,
    arena_reference_image_path: str | None = None,
    planet_a_reference_image_path: str | None = None,
    planet_b_reference_image_path: str | None = None,
    style_reference_image_path: str | None = None,
    include_pair_style: bool = True,
) -> list[dict[str, str]]:
    """
    Ordered deduped reference list for job manifests and providers.

    Order: planet_a → planet_b → arena → optional pair_style.
    """
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    roles: tuple[tuple[str, str | None], ...] = (
        ("planet_a", planet_a_reference_image_path),
        ("planet_b", planet_b_reference_image_path),
        ("arena", arena_reference_image_path),
    )
    if include_pair_style:
        roles = roles + (("pair_style", style_reference_image_path),)
    for role, raw in roles:
        path_str = str(raw or "").strip()
        if not path_str:
            continue
        resolved = _absolute_image_path(path_str)
        if not resolved.is_file():
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        out.append({"role": role, "path": key})
    return out


def approved_planet_references_json_path() -> Path:
    return catstyle_repo_root() / "astro_content_agent" / "content" / "catstyle" / "approved_planet_references.json"


def planet_reference_target_relpath(planet: str, registry_key: str) -> str:
    """Deterministic repo-relative path under ``references/``."""
    planet_slug = normalize_planet_name(planet).lower()
    key_slug = (registry_key or "default").strip().replace("-", "_").lower()
    return f"references/catstyle_planet_{planet_slug}_{key_slug}_approved.png"


class ApprovedPlanetReferenceEntry(BaseModel):
    registry_key: str
    planet: str
    image_path: str
    label: str = ""
    notes: str = ""
    priority: int = 0
    active: bool = True


class ResolvedPlanetReference(BaseModel):
    registry_key: str
    planet: str
    image_path: Path
    label: str
    notes: str
    priority: int


class PlanetReferenceResolveResult(BaseModel):
    """Graceful resolve outcome for one planet (may be missing)."""

    planet: str
    used: bool
    registry_key: str | None = None
    image_path: str | None = None
    label: str | None = None
    notes: str | None = None
    priority: int | None = None
    source: str = "none"
    missing_reason: str | None = None

    def to_manifest_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _absolute_image_path(rel_or_abs: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p.resolve()
    return (catstyle_repo_root() / p).resolve()


def read_planet_registry_entries(path: Path | None = None) -> list[ApprovedPlanetReferenceEntry]:
    p = (path or approved_planet_references_json_path()).expanduser().resolve()
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("entries") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return []
    return [ApprovedPlanetReferenceEntry.model_validate(item) for item in raw]


def write_planet_registry_entries(
    path: Path,
    entries: list[ApprovedPlanetReferenceEntry],
    *,
    version: str = "catstyle-approved-planet-reference-v1",
) -> None:
    p = path.expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=lambda e: (-e.priority, e.registry_key))
    payload: dict[str, Any] = {
        "version": version,
        "entries": [e.model_dump(mode="json") for e in ordered],
    }
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_approved_planet_reference_registry() -> list[ApprovedPlanetReferenceEntry]:
    return read_planet_registry_entries()


def resolve_approved_planet_reference(
    planet: str,
    *,
    registry: list[ApprovedPlanetReferenceEntry] | None = None,
) -> ResolvedPlanetReference | None:
    """Return highest-priority active reference for ``planet``, or ``None``."""
    planet_norm = normalize_planet_name(planet)
    rows = registry if registry is not None else load_approved_planet_reference_registry()
    matches = [
        e for e in rows if e.active and normalize_planet_name(e.planet) == planet_norm
    ]
    if not matches:
        return None
    matches.sort(key=lambda e: (-e.priority, e.registry_key))
    winner = matches[0]
    return ResolvedPlanetReference(
        registry_key=winner.registry_key,
        planet=planet_norm,
        image_path=_absolute_image_path(winner.image_path),
        label=winner.label,
        notes=winner.notes,
        priority=winner.priority,
    )


def resolve_planet_reference(planet: str) -> PlanetReferenceResolveResult:
    """Resolve one planet reference; never raises when missing."""
    planet_norm = normalize_planet_name(planet)
    hit = resolve_approved_planet_reference(planet_norm)
    if hit is None:
        return PlanetReferenceResolveResult(
            planet=planet_norm,
            used=False,
            source="none",
            missing_reason="no_active_registry_entry",
        )
    if not hit.image_path.is_file():
        return PlanetReferenceResolveResult(
            planet=planet_norm,
            used=False,
            registry_key=hit.registry_key,
            image_path=str(hit.image_path),
            label=hit.label,
            notes=hit.notes,
            priority=hit.priority,
            source="registry_missing_file",
            missing_reason="registry_file_not_found",
        )
    return PlanetReferenceResolveResult(
        planet=planet_norm,
        used=True,
        registry_key=hit.registry_key,
        image_path=str(hit.image_path),
        label=hit.label,
        notes=hit.notes,
        priority=hit.priority,
        source="planet_registry",
    )


def resolve_planet_references_for_pair(planet_a: str, planet_b: str) -> dict[str, Any]:
    """Resolve both planets for manifests and image jobs."""
    pa = resolve_planet_reference(planet_a)
    pb = resolve_planet_reference(planet_b)
    return {
        "planet_a": pa.to_manifest_dict(),
        "planet_b": pb.to_manifest_dict(),
        "any_used": pa.used or pb.used,
    }


def active_planet_reference_paths_from_meta(
    planet_references_meta: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Return attached planet A/B paths only when resolve metadata reports used=True with image_path."""
    pa_row = planet_references_meta.get("planet_a") if isinstance(planet_references_meta.get("planet_a"), dict) else {}
    pb_row = planet_references_meta.get("planet_b") if isinstance(planet_references_meta.get("planet_b"), dict) else {}
    pa_path: str | None = None
    pb_path: str | None = None
    if pa_row.get("used") and pa_row.get("image_path"):
        pa_path = str(pa_row["image_path"])
    if pb_row.get("used") and pb_row.get("image_path"):
        pb_path = str(pb_row["image_path"])
    return pa_path, pb_path


def planet_references_active_for_job(planet_references_meta: dict[str, Any]) -> bool:
    """True when at least one resolved planet reference is used with a valid image_path."""
    pa_path, pb_path = active_planet_reference_paths_from_meta(planet_references_meta)
    return bool(pa_path or pb_path)


def list_active_planet_references_grouped() -> dict[str, list[ApprovedPlanetReferenceEntry]]:
    grouped: dict[str, list[ApprovedPlanetReferenceEntry]] = {}
    for e in load_approved_planet_reference_registry():
        if not e.active:
            continue
        key = normalize_planet_name(e.planet)
        grouped.setdefault(key, []).append(e)
    for planet in grouped:
        grouped[planet].sort(key=lambda x: (-x.priority, x.registry_key))
    return grouped


def list_resolved_winners_by_planet() -> dict[str, ResolvedPlanetReference | None]:
    grouped = list_active_planet_references_grouped()
    return {
        planet: resolve_approved_planet_reference(planet, registry=entries)
        for planet, entries in grouped.items()
    }


def format_catstyle_modular_reference_roles_prefix(
    *,
    arena_reference_present: bool,
    planet_a_reference_present: bool,
    planet_b_reference_present: bool,
    pair_style_reference_present: bool,
    planet_a_name: str = "planet A",
    planet_b_name: str = "planet B",
    banner_glyph_a: bool = False,
    banner_glyph_b: bool = False,
) -> str:
    """
    Modular reference roles: A=arena, B=planet_a, C=planet_b, D=optional pair, then banner glyphs.
    """
    if not any(
        (
            arena_reference_present,
            planet_a_reference_present,
            planet_b_reference_present,
            pair_style_reference_present,
            banner_glyph_a,
            banner_glyph_b,
        )
    ):
        return ""
    lines = [
        "[CATSTYLE REFERENCE IMAGE ROLES v3] When the image API accepts multiple reference images:",
    ]
    letter = ord("A")
    if arena_reference_present:
        lines.append(
            "**Image A** = **approved arena/environment reference ONLY**—controls **coliseum brightness**, "
            "**illuminated arches**, **tier depth**, **rich Milky Way sky**, **Earth disk**, **zodiac floor**—"
            "**do NOT** copy characters, poses, planet colors, or glyphs from Image A."
        )
        letter += 1
    if planet_a_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **approved {planet_a_name} character reference ONLY**—controls **{planet_a_name}** "
            "cat-planet body material, silhouette, palette, costume, and identity—**not** environment, "
            "**not** the other planet, **not** aspect pair mood override."
        )
        letter += 1
    if planet_b_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **approved {planet_b_name} character reference ONLY**—controls **{planet_b_name}** "
            "cat-planet body material, silhouette, palette, costume, and identity—**not** environment, "
            "**not** the other planet, **not** aspect pair mood override."
        )
        letter += 1
    if pair_style_reference_present:
        ch = chr(letter)
        lines.append(
            f"**Image {ch}** = **optional pair/aspect approved reference**—**lower priority**; may inform "
            "**pair mood**, **choreography energy**, and campaign finish only—**must NOT** override Image A "
            "environment, **must NOT** override per-planet character identity on Images B/C, **must NOT** "
            "pull watercolor/cute ordinary cats or weak planet-cat identity over modular planet plates. "
            "**Aspect choreography comes from prompt text**, not from overriding planet identity."
        )
        letter += 1
    if banner_glyph_a:
        ch = chr(letter)
        lines.append(f"**Image {ch}** = narrow **left/port banner glyph** crop—heraldic cloth glyph only.")
        letter += 1
    if banner_glyph_b:
        ch = chr(letter)
        lines.append(f"**Image {ch}** = narrow **right/starboard banner glyph** crop—heraldic cloth glyph only.")
    lines.append(
        "**Modular priority lock:** arena (A) wins environment; planet references win their planet identity; "
        "optional pair reference is lowest-priority mood/choreography assist only."
    )
    return " ".join(lines)


def format_modular_reference_provider_priority_preamble(
    *,
    arena_present: bool,
    planet_a_present: bool,
    planet_b_present: bool,
    pair_style_present: bool,
    planet_a_name: str = "planet A",
    planet_b_name: str = "planet B",
) -> str:
    parts: list[str] = []
    if arena_present:
        parts.append(
            "**Image A (arena)** is authoritative for brighter coliseum, rich sky, Earth disk, and zodiac floor—"
            "never inherit a darker arena shell from other references."
        )
    if planet_a_present:
        parts.append(
            f"**Per-planet reference for {planet_a_name}** controls that cat-planet's identity only—"
            "not the arena shell or the other planet's body."
        )
    if planet_b_present:
        parts.append(
            f"**Per-planet reference for {planet_b_name}** controls that cat-planet's identity only—"
            "not the arena shell or the other planet's body."
        )
    if pair_style_present:
        parts.append(
            "**Optional pair/aspect reference** is lowest priority—pair mood/choreography assist only; "
            "do not let it override arena environment or per-planet character identity; "
            "aspect staging follows prompt text."
        )
    return " ".join(parts)


__all__ = [
    "APPROVED_PLANET_REFERENCE_LOCK_MARKER",
    "ApprovedPlanetReferenceEntry",
    "PlanetReferenceResolveResult",
    "ResolvedPlanetReference",
    "active_planet_reference_paths_from_meta",
    "append_planet_reference_override_at_end",
    "apply_approved_planet_reference_lock_to_prompt_pack",
    "approved_planet_references_json_path",
    "build_approved_planet_reference_lock_block",
    "build_job_reference_images",
    "format_catstyle_modular_reference_roles_prefix",
    "format_modular_reference_provider_priority_preamble",
    "list_active_planet_references_grouped",
    "list_resolved_winners_by_planet",
    "load_approved_planet_reference_registry",
    "neutral_aspect_choreography_for_pair",
    "planet_reference_target_relpath",
    "planet_references_active_for_job",
    "read_planet_registry_entries",
    "resolve_approved_planet_reference",
    "resolve_planet_reference",
    "resolve_planet_references_for_pair",
    "sanitize_core_tension_and_constructive_for_planet_refs",
    "sanitize_prompt_for_planet_reference_override",
    "sanitize_scene_beat_for_planet_refs",
    "sanitize_visual_metaphor_for_planet_refs",
    "write_planet_registry_entries",
]
