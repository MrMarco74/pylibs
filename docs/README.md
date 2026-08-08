# pylibs Dokumentation

Diese Seiten ergänzen die generierte API-Referenz unter [`html/index.html`](html/index.html)
(gebaut via `pdoc`, siehe `scripts/build_docs.sh`) um handgeschriebene Konzepte,
Rezepte und Migrationshinweise, die aus reinen Docstrings nicht gut hervorgehen.

## Module

| Modul | Doku | Zweck |
|---|---|---|
| `pylibs.config` | [config.md](config.md) | Config Load/Save (YAML/JSON), Secrets ohne Klartext im Repo |
| `pylibs.ftp` | [ftp.md](ftp.md) | FTP/FTPS/SFTP-Client mit Diff-Sync-Upload |
| `pylibs.ollama` | [ollama.md](ollama.md) | Client für einen Ollama-Proxy, Modell-Capabilities |
| `pylibs.logging` | [logging.md](logging.md) | Einheitliches Logging-Setup, Secret-Redaction, Redis-Live-Log |
| `pylibs.log_viewer` | [log_viewer.md](log_viewer.md) | Datei-Tail, SSE-Streaming, Redis-Log-Reader |
| `pylibs.http` | [http.md](http.md) | requests.Session mit Retry/Backoff |
| `pylibs.netutil` | [netutil.md](netutil.md) | Externe IP, Hostname/DNS-Helfer |
| `pylibs.telegram` | [telegram.md](telegram.md) | Telegram Bot Client für Status-Updates und Medienversand |

## Warum diese Bibliothek existiert

Eine Recherche über ~20 interne Projekte hat gezeigt, dass FTP-Upload zum Hosting-Webspace,
Ollama-Zugriff über einen internen LLM-Proxy, Config-Handling und Logging jeweils mehrfach
unabhängig voneinander implementiert wurden — mit unterschiedlichem Reifegrad und teils
unsicherer Credential-Verwaltung (siehe [config.md](config.md)).
`pylibs` bündelt die jeweils beste gefundene Implementierung als wiederverwendbares,
getestetes Package.

## Installation in einem anderen Projekt

```bash
pip install -e "/pfad/zu/pylibs[ftp,ollama]"
# oder als git-Dependency, auf einen Commit gepinnt:
pip install "pylibs[ftp,ollama] @ git+https://gitlab.example/pylibs.git@<sha>"
```

## Migrationsreihenfolge (Empfehlung)

1. **config + secrets** zuerst — dringend wegen eines Klartext-Passwort-Funds in
   mehreren internen Projekten (siehe [config.md](config.md)).
2. **netutil + http** — risikoarme reine Utility-Extraktion aus einem internen Projekt.
3. **logging** — schrittweise pro Projekt, altes Format via `fmt=` beibehalten.
4. **ftp** — Projekt für Projekt, beginnend mit dem einfachsten Fall.
5. **ollama** — zuletzt, da am meisten projektspezifische Logik (Zweck-Configs,
   Capability-Regeln) involviert ist.

Jede Migration ist ein eigener Task in den jeweiligen Projekten, nicht Teil dieses Repos.
