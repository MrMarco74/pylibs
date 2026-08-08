import socket
from unittest.mock import patch

from pylibs.netutil.external_ip import get_external_ip, get_hostname, resolve_ips


def test_get_external_ip_uses_first_working_service():
    with patch("pylibs.netutil.external_ip.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b"1.2.3.4"
        ip = get_external_ip(force_refresh=True, services=["https://fake-service.test"])
    assert ip == "1.2.3.4"


def test_get_external_ip_falls_back_to_socket_trick():
    with patch("pylibs.netutil.external_ip.urllib.request.urlopen", side_effect=OSError):
        with patch("pylibs.netutil.external_ip.socket.socket") as mock_socket_cls:
            mock_sock = mock_socket_cls.return_value.__enter__.return_value
            mock_sock.getsockname.return_value = ("10.0.0.5", 12345)
            ip = get_external_ip(force_refresh=True, services=["https://fake-service.test"])
    assert ip == "10.0.0.5"


def test_get_external_ip_caches_result():
    with patch("pylibs.netutil.external_ip.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b"9.9.9.9"
        first = get_external_ip(force_refresh=True, services=["https://fake-service.test"])
        # Second call should use the cache and not hit urlopen again.
        mock_urlopen.reset_mock()
        second = get_external_ip(force_refresh=False, services=["https://fake-service.test"])

    assert first == second == "9.9.9.9"
    mock_urlopen.assert_not_called()


def test_get_hostname_matches_socket():
    assert get_hostname() == socket.gethostname()


def test_resolve_ips_invalid_domain_returns_empty():
    assert resolve_ips("this-domain-does-not-exist.invalid") == []
