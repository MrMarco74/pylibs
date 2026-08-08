"""External IP / hostname helpers, ported from yads/yads/core/redis_logger.py."""

from __future__ import annotations

import socket
import threading
import time
import urllib.request

_DEFAULT_SERVICES = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
]

_cache_lock = threading.Lock()
_cached_ip: str | None = None
_cached_at: float = 0.0


def get_external_ip(
    force_refresh: bool = False,
    cache_ttl: int = 300,
    services: list[str] | None = None,
) -> str | None:
    """Return this machine's external IP, trying several services then falling back.

    Fallback order: configured HTTP services -> outbound UDP socket trick
    (connects to 8.8.8.8, reads the local address, sends nothing) ->
    hostname resolution. Result is cached for ``cache_ttl`` seconds.
    """
    global _cached_ip, _cached_at

    with _cache_lock:
        if not force_refresh and _cached_ip and (time.time() - _cached_at) < cache_ttl:
            return _cached_ip

        for url in services or _DEFAULT_SERVICES:
            try:
                with urllib.request.urlopen(url, timeout=3) as resp:
                    ip = resp.read().decode().strip()
                    if ip:
                        _cached_ip = ip
                        _cached_at = time.time()
                        return ip
            except OSError:
                continue

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                ip = sock.getsockname()[0]
                _cached_ip = ip
                _cached_at = time.time()
                return ip
        except OSError:
            pass

        try:
            ip = socket.gethostbyname(socket.gethostname())
            _cached_ip = ip
            _cached_at = time.time()
            return ip
        except OSError:
            return None


def get_hostname() -> str:
    return socket.gethostname()


def resolve_ips(domain: str) -> list[str]:
    try:
        return list({info[4][0] for info in socket.getaddrinfo(domain, None)})
    except socket.gaierror:
        return []
