# pylibs.log_viewer

Framework-agnostische Bausteine für Log-Viewer-UIs — die Kernlogik importiert weder
Flask noch FastAPI, damit sie in beiden nutzbar ist (die sechs bisherigen
Log-Viewer-Implementierungen über mehrere interne Projekte hinweg waren jeweils an
ein Framework gekoppelt).

## Datei-Tail

```python
from pylibs.log_viewer import tail_lines, follow_file

last_200 = tail_lines("myservice.log", n=200)

for line in follow_file("myservice.log", poll_interval=0.5):
    print(line, end="")
```

## SSE-Streaming (Flask-Beispiel, wie `/hub/logs/stream` in einem internen Projekt)

```python
from flask import Response
from pylibs.log_viewer import follow_file, sse_stream_from_iterator

@app.route("/logs/stream")
def stream_logs():
    lines = follow_file("myservice.log")
    return Response(sse_stream_from_iterator(lines), mimetype="text/event-stream")
```

## SSE-Streaming (FastAPI-Beispiel)

```python
from fastapi.responses import StreamingResponse
from pylibs.log_viewer import follow_file, sse_stream_from_iterator

@app.get("/logs/stream")
def stream_logs():
    lines = follow_file("myservice.log")
    return StreamingResponse(sse_stream_from_iterator(lines), media_type="text/event-stream")
```

## Redis-Log-Reader mit Filterung (wie `/logs/unified` in einem internen Projekt)

```python
from pylibs.log_viewer import read_redis_logs
import redis

r = redis.Redis()
entries = read_redis_logs(
    r, "logs:myservice", limit=100, level="ERROR", since=1700000000, tenant_id=42,
)
```

Benötigt für die Redis-Funktionen die `redis`-Extra (`pip install "pylibs[redis]"`).
