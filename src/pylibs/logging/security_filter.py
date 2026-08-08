"""Secret redaction filter, ported from an internal project's logging config
(the only surveyed project with built-in log redaction).
"""

from __future__ import annotations

import logging
import re

_DEFAULT_PATTERNS = [
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"""((?:token|password|passwd|api_key|apikey)\s*=\s*)["']?[^"'\s&]+["']?""", re.IGNORECASE),
]

_REDACTED = r"\1***REDACTED***"


class SecurityFilter(logging.Filter):
    """Redacts bearer tokens and key=value secrets from log messages before they are written."""

    def __init__(self, extra_patterns: list[re.Pattern] | None = None):
        super().__init__()
        self.patterns = list(_DEFAULT_PATTERNS) + (extra_patterns or [])

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = message
        for pattern in self.patterns:
            redacted = pattern.sub(_REDACTED, redacted)

        if redacted != message:
            record.msg = redacted
            record.args = ()

        return True
