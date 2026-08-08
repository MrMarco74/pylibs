"""Purpose-based model selection config, modeled on a pattern used in an
internal test-automation GUI:

{
  "ollama_url": "http://localhost:11434",
  "test_llm": "codellama:latest",
  "judge_llm": "llama3:latest",
  "code_llm": "deepseek-coder:latest",
  "vision_llm": "",
  "cached_models": []
}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .client import OllamaClient
from .models import list_models


@dataclass
class PurposeModelConfig:
    purposes: dict[str, str] = field(default_factory=dict)
    cached_models: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "PurposeModelConfig":
        path = Path(path)
        if not path.exists():
            return cls()

        import yaml

        data = yaml.safe_load(path.read_text()) or {}
        return cls(
            purposes=data.get("purposes", {}),
            cached_models=data.get("cached_models", []),
        )

    def save(self, path: str | Path) -> None:
        import yaml

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                {"purposes": self.purposes, "cached_models": self.cached_models},
                sort_keys=False,
            )
        )

    def get_model(self, purpose: str, fallback: str | None = None) -> str:
        value = self.purposes.get(purpose)
        if value:
            return value
        if fallback is not None:
            return fallback
        raise KeyError(f"No model configured for purpose '{purpose}'")

    def refresh_cache(self, client: OllamaClient) -> None:
        self.cached_models = [m.name for m in list_models(client)]
