# pylibs

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Language](https://img.shields.io/badge/language-Python-informational.svg) ![AI generated](https://img.shields.io/badge/AI-generated-8A2BE2.svg)

A small collection of Python utilities for recurring backend tasks: FTP/SFTP
upload, an Ollama client (with an automatic vision-call bypass for proxy
setups that don't forward multimodal requests), config load/save, and
logging helpers including a log-viewer toolkit.

These modules were extracted and generalized from patterns that kept getting
reimplemented, slightly differently, across several internal projects. See
[`docs/README.md`](docs/README.md) for background, concepts, and recipes, and
[`docs/html/index.html`](docs/html/index.html) for the generated API
reference (built via `pdoc`, see `scripts/build_docs.sh`).

## Installation

```bash
# local, editable, with the extras you need
pip install -e ".[ftp,ollama]"

# or as a git dependency in another project, pinned to a commit
pip install "pylibs[ftp,ollama] @ git+https://github.com/example/pylibs.git@<sha>"
```

## Modules

| Module | Purpose |
|---|---|
| `pylibs.config` | Config load/save (YAML/JSON), dot notation, safe secrets file |
| `pylibs.ftp` | FTP/FTPS/SFTP client with diff-sync upload |
| `pylibs.ollama` | Client for an Ollama (or Ollama-compatible proxy) server, incl. vision bypass and model capability detection |
| `pylibs.logging` | Unified logging setup, secret redaction, Redis live-log handler |
| `pylibs.log_viewer` | File tailing, SSE streaming helper, Redis log reader |
| `pylibs.http` | `requests.Session` with retry/backoff |
| `pylibs.netutil` | External IP lookup, hostname/DNS helpers |
| `pylibs.telegram` | Telegram bot client for status updates and media delivery |

## Quick usage

### FTP upload

```python
from pylibs.ftp import FtpClient, FtpConfig

config = FtpConfig(host="ftp.example.com", user="myuser", password="...")
with FtpClient(config) as client:
    client.upload_file("dist/index.html", "/public_html/index.html")
```

### Ollama client

```python
from pylibs.ollama import OllamaClient, OllamaEndpoints

client = OllamaClient(OllamaEndpoints(base_url="http://localhost:11434"))
text = client.generate("llama3", "Summarize this text: ...")
```

### Config load/save

```python
from pylibs.config import load_config, save_config

cfg = load_config("~/.config/myproject/config.yaml", defaults={"upload": {"method": "ssh"}})
print(cfg.get("upload.ssh.host"))
```

### Logging setup

```python
from pylibs.logging import setup_logging, get_logger

setup_logging("myservice")  # console + rotating file handler, secret redaction on
logger = get_logger(__name__)
logger.info("service started")
```

See the module table above for links to fuller documentation and more
recipes (directory sync, SSH/rsync upload, model capability detection,
purpose-based model selection, async-safe logging, Redis log streaming,
Telegram notifications, etc.) in [`docs/`](docs/).

## Tests

```bash
pip install -e ".[all,dev]"
pytest -m "not integration"
```

## License

MIT, see [LICENSE](LICENSE).
