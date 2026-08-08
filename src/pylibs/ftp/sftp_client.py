"""SFTP/SSH client, ported from domainstats/src/ssh_utils.py and another
internal project's rsync-first upload path.

Requires the ``ftp`` extra (paramiko).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SftpConfig:
    host: str
    user: str
    port: int = 22
    key_file: str | None = None  # None -> autodetect ~/.ssh/id_ed25519, id_rsa, id_ecdsa
    password: str | None = None
    passphrase: str | None = None


def _autodetect_key_file() -> str | None:
    for name in ("id_ed25519", "id_rsa", "id_ecdsa"):
        candidate = Path.home() / ".ssh" / name
        if candidate.exists():
            return str(candidate)
    return None


class SftpClient:
    """Singleton-per-instance SFTP client (mirrors domainstats' get_ssh_client())."""

    def __init__(self, config: SftpConfig):
        self.config = config
        self._client = None
        self._sftp = None

    def get_client(self):
        if self._client is None:
            import paramiko

            key_file = self.config.key_file or _autodetect_key_file()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.config.host,
                port=self.config.port,
                username=self.config.user,
                key_filename=key_file,
                password=self.config.password,
                passphrase=self.config.passphrase,
            )
            self._client = client
        return self._client

    def get_sftp(self):
        if self._sftp is None:
            self._sftp = self.get_client().open_sftp()
        return self._sftp

    def upload_file(self, local: str | Path, remote: str) -> None:
        self.get_sftp().put(str(local), remote)

    def download_file(self, remote: str, local: str | Path) -> None:
        self.get_sftp().get(remote, str(local))

    def close(self) -> None:
        if self._sftp is not None:
            self._sftp.close()
            self._sftp = None
        if self._client is not None:
            self._client.close()
            self._client = None


def upload_via_rsync(
    local_dir: str | Path,
    remote: str,
    host: str,
    user: str,
    identity_file: str | None = None,
    port: int = 22,
    delete: bool = False,
) -> subprocess.CompletedProcess:
    """rsync-over-ssh upload, mirroring the SSH path used in an internal FTP-upload script."""
    identity_file = identity_file or _autodetect_key_file()
    ssh_cmd = f"ssh -p {port}"
    if identity_file:
        ssh_cmd += f" -i {identity_file}"

    args = ["rsync", "-az", "-e", ssh_cmd]
    if delete:
        args.append("--delete")
    args.append(f"{Path(local_dir)}/")
    args.append(f"{user}@{host}:{remote}")

    return subprocess.run(args, capture_output=True, text=True, check=True)
