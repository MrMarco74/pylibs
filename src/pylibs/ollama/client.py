"""Client for an Ollama-compatible proxy (e.g. a shared internal reverse
proxy in front of one or more Ollama servers).

Some proxy setups do NOT forward multimodal (vision) calls and instead
require falling back to the underlying Ollama server's port directly (a
pattern seen in at least one internal project as
``ollama_port = 11434 if port == 11435 else port``). This client centralizes
that bypass instead of every caller reimplementing the port substitution.
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from typing import Iterator
from urllib.parse import urlparse

import requests

_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


@dataclass
class OllamaEndpoints:
    base_url: str = "http://localhost:11434"
    vision_base_url: str | None = None  # None -> derive from base_url (see _resolve_url)
    health_path: str = "/health"


class OllamaClient:
    def __init__(
        self,
        endpoints: OllamaEndpoints | None = None,
        timeout: float = 60.0,
        session: requests.Session | None = None,
        token: str | None = None,
    ):
        self.endpoints = endpoints or OllamaEndpoints()
        self.timeout = timeout
        self.session = session or requests.Session()
        token = token if token is not None else os.environ.get("LLMPROXY_TOKEN")
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _resolve_url(self, requires_vision: bool) -> str:
        """Return the base URL to use, bypassing the proxy for vision calls.

        If ``requires_vision`` and no explicit ``vision_base_url`` is set,
        and the current ``base_url`` port matches the proxy port (default
        11435), substitute the vision port (default 11434) instead. Both
        ports are overridable via ``OLLAMA_PROXY_PORT`` / ``OLLAMA_VISION_PORT``
        for setups other than the default.
        """
        if not requires_vision:
            return self.endpoints.base_url

        if self.endpoints.vision_base_url:
            return self.endpoints.vision_base_url

        proxy_port = int(os.environ.get("OLLAMA_PROXY_PORT", "11435"))
        vision_port = int(os.environ.get("OLLAMA_VISION_PORT", "11434"))

        parsed = urlparse(self.endpoints.base_url)
        if parsed.port != proxy_port:
            return self.endpoints.base_url

        new_netloc = f"{parsed.hostname}:{vision_port}"
        return parsed._replace(netloc=new_netloc).geturl()

    def _post(self, path: str, payload: dict, requires_vision: bool = False):
        url = self._resolve_url(requires_vision) + path
        stream = payload.get("stream", False)
        response = self.session.post(url, json=payload, timeout=self.timeout, stream=stream)
        response.raise_for_status()
        return response

    def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        stream: bool = False,
        options: dict | None = None,
        think: bool | None = None,
    ) -> "str | Iterator[str]":
        payload = {"model": model, "prompt": prompt, "stream": stream}
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options
        if think is not None:
            payload["think"] = think

        response = self._post("/api/generate", payload)
        if stream:
            return self._iter_ndjson_field(response, "response")

        return response.json().get("response", "")

    def chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
        format: str | dict | None = None,
        options: dict | None = None,
    ) -> "dict | Iterator[dict]":
        payload = {"model": model, "messages": messages, "stream": stream}
        if tools:
            payload["tools"] = tools
        if format is not None:
            payload["format"] = format
        if options is not None:
            payload["options"] = options

        response = self._post("/api/chat", payload)
        if stream:
            return (json.loads(line) for line in response.iter_lines() if line)

        return response.json()

    def generate_vision(
        self,
        model: str,
        prompt: str,
        images: list[bytes | str],
        system: str | None = None,
    ) -> str:
        """Generate a response from images + text. Always bypasses the proxy port."""
        encoded_images = [
            img if isinstance(img, str) else base64.b64encode(img).decode("ascii")
            for img in images
        ]
        payload = {
            "model": model,
            "prompt": prompt,
            "images": encoded_images,
            "stream": False,
        }
        if system:
            payload["system"] = system

        response = self._post("/api/generate", payload, requires_vision=True)
        return response.json().get("response", "")

    def health(self) -> bool:
        base = self.endpoints.base_url
        try:
            resp = self.session.get(base + self.endpoints.health_path, timeout=5)
            if resp.ok:
                return True
        except requests.RequestException:
            pass

        try:
            resp = self.session.get(base + "/api/tags", timeout=5)
            return resp.ok
        except requests.RequestException:
            return False

    @staticmethod
    def strip_reasoning(text: str) -> str:
        """Remove <think>...</think> reasoning blocks (DeepSeek-R1/Qwen3 style)."""
        return _THINK_BLOCK_RE.sub("", text)

    @staticmethod
    def _iter_ndjson_field(response: requests.Response, field: str) -> Iterator[str]:
        for line in response.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if field in chunk:
                yield chunk[field]
