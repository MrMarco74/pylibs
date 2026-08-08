"""FTP/FTPS client with a safe-by-default TLS posture.

Consolidates the patterns found across several internal projects (including
domainstats/src/ftp_utils.py) into one client. Default is TLS required and
verified; plain FTP must be opted into explicitly via
``allow_plain_fallback``.
"""

from __future__ import annotations

import ftplib
import ssl
from dataclasses import dataclass
from pathlib import Path

from .exceptions import FtpAuthError, FtpConnectionBlockedError, FtpError, FtpPermissionError


@dataclass
class FtpConfig:
    host: str
    user: str
    password: str | None = None  # None -> caller resolved it via pylibs.config.load_secrets()
    port: int = 21
    use_tls: bool = True
    verify_ssl: bool = True
    ca_cert_path: str | None = None
    allow_plain_fallback: bool = False


class FtpClient:
    def __init__(self, config: FtpConfig):
        self.config = config
        self._ftp: ftplib.FTP | None = None

    def _build_ssl_context(self) -> ssl.SSLContext:
        context = ssl.create_default_context(cafile=self.config.ca_cert_path)
        if not self.config.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context

    def connect(self) -> None:
        cfg = self.config
        try:
            if cfg.use_tls:
                ftp = ftplib.FTP_TLS(context=self._build_ssl_context())
                ftp.connect(cfg.host, cfg.port)
                ftp.login(cfg.user, cfg.password)
                ftp.prot_p()
            else:
                ftp = ftplib.FTP()
                ftp.connect(cfg.host, cfg.port)
                ftp.login(cfg.user, cfg.password)
        except ftplib.error_perm as exc:
            code = str(exc)[:3]
            if code == "530":
                raise FtpAuthError(f"Authentication failed for {cfg.user}@{cfg.host}: {exc}") from exc
            if code == "550":
                raise FtpPermissionError(f"Permission denied on {cfg.host}: {exc}") from exc
            raise FtpError(str(exc)) from exc
        except ConnectionRefusedError as exc:
            if cfg.use_tls and cfg.allow_plain_fallback:
                fallback_cfg = FtpConfig(**{**cfg.__dict__, "use_tls": False})
                self.config = fallback_cfg
                self.connect()
                return
            raise FtpConnectionBlockedError(
                f"Connection to {cfg.host}:{cfg.port} refused (possible IP block): {exc}"
            ) from exc

        self._ftp = ftp

    @property
    def ftp(self) -> ftplib.FTP:
        if self._ftp is None:
            raise FtpError("Not connected - call connect() first")
        return self._ftp

    def ensure_dir(self, remote_dir: str) -> None:
        parts = [p for p in remote_dir.strip("/").split("/") if p]
        current = "/"
        for part in parts:
            current = current.rstrip("/") + "/" + part
            try:
                self.ftp.cwd(current)
            except ftplib.error_perm:
                self.ftp.mkd(current)
                self.ftp.cwd(current)
        self.ftp.cwd("/")

    def upload_file(self, local: str | Path, remote: str) -> None:
        local = Path(local)
        remote_dir = str(Path(remote).parent)
        if remote_dir not in (".", "/"):
            self.ensure_dir(remote_dir)
        with local.open("rb") as fh:
            self.ftp.storbinary(f"STOR {remote}", fh)

    def upload_dir(self, local_dir: str | Path, remote_dir: str, recursive: bool = True) -> None:
        local_dir = Path(local_dir)
        self.ensure_dir(remote_dir)
        for item in sorted(local_dir.iterdir()):
            remote_path = f"{remote_dir.rstrip('/')}/{item.name}"
            if item.is_dir():
                if recursive:
                    self.upload_dir(item, remote_path, recursive=True)
            else:
                self.upload_file(item, remote_path)

    def list_dir(self, remote_dir: str) -> list[dict]:
        entries = []
        for name, facts in self.ftp.mlsd(remote_dir):
            if name in (".", ".."):
                continue
            entries.append(
                {
                    "name": name,
                    "type": facts.get("type"),
                    "size": int(facts["size"]) if "size" in facts else None,
                    "modify": facts.get("modify"),
                }
            )
        return entries

    def close(self) -> None:
        if self._ftp is not None:
            try:
                self._ftp.quit()
            except Exception:
                self._ftp.close()
            self._ftp = None

    def __enter__(self) -> "FtpClient":
        self.connect()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
