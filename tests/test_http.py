import responses

from pylibs.http import RetrySession, get_retry_session


@responses.activate
def test_retry_session_succeeds_after_transient_error():
    responses.add(responses.GET, "http://example.com/data", status=500)
    responses.add(responses.GET, "http://example.com/data", json={"ok": True}, status=200)

    session = RetrySession(total_retries=2, backoff_factor=0.01)
    resp = session.get("http://example.com/data")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@responses.activate
def test_retry_session_calls_rate_limiter_hook():
    responses.add(responses.GET, "http://example.com/data", json={}, status=200)

    calls = []
    session = RetrySession(rate_limiter=lambda: calls.append(1))
    session.get("http://example.com/data")

    assert calls == [1]


@responses.activate
def test_retry_session_applies_default_headers():
    responses.add(responses.GET, "http://example.com/data", json={}, status=200)

    session = RetrySession(default_headers={"X-Custom": "yes"})
    session.get("http://example.com/data")

    sent_request = responses.calls[0].request
    assert sent_request.headers["X-Custom"] == "yes"


def test_get_retry_session_factory():
    session = get_retry_session(total_retries=5)
    assert isinstance(session, RetrySession)
