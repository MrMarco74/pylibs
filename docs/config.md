# pylibs.config

Generisches Config Load/Save (YAML und JSON, Format wird aus der Dateiendung erkannt)
mit `${VAR_NAME}`-Interpolation aus Umgebungsvariablen und Dot-Notation-Zugriff.

```python
from pylibs.config import load_config, save_config

cfg = load_config("~/.config/myproject/config.yaml", defaults={"upload": {"method": "ssh"}})
print(cfg.get("upload.ssh.host"))

save_config("~/.config/myproject/config.yaml", cfg)
```

## Sicherheitsbefund, der dieses Modul motiviert hat

In mehreren internen Projekten lag ein identisches Klartext-FTP-Passwort für denselben
Hosting-Account (`ftp.example.com`, User `myuser`) hartkodiert im Repo. Mindestens vier
Projekte sprachen denselben Account mit uneinheitlicher Credential-Verwaltung an (ENV,
ENV+DB, JSON-Default, YAML-Klartext). **So nicht mehr.**

## Secrets richtig laden

```python
from pylibs.config import ensure_secrets_file, load_secrets

# einmalig: Datei anlegen (chmod 600), dann manuell befüllen
ensure_secrets_file()  # -> ~/.config/pylibs/secrets.yaml

# ~/.config/pylibs/secrets.yaml:
#   hetzner:
#     ftp_password: "..."

secrets = load_secrets("hetzner")
ftp_password = secrets["ftp_password"]
```

Auflösungsreihenfolge (letzter gewinnt):
1. `~/.config/pylibs/secrets.yaml`, Key `hetzner` (oder eigener Namespace)
2. Umgebungsvariable `PYLIBS_SECRET_HETZNER_FTP_PASSWORD` (überschreibt die Datei)

`load_secrets()` liest **nie** aus dem Projektverzeichnis. Es gibt bewusst keinen
`default=`-Parameter, der einen echten Wert akzeptiert — der sichere Weg ist der
bequeme Weg.

## Gegen erneutes Secret-Leaking

- `.gitignore`-Vorlage für Projekte, die pylibs nutzen:
  ```
  secrets.yaml
  *.secrets.yaml
  .env
  ```
- Regressions-Check als CLI:
  ```bash
  python -m pylibs.config.secrets scan .
  ```
  Findet `password=`/`token=`/`api_key=`-artige Klartext-Zuweisungen (Regex-Heuristik,
  keine Garantie) und gibt Exit-Code 1 bei Funden zurück — eignet sich als
  pre-commit-Hook:
  ```yaml
  # .pre-commit-config.yaml
  - repo: local
    hooks:
      - id: pylibs-secret-scan
        name: pylibs secret scan
        entry: python -m pylibs.config.secrets scan .
        language: system
        pass_filenames: false
  ```

## Hetzner-Rezept

```python
from pylibs.config import load_secrets
from pylibs.ftp import FtpClient, FtpConfig

config = FtpConfig(
    host="ftp.example.com",
    user="myuser",
    password=load_secrets("hetzner")["ftp_password"],
)
with FtpClient(config) as client:
    client.upload_file("index.html", "/index.html")
```
