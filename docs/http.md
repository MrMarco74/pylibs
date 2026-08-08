# pylibs.http

`requests.Session` mit Retry/Backoff, portiert aus einem internen Security-Scanning-Projekt.
Die dortige Bandbreiten-/Domain-Drosselung ist bewusst **nicht** eingebaut (das ist zu
projektspezifisch) — stattdessen ein optionaler `rate_limiter`-Hook.

```python
from pylibs.http import RetrySession, get_retry_session

session = RetrySession(
    total_retries=2,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),  # Default
    default_timeout=10.0,
)
resp = session.get("https://example.com/api")

# oder als Factory:
session = get_retry_session()
```

Mit Rate-Limiter (z.B. für Scanning-Workloads):

```python
import time

last_call = {"t": 0.0}

def rate_limiter():
    elapsed = time.monotonic() - last_call["t"]
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    last_call["t"] = time.monotonic()

session = RetrySession(rate_limiter=rate_limiter)
```

Benötigt die `http`-Extra (`pip install "pylibs[http]"`, installiert `requests`+`urllib3`).
