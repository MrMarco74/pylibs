"""Generalizes the filtering logic from an internal project's /logs/unified
endpoint to any Redis list of JSON log entries.
"""

from __future__ import annotations

import json


def read_redis_logs(
    redis_client,
    key: str,
    limit: int = 200,
    level: str | None = None,
    since: float | None = None,
    tenant_id: "int | str | None" = None,
) -> list[dict]:
    """Read up to ``limit`` most recent entries from a Redis list of JSON log lines.

    Filters by ``level`` (exact match on the ``level`` field), ``since``
    (unix timestamp, entries with ``ts`` >= since), and ``tenant_id`` (exact
    match on a ``tenant_id`` field, if present in the entry). Malformed JSON
    lines are skipped.
    """
    raw_entries = redis_client.lrange(key, -limit, -1)

    entries = []
    for raw in raw_entries:
        try:
            entry = json.loads(raw)
        except (TypeError, ValueError):
            continue

        if level and entry.get("level") != level:
            continue
        if since is not None and entry.get("ts", 0) < since:
            continue
        if tenant_id is not None and entry.get("tenant_id") != tenant_id:
            continue

        entries.append(entry)

    return entries
