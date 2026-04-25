from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import redis.exceptions

from infra.cache.redis_client import close_redis_client, get_redis_client, ping_redis


@pytest.fixture(autouse=True)
def _reset_global_client():
    """Ensure each test starts with no cached Redis client."""
    import infra.cache.redis_client as mod

    mod._client = None
    yield
    mod._client = None


def test_get_redis_client_returns_client_from_url():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_client

        client = get_redis_client()

        mock_redis_cls.from_url.assert_called_once()
        call_kwargs = mock_redis_cls.from_url.call_args.kwargs
        assert call_kwargs["decode_responses"] is True
        assert call_kwargs["socket_connect_timeout"] == 3
        assert client is mock_client


def test_get_redis_client_reuses_client_on_second_call():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_client

        a = get_redis_client()
        b = get_redis_client()

        assert a is b
        mock_redis_cls.from_url.assert_called_once()


def test_get_redis_client_reconnects_when_ping_fails():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        old_client = MagicMock()
        old_client.ping.side_effect = [True, redis.exceptions.ConnectionError("broken")]
        new_client = MagicMock()
        new_client.ping.return_value = True
        mock_redis_cls.from_url.side_effect = [old_client, new_client]

        a = get_redis_client()
        b = get_redis_client()

        assert a is not b
        assert b is new_client
        assert mock_redis_cls.from_url.call_count == 2


def test_ping_redis_returns_true():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_client

        assert ping_redis() is True


def test_ping_redis_returns_false_on_connection_error():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_redis_cls.from_url.side_effect = redis.exceptions.ConnectionError("no redis")

        assert ping_redis() is False


def test_close_redis_client_clears_client():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_client

        get_redis_client()
        close_redis_client()

        mock_client.close.assert_called_once()


def test_close_redis_client_handles_exception():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.close.side_effect = RuntimeError("boom")
        mock_redis_cls.from_url.return_value = mock_client

        get_redis_client()
        close_redis_client()

        mock_client.close.assert_called_once()


def test_get_redis_client_reuses_after_ping_ok():
    with patch("infra.cache.redis_client.redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_cls.from_url.return_value = mock_client

        get_redis_client()
        get_redis_client()
        get_redis_client()

        assert mock_redis_cls.from_url.call_count == 1
