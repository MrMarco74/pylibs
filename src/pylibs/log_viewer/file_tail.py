"""Framework-agnostic file tailing, ported from an internal project's SSE log stream."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Iterator


def tail_lines(path: str | Path, n: int = 200) -> list[str]:
    """Return the last ``n`` lines of ``path`` (empty list if the file doesn't exist)."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", errors="ignore") as fh:
        return fh.readlines()[-n:]


def follow_file(
    path: str | Path,
    poll_interval: float = 0.5,
    stop: Callable[[], bool] | None = None,
) -> Iterator[str]:
    """Generator that yields new lines appended to ``path`` (tail -f style).

    Starts at end-of-file; does not replay existing content (use
    :func:`tail_lines` first if you want history). Stops when ``stop()``
    returns True, if provided.
    """
    path = Path(path)
    with path.open("r", errors="ignore") as fh:
        fh.seek(0, os.SEEK_END)
        while True:
            if stop and stop():
                return
            line = fh.readline()
            if line:
                yield line
            else:
                time.sleep(poll_interval)
