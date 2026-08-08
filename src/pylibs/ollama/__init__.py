from .capabilities import Capability, CapabilityDetector, CapabilityRule, DEFAULT_RULES
from .client import OllamaClient, OllamaEndpoints
from .models import ModelInfo, list_models, show_model
from .purpose_config import PurposeModelConfig

__all__ = [
    "OllamaClient",
    "OllamaEndpoints",
    "ModelInfo",
    "list_models",
    "show_model",
    "Capability",
    "CapabilityRule",
    "CapabilityDetector",
    "DEFAULT_RULES",
    "PurposeModelConfig",
]
