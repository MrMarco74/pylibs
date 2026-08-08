"""Unified logging setup, merging a simple stdlib-based setup (as used in
several internal projects) with a per-service RotatingFileHandler approach,
plus an optional QueueHandler/QueueListener path for async-safe logging.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import queue
import sys
from pathlib import Path

from .security_filter import SecurityFilter

DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"


def _resolve_log_dir(service_name: str, log_dir: str | Path | None) -> Path:
    if log_dir is not None:
        return Path(log_dir)

    env_dir = os.environ.get("LOG_DIR")
    if env_dir:
        return Path(env_dir)

    candidate = Path.home() / ".local" / "state" / service_name / "logs"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except OSError:
        fallback = Path("/tmp") / service_name / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def setup_logging(
    service_name: str,
    log_dir: str | Path | None = None,
    level: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console: bool = True,
    fmt: str = DEFAULT_FORMAT,
    use_queue: bool = False,
    redact_secrets: bool = True,
    extra_handlers: list[logging.Handler] | None = None,
) -> logging.Logger:
    """Configure the root logger for ``service_name`` and return it.

    ``level`` falls back to the ``LOG_LEVEL`` env var, then INFO. Log files
    are written to ``log_dir`` (or ``LOG_DIR`` env var, or
    ``~/.local/state/{service_name}/logs``, falling back to ``/tmp`` on
    permission errors).
    """
    resolved_level = (level or os.environ.get("LOG_LEVEL") or "INFO").upper()
    resolved_dir = _resolve_log_dir(service_name, log_dir)

    formatter = logging.Formatter(fmt)

    handlers: list[logging.Handler] = []

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        resolved_dir / f"{service_name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

    if extra_handlers:
        for handler in extra_handlers:
            handler.setFormatter(formatter)
        handlers.extend(extra_handlers)

    if redact_secrets:
        security_filter = SecurityFilter()
        for handler in handlers:
            handler.addFilter(security_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)
    # Avoid duplicate handlers if setup_logging is called more than once.
    root_logger.handlers.clear()

    if use_queue:
        log_queue: queue.SimpleQueue = queue.SimpleQueue()
        queue_handler = logging.handlers.QueueHandler(log_queue)
        root_logger.addHandler(queue_handler)

        listener = logging.handlers.QueueListener(log_queue, *handlers, respect_handler_level=True)
        listener.start()
        root_logger._pylibs_queue_listener = listener  # keep a reference so it isn't GC'd
    else:
        for handler in handlers:
            root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
