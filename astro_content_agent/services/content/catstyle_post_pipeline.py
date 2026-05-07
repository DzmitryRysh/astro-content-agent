"""Catstyle post pipeline v1 — orchestrate local package → QC → manual review → optional approval → handoff."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from astro_content_agent.services.content.catstyle_manual_review import (
    approve_catstyle_manual_review,
    build_catstyle_manual_review,
    write_catstyle_manual_review,
)
from astro_content_agent.services.content.catstyle_post_package import (
    build_catstyle_post_package,
    write_catstyle_post_package,
)
from astro_content_agent.services.content.catstyle_post_package_quality import (
    check_catstyle_post_package,
)
from astro_content_agent.services.content.catstyle_publish_handoff import (
    CatstylePublishHandoffError,
    build_catstyle_publish_handoff,
    write_catstyle_publish_handoff,
)

PIPELINE_VERSION = "catstyle-post-pipeline-v1"


class CatstylePostPipelineResult(BaseModel):
    """Outcome of ``run_catstyle_post_pipeline``."""

    version: str = PIPELINE_VERSION
    date: str
    status: Literal["review_ready", "ready_for_manual_publish", "needs_attention"]
    package_dir: str
    quality_status: str
    quality_score: int = Field(ge=0, le=100)
    manual_review_path: str
    publish_handoff_dir: str | None = None
    recommended_primary_image: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    files_written: list[str] = Field(default_factory=list)


def run_catstyle_post_pipeline(
    manifest_path: Path | str,
    *,
    generated_images_dir: Path | str | None = None,
    post_package_dir: Path | str | None = None,
    publish_handoff_dir: Path | str | None = None,
    approve: bool = False,
    approval_notes: str = "",
    overwrite: bool = False,
) -> CatstylePostPipelineResult:
    """Run the local Catstyle post workflow after images exist on disk."""
    mp = Path(manifest_path).expanduser().resolve()

    pkg = build_catstyle_post_package(mp, generated_images_dir=generated_images_dir)
    pkg_out = (
        Path(post_package_dir).expanduser().resolve()
        if post_package_dir is not None
        else (Path("catstyle_post_packages") / pkg.date).resolve()
    )

    files_written: list[str] = []
    for name in write_catstyle_post_package(pkg, pkg_out, overwrite=overwrite):
        files_written.append(str((pkg_out / name).resolve()))

    qc = check_catstyle_post_package(pkg_out)
    errors = list(qc.errors)
    warnings = list(qc.warnings)

    mr = build_catstyle_manual_review(pkg_out, quality_result=qc)
    for name in write_catstyle_manual_review(mr, pkg_out, overwrite=overwrite):
        p = str((pkg_out / name).resolve())
        if p not in files_written:
            files_written.append(p)

    manual_review_path = str((pkg_out / "manual_review.json").resolve())
    primary = pkg.recommended_primary_image

    base = CatstylePostPipelineResult(
        date=pkg.date,
        status="needs_attention",
        package_dir=str(pkg_out.resolve()),
        quality_status=qc.status,
        quality_score=qc.score,
        manual_review_path=manual_review_path,
        publish_handoff_dir=None,
        recommended_primary_image=primary,
        errors=errors,
        warnings=warnings,
        files_written=files_written,
    )

    if qc.status != "ready":
        return base.model_copy(update={"status": "needs_attention"})

    if not approve:
        return base.model_copy(update={"status": "review_ready", "errors": []})

    notes = approval_notes if approval_notes is not None else ""
    approve_catstyle_manual_review(pkg_out, "approve", reviewer_notes=notes, overwrite=overwrite)

    ph_out = (
        Path(publish_handoff_dir).expanduser().resolve()
        if publish_handoff_dir is not None
        else (Path("catstyle_publish_handoffs") / pkg.date).resolve()
    )

    try:
        handoff = build_catstyle_publish_handoff(pkg_out)
        for name in write_catstyle_publish_handoff(handoff, ph_out, overwrite=overwrite):
            path_str = str((ph_out / name).resolve())
            if path_str not in files_written:
                files_written.append(path_str)
    except CatstylePublishHandoffError as exc:
        merged_errors = list(errors) + [str(exc)]
        return base.model_copy(
            update={
                "status": "needs_attention",
                "errors": merged_errors,
                "publish_handoff_dir": None,
                "files_written": files_written,
            }
        )
    except FileExistsError as exc:
        merged_errors = list(errors) + [str(exc)]
        return base.model_copy(
            update={
                "status": "needs_attention",
                "errors": merged_errors,
                "publish_handoff_dir": None,
                "files_written": files_written,
            }
        )

    return base.model_copy(
        update={
            "status": "ready_for_manual_publish",
            "errors": [],
            "publish_handoff_dir": str(ph_out.resolve()),
            "files_written": files_written,
        }
    )


__all__ = [
    "PIPELINE_VERSION",
    "CatstylePostPipelineResult",
    "run_catstyle_post_pipeline",
]
