"""Secret loading that never reads from a project checkout.

Secrets live in ``~/.config/pylibs/secrets.yaml``, a single file namespaced by
name (e.g. ``hetzner``, ``ollama``), or in environment variables. This module
deliberately has no ``default=`` parameter that accepts a literal secret
value - the easy path is always the safe path.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SECRETS_PATH = Path.home() / ".config" / "pylibs" / "secrets.yaml"

_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
_SCAN_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".env", ".cfg", ".ini"}

_SECRET_KEY_HINTS = ("password", "passwd", "pwd", "secret", "token", "api_key", "apikey")

_LEAK_PATTERNS = [
    re.compile(
        r"""(?P<key>\b(?:password|passwd|pwd|secret|token|api_key|apikey)\b)["']?\s*[:=]\s*["']
            (?P<value>[^"'\s]{6,})["']""",
        re.IGNORECASE | re.VERBOSE,
    ),
]


def ensure_secrets_file(path: str | Path = DEFAULT_SECRETS_PATH) -> Path:
    """Create ``path`` (empty YAML doc) with chmod 600 if missing, else fix permissions."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text("{}\n")
        path.chmod(0o600)
        return path

    mode = path.stat().st_mode & 0o777
    if mode != 0o600:
        logger.warning("Fixing insecure permissions on %s (was %o, expected 600)", path, mode)
        path.chmod(0o600)
    return path


def load_secrets(name: str, search_paths: list[Path] | None = None) -> dict:
    """Load the secrets namespaced under ``name``.

    Resolution order (later wins):
    1. ``~/.config/pylibs/secrets.yaml`` (or the first existing file in
       ``search_paths``), looked up under the top-level key ``name``.
    2. Environment variables ``PYLIBS_SECRET_{NAME}_{KEY}`` (uppercased),
       which override individual keys from the file.
    """
    paths = search_paths or [DEFAULT_SECRETS_PATH]
    data: dict = {}

    for path in paths:
        path = Path(path)
        if path.exists():
            import yaml

            content = yaml.safe_load(path.read_text()) or {}
            data = dict(content.get(name, {}))
            break

    env_prefix = f"PYLIBS_SECRET_{name.upper()}_"
    for env_key, env_value in os.environ.items():
        if env_key.startswith(env_prefix):
            secret_key = env_key[len(env_prefix):].lower()
            data[secret_key] = env_value

    return data


def scan_for_leaked_secrets(root: str | Path, patterns: list[re.Pattern] | None = None) -> list[tuple[Path, int, str]]:
    """Best-effort scan of a project tree for hardcoded secret-like literals.

    Returns a list of ``(file, line_number, matched_key)`` tuples. This is a
    heuristic regression check, not a security guarantee - it looks for
    ``password: "..."``-style assignments with a plausible-length value.
    """
    root = Path(root)
    rules = patterns or _LEAK_PATTERNS
    findings: list[tuple[Path, int, str]] = []

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in _SCAN_EXTENSIONS:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            for rule in rules:
                match = rule.search(line)
                if match:
                    findings.append((path, lineno, match.group("key")))

    return findings


def _cli() -> None:
    import sys

    if len(sys.argv) < 3 or sys.argv[1] != "scan":
        print("Usage: python -m pylibs.config.secrets scan <root>")
        raise SystemExit(2)

    findings = scan_for_leaked_secrets(sys.argv[2])
    for path, lineno, key in findings:
        print(f"{path}:{lineno}: possible leaked secret ({key})")

    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    _cli()
