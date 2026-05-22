"""Reference candidate workflow for unstable Catstyle pairs (generate → review → approve)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from astro_content_agent.content.catstyle.approved_reference_registry import normalize_pair_key
from astro_content_agent.content.catstyle.planet_canon_v1 import normalize_planet_name
from astro_content_agent.services.content.catstyle_creative_publish_stability import (
    evaluate_creative_publish_stability,
)

REFERENCE_REVIEW_CHECKLIST_ITEMS: tuple[str, ...] = (
    "Premium cinematic comic-poster finish (not storybook / children-book / soft watercolor)?",
    "Each planet-cat identity is clear and on-canon (silhouette, props, planetary read)?",
    "Cosmic zodiac coliseum arena with monumental scale, engraved zodiac stone floor, Earth above arena?",
    "Faction flags show correct canonical glyphs integrated into cloth (large, clean, readable)?",
    "No storybook illustration, watercolor drift, flat mascot, or toy-like cats?",
    "Pair metaphor / aspect read is sharp (not generic cute argument or static face-off)?",
)

REFERENCE_CANDIDATES_ROOT = "catstyle_reference_candidates"


def pair_folder_slug(planet_a: str, planet_b: str, aspect_type: str, mode: str) -> str:
    return normalize_pair_key(planet_a, planet_b, aspect_type, mode).replace("|", "_")


def reference_candidate_dir(
    work_root: Path,
    day: date,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
) -> Path:
    slug = pair_folder_slug(planet_a, planet_b, aspect_type, mode)
    return (work_root / REFERENCE_CANDIDATES_ROOT / day.isoformat() / slug).resolve()


def build_visual_review_checklist_markdown(
    *,
    date_iso: str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    candidate_image_paths: list[Path],
    manifest_path: Path | None,
    creatively_stable: bool,
    stability_reason: str,
) -> str:
    pa = normalize_planet_name(planet_a)
    pb = normalize_planet_name(planet_b)
    asp = (aspect_type or "").strip().lower()
    mo = (mode or "").strip().lower()
    lines = [
        "# Catstyle reference candidate visual review",
        "",
        f"- **Date:** {date_iso}",
        f"- **Pair:** {pa} {asp} {pb}",
        f"- **Mode:** {mo}",
        f"- **Creative publish stability:** {'stable' if creatively_stable else 'unstable'} ({stability_reason})",
        "",
        "## Candidate images",
        "",
    ]
    if candidate_image_paths:
        for i, p in enumerate(candidate_image_paths, start=1):
            lines.append(f"{i}. `{p.resolve()}`")
    else:
        lines.append("(no candidate images found)")
    if manifest_path and manifest_path.is_file():
        lines.append("")
        lines.append(f"- **Jobs manifest:** `{manifest_path.resolve()}`")
    lines.extend(["", "## Checklist", ""])
    for item in REFERENCE_REVIEW_CHECKLIST_ITEMS:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## Next step",
            "",
            "Pick the best candidate, then register it as the approved style reference:",
            "",
            "```powershell",
            format_approval_cli_command(
                image_path=candidate_image_paths[0] if candidate_image_paths else Path("PATH/TO/selected.png"),
                planet_a=pa,
                planet_b=pb,
                aspect_type=asp,
                mode=mo,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def format_approval_cli_command(
    *,
    image_path: Path | str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    label: str = "",
    notes: str = "",
) -> str:
    img = str(Path(image_path))
    parts = [
        "python scripts/aca/approve_catstyle_reference_candidate.py",
        f'--image-path "{img}"',
        f'--planet-a "{normalize_planet_name(planet_a)}"',
        f'--planet-b "{normalize_planet_name(planet_b)}"',
        f'--aspect-type "{aspect_type}"',
        f'--mode "{mode}"',
    ]
    if label.strip():
        parts.append(f'--label "{label.strip()}"')
    if notes.strip():
        parts.append(f'--notes "{notes.strip()}"')
    return " `\n  ".join(parts)


def collect_candidate_image_paths(images_dir: Path, jobs: list[Any]) -> list[Path]:
    """Prefer job suggested_output_name PNGs; fall back to sorted *.png in dir."""
    found: list[Path] = []
    for j in jobs:
        name = str(getattr(j, "suggested_output_name", "") or "").strip()
        if not name.lower().endswith(".png"):
            continue
        p = images_dir / Path(name).name
        if p.is_file():
            found.append(p.resolve())
    if found:
        return sorted(found, key=lambda p: p.name)
    return sorted(images_dir.glob("*.png"), key=lambda p: p.name)


def write_reference_candidate_artifacts(
    candidate_root: Path,
    *,
    date_iso: str,
    planet_a: str,
    planet_b: str,
    aspect_type: str,
    mode: str,
    candidate_image_paths: list[Path],
    manifest_path: Path | None,
    jobs_count: int,
    provider: str,
) -> tuple[Path, Path]:
    """Write visual review markdown + small metadata JSON; return (review_path, meta_path)."""
    import json

    candidate_root.mkdir(parents=True, exist_ok=True)
    stability = evaluate_creative_publish_stability(planet_a, planet_b, aspect_type, mode)
    review_path = candidate_root / "visual_review_checklist.md"
    review_path.write_text(
        build_visual_review_checklist_markdown(
            date_iso=date_iso,
            planet_a=planet_a,
            planet_b=planet_b,
            aspect_type=aspect_type,
            mode=mode,
            candidate_image_paths=candidate_image_paths,
            manifest_path=manifest_path,
            creatively_stable=stability.stable,
            stability_reason=stability.reason,
        ),
        encoding="utf-8",
    )
    meta = {
        "version": "catstyle-reference-candidates-v1",
        "date": date_iso,
        "planet_a": normalize_planet_name(planet_a),
        "planet_b": normalize_planet_name(planet_b),
        "aspect_type": (aspect_type or "").strip().lower(),
        "mode": (mode or "").strip().lower(),
        "jobs_count": jobs_count,
        "provider": provider,
        "candidate_images": [str(p) for p in candidate_image_paths],
        "manifest_path": str(manifest_path.resolve()) if manifest_path else None,
        "creative_publish_stable": stability.stable,
        "stability_reason": stability.reason,
    }
    meta_path = candidate_root / "reference_candidate_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return review_path, meta_path


__all__ = [
    "REFERENCE_CANDIDATES_ROOT",
    "REFERENCE_REVIEW_CHECKLIST_ITEMS",
    "build_visual_review_checklist_markdown",
    "collect_candidate_image_paths",
    "format_approval_cli_command",
    "pair_folder_slug",
    "reference_candidate_dir",
    "write_reference_candidate_artifacts",
]
