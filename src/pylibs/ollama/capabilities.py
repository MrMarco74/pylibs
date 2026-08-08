"""Extensible model capability detection.

No Ollama project in the surveyed codebase actually reads the real
``families``/``capabilities`` fields from /api/show to determine modality -
they all use ad-hoc substring blocklists on the model name. This module
keeps that heuristic as a configurable fallback, but prefers real API
fields when the model provides them, and makes the rules data instead of
duplicated code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .models import ModelInfo


class Capability(str, Enum):
    TEXT = "text"
    VISION = "vision"
    CODE = "code"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    TOOL_CALLING = "tool_calling"


@dataclass
class CapabilityRule:
    capability: Capability
    name_substrings: list[str] = field(default_factory=list)
    family_names: list[str] = field(default_factory=list)

    def matches(self, model: ModelInfo) -> bool:
        name_lower = model.name.lower()
        if any(sub in name_lower for sub in self.name_substrings):
            return True
        families_lower = [f.lower() for f in model.families]
        return any(fam in families_lower for fam in self.family_names)


# Ported from near-identical blocklists found across several internal projects.
DEFAULT_RULES: list[CapabilityRule] = [
    CapabilityRule(
        Capability.VISION,
        name_substrings=["vision", "-vl:", "-vl-", "llava", "moondream", "minicpm-v"],
        family_names=["clip", "mllama"],
    ),
    CapabilityRule(
        Capability.CODE,
        name_substrings=["coder", "codestral", "codellama", "devstral", "deepseek-coder"],
    ),
    CapabilityRule(Capability.EMBEDDING, name_substrings=["embed"]),
    CapabilityRule(Capability.REASONING, name_substrings=["deepseek-r1", "qwen3"]),
]


class CapabilityDetector:
    """Detects capabilities from real API fields first, then configurable rules."""

    def __init__(
        self,
        rules: list[CapabilityRule] | None = None,
        extra_rules: list[CapabilityRule] | None = None,
    ):
        self.rules = (rules if rules is not None else list(DEFAULT_RULES)) + (extra_rules or [])

    def detect(self, model: ModelInfo) -> set[Capability]:
        capabilities: set[Capability] = set()

        # Prefer capabilities Ollama itself reports, if present.
        raw_capabilities = model.raw.get("capabilities")
        if raw_capabilities:
            for cap in raw_capabilities:
                try:
                    capabilities.add(Capability(cap))
                except ValueError:
                    pass

        for rule in self.rules:
            if rule.matches(model):
                capabilities.add(rule.capability)

        if not capabilities:
            capabilities.add(Capability.TEXT)

        return capabilities

    def is_capable(self, model: ModelInfo, capability: Capability) -> bool:
        return capability in self.detect(model)

    @classmethod
    def from_config(cls, path: str | Path) -> "CapabilityDetector":
        """Load extra rules from YAML, e.g. to reuse an existing project's blocklist:

        rules:
          - capability: vision
            name_substrings: [vision, llava]
            family_names: [clip]
        """
        import yaml

        data = yaml.safe_load(Path(path).read_text()) or {}
        extra_rules = [
            CapabilityRule(
                capability=Capability(rule["capability"]),
                name_substrings=rule.get("name_substrings", []),
                family_names=rule.get("family_names", []),
            )
            for rule in data.get("rules", [])
        ]
        return cls(extra_rules=extra_rules)
