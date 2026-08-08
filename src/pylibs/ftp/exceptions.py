class FtpError(Exception):
    """Base class for pylibs.ftp errors."""


class FtpAuthError(FtpError):
    """FTP login failed (550/530)."""


class FtpPermissionError(FtpError):
    """Server rejected an operation for permission reasons (550)."""


class FtpConnectionBlockedError(FtpError):
    """Connection was refused - often an IP block by the hoster (e.g. Hetzner)."""
