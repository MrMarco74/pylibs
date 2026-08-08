"""Diff-based directory sync upload, ported from an internal project's publisher module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .client import FtpClient


@dataclass
class SyncResult:
    uploaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)


def _remote_sizes(client: FtpClient, remote_dir: str) -> dict[str, int]:
    sizes: dict[str, int] = {}
    try:
        for entry in client.list_dir(remote_dir):
            if entry["type"] == "file" and entry["size"] is not None:
                sizes[entry["name"]] = entry["size"]
    except Exception:
        pass
    return sizes


def sync_upload(
    local_dir: str | Path,
    remote_root: str,
    client: FtpClient,
    delete_orphans: bool = False,
    dry_run: bool = False,
    cancel_flag: Callable[[], bool] | None = None,
) -> SyncResult:
    """Upload ``local_dir`` to ``remote_root``, skipping files whose size matches.

    Optionally deletes remote files that have no local counterpart. Set
    ``dry_run=True`` to only compute what would happen.
    """
    local_dir = Path(local_dir)
    result = SyncResult()

    if not dry_run:
        client.ensure_dir(remote_root)

    remote_sizes = _remote_sizes(client, remote_root)
    local_names = set()

    for item in sorted(local_dir.rglob("*")):
        if cancel_flag and cancel_flag():
            break
        if item.is_dir():
            continue

        rel = item.relative_to(local_dir).as_posix()
        local_names.add(rel)
        remote_path = f"{remote_root.rstrip('/')}/{rel}"

        local_size = item.stat().st_size
        remote_size = remote_sizes.get(rel)

        if remote_size == local_size:
            result.skipped.append(rel)
            continue

        if dry_run:
            result.uploaded.append(rel)
            continue

        try:
            client.upload_file(item, remote_path)
            result.uploaded.append(rel)
        except Exception as exc:
            result.errors.append((rel, str(exc)))

    if delete_orphans:
        for remote_name in remote_sizes:
            if remote_name not in local_names:
                remote_path = f"{remote_root.rstrip('/')}/{remote_name}"
                if dry_run:
                    result.deleted.append(remote_name)
                    continue
                try:
                    client.ftp.delete(remote_path)
                    result.deleted.append(remote_name)
                except Exception as exc:
                    result.errors.append((remote_name, str(exc)))

    return result
