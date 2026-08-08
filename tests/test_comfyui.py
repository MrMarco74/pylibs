import responses

from pylibs.comfyui import ComfyUIClient, ComfyUIError


def test_queue_prompt_returns_prompt_id():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "http://gpu-worker-1:8188/prompt",
            json={"prompt_id": "abc123"},
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        result = client.queue_prompt({"1": {"class_type": "Test", "inputs": {}}})
        assert result == "abc123"


def test_wait_for_result_polls_until_outputs_present():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://gpu-worker-1:8188/history/abc123",
            json={},
            status=200,
        )
        rsps.add(
            responses.GET,
            "http://gpu-worker-1:8188/history/abc123",
            json={"abc123": {"outputs": {"7": {"images": [{"filename": "out.png"}]}}}},
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        result = client.wait_for_result("abc123", poll_interval=0)
        assert result["outputs"]["7"]["images"][0]["filename"] == "out.png"


def test_wait_for_result_raises_on_execution_error():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://gpu-worker-1:8188/history/abc123",
            json={"abc123": {"status": {"status_str": "error", "messages": [["execution_error", {"exception_message": "boom"}]]}}},
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        try:
            client.wait_for_result("abc123", poll_interval=0)
            assert False, "expected ComfyUIError"
        except ComfyUIError as exc:
            assert "boom" in str(exc)


def test_wait_for_result_raises_on_timeout():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://gpu-worker-1:8188/history/abc123",
            json={},
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        try:
            client.wait_for_result("abc123", timeout=0, poll_interval=0)
            assert False, "expected ComfyUIError"
        except ComfyUIError as exc:
            assert "timeout" in str(exc).lower()


def test_fetch_image_returns_bytes():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://gpu-worker-1:8188/view",
            body=b"PNGDATA",
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        result = client.fetch_image("out.png", "", "output")
        assert result == b"PNGDATA"


def test_queue_prompt_raises_comfyui_error_on_http_failure():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "http://gpu-worker-1:8188/prompt",
            json={"error": "invalid workflow"},
            status=400,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        try:
            client.queue_prompt({})
            assert False, "expected ComfyUIError"
        except ComfyUIError:
            pass


def test_upload_image_bytes_returns_server_filename():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "http://gpu-worker-1:8188/upload/image",
            json={"name": "uploaded123.png"},
            status=200,
        )
        client = ComfyUIClient(server_address="gpu-worker-1:8188")
        result = client.upload_image_bytes(b"PNGDATA", "raw.png")
        assert result == "uploaded123.png"
