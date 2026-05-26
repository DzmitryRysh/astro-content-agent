"""Resolve Catstyle approved arena/environment reference (aspect-agnostic)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from astro_content_agent.content.catstyle.approved_arena_reference_registry import (
    resolve_approved_arena_reference,
)


def resolve_arena_reference(
    *,
    explicit_path: str | None,
    disable_arena_reference_auto: bool = False,
    use_arena_reference_auto: bool = True,
) -> tuple[str | None, dict[str, Any]]:
    """
    Return ``(arena_reference_image_path, meta)`` for manifests and image jobs.

    Resolution: explicit CLI path → default registry entry → none.
    """
    base_none: dict[str, Any] = {
        "arena_reference_used": False,
        "arena_reference_registry_key": None,
        "arena_reference_image_path": None,
        "source": "none",
    }

    if explicit_path:
        resolved = str(Path(explicit_path).expanduser().resolve())
        if not Path(resolved).is_file():
            return None, {**base_none, "source": "explicit_missing", "path": resolved}
        return resolved, {
            **base_none,
            "source": "explicit",
            "arena_reference_used": True,
            "arena_reference_image_path": resolved,
            "path": resolved,
            "log_lines": [f"Using explicit Catstyle arena reference image: {resolved}"],
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
        "source": "arena_registry",
        "arena_reference_used": True,
        "arena_reference_registry_key": hit.registry_key,
        "arena_reference_image_path": ref_path,
        "path": ref_path,
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
