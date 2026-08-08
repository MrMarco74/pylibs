from .client import FtpClient, FtpConfig
from .exceptions import FtpAuthError, FtpConnectionBlockedError, FtpError, FtpPermissionError
from .sync import SyncResult, sync_upload

__all__ = [
    "FtpClient",
    "FtpConfig",
    "FtpError",
    "FtpAuthError",
    "FtpPermissionError",
    "FtpConnectionBlockedError",
    "sync_upload",
    "SyncResult",
]

try:
    from .sftp_client import SftpClient, SftpConfig, upload_via_rsync  # noqa: F401

    __all__ += ["SftpClient", "SftpConfig", "upload_via_rsync"]
except ImportError:
    pass
