"""Pluggable model backends for the sandbox agent. Standard library only.

Every backend speaks the OpenAI-compatible ``/chat/completions`` protocol, so
the same sandbox runs unchanged on:

  - Grok via the xAI API      (``grok_backend``; needs ``XAI_API_KEY``)
  - Ollama locally, free      (``ollama_backend``; needs ``ollama serve``)
  - LM Studio / vLLM / any OpenAI-compatible endpoint

There is no Grok CLI integration on this machine. The only Grok touchpoint in
this project is advisory text arriving through the PC relay file, which is not
callable. Grok-as-a-model goes through xAI's API, which is what ``grok_backend``
wraps. Model names change over time, so the model id is a required argument
rather than a hardcoded default; check xAI's docs for the current ids.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Optional


class ModelBackend(ABC):
    """Chat backend: list of {role, content} messages in, assistant text out."""

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError


class OpenAICompatibleBackend(ModelBackend):
    """POSTs to ``{base_url}/chat/completions``. Covers xAI, Ollama, LM Studio."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 180,
        temperature: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature

    def chat(self, messages: list[dict]) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"backend HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"backend unreachable at {self.base_url}: {exc.reason}"
            ) from exc
        try:
            return body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"unexpected backend response: {body!r}") from exc


def grok_backend(model: str, api_key: Optional[str] = None) -> OpenAICompatibleBackend:
    """Grok through xAI's OpenAI-compatible API.

    Needs ``XAI_API_KEY`` in the environment (or pass ``api_key``). ``model``
    is required because xAI's model ids change; check their docs for current
    values (e.g. a grok-4 series id).
    """
    key = api_key or os.environ.get("XAI_API_KEY")
    if not key:
        raise RuntimeError(
            "grok_backend needs an xAI API key: set XAI_API_KEY or pass api_key="
        )
    return OpenAICompatibleBackend("https://api.x.ai/v1", key, model)


def ollama_backend(
    model: str, base_url: str = "http://localhost:11434/v1"
) -> OpenAICompatibleBackend:
    """Free local backend. Needs ``ollama serve`` running and the model pulled."""
    return OpenAICompatibleBackend(base_url, "ollama", model)


class MockBackend(ModelBackend):
    """Scripted backend for zero-key smoke tests. Pops one response per call."""

    def __init__(self, script: list[str]) -> None:
        self._script = list(script)
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        if not self._script:
            return "FINAL: No more scripted responses."
        return self._script.pop(0)
