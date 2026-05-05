"""Catstyle v0 stub image job executor — reads job manifests, writes reviewable placeholders (no APIs)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


_PREVIEW_MAX = 480


class StubJobOutputRecord(BaseModel):
    job_id: str
    suggested_output_name: str
    prompt_index: int
    stub_filename: str
    status: Literal["generated_stub", "skipped_existing"]
    prompt_preview: str | None = None
    note: str | None = None


class CatstyleImageExecutorStubResult(BaseModel):
    """Result of ``execute_catstyle_image_jobs_stub``."""

    source_manifest_path: str
    outputs_dir: str
    jobs_processed: int
    outputs: list[StubJobOutputRecord] = Field(default_factory=list)
    status: str
    message: str | None = None
    execution_manifest_path: str | None = None
    stub_files_written: list[str] = Field(default_factory=list)
    skipped_count: int = 0


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


def _preview(text: str) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= _PREVIEW_MAX:
        return t
    return t[: _PREVIEW_MAX - 3] + "..."


def execute_catstyle_image_jobs_stub(
    jobs_manifest_path: Path,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> CatstyleImageExecutorStubResult:
    """
    Read ``image_generation_jobs.json`` and write stub text artifacts plus an execution manifest.

    Does not call OpenAI, other image APIs, Cloudinary, or Instagram.
    """
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
        )

    outputs: list[StubJobOutputRecord] = []
    stub_files_written: list[str] = []
    skipped = 0
    seq = 0

    for row in pending:
        seq += 1
        job_id = str(row.get("job_id", "") or f"job-{seq}")
        suggested = str(row.get("suggested_output_name", "") or f"output_{seq}.png")
        prompt_index = int(row.get("prompt_index", seq))
        prompt_text = str(row.get("prompt_text", ""))
        preview = _preview(prompt_text)

        stub_name = f"generated_stub_{seq:02d}.txt"
        stub_path = out / stub_name
        note = "Stub only. No image API was called."

        if stub_path.is_file() and not overwrite:
            outputs.append(
                StubJobOutputRecord(
                    job_id=job_id,
                    suggested_output_name=suggested,
                    prompt_index=prompt_index,
                    stub_filename=stub_name,
                    status="skipped_existing",
                    prompt_preview=preview,
                    note=note,
                )
            )
            skipped += 1
            continue

        body = {
            "job_id": job_id,
            "suggested_output_name": suggested,
            "prompt_index": prompt_index,
            "status": "generated_stub",
            "prompt_preview": preview,
            "note": note,
        }
        stub_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        stub_files_written.append(stub_name)
        outputs.append(
            StubJobOutputRecord(
                job_id=job_id,
                suggested_output_name=suggested,
                prompt_index=prompt_index,
                stub_filename=stub_name,
                status="generated_stub",
                prompt_preview=preview,
                note=note,
            )
        )

    exec_payload: dict[str, Any] = {
        "version": "catstyle-image-executor-stub-v0",
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
    )


__all__ = [
    "CatstyleImageExecutorStubResult",
    "StubJobOutputRecord",
    "execute_catstyle_image_jobs_stub",
]
