"""requests.Session with retry/backoff, ported from an internal project's
throttled HTTP client.

Bandwidth/domain rate limiting from the original is intentionally left out of
the default path (that's specific to that project's scanning use case) - callers who
need it can pass a ``rate_limiter`` hook instead.
"""

from __future__ import annotations

from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RetrySession(requests.Session):
    def __init__(
        self,
        total_retries: int = 2,
        backoff_factor: float = 0.5,
        status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
        rate_limiter: Callable[[], None] | None = None,
        default_timeout: float = 10.0,
        default_headers: dict | None = None,
    ):
        super().__init__()
        self.rate_limiter = rate_limiter
        self.default_timeout = default_timeout

        retry = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=None,  # retry on all methods, matching the internal project this was ported from
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

        if default_headers:
            self.headers.update(default_headers)

    def request(self, method, url, **kwargs):
        if self.rate_limiter:
            self.rate_limiter()
        kwargs.setdefault("timeout", self.default_timeout)
        return super().request(method, url, **kwargs)


def get_retry_session(**kwargs) -> RetrySession:
    return RetrySession(**kwargs)
