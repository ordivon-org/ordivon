"""Unit tests for infra.cache.llm_cache — cache key stability and Redis wrappers."""

from __future__ import annotations

import hashlib
import json
from typing import Any, TypedDict, cast
from unittest.mock import MagicMock, patch

import pytest

from infra.cache.llm_cache import (
    CACHE_SCHEMA_VERSION,
    build_llm_cache_key,
    get_cached_llm_response,
    normalize_query,
    set_cached_llm_response,
    sha256_hex,
    stable_json_dumps,
)


class CacheKeyKwargs(TypedDict, total=False):
    """Typed kwargs for build_llm_cache_key — preserves per-key types through ** unpacking."""

    provider: str
    model: str
    task_type: str
    query: str
    symbol: str | None
    timeframe: str | None
    risk_mode: str | None
    market_signals: dict[str, Any] | None
    memory_lessons: list[Any] | None
    related_reviews: list[Any] | None
    active_policies: list[Any] | None
    portfolio_snapshot: dict[str, Any] | None
    prompt_version: str | None
    cache_schema_version: str


def _k(**overrides: object) -> CacheKeyKwargs:
    """Return typed CacheKeyKwargs from base + overrides — preserves type through ** unpacking."""
    # _BASE_KWARGS is structurally a CacheKeyKwargs; the cast through object
    # is needed because {**TypedDict, **dict} widens to dict in pyright.
    return cast(CacheKeyKwargs, cast(object, {**_BASE_KWARGS, **overrides}))


# Shared kwargs for cache key tests
_BASE_KWARGS: CacheKeyKwargs = cast(
    CacheKeyKwargs,
    cast(
        object,
        dict(
    provider="gemini",
    model="google/gemini-3.1-pro-preview",
    task_type="analysis.generate",
    query="Analyze BTC momentum",
    symbol="BTC/USDT",
    timeframe="1h",
    risk_mode="normal",
    market_signals={"rsi": 45, "macd": "bearish"},
    memory_lessons=["lesson a", "lesson b"],
    related_reviews=["review 1"],
    active_policies=["ForbiddenSymbolsPolicy", "TradingDisciplinePolicy"],
    portfolio_snapshot={"cash": 10000, "positions": []},
    prompt_version="v1",
    ),
),
)


# ── normalize_query ──────────────────────────────────────────


def test_normalize_query_lowercases():
    assert normalize_query("Analyze BTC momentum") == "analyze btc momentum"


def test_normalize_query_collapses_whitespace():
    assert normalize_query("  analyze   btc\nmomentum\tnow  ") == "analyze btc momentum now"


def test_normalize_query_single_word():
    assert normalize_query("BTC") == "btc"


def test_normalize_query_empty():
    assert normalize_query("") == ""


def test_normalize_query_only_whitespace():
    assert normalize_query("   \t\n  ") == ""


# ── stable_json_dumps ────────────────────────────────────────


def test_stable_json_dumps_deterministic():
    a = stable_json_dumps({"b": 1, "a": 2})
    b = stable_json_dumps({"a": 2, "b": 1})
    assert a == b


def test_stable_json_dumps_no_whitespace():
    result = stable_json_dumps({"x": 1})
    assert " " not in result


def test_stable_json_dumps_nested():
    payload = {"a": [{"z": 9, "y": 8}], "b": None}
    assert stable_json_dumps(payload) == '{"a":[{"y":8,"z":9}],"b":null}'


def test_stable_json_dumps_none_vs_string():
    a = stable_json_dumps({"v": None})
    b = stable_json_dumps({"v": "None"})
    assert a != b


# ── sha256_hex ───────────────────────────────────────────────


def test_sha256_hex_deterministic():
    assert sha256_hex("hello") == hashlib.sha256(b"hello").hexdigest()


def test_sha256_hex_length():
    assert len(sha256_hex("test")) == 64


def test_sha256_hex_differs():
    assert sha256_hex("a") != sha256_hex("b")


# ── build_llm_cache_key — identity / stability ───────────────


def test_cache_key_same_for_identical_inputs():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_BASE_KWARGS)
    assert k1 == k2


def test_cache_key_includes_namespace():
    key = build_llm_cache_key(**_BASE_KWARGS)
    assert key.startswith("llm:cache:v1:")


def test_cache_key_includes_provider_model_task_type():
    key = build_llm_cache_key(**_BASE_KWARGS)
    assert "gemini" in key
    assert "google/gemini-3.1-pro-preview" in key
    assert "analysis.generate" in key


def test_cache_key_query_whitespace_stable():
    k1 = build_llm_cache_key(**_k(query="Analyze BTC momentum"))
    k2 = build_llm_cache_key(**_k(query="  analyze   btc  momentum  "))
    assert k1 == k2


def test_cache_key_query_case_stable():
    k1 = build_llm_cache_key(**_k(query="ANALYZE BTC MOMENTUM"))
    k2 = build_llm_cache_key(**_k(query="analyze btc momentum"))
    assert k1 == k2


# ── build_llm_cache_key — field sensitivity ──────────────────


def test_cache_key_changes_on_provider():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(provider="openai"))
    assert k1 != k2


def test_cache_key_changes_on_model():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(model="gpt-4o"))
    assert k1 != k2


def test_cache_key_changes_on_task_type():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(task_type="summarize"))
    assert k1 != k2


def test_cache_key_changes_on_symbol():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(symbol="ETH/USDT"))
    assert k1 != k2


def test_cache_key_changes_on_timeframe():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(timeframe="4h"))
    assert k1 != k2


def test_cache_key_changes_on_risk_mode():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(risk_mode="conservative"))
    assert k1 != k2


def test_cache_key_changes_on_market_signals():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(market_signals={"rsi": 70}))
    assert k1 != k2


def test_cache_key_changes_on_memory_lessons():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(memory_lessons=["new lesson"]))
    assert k1 != k2


def test_cache_key_changes_on_related_reviews():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(related_reviews=["review 2"]))
    assert k1 != k2


def test_cache_key_changes_on_active_policies():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(active_policies=["OnlyOne"]))
    assert k1 != k2


def test_cache_key_changes_on_portfolio_snapshot():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(portfolio_snapshot={"cash": 5000, "positions": []}))
    assert k1 != k2


def test_cache_key_changes_on_prompt_version():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(prompt_version="v2"))
    assert k1 != k2


def test_cache_key_changes_on_cache_schema_version():
    k1 = build_llm_cache_key(**_BASE_KWARGS)
    k2 = build_llm_cache_key(**_k(cache_schema_version="2"))
    assert k1 != k2


# ── build_llm_cache_key — None stability ─────────────────────


def test_cache_key_none_symbol_stable():
    k1 = build_llm_cache_key(**_k(symbol=None))
    k2 = build_llm_cache_key(**_k(symbol=None))
    assert k1 == k2


def test_cache_key_none_timeframe_stable():
    k1 = build_llm_cache_key(**_k(timeframe=None))
    k2 = build_llm_cache_key(**_k(timeframe=None))
    assert k1 == k2


def test_cache_key_none_risk_mode_stable():
    k1 = build_llm_cache_key(**_k(risk_mode=None))
    k2 = build_llm_cache_key(**_k(risk_mode=None))
    assert k1 == k2


def test_cache_key_none_market_signals_stable():
    k1 = build_llm_cache_key(**_k(market_signals=None))
    k2 = build_llm_cache_key(**_k(market_signals=None))
    assert k1 == k2


def test_cache_key_none_memory_lessons_stable():
    k1 = build_llm_cache_key(**_k(memory_lessons=None))
    k2 = build_llm_cache_key(**_k(memory_lessons=None))
    assert k1 == k2


def test_cache_key_none_related_reviews_stable():
    k1 = build_llm_cache_key(**_k(related_reviews=None))
    k2 = build_llm_cache_key(**_k(related_reviews=None))
    assert k1 == k2


def test_cache_key_none_active_policies_stable():
    k1 = build_llm_cache_key(**_k(active_policies=None))
    k2 = build_llm_cache_key(**_k(active_policies=None))
    assert k1 == k2


def test_cache_key_none_portfolio_snapshot_stable():
    k1 = build_llm_cache_key(**_k(portfolio_snapshot=None))
    k2 = build_llm_cache_key(**_k(portfolio_snapshot=None))
    assert k1 == k2


def test_cache_key_none_prompt_version_stable():
    k1 = build_llm_cache_key(**_k(prompt_version=None))
    k2 = build_llm_cache_key(**_k(prompt_version=None))
    assert k1 == k2


def test_cache_key_none_distinguished_from_some():
    k_none = build_llm_cache_key(**_k(symbol=None))
    k_some = build_llm_cache_key(**_k(symbol="BTC/USDT"))
    assert k_none != k_some


# ── settings defaults ────────────────────────────────────────


def test_llm_cache_enabled_default_false():
    from shared.config.settings import settings
    assert settings.llm_cache_enabled is False


def test_llm_cache_ttl_default_900():
    from shared.config.settings import settings
    assert settings.llm_cache_ttl_seconds == 900


def test_llm_cache_namespace_default():
    from shared.config.settings import settings
    assert settings.llm_cache_namespace == "llm:cache:v1"


# ── Redis get_cached_llm_response ────────────────────────────


def test_get_cached_llm_response_returns_none_on_miss():
    mock_client = MagicMock()
    mock_client.get.return_value = None

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        assert get_cached_llm_response("some:key") is None


def test_get_cached_llm_response_returns_parsed_json_on_hit():
    payload = {"summary": "test", "thesis": "t"}
    mock_client = MagicMock()
    mock_client.get.return_value = json.dumps(payload)

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        assert get_cached_llm_response("some:key") == payload


def test_get_cached_llm_response_returns_none_on_redis_error():
    mock_client = MagicMock()
    mock_client.get.side_effect = ConnectionError("no redis")

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        assert get_cached_llm_response("some:key") is None


# ── Redis set_cached_llm_response ────────────────────────────


def test_set_cached_llm_response_sets_key_with_ttl():
    mock_client = MagicMock()

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        ok = set_cached_llm_response("my:key", {"x": 1}, ttl_seconds=300)
        assert ok is True
        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        assert args[0] == "my:key"
        assert args[1] == 300


def test_set_cached_llm_response_uses_default_ttl():
    mock_client = MagicMock()

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        ok = set_cached_llm_response("my:key", {"x": 1})
        assert ok is True
        ttl = mock_client.setex.call_args[0][1]
        assert ttl == 900


def test_set_cached_llm_response_returns_false_on_redis_error():
    mock_client = MagicMock()
    mock_client.setex.side_effect = ConnectionError("no redis")

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        assert set_cached_llm_response("my:key", {"x": 1}) is False


def test_set_cached_llm_response_uses_stable_json():
    mock_client = MagicMock()

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        set_cached_llm_response("k", {"b": 1, "a": 2})
        value = mock_client.setex.call_args[0][2]
        assert value == '{"a":2,"b":1}'


# ── Round-trip with mock ─────────────────────────────────────


def test_cache_key_round_trip_via_mock():
    key = build_llm_cache_key(**_BASE_KWARGS)
    payload = {"summary": "test summary", "thesis": "test thesis"}

    mock_client = MagicMock()
    mock_client.get.side_effect = lambda k: (
        json.dumps(payload) if k == key else None
    )

    with patch("infra.cache.llm_cache.get_redis_client", return_value=mock_client):
        set_cached_llm_response(key, payload)
        result = get_cached_llm_response(key)
        assert result == payload
