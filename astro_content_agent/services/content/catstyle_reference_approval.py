"""Approve a generated Catstyle image as a reusable style reference (local filesystem + JSON registry v1)."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import (
    ApprovedReferenceEntry,
    approved_references_json_path,
    catstyle_repo_root,
    normalize_pair_key,
    read_registry_entries,
    write_registry_entries,
)
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.services.content.catstyle_reference_image_validation import (
    CatstyleReferenceImageValidationError,
    reference_image_quality_ok,
    validate_reference_image_source,
)


class CatstyleReferenceApprovalError(ValueError):
    """Invalid input or conflicting registry state."""


class CatstyleReferenceApprovalResult(BaseModel):
    """Outcome of a successful approval (for CLI and tests)."""

    source_image: str
    target_image: str = Field(description="Repo-relative POSIX path under references/.")
    target_image_absolute: str
    registry_key: str
    planet_pair: str = Field(description="Normalized display: PlanetA + PlanetB (sorted).")
    aspect: str
    mode: str
    active: bool
    overwrite: bool
    files_written: list[str] = Field(default_factory=list)


def _slug(s: str) -> str:
    return normalize_planet_name(s).strip().lower()


def _validate_mode(mode: str) -> str:
    m = (mode or "").strip().lower()
    if m not in ("tension", "compensation", "mixed", "flow"):
        raise CatstyleReferenceApprovalError(
            "mode must be one of: tension, compensation, mixed, flow " f"(got {mode!r})."
        )
    return m


def _deterministic_registry_key(p1: str, p2: str, aspect: str, mode: str) -> str:
    """Planets sorted by slug; aspect/mode lowercase."""
    a, b = sorted((p1, p2))
    asp = (aspect or "").strip().lower()
    mo = (mode or "").strip().lower()
    return f"{a}_{b}_{asp}_{mo}_v1"


def _deterministic_target_filename(p1: str, p2: str, aspect: str, mode: str) -> str:
    a, b = sorted((p1, p2))
    asp = (aspect or "").strip().lower()
    mo = (mode or "").strip().lower()
    return f"catstyle_{a}_{b}_{asp}_{mo}_approved.png"


def _display_pair(pa: str, pb: str) -> str:
    n1 = normalize_planet_name(pa)
    n2 = normalize_planet_name(pb)
    x, y = sorted((n1, n2), key=str.lower)
    return f"{x} + {y}"


def approve_catstyle_reference(
    *,
    source_image: Path | str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    label: str = "",
    notes: str = "",
    priority: int = 100,
    active: bool = True,
    overwrite: bool = False,
    repo_root: Path | None = None,
    registry_json_path: Path | None = None,
) -> CatstyleReferenceApprovalResult:
    """
    Copy ``source_image`` into ``references/`` with a deterministic name and upsert the JSON registry.

    Planet pair identity for matching is order-insensitive (same as ``normalize_pair_key``).
    """
    root = (repo_root or catstyle_repo_root()).expanduser().resolve()
    reg_path = registry_json_path or approved_references_json_path()
    src = Path(source_image).expanduser().resolve()
    try:
        validate_reference_image_source(src)
    except CatstyleReferenceImageValidationError as exc:
        raise CatstyleReferenceApprovalError(str(exc)) from exc

    mode_l = _validate_mode(mode)
    asp_l = (aspect_type or "").strip().lower()
    if not asp_l:
        raise CatstyleReferenceApprovalError("aspect_type must be non-empty.")

    s1 = _slug(planet_a)
    s2 = _slug(planet_b)
    if not s1 or not s2:
        raise CatstyleReferenceApprovalError("planet_a and planet_b must be non-empty.")

    pn_a = normalize_planet_name(planet_a)
    pn_b = normalize_planet_name(planet_b)
    pair_key = normalize_pair_key(pn_a, pn_b, asp_l, mode_l)
    reg_key = _deterministic_registry_key(s1, s2, asp_l, mode_l)
    fname = _deterministic_target_filename(s1, s2, asp_l, mode_l)
    rel_target = f"references/{fname}"
    abs_target = (root / "references" / fname).resolve()

    refs_dir = abs_target.parent
    refs_dir.mkdir(parents=True, exist_ok=True)

    entries = read_registry_entries(reg_path)
    idx_existing: int | None = None
    for i, e in enumerate(entries):
        if normalize_pair_key(e.planet_a, e.planet_b, e.aspect_type, e.mode) == pair_key:
            idx_existing = i
            break

    if idx_existing is not None and not overwrite:
        raise CatstyleReferenceApprovalError(
            "An approved reference already exists for this planet pair, aspect, and mode. "
            "Pass --overwrite to replace the image and update the registry entry."
        )

    if abs_target.is_file() and reference_image_quality_ok(abs_target) and not overwrite:
        raise CatstyleReferenceApprovalError(
            f"Production reference image already exists at {rel_target} "
            f"({abs_target.stat().st_size} bytes). Pass --overwrite to replace with a new valid PNG."
        )

    shutil.copy2(src, abs_target)

    new_entry = ApprovedReferenceEntry(
        registry_key=reg_key,
        planet_a=pn_a,
        planet_b=pn_b,
        aspect_type=asp_l,
        mode=mode_l,
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

    write_registry_entries(reg_path, entries)

    files_written = [rel_target.replace("\\", "/"), str(reg_path)]
    # registry path: prefer repo-relative when under root
    try:
        reg_rel = reg_path.resolve().relative_to(root)
        files_written[1] = str(reg_rel).replace("\\", "/")
    except ValueError:
        files_written[1] = str(reg_path.resolve())

    return CatstyleReferenceApprovalResult(
        source_image=str(src),
        target_image=rel_target.replace("\\", "/"),
        target_image_absolute=str(abs_target),
        registry_key=reg_key,
        planet_pair=_display_pair(planet_a, planet_b),
        aspect=asp_l,
        mode=mode_l,
        active=new_entry.active,
        overwrite=bool(idx_existing is not None),
        files_written=files_written,
    )


def approval_result_as_jsonable(res: CatstyleReferenceApprovalResult) -> dict[str, Any]:
    return res.model_dump(mode="json")


__all__ = [
    "CatstyleReferenceApprovalError",
    "CatstyleReferenceApprovalResult",
    "approval_result_as_jsonable",
    "approve_catstyle_reference",
]
