"""Catstyle v0 image job executor — orchestrates providers (stub / OpenAI Images)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from astro_content_agent.services.content.catstyle_image_providers import (
    CatstyleImageProviderResult,
    get_catstyle_image_provider,
)


class StubJobOutputRecord(BaseModel):
    job_id: str
    suggested_output_name: str
    prompt_index: int
    stub_filename: str
    status: Literal["generated_stub", "skipped_existing", "generated", "failed"]
    prompt_preview: str | None = None
    note: str | None = None
    final_prompt_length: int | None = None
    reference_used: bool | None = None
    reference_path: str | None = None
    reference_skip_reason: str | None = None
    generation_mode: str | None = None


class CatstyleImageExecutorStubResult(BaseModel):
    """Result of ``execute_catstyle_image_jobs`` / ``execute_catstyle_image_jobs_stub``."""

    source_manifest_path: str
    outputs_dir: str
    jobs_processed: int
    outputs: list[StubJobOutputRecord] = Field(default_factory=list)
    status: str
    message: str | None = None
    execution_manifest_path: str | None = None
    stub_files_written: list[str] = Field(default_factory=list)
    skipped_count: int = 0
    provider_name: str = "stub"


def _default_output_dir(manifest_path: Path, provider_name: str) -> Path:
    parent = manifest_path.parent
    key = (provider_name or "").strip().lower()
    if key == "openai_image":
        return (parent / "generated_images").resolve()
    return (parent / "generated_stub").resolve()


def _completion_meta(provider_name: str) -> tuple[str, str]:
    key = (provider_name or "").strip().lower()
    if key == "stub":
        return (
            "completed_stub",
            "Stub executor finished. No image model was invoked.",
        )
    if key == "openai_image":
        return (
            "completed_openai",
            "OpenAI image generation finished. Files saved locally for manual review (no upload).",
        )
    return ("completed", "Execution finished.")


def _load_jobs_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Jobs manifest not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in jobs manifest {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ValueError(f"Jobs manifest must be a JSON object: {path}")
    if "jobs" not in raw:
        raise ValueError(f"Jobs manifest missing 'jobs' array: {path}")
    if not isinstance(raw["jobs"], list):
        raise ValueError(f"Jobs manifest 'jobs' must be an array: {path}")
    return raw


def _provider_result_to_stub_record(
    row: dict[str, Any],
    seq: int,
    res: CatstyleImageProviderResult,
) -> StubJobOutputRecord:
    note = res.metadata.get("note")
    if res.provider == "openai_image" and note is None:
        note = res.message
    return StubJobOutputRecord(
        job_id=res.job_id,
        suggested_output_name=str(row.get("suggested_output_name", "") or f"output_{seq}.png"),
        prompt_index=int(row.get("prompt_index", seq)),
        stub_filename=res.output_filename or "",
        status=res.status,
        prompt_preview=res.metadata.get("prompt_preview"),
        note=note if isinstance(note, str) else None,
        final_prompt_length=int(res.metadata["final_prompt_length"])
        if isinstance(res.metadata.get("final_prompt_length"), int)
        else None,
        reference_used=bool(res.metadata["reference_used"])
        if isinstance(res.metadata.get("reference_used"), bool)
        else None,
        reference_path=str(res.metadata["reference_path"])
        if isinstance(res.metadata.get("reference_path"), str)
        else None,
        reference_skip_reason=str(res.metadata["reference_skip_reason"])
        if isinstance(res.metadata.get("reference_skip_reason"), str)
        else None,
        generation_mode=str(res.metadata["generation_mode"])
        if isinstance(res.metadata.get("generation_mode"), str)
        else None,
    )


def _emit_reference_logs(data: dict[str, Any], job_row: dict[str, Any]) -> list[str]:
    """Return log lines for approved/explicit reference usage (also suitable for execution manifest)."""
    lines: list[str] = []
    style_ref = data.get("style_reference")
    if isinstance(style_ref, dict) and style_ref.get("approved_reference_used"):
        for line in style_ref.get("log_lines") or []:
            if line not in lines:
                lines.append(line)
        if not lines:
            path = style_ref.get("approved_reference_image_path") or style_ref.get("path") or ""
            lines.append(f"Using approved Catstyle reference image: {path}")
            lines.append("Reference source: approved_reference_registry")
    elif str(job_row.get("style_reference_image_path") or "").strip():
        lines.append(
            f"Using explicit style reference image: {job_row.get('style_reference_image_path')}"
        )
    return lines


def execute_catstyle_image_jobs(
    jobs_manifest_path: Path,
    provider_name: str = "stub",
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> CatstyleImageExecutorStubResult:
    """
    Read ``image_generation_jobs.json`` and run the named provider for each pending job.

    Supports ``provider_name`` ``stub`` or ``openai_image``. Default output directory is
    ``<manifest_dir>/generated_stub`` or ``<manifest_dir>/generated_images`` respectively,
    unless ``output_dir`` is given.
    """
    provider = get_catstyle_image_provider(provider_name)
    manifest_path = jobs_manifest_path.expanduser().resolve()
    done_status, done_message = _completion_meta(provider_name)
    data = _load_jobs_manifest(manifest_path)
    jobs_raw: list[Any] = data["jobs"]

    if not jobs_raw:
        out_default = _default_output_dir(manifest_path, provider_name)
        out = (output_dir.expanduser().resolve() if output_dir is not None else out_default)
        return CatstyleImageExecutorStubResult(
            source_manifest_path=str(manifest_path),
            outputs_dir=str(out),
            jobs_processed=0,
            outputs=[],
            status="no_jobs",
            message="Manifest contained no jobs; nothing to execute.",
            provider_name=provider_name,
        )

    out = (
        output_dir.expanduser().resolve()
        if output_dir is not None
        else _default_output_dir(manifest_path, provider_name)
    )
    out.mkdir(parents=True, exist_ok=True)

    pending: list[dict[str, Any]] = []
    for row in jobs_raw:
        if not isinstance(row, dict):
            continue
        st = str(row.get("status", "pending")).strip().lower()
        if st == "pending":
            pending.append(row)

    if not pending:
        exec_payload = {
            "version": "catstyle-image-executor-stub-v0",
            "provider": provider_name,
            "source_manifest_path": str(manifest_path),
            "outputs_dir": str(out),
            "jobs_processed": 0,
            "status": "no_pending_jobs",
            "message": "No jobs with status 'pending' in manifest; nothing executed.",
            "outputs": [],
            "skipped_existing_count": 0,
            "stub_files_written": [],
        }
        exec_path = out / "image_generation_execution_stub.json"
        exec_path.write_text(json.dumps(exec_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return CatstyleImageExecutorStubResult(
            source_manifest_path=str(manifest_path),
            outputs_dir=str(out),
            jobs_processed=0,
            outputs=[],
            status="no_pending_jobs",
            message="No jobs with status 'pending' in manifest; nothing executed.",
            execution_manifest_path=str(exec_path),
            provider_name=provider_name,
        )

    outputs: list[StubJobOutputRecord] = []
    stub_files_written: list[str] = []
    skipped = 0
    seq = 0
    reference_log_lines: list[str] = []

    for row in pending:
        seq += 1
        for log_line in _emit_reference_logs(data, row):
            if log_line not in reference_log_lines:
                reference_log_lines.append(log_line)
                print(log_line, flush=True)
        style_src = None
        style_block = data.get("style_reference")
        if isinstance(style_block, dict):
            style_src = style_block.get("source")
        job_in = {**row, "_stub_output_seq": seq, "reference_source": style_src}
        res = provider.generate(job_in, out, overwrite)
        outputs.append(_provider_result_to_stub_record(row, seq, res))
        if res.status == "skipped_existing":
            skipped += 1
        elif res.status in ("generated_stub", "generated") and res.output_filename:
            stub_files_written.append(res.output_filename)

    exec_payload: dict[str, Any] = {
        "version": "catstyle-image-executor-stub-v0",
        "provider": provider_name,
        "source_manifest_path": str(manifest_path),
        "outputs_dir": str(out),
        "jobs_processed": len(pending),
        "status": done_status,
        "message": done_message,
        "reference_log_lines": reference_log_lines,
        "outputs": [o.model_dump(mode="json") for o in outputs],
        "skipped_existing_count": skipped,
        "stub_files_written": stub_files_written,
    }
    exec_path = out / "image_generation_execution_stub.json"
    exec_path.write_text(json.dumps(exec_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return CatstyleImageExecutorStubResult(
        source_manifest_path=str(manifest_path),
        outputs_dir=str(out),
        jobs_processed=len(pending),
        outputs=outputs,
        status=done_status,
        message=done_message,
        execution_manifest_path=str(exec_path),
        stub_files_written=stub_files_written,
        skipped_count=skipped,
        provider_name=provider_name,
    )


def execute_catstyle_image_jobs_stub(
    jobs_manifest_path: Path,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> CatstyleImageExecutorStubResult:
    """Backward-compatible alias for ``execute_catstyle_image_jobs(..., provider_name=\"stub\")``."""
    return execute_catstyle_image_jobs(
        jobs_manifest_path,
        provider_name="stub",
        output_dir=output_dir,
        overwrite=overwrite,
    )


__all__ = [
    "CatstyleImageExecutorStubResult",
    "StubJobOutputRecord",
    "execute_catstyle_image_jobs",
    "execute_catstyle_image_jobs_stub",
]
