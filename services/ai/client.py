from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


class ResponsesAPI(Protocol):
    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        text: dict,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        metadata: dict | None = None,
    ):
        """Create a response via OpenAI Responses API."""


class OpenAIClient(Protocol):
    @property
    def responses(self) -> ResponsesAPI: ...


@dataclass(frozen=True)
class OpenAIClientFactory:
    api_key: str

    def create(self) -> OpenAIClient:
        return OpenAI(api_key=self.api_key)

