# pylibs.ollama

Client für einen Ollama-Proxy, z.B. `http://llmproxy.example.com:11435`, der Text/Chat an
mehrere GPU-Hosts (`gpu-worker-2:11434`/`gpu-worker-2:11438`) verteilt.

## Die wichtigste Eigenheit: kein Vision-Support über den Proxy

Manche Proxy-Setups leiten **keine** multimodalen (Bild-)Aufrufe weiter. Bestätigt in
einem internen Projekt:

```python
# use Ollama directly on port 11434 — llmproxy does not forward multimodal calls
ollama_port = 11434 if port == 11435 else port
```

`OllamaClient` löst das zentral: `generate_vision()` ruft automatisch die Vision-URL auf
(Port 11434 statt 11435), ohne dass der Aufrufer das selbst wissen muss.

```python
from pylibs.ollama import OllamaClient, OllamaEndpoints

client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))

text = client.generate("llama3", "Fasse diesen Text zusammen: ...")

answer = client.generate_vision(
    "llava:13b",
    "Was ist auf dem Bild zu sehen?",
    images=[open("photo.jpg", "rb").read()],
)
# -> ruft intern http://gpu-worker-1:11434/api/generate auf, nicht den Proxy-Port
```

Andere Proxy-Setups: Ports über `OLLAMA_PROXY_PORT`/`OLLAMA_VISION_PORT` env-Variablen
überschreibbar, oder `OllamaEndpoints(vision_base_url="http://gpu-worker-2:11434")` explizit setzen.

## Modelle auflisten und Capabilities erkennen

Kein bisheriges Projekt wertet die echten `families`/`capabilities`-Felder aus
`/api/show` aus — alle nutzen Substring-Heuristiken auf dem Modellnamen.
`pylibs.ollama` bevorzugt die echten API-Felder, fällt aber auf konfigurierbare
Regeln zurück:

```python
from pylibs.ollama import CapabilityDetector, Capability
from pylibs.ollama.models import list_models, show_model

models = list_models(client)                  # schnell, nur /api/tags
info = show_model(client, "llava:13b")         # /api/show, liest families/capabilities

detector = CapabilityDetector()
if detector.is_capable(info, Capability.VISION):
    ...
```

Bestehende Blocklisten/Präferenzlisten aus internen Projekten lassen sich 1:1 als YAML
übernehmen, ohne den pylibs-Code zu forken:

```yaml
# capability_rules.yaml
rules:
  - capability: code
    name_substrings: [coder, codestral, codellama, devstral, deepseek-coder]
  - capability: vision
    name_substrings: [vision, "-vl:", llava, moondream, minicpm-v]
```

```python
detector = CapabilityDetector.from_config("capability_rules.yaml")
```

## Modell-Auswahl pro Zweck (wie in einem internen Test-Automatisierungs-Tool)

```python
from pylibs.ollama import PurposeModelConfig

purpose_config = PurposeModelConfig.load("~/.config/myproject/models.yaml")
purpose_config.refresh_cache(client)  # aktualisiert cached_models via /api/tags

test_model = purpose_config.get_model("test", fallback="codellama:latest")
vision_model = purpose_config.get_model("vision", fallback="")

purpose_config.save("~/.config/myproject/models.yaml")
```

## Reasoning-Blöcke entfernen (DeepSeek-R1/Qwen3)

```python
raw = client.generate("deepseek-r1:14b", "Löse dieses Problem: ...")
clean = client.strip_reasoning(raw)  # entfernt <think>...</think>
```

Benötigt die `ollama`-Extra (`pip install "pylibs[ollama]"`, installiert `requests`).
