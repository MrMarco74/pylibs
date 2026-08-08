# pylibs.logging

Einheitliches Setup, das die verschiedenen über mehrere interne Projekte verstreuten
Logging-Ansätze (darunter roher `print()`-basierter Ad-hoc-Code) ablösen soll.

```python
from pylibs.logging import setup_logging, get_logger

setup_logging("myservice")  # Console + RotatingFileHandler (10MB/5 Backups), Secret-Redaction an
logger = get_logger(__name__)
logger.info("Service gestartet")
```

`log_dir` fällt zurück auf `LOG_DIR`-ENV, dann `~/.local/state/{service}/logs`, dann
`/tmp/{service}/logs` bei Permission-Fehlern. `level` fällt zurück auf `LOG_LEVEL`-ENV,
dann `INFO`.

## Secret-Redaction

Portiert aus einem internen Projekt (dem einzigen gefundenen Projekt mit
eingebauter Redaction). Standardmäßig aktiv (`redact_secrets=True`), redigiert
Bearer-Tokens und `password=`/`token=`/`api_key=`-Muster, bevor sie geschrieben werden:

```python
logger.info('calling API with token="abc123"')
# -> geschrieben wird: calling API with token=***REDACTED***
```

Eigene Muster ergänzen:

```python
from pylibs.logging import SecurityFilter
import re

setup_logging("myservice")  # Standard-Filter
# oder manuell mit Zusatzmustern:
extra = [re.compile(r"session_id=[a-f0-9]+")]
handler.addFilter(SecurityFilter(extra_patterns=extra))
```

## Async-sicheres Logging (QueueHandler/QueueListener)

Für FastAPI/asyncio-Kontexte, in denen synchrones File-I/O im Event-Loop vermieden
werden soll (wie in einem der internen Referenzprojekte):

```python
setup_logging("myservice", use_queue=True)
```

## Live-Log-Streaming über Redis

Für Multi-Worker-Setups wie Scan-Logs in einem internen Security-Scanner-Projekt,
bei denen mehrere Prozesse in denselben Log-Stream schreiben:

```python
from pylibs.logging import RedisLogHandler
import redis

r = redis.Redis()
handler = RedisLogHandler(r, key_prefix="logs:myservice", max_entries=200, ttl=3600)
setup_logging("myservice", extra_handlers=[handler])
```

Für projektspezifische Key-Schemata (z.B. `scan:logs:{target_id}`) einen
eigenen `key_fn` übergeben:

```python
handler = RedisLogHandler(r, key_fn=lambda record: f"scan:logs:{record.target_id}")
```

Benötigt die `redis`-Extra (`pip install "pylibs[redis]"`).
