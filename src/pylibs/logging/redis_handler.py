"""Redis-backed ring-buffer log handler, generalized from an internal project's redis logger.

Requires the ``redis`` extra.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Callable


class RedisLogHandler(logging.Handler):
    """Pushes log records as JSON into a Redis list, trimmed to ``max_entries`` with a TTL.

    Unlike the hardcoded ``scan:logs:{target_id}`` scheme it was generalized from, the Redis key is
    derived per-record via ``key_fn`` (default: constant ``key_prefix``), so
    each project keeps its own key layout without forking the handler.
    """

    def __init__(
        self,
        redis_client,
        key_prefix: str = "logs",
        key_fn: Callable[[logging.LogRecord], str] | None = None,
        ttl: int = 3600,
        max_entries: int = 200,
    ):
        super().__init__()
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.key_fn = key_fn or (lambda record: key_prefix)
        self.ttl = ttl
        self.max_entries = max_entries
        self._emitting = False  # re-entry guard against redis errors recursing into logging

    def emit(self, record: logging.LogRecord) -> None:
        if self._emitting:
            return

        self._emitting = True
        try:
            key = self.key_fn(record)
            payload = json.dumps(
                {
                    "ts": record.created if hasattr(record, "created") else time.time(),
                    "level": record.levelname,
                    "logger": record.name,
                    "msg": self.format(record),
                }
            )
            pipe = self.redis_client.pipeline()
            pipe.rpush(key, payload)
            pipe.ltrim(key, -self.max_entries, -1)
            pipe.expire(key, self.ttl)
            pipe.execute()
        except Exception:
            pass  # never let logging infrastructure raise into the caller
        finally:
            self._emitting = False
