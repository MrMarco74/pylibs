# pylibs.ftp

FTP/FTPS-Client mit Diff-Sync-Upload, konsolidiert aus mehreren internen Projekten:
- ein internes FTP-Upload-Skript (TLS-Optionen, Fehlerbehandlung, SSH/rsync-Fallback)
- ein internes Publishing-Skript (Diff-Sync, verwaiste Dateien löschen)
- `domainstats/src/ftp_utils.py` / `ssh_utils.py` (Verzeichnis-Walk, Singleton-SFTP)

## Einzeldatei-Upload

```python
from pylibs.config import load_secrets
from pylibs.ftp import FtpClient, FtpConfig

config = FtpConfig(
    host="ftp.example.com",
    user="myuser",
    password=load_secrets("hetzner")["ftp_password"],
    use_tls=True,       # Default: True
    verify_ssl=True,    # Default: True - nur für Legacy-Server mit selbstsigniertem Zert. deaktivieren
)

with FtpClient(config) as client:
    client.upload_file("dist/index.html", "/public_html/index.html")
```

## Verzeichnis-Sync (Diff-basiert)

```python
from pylibs.ftp import sync_upload

with FtpClient(config) as client:
    result = sync_upload(
        local_dir="dist/",
        remote_root="/public_html/myblog",
        client=client,
        delete_orphans=True,   # löscht Remote-Dateien ohne lokales Gegenstück
        dry_run=False,
    )

print(f"{len(result.uploaded)} hochgeladen, {len(result.skipped)} übersprungen (identisch)")
print(f"{len(result.deleted)} gelöscht, {len(result.errors)} Fehler")
```

## Fehlerbehandlung

```python
from pylibs.ftp import FtpAuthError, FtpConnectionBlockedError, FtpPermissionError

try:
    with FtpClient(config) as client:
        ...
except FtpAuthError:
    ...  # 530 - falsches Passwort
except FtpPermissionError:
    ...  # 550 - keine Schreibrechte
except FtpConnectionBlockedError:
    ...  # Verbindung abgelehnt - oft eine IP-Sperre beim Hoster
```

## SSH/rsync statt FTP

Für Fälle wie Release-Uploads, wo SSH-Zugriff existiert, ist rsync über SSH schneller
und robuster als FTP:

```python
from pylibs.ftp import upload_via_rsync

upload_via_rsync(
    local_dir="dist/",
    remote="/var/www/releases/",
    host="releases.example.com",
    user="deploy",
)
```

Benötigt die `ftp`-Extra (`pip install "pylibs[ftp]"`, installiert `paramiko`) sowie
lokal installierte `rsync`/`ssh`-Kommandos.
