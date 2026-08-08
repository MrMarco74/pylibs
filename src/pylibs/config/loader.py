"""Load/save config files (YAML or JSON, detected from the file extension).

Supports ``${VAR_NAME}`` interpolation from environment variables so that
config files can reference secrets/host-specific values without embedding
them in the file itself.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .dotdict import Config

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _interpolate(value: Any) -> Any:
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            name = match.group(1)
            return os.environ.get(name, match.group(0))

        return _ENV_VAR_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


def _read_raw(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        import yaml

        return yaml.safe_load(text) or {}
    if path.suffix == ".json":
        return json.loads(text) if text.strip() else {}
    raise ValueError(f"Unsupported config file extension: {path.suffix} ({path})")


def load_config(
    path: str | Path,
    defaults: dict | None = None,
    interpolate_env: bool = True,
) -> Config:
    """Load a YAML or JSON config file, merged over ``defaults``.

    If the file does not exist, ``defaults`` (or an empty dict) is returned
    as-is - callers decide whether to then call :func:`save_config` to
    persist a first-run default file.
    """
    path = Path(path)
    merged: dict = dict(defaults) if defaults else {}

    if path.exists():
        raw = _read_raw(path)
        merged.update(raw)

    if interpolate_env:
        merged = _interpolate(merged)

    return Config(merged)


def save_config(path: str | Path, data: dict | Config, mode: int = 0o600) -> None:
    """Save ``data`` as YAML or JSON (detected from extension), then chmod it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = data.to_dict() if isinstance(data, Config) else data

    if path.suffix in (".yaml", ".yml"):
        import yaml

        path.write_text(yaml.safe_dump(payload, sort_keys=False))
    elif path.suffix == ".json":
        path.write_text(json.dumps(payload, indent=2))
    else:
        raise ValueError(f"Unsupported config file extension: {path.suffix} ({path})")

    path.chmod(mode)
