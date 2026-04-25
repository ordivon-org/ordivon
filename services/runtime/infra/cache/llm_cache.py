"""LLM response cache — pure functions and Redis wrappers.

This module provides cache key construction and Redis get/set operations.
It does NOT integrate with any business runtime (HermesRuntime, workflows, etc.).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from infra.cache.redis_client import get_redis_client
from shared.config.settings import settings

# Bump this when cache key schema changes in an incompatible way.
CACHE_SCHEMA_VERSION = "1"


def normalize_query(query: str) -> str:
    """Normalize a query string for cache key stability.

    - Lowercase
    - Collapse all whitespace to single spaces
    - Strip leading/trailing whitespace
    """
    collapsed = re.sub(r"\s+", " ", query.lower().strip())
    return collapsed


def stable_json_dumps(payload: dict[str, Any]) -> str:
    """Serialize a dict to a deterministic JSON string.

    Keys are sorted and no extra whitespace is emitted, so the output
    is byte-identical for semantically equal inputs.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: str) -> str:
    """Return the SHA-256 hex digest of *data*."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _hash_or_none(value: Any) -> str | None:
    """Return the SHA-256 hex hash of the JSON representation of *value*, or None.

    If *value* is None, return None (not the string "None").
    Otherwise, stable_json_dumps + sha256_hex.
    """
    if value is None:
        return None
    return sha256_hex(stable_json_dumps(value))


def build_llm_cache_key(
    *,
    provider: str,
    model: str,
    task_type: str,
    query: str,
    symbol: str | None = None,
    timeframe: str | None = None,
    risk_mode: str | None = None,
    market_signals: dict[str, Any] | None = None,
    memory_lessons: list[Any] | None = None,
    related_reviews: list[Any] | None = None,
    active_policies: list[Any] | None = None,
    portfolio_snapshot: dict[str, Any] | None = None,
    prompt_version: str | None = None,
    cache_schema_version: str = CACHE_SCHEMA_VERSION,
) -> str:
    """Build a deterministic LLM cache key.

    The key is composed of the namespace (from settings) and a SHA-256
    hex digest of all cache-relevant fields.

    None values are represented as JSON ``null`` so the key remains stable
    regardless of whether a field was explicitly None or omitted.
    """
    namespace = settings.llm_cache_namespace
    payload: dict[str, Any] = {
        "cache_schema_version": cache_schema_version,
        "provider": provider,
        "model": model,
        "task_type": task_type,
        "query": normalize_query(query),
        "symbol": symbol,
        "timeframe": timeframe,
        "risk_mode": risk_mode,
        "market_signals_hash": _hash_or_none(market_signals),
        "memory_lessons_hash": _hash_or_none(memory_lessons),
        "related_reviews_hash": _hash_or_none(related_reviews),
        "active_policies_hash": _hash_or_none(active_policies),
        "portfolio_snapshot_hash": _hash_or_none(portfolio_snapshot),
        "prompt_version": prompt_version,
    }
    digest = sha256_hex(stable_json_dumps(payload))
    return f"{namespace}:{provider}:{model}:{task_type}:{digest}"


# ---------------------------------------------------------------------------
# Redis wrappers (thin — no business logic)
# ---------------------------------------------------------------------------


def get_cached_llm_response(cache_key: str) -> dict[str, Any] | None:
    """Retrieve a cached LLM response from Redis.

    Returns None if the key is not found or Redis is unavailable.
    Does NOT raise — callers decide how to handle a miss.
    """
    try:
        client = get_redis_client()
        raw = client.get(cache_key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def set_cached_llm_response(
    cache_key: str,
    response: dict[str, Any],
    ttl_seconds: int | None = None,
) -> bool:
    """Store an LLM response in Redis with an optional TTL.

    Returns True on success, False on failure.
    """
    try:
        client = get_redis_client()
        ttl = ttl_seconds if ttl_seconds is not None else settings.llm_cache_ttl_seconds
        raw = stable_json_dumps(response)
        client.setex(cache_key, ttl, raw)
        return True
    except Exception:
        return False
