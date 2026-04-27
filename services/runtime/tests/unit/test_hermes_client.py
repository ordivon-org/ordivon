import pytest

import httpx

from intelligence.runtime.hermes_client import HermesClient, HermesTaskError, HermesUnavailableError


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("boom", request=request, response=response)

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response=None, exc=None, *args, **kwargs):
        self.response = response
        self.exc = exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        if self.exc:
            raise self.exc
        return self.response

    def post(self, *args, **kwargs):
        if self.exc:
            raise self.exc
        return self.response


def test_hermes_client_health_check_handles_timeout(monkeypatch):
    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.httpx.Client",
        lambda *args, **kwargs: _FakeClient(exc=httpx.TimeoutException("timeout")),
    )
    client = HermesClient(base_url="http://test")

    with pytest.raises(HermesUnavailableError):
        client.health_check()


def test_hermes_client_run_task_returns_payload(monkeypatch):
    payload = {"status": "completed", "task_id": "task_1", "output": {"summary": "ok"}}
    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.httpx.Client",
        lambda *args, **kwargs: _FakeClient(response=_FakeResponse(200, payload)),
    )
    client = HermesClient(base_url="http://test")

    result = client.run_task("analysis.generate", {"task_id": "task_1"})
    assert result["task_id"] == "task_1"


def test_hermes_client_run_task_raises_on_non_success_payload(monkeypatch):
    payload = {"status": "failed", "error": "bad output"}
    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.httpx.Client",
        lambda *args, **kwargs: _FakeClient(response=_FakeResponse(200, payload)),
    )
    client = HermesClient(base_url="http://test")

    with pytest.raises(HermesTaskError):
        client.run_task("analysis.generate", {"task_id": "task_1"})


def test_hermes_client_run_task_retries_timeout(monkeypatch):
    calls = {"count": 0}

    class _RetryClient(_FakeClient):
        def post(self, *args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise httpx.TimeoutException("timeout")
            return _FakeResponse(200, {"status": "completed", "task_id": "task_1", "output": {"summary": "ok"}})

    monkeypatch.setattr("intelligence.runtime.hermes_client.httpx.Client", lambda *args, **kwargs: _RetryClient())
    monkeypatch.setattr("intelligence.runtime.hermes_client.time.sleep", lambda *args, **kwargs: None)
    client = HermesClient(base_url="http://test", max_retries=1, retry_backoff_seconds=0)

    result = client.run_task("analysis.generate", {"task_id": "task_1"})

    assert result["task_id"] == "task_1"
    assert calls["count"] == 2


def test_hermes_client_run_task_raises_detailed_server_error(monkeypatch):
    response = _FakeResponse(503, {"detail": "bridge unavailable"})
    monkeypatch.setattr(
        "intelligence.runtime.hermes_client.httpx.Client", lambda *args, **kwargs: _FakeClient(response=response)
    )
    client = HermesClient(base_url="http://test", max_retries=0)

    with pytest.raises(HermesTaskError, match="503"):
        client.run_task("analysis.generate", {"task_id": "task_1"})
