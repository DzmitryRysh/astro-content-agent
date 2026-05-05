"""Catstyle v0 image provider abstraction (stub only — no external image APIs)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

CatstyleImageProviderName = Literal["stub"]

_PREVIEW_MAX = 480


def _preview(text: str) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= _PREVIEW_MAX:
        return t
    return t[: _PREVIEW_MAX - 3] + "..."


class CatstyleImageProviderResult(BaseModel):
    """Per-job outcome from a ``CatstyleImageProvider.generate`` call."""

    provider: str
    job_id: str
    status: Literal["generated_stub", "skipped_existing"]
    output_path: str | None = None
    output_filename: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class CatstyleImageProvider(Protocol):
    """Pluggable image generation backend (v0: stub only)."""

    def generate(self, job: dict[str, Any], output_dir: Path, overwrite: bool = False) -> CatstyleImageProviderResult:
        """Run one job. ``job`` may include executor-only keys such as ``_stub_output_seq`` (1-based)."""
        ...


STUB_NOTE = "Stub only. No image API was called."


class StubCatstyleImageProvider:
    """Writes JSON placeholder files; no image model."""

    provider_name: str = "stub"

    def generate(self, job: dict[str, Any], output_dir: Path, overwrite: bool = False) -> CatstyleImageProviderResult:
        seq = int(job.get("_stub_output_seq", 1))
        job_id = str(job.get("job_id", "") or f"job-{seq}")
        suggested = str(job.get("suggested_output_name", "") or f"output_{seq}.png")
        prompt_index = int(job.get("prompt_index", seq))
        prompt_text = str(job.get("prompt_text", ""))
        preview = _preview(prompt_text)

        stub_name = f"generated_stub_{seq:02d}.txt"
        stub_path = output_dir / stub_name

        if stub_path.is_file() and not overwrite:
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="skipped_existing",
                output_path=str(stub_path.resolve()),
                output_filename=stub_name,
                message="Stub file exists; skipped (overwrite=False).",
                metadata={
                    "prompt_preview": preview,
                    "note": STUB_NOTE,
                    "suggested_output_name": suggested,
                    "prompt_index": prompt_index,
                },
            )

        body = {
            "job_id": job_id,
            "suggested_output_name": suggested,
            "prompt_index": prompt_index,
            "status": "generated_stub",
            "prompt_preview": preview,
            "note": STUB_NOTE,
        }
        stub_path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return CatstyleImageProviderResult(
            provider=self.provider_name,
            job_id=job_id,
            status="generated_stub",
            output_path=str(stub_path.resolve()),
            output_filename=stub_name,
            message="Stub artifact written.",
            metadata={
                "prompt_preview": preview,
                "note": STUB_NOTE,
                "suggested_output_name": suggested,
                "prompt_index": prompt_index,
            },
        )


def get_catstyle_image_provider(name: str) -> CatstyleImageProvider:
    key = (name or "").strip().lower()
    if key == "stub":
        return StubCatstyleImageProvider()
    raise ValueError(
        f"Unsupported Catstyle image provider {name!r}. v0 supports only: stub."
    )


__all__ = [
    "STUB_NOTE",
    "CatstyleImageProvider",
    "CatstyleImageProviderName",
    "CatstyleImageProviderResult",
    "StubCatstyleImageProvider",
    "get_catstyle_image_provider",
]
