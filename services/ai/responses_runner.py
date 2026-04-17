from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from astro_content_agent.core.config import get_settings
from astro_content_agent.db.models import ModelRun, PromptVersion
from astro_content_agent.services.ai.client import OpenAIClientFactory

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Language-aware prompt resolution
# ---------------------------------------------------------------------------

_SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"ru", "en"})


def prompt_ref_for_language(name: str, language: str) -> "PromptRef":
    """Return a :class:`PromptRef` for *name* in the given *language*.

    Russian prompts live in ``prompts/ru/<name>.md``.
    English (and any unsupported language) falls back to ``prompts/<name>.md``.

    Extension: add a new ``prompts/<lang>/`` subdirectory and register the
    language code in ``_SUPPORTED_LANGUAGES`` to support future languages.
    """
    lang = language if language in _SUPPORTED_LANGUAGES else "en"
    if lang == "ru":
        return PromptRef(name=f"{name}_ru", path=Path(f"ru/{name}.md"))
    return PromptRef(name=name, path=Path(f"{name}.md"))


# ---------------------------------------------------------------------------
# OpenAI Responses API strict-mode schema helpers
# ---------------------------------------------------------------------------


def _patch_strict(node: Any) -> None:  # noqa: ANN401
    """Recursively patch a JSON schema node in-place for OpenAI strict mode.

    Strict mode requires every object schema to have:
    - ``"additionalProperties": false``
    - All property keys listed in ``"required"``
    """
    if not isinstance(node, dict):
        return

    # Recurse into $defs (Pydantic v2 hoists nested model schemas here).
    for sub in node.get("$defs", {}).values():
        _patch_strict(sub)

    # Recurse into union variants (anyOf is used for Optional / str | None fields).
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in node.get(key, []):
            _patch_strict(sub)

    # Recurse into array item schema.
    if isinstance(node.get("items"), dict):
        _patch_strict(node["items"])

    # Patch explicit object schemas: any schema that is typed as "object" or
    # that declares "properties" is an object and needs the strict constraints.
    if node.get("type") == "object" or "properties" in node:
        node["type"] = "object"
        node["additionalProperties"] = False
        props: dict = node.setdefault("properties", {})
        # All properties must appear in "required" for strict mode.
        node["required"] = list(props.keys())
        for sub in props.values():
            _patch_strict(sub)

    # dict[str, Any] fields produce a bare {} schema in Pydantic v2.
    # Convert to a closed empty object so strict mode accepts it.
    elif not node:
        node.update({
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "required": [],
        })


def make_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of *schema* patched for OpenAI Responses API strict mode.

    Applies :func:`_patch_strict` recursively so every object definition carries
    ``"additionalProperties": false`` and a complete ``"required"`` array.
    """
    result = copy.deepcopy(schema)
    _patch_strict(result)
    return result


class AIResponseFormatError(ValueError):
    pass


@dataclass(frozen=True)
class PromptRef:
    name: str
    path: Path


class ResponsesRunner:
    """Executes Responses API calls and returns validated JSON outputs.

    This runner is intentionally small and testable:
    - prompt content is loaded from files
    - prompt versions are stored in DB (hash-based version)
    - model runs are logged in DB
    """

    def __init__(self, *, model: str, client, prompts_root: Path | None = None) -> None:
        self._model = model
        self._client = client
        self._prompts_root = prompts_root or (Path(__file__).parent / "prompts")

    @classmethod
    def from_settings(cls) -> "ResponsesRunner":
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        client = OpenAIClientFactory(api_key=settings.openai_api_key).create()
        return cls(model=settings.openai_model, client=client)

    def load_prompt(self, ref: PromptRef) -> str:
        full = ref.path
        if not full.is_absolute():
            full = self._prompts_root / ref.path
        return full.read_text(encoding="utf-8")

    def ensure_prompt_version(self, db: Session, *, ref: PromptRef) -> PromptVersion:
        content = self.load_prompt(ref)
        version = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

        existing = (
            db.query(PromptVersion)
            .filter(PromptVersion.name == ref.name, PromptVersion.version == version)
            .first()
        )
        if existing is not None:
            return existing

        pv = PromptVersion(
            name=ref.name,
            version=version,
            content=content,
            meta={"path": str(ref.path)},
        )
        db.add(pv)
        db.commit()
        db.refresh(pv)
        return pv

    def run_json(
        self,
        *,
        db: Session,
        prompt_ref: PromptRef,
        schema: type[T],
        input_payload: dict[str, Any],
        temperature: float | None = 0.3,
        max_output_tokens: int | None = 1200,
        metadata: dict[str, Any] | None = None,
    ) -> T:
        prompt_version = self.ensure_prompt_version(db, ref=prompt_ref)
        instructions = prompt_version.content

        schema_json = make_strict_schema(schema.model_json_schema())
        text_format = {"type": "json_schema", "name": schema.__name__, "schema": schema_json, "strict": True}

        started = time.perf_counter()
        model_run = ModelRun(
            prompt_version_id=prompt_version.id,
            model=self._model,
            input={"payload": input_payload, "prompt": {"name": prompt_ref.name, "version": prompt_version.version}},
            status="running",
        )
        db.add(model_run)
        db.commit()
        db.refresh(model_run)

        try:
            meta = {"prompt_name": prompt_ref.name, "prompt_version": prompt_version.version}
            if metadata:
                meta.update(metadata)
            response = self._client.responses.create(
                model=self._model,
                instructions=instructions,
                input=json.dumps(input_payload, ensure_ascii=False),
                text={"format": text_format},
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                metadata=meta,
            )
            raw = response.output_text
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise AIResponseFormatError(f"Model did not return valid JSON: {e}") from e

            try:
                parsed = schema.model_validate(data)
            except ValidationError as e:
                raise AIResponseFormatError(f"Model JSON failed schema validation: {e}") from e

            duration_ms = int((time.perf_counter() - started) * 1000)
            model_run.status = "succeeded"
            model_run.duration_ms = duration_ms
            model_run.output = parsed.model_dump(mode="json")
            db.add(model_run)
            db.commit()
            return parsed
        except Exception as e:
            duration_ms = int((time.perf_counter() - started) * 1000)
            model_run.status = "failed"
            model_run.duration_ms = duration_ms
            model_run.error = str(e)
            db.add(model_run)
            db.commit()
            raise

