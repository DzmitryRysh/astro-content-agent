"""Catstyle v0 image providers: stub (no API) and OpenAI Images (local files only)."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, Field

from astro_content_agent.core.config import get_settings
from astro_content_agent.services.ai.client import OpenAIClientFactory

CatstyleImageProviderName = Literal["stub", "openai_image"]

_PREVIEW_MAX = 480


def _preview(text: str) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= _PREVIEW_MAX:
        return t
    return t[: _PREVIEW_MAX - 3] + "..."


def _sanitize_error_message(msg: str) -> str:
    """Remove likely secrets from API error strings (never log raw keys)."""
    out = str(msg)
    out = re.sub(r"sk-(?:proj|live|ant|test)?[a-zA-Z0-9_-]{8,}", "[REDACTED_API_KEY]", out)
    out = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", out)
    out = re.sub(r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "api_key=[REDACTED]", out, flags=re.I)
    if len(out) > 800:
        out = out[:797] + "..."
    return out


def _build_combined_prompt(job: dict[str, Any]) -> str:
    main = str(job.get("prompt_text", "") or "").strip()
    neg = str(job.get("negative_prompt", "") or "").strip()
    if neg:
        return f"{main}\n\nAvoid / negative guidance: {neg}"
    return main


class CatstyleImageProviderResult(BaseModel):
    """Per-job outcome from a ``CatstyleImageProvider.generate`` call."""

    provider: str
    job_id: str
    status: Literal["generated_stub", "skipped_existing", "generated", "failed"]
    output_path: str | None = None
    output_filename: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class CatstyleImageProvider(Protocol):
    """Pluggable image generation backend."""

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


class OpenAICatstyleImageProvider:
    """Calls OpenAI Images API; saves PNGs locally only (no Cloudinary / Instagram)."""

    provider_name: str = "openai_image"

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
        size: str | None = None,
    ) -> None:
        self._client = client
        self._model_override = model
        self._size_override = size

    def _effective_client(self, api_key: str) -> Any:
        if self._client is not None:
            return self._client
        return OpenAIClientFactory(api_key=api_key).create()

    def generate(self, job: dict[str, Any], output_dir: Path, overwrite: bool = False) -> CatstyleImageProviderResult:
        seq = int(job.get("_stub_output_seq", 1))
        job_id = str(job.get("job_id", "") or f"job-{seq}")
        prompt_index = int(job.get("prompt_index", seq))
        suggested = str(job.get("suggested_output_name", "") or f"output_{seq}.png")
        stem = Path(suggested).stem or f"output_{seq}"
        filename = f"{stem}.png"
        out_path = output_dir / filename

        settings = get_settings()
        model = (self._model_override or settings.openai_image_model).strip()
        size = (self._size_override or settings.catstyle_image_size).strip()
        preview = _preview(str(job.get("prompt_text", "")))

        meta_base = {
            "model": model,
            "size": size,
            "prompt_index": prompt_index,
            "suggested_output_name": suggested,
        }

        api_key = settings.openai_api_key
        if not api_key or not str(api_key).strip():
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message="OPENAI_API_KEY is not set. Add it to the environment or .env file.",
                metadata={**meta_base, "prompt_preview": preview},
            )

        if out_path.is_file() and not overwrite:
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="skipped_existing",
                output_path=str(out_path.resolve()),
                output_filename=filename,
                message="Image file exists; skipped (overwrite=False).",
                metadata={**meta_base, "prompt_preview": preview},
            )

        prompt = _build_combined_prompt(job)
        if not prompt.strip():
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message="Job has no prompt_text (empty after combining with negative_prompt).",
                metadata={**meta_base, "prompt_preview": preview},
            )

        client = self._effective_client(str(api_key).strip())
        try:
            resp = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,  # type: ignore[arg-type]
                n=1,
                response_format="b64_json",
            )
        except Exception as exc:  # noqa: BLE001 — surface safe summary only
            safe = _sanitize_error_message(str(exc))
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message=f"OpenAI image API error: {safe}",
                metadata={**meta_base, "prompt_preview": preview, "error_type": type(exc).__name__},
            )

        if not getattr(resp, "data", None) or len(resp.data) < 1:
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message="OpenAI image API returned no image data.",
                metadata={**meta_base, "prompt_preview": preview},
            )

        item = resp.data[0]
        raw_png: bytes | None = None
        b64 = getattr(item, "b64_json", None)
        if b64:
            try:
                raw_png = base64.b64decode(b64)
            except Exception as exc:  # noqa: BLE001
                safe = _sanitize_error_message(str(exc))
                return CatstyleImageProviderResult(
                    provider=self.provider_name,
                    job_id=job_id,
                    status="failed",
                    message=f"Failed to decode image bytes: {safe}",
                    metadata={**meta_base, "prompt_preview": preview},
                )
        else:
            url = getattr(item, "url", None)
            if url:
                try:
                    r = httpx.get(url, timeout=120.0)
                    r.raise_for_status()
                    raw_png = r.content
                except Exception as exc:  # noqa: BLE001
                    safe = _sanitize_error_message(str(exc))
                    return CatstyleImageProviderResult(
                        provider=self.provider_name,
                        job_id=job_id,
                        status="failed",
                        message=f"Failed to download image URL: {safe}",
                        metadata={**meta_base, "prompt_preview": preview},
                    )

        if not raw_png:
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message="OpenAI image response had neither b64_json nor url.",
                metadata={**meta_base, "prompt_preview": preview},
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(raw_png)

        return CatstyleImageProviderResult(
            provider=self.provider_name,
            job_id=job_id,
            status="generated",
            output_path=str(out_path.resolve()),
            output_filename=filename,
            message="Image saved locally for manual review.",
            metadata={**meta_base, "prompt_preview": preview},
        )


def get_catstyle_image_provider(name: str) -> CatstyleImageProvider:
    key = (name or "").strip().lower()
    if key == "stub":
        return StubCatstyleImageProvider()
    if key == "openai_image":
        return OpenAICatstyleImageProvider()
    raise ValueError(
        f"Unsupported Catstyle image provider {name!r}. Supported: stub, openai_image."
    )


__all__ = [
    "STUB_NOTE",
    "CatstyleImageProvider",
    "CatstyleImageProviderName",
    "CatstyleImageProviderResult",
    "OpenAICatstyleImageProvider",
    "StubCatstyleImageProvider",
    "get_catstyle_image_provider",
]
