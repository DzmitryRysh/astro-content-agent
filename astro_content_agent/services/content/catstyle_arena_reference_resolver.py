"""Resolve Catstyle approved arena/environment reference (aspect-agnostic)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from astro_content_agent.content.catstyle.approved_arena_reference_registry import (
    resolve_approved_arena_reference,
)
from astro_content_agent.content.catstyle.arena_pool_selector_v1 import (
    DEFAULT_ARENA_POOL_SELECTION,
    select_arena_pool_candidate,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name


def _base_arena_meta_none() -> dict[str, Any]:
    return {
        "arena_reference_used": False,
        "arena_reference_registry_key": None,
        "arena_reference_image_path": None,
        "selected_arena_reference_path": None,
        "source": "none",
        "arena_pool_key": None,
        "selected_arena_pool_candidate_key": None,
        "arena_selection_mode": None,
    }


def resolve_arena_reference(
    *,
    explicit_path: str | None,
    arena_pool_key: str | None = None,
    arena_pool_selection: str = DEFAULT_ARENA_POOL_SELECTION,
    planet_a: str | None = None,
    planet_b: str | None = None,
    aspect_type: str | None = None,
    mode: str | None = None,
    disable_arena_reference_auto: bool = False,
    use_arena_reference_auto: bool = True,
) -> tuple[str | None, dict[str, Any]]:
    """
    Return ``(arena_reference_image_path, meta)`` for manifests and image jobs.

    Resolution priority:
    1. explicit CLI path
    2. arena pool key (deterministic stable_by_pair selection)
    3. default approved arena registry entry
    4. none
    """
    base_none = _base_arena_meta_none()

    if explicit_path:
        resolved = str(Path(explicit_path).expanduser().resolve())
        if not Path(resolved).is_file():
            return None, {**base_none, "source": "explicit_missing", "path": resolved}
        return resolved, {
            **base_none,
            "source": "explicit",
            "arena_reference_used": True,
            "arena_reference_image_path": resolved,
            "selected_arena_reference_path": resolved,
            "path": resolved,
            "arena_selection_mode": "explicit",
            "log_lines": [f"Using explicit Catstyle arena reference image: {resolved}"],
        }

    pool_key = (arena_pool_key or "").strip()
    if pool_key:
        if not planet_a or not planet_b or not aspect_type or not mode:
            raise ValueError(
                "arena_pool_key requires planet_a, planet_b, aspect_type, and mode for selection"
            )
        selection = (arena_pool_selection or DEFAULT_ARENA_POOL_SELECTION).strip()
        hit = select_arena_pool_candidate(
            pool_key,
            normalize_planet_name(planet_a),
            normalize_planet_name(planet_b),
            aspect_type,
            mode,
            selection_mode=selection,  # type: ignore[arg-type]
        )
        ref_path = str(hit.image_path)
        if not hit.image_path.is_file():
            return None, {
                **base_none,
                "source": "arena_pool_missing_file",
                "arena_pool_key": pool_key,
                "selected_arena_pool_candidate_key": hit.candidate_key,
                "arena_selection_mode": selection,
                "registry_image_path": ref_path,
            }
        return ref_path, {
            **base_none,
            "source": "arena_pool",
            "arena_reference_used": True,
            "arena_reference_image_path": ref_path,
            "selected_arena_reference_path": ref_path,
            "path": ref_path,
            "arena_pool_key": pool_key,
            "selected_arena_pool_candidate_key": hit.candidate_key,
            "arena_selection_mode": selection,
            "label": hit.label,
            "notes": hit.notes,
            "log_lines": [
                f"Using Catstyle arena pool ({pool_key}) candidate {hit.candidate_key}: {ref_path}",
                f"Arena selection mode: {selection}",
            ],
        }

    if disable_arena_reference_auto or not use_arena_reference_auto:
        return None, {**base_none, "auto_resolve_disabled": True}

    hit = resolve_approved_arena_reference()
    if hit is None:
        return None, base_none

    ref_path = str(hit.image_path)
    if not hit.image_path.is_file():
        return None, {
            **base_none,
            "source": "registry_missing_file",
            "arena_reference_registry_key": hit.registry_key,
            "registry_image_path": ref_path,
        }

    meta = {
        **base_none,
        "source": "arena_registry",
        "arena_reference_used": True,
        "arena_reference_registry_key": hit.registry_key,
        "arena_reference_image_path": ref_path,
        "selected_arena_reference_path": ref_path,
        "path": ref_path,
        "arena_selection_mode": "arena_registry_default",
        "label": hit.label,
        "priority": hit.priority,
        "notes": hit.notes,
        "log_lines": [
            f"Using approved Catstyle arena reference ({hit.registry_key}): {ref_path}",
            "Reference source: approved_arena_reference_registry",
        ],
    }
    return ref_path, meta


__all__ = ["resolve_arena_reference"]
