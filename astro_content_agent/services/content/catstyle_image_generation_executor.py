"""Catstyle v0 image job executor — orchestrates providers (stub default; no APIs)."""
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
    status: Literal["generated_stub", "skipped_existing"]
    prompt_preview: str | None = None
    note: str | None = None


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
    return StubJobOutputRecord(
        job_id=res.job_id,
        suggested_output_name=str(row.get("suggested_output_name", "") or f"output_{seq}.png"),
        prompt_index=int(row.get("prompt_index", seq)),
        stub_filename=res.output_filename or "",
        status=res.status,
        prompt_preview=res.metadata.get("prompt_preview"),
        note=res.metadata.get("note"),
    )


def execute_catstyle_image_jobs(
    jobs_manifest_path: Path,
    provider_name: str = "stub",
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> CatstyleImageExecutorStubResult:
    """
    Read ``image_generation_jobs.json`` and run the named provider for each pending job.

    v0 supports only ``provider_name=\"stub\"``.
    """
    provider = get_catstyle_image_provider(provider_name)
    manifest_path = jobs_manifest_path.expanduser().resolve()
    data = _load_jobs_manifest(manifest_path)
    jobs_raw: list[Any] = data["jobs"]

    if not jobs_raw:
        out_default = (manifest_path.parent / "generated_stub").resolve()
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
        else (manifest_path.parent / "generated_stub").resolve()
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

    for row in pending:
        seq += 1
        job_in = {**row, "_stub_output_seq": seq}
        res = provider.generate(job_in, out, overwrite)
        outputs.append(_provider_result_to_stub_record(row, seq, res))
        if res.status == "skipped_existing":
            skipped += 1
        elif res.status == "generated_stub" and res.output_filename:
            stub_files_written.append(res.output_filename)

    exec_payload: dict[str, Any] = {
        "version": "catstyle-image-executor-stub-v0",
        "provider": provider_name,
        "source_manifest_path": str(manifest_path),
        "outputs_dir": str(out),
        "jobs_processed": len(pending),
        "status": "completed_stub",
        "message": "Stub executor finished. No image model was invoked.",
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
        status="completed_stub",
        message="Stub executor finished. No image model was invoked.",
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
