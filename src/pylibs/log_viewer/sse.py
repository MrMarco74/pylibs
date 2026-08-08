"""Framework-agnostic Server-Sent-Events formatting - usable from Flask and FastAPI alike."""

from __future__ import annotations

from typing import Iterator


def format_sse(data: str, event: str | None = None) -> str:
    lines = [f"data: {chunk}" for chunk in data.splitlines() or [""]]
    if event:
        lines.insert(0, f"event: {event}")
    return "\n".join(lines) + "\n\n"


def sse_stream_from_iterator(lines: Iterator[str], event: str | None = None) -> Iterator[str]:
    for line in lines:
        yield format_sse(line.rstrip("\n"), event=event)
