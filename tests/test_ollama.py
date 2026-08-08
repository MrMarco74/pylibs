import json

import responses

from pylibs.ollama import (
    Capability,
    CapabilityDetector,
    ModelInfo,
    OllamaClient,
    OllamaEndpoints,
    PurposeModelConfig,
)
from pylibs.ollama.models import list_models, show_model


def test_resolve_url_bypasses_proxy_for_vision():
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    assert client._resolve_url(requires_vision=False) == "http://llmproxy.example.com:11435"
    assert client._resolve_url(requires_vision=True) == "http://example-host:11434"


def test_resolve_url_respects_explicit_vision_base_url():
    client = OllamaClient(
        OllamaEndpoints(base_url="http://llmproxy.example.com:11435", vision_base_url="http://gpu-worker-2:9999")
    )
    assert client._resolve_url(requires_vision=True) == "http://gpu-worker-2:9999"


def test_resolve_url_leaves_non_proxy_port_untouched():
    client = OllamaClient(OllamaEndpoints(base_url="http://gpu-worker-2:11434"))
    assert client._resolve_url(requires_vision=True) == "http://gpu-worker-2:11434"


@responses.activate
def test_generate_non_streaming():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/generate",
        json={"response": "hello world"},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    result = client.generate("llama3", "hi")
    assert result == "hello world"


@responses.activate
def test_generate_passes_think_false_when_given():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/generate",
        json={"response": "hello world"},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    client.generate("llama3", "hi", think=False)

    sent_payload = json.loads(responses.calls[0].request.body)
    assert sent_payload["think"] is False


@responses.activate
def test_generate_omits_think_when_not_given():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/generate",
        json={"response": "hello world"},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    client.generate("llama3", "hi")

    sent_payload = json.loads(responses.calls[0].request.body)
    assert "think" not in sent_payload


@responses.activate
def test_generate_vision_uses_vision_port():
    responses.add(
        responses.POST,
        "http://example-host:11434/api/generate",
        json={"response": "a cat"},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    result = client.generate_vision("llava:13b", "what is this?", images=[b"fakebytes"])
    assert result == "a cat"


@responses.activate
def test_health_falls_back_to_api_tags():
    responses.add(responses.GET, "http://llmproxy.example.com:11435/health", status=500)
    responses.add(responses.GET, "http://llmproxy.example.com:11435/api/tags", json={"models": []}, status=200)

    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    assert client.health() is True


@responses.activate
def test_chat_passes_format_and_options_when_given():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/chat",
        json={"message": {"role": "assistant", "content": "ok"}},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))

    client.chat(
        model="llama3",
        messages=[{"role": "user", "content": "hi"}],
        format="json",
        options={"temperature": 0.2},
    )

    sent_payload = json.loads(responses.calls[0].request.body)
    assert sent_payload["format"] == "json"
    assert sent_payload["options"] == {"temperature": 0.2}


@responses.activate
def test_chat_omits_format_and_options_when_not_given():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/chat",
        json={"message": {"role": "assistant", "content": "ok"}},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))

    client.chat(model="llama3", messages=[{"role": "user", "content": "hi"}])

    sent_payload = json.loads(responses.calls[0].request.body)
    assert "format" not in sent_payload
    assert "options" not in sent_payload


def test_strip_reasoning_removes_think_blocks():
    text = "<think>internal monologue</think>final answer"
    assert OllamaClient.strip_reasoning(text) == "final answer"


@responses.activate
def test_list_models():
    responses.add(
        responses.GET,
        "http://llmproxy.example.com:11435/api/tags",
        json={"models": [{"name": "llama3:latest", "details": {"families": ["llama"]}}]},
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    models = list_models(client)
    assert models[0].name == "llama3:latest"
    assert models[0].families == ["llama"]


@responses.activate
def test_show_model_reads_context_length():
    responses.add(
        responses.POST,
        "http://llmproxy.example.com:11435/api/show",
        json={
            "details": {"families": ["llama"]},
            "model_info": {"llama.context_length": 8192},
        },
        status=200,
    )
    client = OllamaClient(OllamaEndpoints(base_url="http://llmproxy.example.com:11435"))
    info = show_model(client, "llama3:latest")
    assert info.context_length == 8192


def test_capability_detector_vision_by_name():
    detector = CapabilityDetector()
    model = ModelInfo(name="llava:13b")
    assert detector.is_capable(model, Capability.VISION)


def test_capability_detector_prefers_real_api_field():
    detector = CapabilityDetector()
    model = ModelInfo(name="mystery-model", raw={"capabilities": ["embedding"]})
    assert detector.is_capable(model, Capability.EMBEDDING)


def test_capability_detector_extra_rules_from_existing_blocklist():
    from pylibs.ollama.capabilities import CapabilityRule

    detector = CapabilityDetector(
        extra_rules=[CapabilityRule(Capability.CODE, name_substrings=["stresserbse"])]
    )
    model = ModelInfo(name="stresserbse-special")
    assert detector.is_capable(model, Capability.CODE)


def test_purpose_model_config_roundtrip(tmp_path):
    path = tmp_path / "purpose.yaml"
    config = PurposeModelConfig(purposes={"test": "codellama:latest"})
    config.save(path)

    loaded = PurposeModelConfig.load(path)
    assert loaded.get_model("test") == "codellama:latest"


def test_purpose_model_config_missing_purpose_uses_fallback():
    config = PurposeModelConfig()
    assert config.get_model("vision", fallback="none") == "none"
