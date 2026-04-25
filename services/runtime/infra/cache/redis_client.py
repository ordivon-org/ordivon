from __future__ import annotations

import logging
from typing import Optional

import redis

from shared.config.settings import settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Return a shared Redis client instance, creating it on first call.

    Returns:
        A connected redis.Redis client.

    Raises:
        redis.exceptions.ConnectionError: If Redis is not reachable.
    """
    global _client
    if _client is not None:
        try:
            _client.ping()
            return _client
        except redis.exceptions.ConnectionError:
            _client = None

    _client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_keepalive=True,
        health_check_interval=30,
    )
    _client.ping()
    logger.info("Redis client connected to %s", settings.redis_url)
    return _client


def ping_redis() -> bool:
    """Check whether Redis is reachable.

    Returns:
        True if Redis responds to PING, False otherwise.
    """
    try:
        client = get_redis_client()
        return client.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        return False


def close_redis_client() -> None:
    """Close the shared Redis client and release its connection pool."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        finally:
            _client = None
            logger.info("Redis client closed")
