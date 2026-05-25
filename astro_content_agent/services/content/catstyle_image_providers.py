"""Catstyle v0 image providers: stub (no API) and OpenAI Images (local files only)."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, Field

from astro_content_agent.content.catstyle.approved_reference_registry import catstyle_repo_root
from astro_content_agent.core.config import get_settings
from astro_content_agent.services.ai.client import OpenAIClientFactory

CatstyleImageProviderName = Literal["stub", "openai_image"]

_PREVIEW_MAX = 480
_PROVIDER_PROMPT_TRIM_TRIGGER = 31_900
_PROVIDER_PROMPT_TARGET_MAX = 31_850


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


def _banner_glyph_reference_prefix(job: dict[str, Any]) -> str:
    """Provider preamble when banner glyph reference paths are on the job."""
    ga = str(job.get("banner_glyph_reference_planet_a_path") or "").strip()
    gb = str(job.get("banner_glyph_reference_planet_b_path") or "").strip()
    if not ga and not gb:
        return ""
    style = str(job.get("style_reference_image_path") or "").strip()
    parts = [
        "[REFERENCE INPUT] When the image API accepts multiple reference images: "
    ]
    if style:
        parts.append(
            "Image A = attached primary style/scene reference (catplanet DNA, arena, CG finish). "
        )
    label_b = "B" if style else "A"
    label_c = "C" if style else "B"
    if ga:
        parts.append(
            f"Image {label_b} = left/port banner glyph crop (planet A)—canonical heraldic glyph on cloth only. "
        )
    if gb:
        parts.append(
            f"Image {label_c} = right/starboard banner glyph crop (planet B)—canonical heraldic glyph on cloth only. "
        )
    parts.append(
        "Use banner glyph references only for correct glyphs on faction flags; no extra glyphs elsewhere. "
    )
    return "".join(parts)


def _build_combined_prompt(job: dict[str, Any]) -> str:
    main = str(job.get("prompt_text", "") or "").strip()
    neg = str(job.get("negative_prompt", "") or "").strip()
    prefix = _banner_glyph_reference_prefix(job)
    body = main
    if neg:
        body = f"{body}\n\nAvoid / negative guidance: {neg}"
    if prefix:
        return f"{prefix}{body}"
    return body


def _fit_provider_prompt(prompt: str) -> str:
    """
    Final provider-boundary prompt guard.

    Keeps the rich prompt intact unless it is near provider limits, then applies a
    deterministic surgical trim to stay safely under OpenAI 32k limit.
    """
    s = " ".join((prompt or "").split())
    if len(s) <= _PROVIDER_PROMPT_TRIM_TRIGGER:
        return s
    cut = s.rfind(". ", 0, _PROVIDER_PROMPT_TARGET_MAX)
    if cut > int(_PROVIDER_PROMPT_TARGET_MAX * 0.92):
        return s[:cut].rstrip() + "."
    return s[:_PROVIDER_PROMPT_TARGET_MAX].rstrip()


def _images_response_to_png_bytes(resp: Any) -> tuple[bytes | None, str | None]:
    """Decode first image from Images API response (b64_json preferred, else URL download)."""
    if not getattr(resp, "data", None) or len(resp.data) < 1:
        return None, "OpenAI image API returned no image data."

    item = resp.data[0]
    raw_png: bytes | None = None
    b64 = getattr(item, "b64_json", None)
    if b64:
        try:
            raw_png = base64.b64decode(b64)
        except Exception as exc:  # noqa: BLE001
            return None, f"Failed to decode image bytes: {_sanitize_error_message(str(exc))}"
    else:
        url = getattr(item, "url", None)
        if url:
            try:
                r = httpx.get(url, timeout=120.0)
                r.raise_for_status()
                raw_png = r.content
            except Exception as exc:  # noqa: BLE001
                return None, f"Failed to download image URL: {_sanitize_error_message(str(exc))}"

    if not raw_png:
        return None, "OpenAI image response had neither b64_json nor url."
    return raw_png, None


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
        style_reference_image_path = (
            str(job.get("style_reference_image_path", "")).strip() or None
            if job.get("style_reference_image_path") is not None
            else None
        )
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
                    "style_reference_image_path": style_reference_image_path,
                },
            )

        body = {
            "job_id": job_id,
            "suggested_output_name": suggested,
            "prompt_index": prompt_index,
            "status": "generated_stub",
            "prompt_preview": preview,
            "note": STUB_NOTE,
            "style_reference_image_path": style_reference_image_path,
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
                "style_reference_image_path": style_reference_image_path,
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
        style_reference_image_path = (
            str(job.get("style_reference_image_path", "")).strip() or None
            if job.get("style_reference_image_path") is not None
            else None
        )
        preview = _preview(str(job.get("prompt_text", "")))

        meta_base = {
            "model": model,
            "size": size,
            "prompt_index": prompt_index,
            "suggested_output_name": suggested,
            "style_reference_image_path": style_reference_image_path,
            "reference_used": False,
            "reference_path": style_reference_image_path,
            "reference_skip_reason": "no_reference_provided" if not style_reference_image_path else None,
            "generation_mode": "text_generate",
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

        ref_path: Path | None = None
        if style_reference_image_path:
            ref_path = Path(style_reference_image_path).expanduser()
            if not ref_path.is_absolute():
                candidate = (catstyle_repo_root() / ref_path).resolve()
                ref_path = candidate if candidate.is_file() else (Path.cwd() / ref_path).resolve()
            else:
                ref_path = ref_path.resolve()
            style_reference_image_path = str(ref_path)
            meta_base["style_reference_image_path"] = style_reference_image_path
            meta_base["reference_path"] = style_reference_image_path
            if not ref_path.is_file():
                return CatstyleImageProviderResult(
                    provider=self.provider_name,
                    job_id=job_id,
                    status="failed",
                    message=f"style_reference_image_path not found: {ref_path}",
                    metadata={
                        **meta_base,
                        "prompt_preview": preview,
                        "reference_skip_reason": "reference_file_missing",
                        "generation_mode": "text_generate",
                        "reference_used": False,
                        "final_prompt_length": None,
                    },
                )
            meta_base["reference_skip_reason"] = None
            meta_base["reference_used"] = True
            meta_base["generation_mode"] = "image_edit"
            ref_src = str(job.get("reference_source") or "").strip()
            meta_base["reference_source"] = ref_src or "style_reference_image"

        prompt = _build_combined_prompt(job)
        if ref_path is not None:
            prompt = (
                "Use the provided reference image as the strict primary visual DNA anchor "
                "(campaign sibling; preserve render density, catplanet bodies, arena scale). "
                f"{prompt}"
            )
        prompt = _fit_provider_prompt(prompt)
        final_prompt_length = len(prompt)
        if not prompt.strip():
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message="Job has no prompt_text (empty after combining with negative_prompt).",
                metadata={**meta_base, "prompt_preview": preview, "final_prompt_length": final_prompt_length},
            )

        client = self._effective_client(str(api_key).strip())
        resp: Any
        api_model = model
        try:
            if ref_path is not None:
                edit_fn = getattr(client.images, "edit", None)
                if edit_fn is None or not callable(edit_fn):
                    return CatstyleImageProviderResult(
                        provider=self.provider_name,
                        job_id=job_id,
                        status="failed",
                        message=(
                            "style reference image generation is not supported by this OpenAI SDK/client path: "
                            "client.images.edit is not available."
                        ),
                        metadata={
                            **meta_base,
                            "prompt_preview": preview,
                            "reference_used": False,
                            "reference_skip_reason": "images_edit_not_available",
                            "final_prompt_length": final_prompt_length,
                        },
                    )
                with ref_path.open("rb") as image_file:
                    resp = client.images.edit(
                        model=api_model,
                        image=image_file,
                        prompt=prompt,
                        size=size,  # type: ignore[arg-type]
                        n=1,
                    )
            else:
                # GPT image models (e.g. gpt-image-1): no response_format — base64 is default;
                # use output_format instead (response_format is invalid for these models).
                resp = client.images.generate(
                    model=api_model,
                    prompt=prompt,
                    size=size,  # type: ignore[arg-type]
                    n=1,
                    output_format="png",
                )
        except TypeError as exc:
            if ref_path is not None:
                safe = _sanitize_error_message(str(exc))
                return CatstyleImageProviderResult(
                    provider=self.provider_name,
                    job_id=job_id,
                    status="failed",
                    message=(
                        "style reference image generation is not supported by this OpenAI SDK/client path: "
                        f"{safe}"
                    ),
                    metadata={
                        **meta_base,
                        "prompt_preview": preview,
                        "error_type": type(exc).__name__,
                        "final_prompt_length": final_prompt_length,
                    },
                )
            safe = _sanitize_error_message(str(exc))
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message=f"OpenAI image API error: {safe}",
                metadata={
                    **meta_base,
                    "prompt_preview": preview,
                    "error_type": type(exc).__name__,
                    "final_prompt_length": final_prompt_length,
                },
            )
        except Exception as exc:  # noqa: BLE001 — surface safe summary only
            safe = _sanitize_error_message(str(exc))
            if ref_path is not None:
                msg = f"OpenAI images.edit API error: {safe}"
            else:
                msg = f"OpenAI image API error: {safe}"
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message=msg,
                metadata={
                    **meta_base,
                    "prompt_preview": preview,
                    "error_type": type(exc).__name__,
                    "final_prompt_length": final_prompt_length,
                },
            )

        raw_png, decode_err = _images_response_to_png_bytes(resp)
        if decode_err or raw_png is None:
            return CatstyleImageProviderResult(
                provider=self.provider_name,
                job_id=job_id,
                status="failed",
                message=decode_err or "OpenAI image decode failed.",
                metadata={**meta_base, "prompt_preview": preview, "final_prompt_length": final_prompt_length},
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
            metadata={
                **meta_base,
                "prompt_preview": preview,
                "final_prompt_length": final_prompt_length,
            },
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
