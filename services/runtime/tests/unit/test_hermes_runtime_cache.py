"""Integration tests for HermesRuntime LLM cache behaviour."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from adapters.runtimes.hermes.runtime import HermesRuntime
from infra.cache.llm_cache import build_llm_cache_key, stable_json_dumps
from intelligence.runtime.hermes_client import HermesRuntimeError
from intelligence.tasks import build_analysis_task
from orchestrator.context.context_builder import AnalysisContext, ContextBuilder
from domains.research.models import AnalysisRequest


def _make_context(query: str = "Analyze BTC momentum", symbol: str = "BTC/USDT") -> AnalysisContext:
    return ContextBuilder().build(AnalysisRequest(query=query, symbol=symbol))


def _fake_hermes_response() -> dict:
    return {
        "status": "completed",
        "task_id": "task-001",
        "task_type": "analysis.generate",
        "provider": "gemini",
        "model": "google/gemini-3.1-pro-preview",
        "session_id": "sess-001",
        "trace_id": "trace-001",
        "idempotency_key": "idem-001",
        "reason": "test",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:05Z",
        "output": {
            "summary": "Fake summary",
            "thesis": "Fake thesis",
            "risks": ["risk 1"],
            "suggested_actions": ["action 1"],
        },
        "tool_trace": [],
        "memory_events": [],
        "delegation_trace": [],
        "usage": {"tokens": 100},
    }


# ── cache disabled — always calls provider ─────────────────────


def test_cache_disabled_calls_provider():
    """llm_cache_enabled=False must always call HermesClient.run_task."""
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings:
        mock_settings.llm_cache_enabled = False
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    mock_client.run_task.assert_called_once()
    assert result.summary == "Fake summary"
    assert "cache_hit" not in result.metadata


def test_cache_disabled_never_calls_redis():
    """llm_cache_enabled=False must not touch Redis at all."""
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response") as mock_get, \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response") as mock_set:

        mock_settings.llm_cache_enabled = False
        mock_settings.llm_cache_ttl_seconds = 900
        runtime.analyze(ctx)

    mock_get.assert_not_called()
    mock_set.assert_not_called()


# ── cache enabled + miss → calls provider + sets cache ────────


def test_cache_miss_calls_provider_and_sets_cache():
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=None) as mock_get, \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response") as mock_set:

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    mock_client.run_task.assert_called_once()
    mock_get.assert_called_once()
    mock_set.assert_called_once()
    assert result.summary == "Fake summary"
    assert "cache_hit" not in result.metadata


# ── cache enabled + hit → skips provider ──────────────────────


def test_cache_hit_skips_provider():
    ctx = _make_context()
    cached = _fake_hermes_response()

    mock_client = MagicMock()
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=cached) as mock_get:

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    mock_get.assert_called_once()
    mock_client.run_task.assert_not_called()
    assert result.summary == "Fake summary"
    assert result.thesis == "Fake thesis"
    assert result.risks == ["risk 1"]
    assert result.suggested_actions == ["action 1"]


def test_cache_hit_result_has_cache_hit_metadata():
    ctx = _make_context()
    cached = _fake_hermes_response()

    mock_client = MagicMock()
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=cached):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    assert result.metadata["cache_hit"] is True
    assert "cache_key" in result.metadata
    assert result.metadata["cache_key"].startswith("llm:cache:v1:")


def test_cache_hit_result_has_agent_action():
    ctx = _make_context()
    cached = _fake_hermes_response()

    mock_client = MagicMock()
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=cached):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    assert "agent_action" in result.metadata
    agent_action = result.metadata["agent_action"]
    assert agent_action["status"] == "completed"
    assert agent_action["task_type"] == "analysis.generate"


# ── same input → same cache key (determinism) ─────────────────


def test_same_input_produces_same_cache_key():
    ctx1 = _make_context("Analyze BTC", "BTC/USDT")
    ctx2 = _make_context("Analyze BTC", "BTC/USDT")
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    keys: list[str] = []

    def _capture_key(key, response, ttl_seconds=None):
        keys.append(key)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=None), \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response", side_effect=_capture_key):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        runtime.analyze(ctx1)
        runtime.analyze(ctx2)

    assert len(keys) == 2
    assert keys[0] == keys[1]


# ── Redis get error → fallback to provider ────────────────────


def test_redis_get_error_falls_back_to_provider():
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", side_effect=ConnectionError("boom")) as mock_get:

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    mock_get.assert_called_once()
    mock_client.run_task.assert_called_once()
    assert result.summary == "Fake summary"


# ── provider error → not cached ───────────────────────────────


def test_provider_error_not_cached():
    ctx = _make_context()

    mock_client = MagicMock()
    mock_client.run_task.side_effect = HermesRuntimeError("simulated failure", retryable=False)
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=None) as mock_get, \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response") as mock_set:

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        with pytest.raises(HermesRuntimeError):
            runtime.analyze(ctx)

    mock_get.assert_called_once()
    mock_client.run_task.assert_called_once()
    mock_set.assert_not_called()


# ── Redis set error → does not crash the caller ───────────────


def test_redis_set_error_does_not_crash():
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=None), \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response", side_effect=ConnectionError("redis down")):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    assert result.summary == "Fake summary"
    assert "cache_hit" not in result.metadata


# ── cache key excludes secrets ────────────────────────────────


def test_cache_key_never_contains_api_token():
    ctx = _make_context()
    request = build_analysis_task(ctx)
    payload = request.to_payload()
    # The request payload should not contain auth material
    assert "token" not in str(payload).lower() or "api_token" not in payload

    from adapters.runtimes.hermes.runtime import _build_cache_key_from_request
    key = _build_cache_key_from_request(request)
    assert key is not None
    assert "token" not in key.lower()
    assert "secret" not in key.lower()
    assert "api_key" not in key.lower()


# ── default settings keep behavior unchanged ──────────────────


def test_default_llm_cache_enabled_is_false():
    from shared.config.settings import settings
    assert settings.llm_cache_enabled is False


def test_default_runtime_does_not_use_cache():
    """With default settings (cache disabled), Runtime calls provider directly."""
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.get_cached_llm_response") as mock_get, \
         patch("adapters.runtimes.hermes.runtime.set_cached_llm_response") as mock_set:

        result = runtime.analyze(ctx)

    mock_get.assert_not_called()
    mock_set.assert_not_called()
    mock_client.run_task.assert_called_once()
    assert result.summary == "Fake summary"
    assert "cache_hit" not in result.metadata


# ── verify downstream workflow fields are preserved ───────────


def test_cache_hit_produces_runtime_metadata():
    ctx = _make_context()
    cached = _fake_hermes_response()

    mock_client = MagicMock()
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=cached):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    assert result.metadata["runtime_name"] == "agent_runtime"
    assert result.metadata["runtime_adapter"].startswith("adapters.runtimes.hermes.runtime")
    assert result.metadata["agent_action"]["provider"] == "gemini"
    assert result.metadata["agent_action"]["model"] == "google/gemini-3.1-pro-preview"


def test_live_response_does_not_have_cache_hit():
    ctx = _make_context()
    fake_response = _fake_hermes_response()

    mock_client = MagicMock()
    mock_client.run_task.return_value = fake_response
    runtime = HermesRuntime(client=mock_client)

    with patch("adapters.runtimes.hermes.runtime.settings") as mock_settings, \
         patch("adapters.runtimes.hermes.runtime.get_cached_llm_response", return_value=None):

        mock_settings.llm_cache_enabled = True
        mock_settings.llm_cache_ttl_seconds = 900
        mock_settings.llm_cache_namespace = "llm:cache:v1"

        result = runtime.analyze(ctx)

    assert "cache_hit" not in result.metadata
