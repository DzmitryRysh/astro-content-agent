"""Two-tier Catstyle style reference resolution: exact approved → archetype → none."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from astro_content_agent.content.catstyle.approved_reference_registry import resolve_approved_reference
from astro_content_agent.content.catstyle.visual_archetype_registry_v1 import resolve_archetype_reference

ReferenceTier = Literal["exact", "archetype", "none"]


def _archetype_log_lines(meta: dict[str, Any]) -> list[str]:
    key = meta.get("archetype_key") or ""
    path = meta.get("style_reference_image_path") or meta.get("path") or ""
    return [
        f"Using Catstyle archetype reference ({key}): {path}",
        "Reference source: archetype_registry",
    ]


def _exact_log_lines(meta: dict[str, Any]) -> list[str]:
    path = meta.get("approved_reference_image_path") or meta.get("path") or ""
    return [
        f"Using approved Catstyle reference image: {path}",
        "Reference source: approved_reference_registry",
    ]


def resolve_style_reference(
    *,
    explicit_path: str | None,
    disable_approved_reference_auto: bool,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> tuple[str | None, dict[str, Any]]:
    """
    Return ``(style_reference_image_path, meta)`` for manifests and image jobs.

    Resolution order: explicit CLI → exact approved pair → archetype fallback → none.
    """
    base_none: dict[str, Any] = {
        "reference_tier": "none",
        "exact_reference_used": False,
        "archetype_reference_used": False,
        "archetype_key": None,
        "approved_reference_used": False,
        "approved_reference_registry_key": None,
        "approved_reference_image_path": None,
        "style_reference_image_path": None,
    }

    if explicit_path:
        resolved = str(Path(explicit_path).expanduser().resolve())
        return resolved, {
            **base_none,
            "source": "explicit",
            "path": resolved,
            "style_reference_image_path": resolved,
        }

    if disable_approved_reference_auto:
        return None, {
            **base_none,
            "source": "none",
            "auto_resolve_disabled": True,
        }

    exact = resolve_approved_reference(planet_a, planet_b, aspect_type, mode)
    if exact is not None:
        ref_path = str(Path(exact.image_path).expanduser().resolve())
        meta = {
            "source": "approved_registry",
            "reference_tier": "exact",
            "exact_reference_used": True,
            "archetype_reference_used": False,
            "archetype_key": None,
            "path": ref_path,
            "style_reference_image_path": ref_path,
            "registry_key": exact.registry_key,
            "label": exact.label,
            "priority": exact.priority,
            "approved_reference_used": True,
            "approved_reference_registry_key": exact.registry_key,
            "approved_reference_image_path": ref_path,
            "archetype_prompt_guidance": None,
        }
        meta["log_lines"] = _exact_log_lines(meta)
        return ref_path, meta

    arch = resolve_archetype_reference(planet_a, planet_b, aspect_type, mode)
    if arch is not None:
        ref_path = str(Path(arch.image_path).expanduser().resolve())
        meta = {
            "source": "archetype_registry",
            "reference_tier": "archetype",
            "exact_reference_used": False,
            "archetype_reference_used": True,
            "archetype_key": arch.archetype_key,
            "path": ref_path,
            "style_reference_image_path": ref_path,
            "registry_key": arch.archetype_key,
            "label": arch.archetype_key,
            "priority": arch.priority,
            "approved_reference_used": False,
            "approved_reference_registry_key": None,
            "approved_reference_image_path": None,
            "archetype_prompt_guidance": arch.prompt_guidance,
            "archetype_description": arch.description,
        }
        meta["log_lines"] = _archetype_log_lines(meta)
        return ref_path, meta

    return None, {**base_none, "source": "none"}


__all__ = [
    "ReferenceTier",
    "resolve_style_reference",
]
