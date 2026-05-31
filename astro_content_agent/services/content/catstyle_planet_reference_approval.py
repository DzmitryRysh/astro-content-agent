"""Approve a Catstyle per-planet character reference image (local filesystem + JSON registry v1)."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.content.catstyle.catstyle_approved_planet_reference_v1 import (
    ApprovedPlanetReferenceEntry,
    approved_planet_references_json_path,
    planet_reference_target_relpath,
    read_planet_registry_entries,
    write_planet_registry_entries,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.services.content.catstyle_reference_image_validation import (
    CatstyleReferenceImageValidationError,
    reference_image_quality_ok,
    validate_reference_image_source,
)


class CatstylePlanetReferenceApprovalError(ValueError):
    """Invalid input or conflicting registry state."""


class CatstylePlanetReferenceApprovalResult(BaseModel):
    source_image: str
    target_image: str
    target_image_absolute: str
    registry_key: str
    planet: str
    active: bool
    overwrite: bool
    files_written: list[str] = Field(default_factory=list)


def approve_catstyle_planet_reference(
    *,
    source_image: Path | str,
    planet: str,
    registry_key: str,
    label: str = "",
    notes: str = "",
    priority: int = 100,
    active: bool = True,
    overwrite: bool = False,
    repo_root: Path | None = None,
    registry_json_path: Path | None = None,
) -> CatstylePlanetReferenceApprovalResult:
    root = (repo_root or catstyle_repo_root()).expanduser().resolve()
    reg_path = registry_json_path or approved_planet_references_json_path()
    src = Path(source_image).expanduser().resolve()
    try:
        validate_reference_image_source(src)
    except CatstyleReferenceImageValidationError as exc:
        raise CatstylePlanetReferenceApprovalError(str(exc)) from exc

    planet_norm = normalize_planet_name(planet)
    reg_key = (registry_key or "").strip()
    if not reg_key:
        raise CatstylePlanetReferenceApprovalError("registry_key must be non-empty.")

    rel_target = planet_reference_target_relpath(planet_norm, reg_key)
    abs_target = (root / rel_target).resolve()

    entries = read_planet_registry_entries(reg_path)
    idx_existing: int | None = None
    for i, e in enumerate(entries):
        if e.registry_key == reg_key:
            idx_existing = i
            break

    if idx_existing is not None and not overwrite:
        raise CatstylePlanetReferenceApprovalError(
            f"An approved planet reference already exists for registry_key={reg_key!r}. "
            "Pass --overwrite to replace."
        )

    if abs_target.is_file() and reference_image_quality_ok(abs_target) and not overwrite:
        raise CatstylePlanetReferenceApprovalError(
            f"Planet reference image already exists at {rel_target}. Pass --overwrite to replace."
        )

    abs_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, abs_target)

    new_entry = ApprovedPlanetReferenceEntry(
        registry_key=reg_key,
        planet=planet_norm,
        image_path=rel_target.replace("\\", "/"),
        label=(label or "").strip(),
        notes=(notes or "").strip(),
        priority=int(priority),
        active=bool(active),
    )
    if idx_existing is not None:
        entries[idx_existing] = new_entry
    else:
        entries.append(new_entry)

    write_planet_registry_entries(reg_path, entries)

    files_written = [rel_target.replace("\\", "/"), str(reg_path)]
    try:
        files_written[1] = str(reg_path.resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        files_written[1] = str(reg_path.resolve())

    return CatstylePlanetReferenceApprovalResult(
        source_image=str(src),
        target_image=rel_target.replace("\\", "/"),
        target_image_absolute=str(abs_target),
        registry_key=reg_key,
        planet=planet_norm,
        active=bool(active),
        overwrite=bool(overwrite),
        files_written=files_written,
    )


def approval_result_as_jsonable(result: CatstylePlanetReferenceApprovalResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


__all__ = [
    "CatstylePlanetReferenceApprovalError",
    "CatstylePlanetReferenceApprovalResult",
    "approval_result_as_jsonable",
    "approve_catstyle_planet_reference",
]
