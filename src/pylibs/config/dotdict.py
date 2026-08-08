"""Dot-notation access on top of a plain nested dict."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class Config:
    """Dict-like container with dot-notation get/set, e.g. ``cfg.get("upload.ssh.host")``."""

    def __init__(self, data: dict | None = None):
        self._data: dict = data if data is not None else {}

    def get(self, key: str, default: Any = None) -> Any:
        node: Any = self._data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def to_dict(self) -> dict:
        return self._data

    def save(self, path: str | Path | None = None) -> None:
        from .loader import save_config

        if path is None:
            raise ValueError("path is required (Config does not remember its origin file)")
        save_config(Path(path), self._data)

    def __repr__(self) -> str:
        return f"Config({self._data!r})"
