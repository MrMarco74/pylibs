"""Generic ComfyUI HTTP client: queue a workflow, poll for completion, fetch
the resulting image. No workflow-specific or comic-specific knowledge lives
here — that belongs to the caller.
"""

from __future__ import annotations

import time

import requests


class ComfyUIError(Exception):
    pass


class ComfyUIClient:
    def __init__(
        self,
        server_address: str,
        timeout: float = 60.0,
        session: requests.Session | None = None,
    ):
        self.server_address = server_address
        self.timeout = timeout
        self.session = session or requests.Session()

    def _url(self, path: str) -> str:
        return f"http://{self.server_address}{path}"

    def queue_prompt(self, workflow: dict) -> str:
        response = self.session.post(
            self._url("/prompt"), json={"prompt": workflow}, timeout=self.timeout
        )
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /prompt failed ({response.status_code}): {response.text}")
        data = response.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyUIError(f"ComfyUI /prompt response missing prompt_id: {data}")
        return prompt_id

    def wait_for_result(self, prompt_id: str, timeout: float = 180, poll_interval: float = 2.0) -> dict:
        deadline = time.monotonic() + timeout
        while True:
            response = self.session.get(self._url(f"/history/{prompt_id}"), timeout=self.timeout)
            if response.status_code >= 400:
                raise ComfyUIError(f"ComfyUI /history failed ({response.status_code}): {response.text}")
            history = response.json()
            entry = history.get(prompt_id)
            if entry is not None:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    messages = status.get("messages", [])
                    detail = messages[0][1] if messages else status
                    raise ComfyUIError(f"ComfyUI execution error: {detail}")
                if entry.get("outputs"):
                    return entry
            if time.monotonic() >= deadline:
                raise ComfyUIError(f"Timeout waiting for ComfyUI prompt '{prompt_id}'")
            time.sleep(poll_interval)

    def fetch_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        response = self.session.get(
            self._url("/view"),
            params={"filename": filename, "subfolder": subfolder, "type": folder_type},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /view failed ({response.status_code}): {response.text}")
        return response.content

    def upload_image(self, image_path: str) -> str:
        """Uploads a local image to ComfyUI, returns the server-side filename.

        Not called by comicmakerng's Phase 6 flow; kept for parity with
        comic-generator's client and for future phases (compositing/re-render).
        """
        import os

        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f)}
            response = self.session.post(self._url("/upload/image"), files=files, timeout=self.timeout)
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /upload/image failed ({response.status_code}): {response.text}")
        return response.json()["name"]

    def upload_image_bytes(self, image_bytes: bytes, filename: str) -> str:
        """Like upload_image, but from in-memory bytes instead of a file on disk.

        Used when the caller builds an image in memory (e.g. a composited
        reference image) and never needs to write it to disk itself.
        """
        files = {"image": (filename, image_bytes)}
        response = self.session.post(self._url("/upload/image"), files=files, timeout=self.timeout)
        if response.status_code >= 400:
            raise ComfyUIError(f"ComfyUI /upload/image failed ({response.status_code}): {response.text}")
        return response.json()["name"]
