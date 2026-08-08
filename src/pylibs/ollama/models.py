"""Model listing/inspection - prefers real /api/show fields over name heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field

from .client import OllamaClient


@dataclass
class ModelInfo:
    name: str
    families: list[str] = field(default_factory=list)
    parameter_size: str | None = None
    context_length: int | None = None
    raw: dict = field(default_factory=dict)


def list_models(client: OllamaClient) -> list[ModelInfo]:
    """GET /api/tags - fast, name-only listing (no per-model /api/show call)."""
    url = client._resolve_url(requires_vision=False) + "/api/tags"
    response = client.session.get(url, timeout=client.timeout)
    response.raise_for_status()
    data = response.json()

    models = []
    for entry in data.get("models", []):
        details = entry.get("details", {})
        models.append(
            ModelInfo(
                name=entry.get("name", entry.get("model", "")),
                families=details.get("families") or [],
                parameter_size=details.get("parameter_size"),
                raw=entry,
            )
        )
    return models


def show_model(client: OllamaClient, name: str) -> ModelInfo:
    """GET /api/show - reads real families/capabilities fields plus context length."""
    url = client._resolve_url(requires_vision=False) + "/api/show"
    response = client.session.post(url, json={"model": name}, timeout=client.timeout)
    response.raise_for_status()
    data = response.json()

    details = data.get("details", {})
    model_info = data.get("model_info", {})

    context_length = None
    for key, value in model_info.items():
        if key.endswith(".context_length"):
            context_length = value
            break

    return ModelInfo(
        name=name,
        families=details.get("families") or data.get("capabilities") or [],
        parameter_size=details.get("parameter_size"),
        context_length=context_length,
        raw=data,
    )
