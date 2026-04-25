"""Minimal Redis connectivity smoke check.

Usage:
    uv run python scripts/check_redis.py

Exits 0 if Redis replies to PING, 1 otherwise.
"""

from __future__ import annotations

import sys

from infra.cache import ping_redis
from infra.cache.redis_client import close_redis_client
from shared.config.settings import settings


def main() -> int:
    print(f"Redis URL: {settings.redis_url}")

    ok = ping_redis()
    if ok:
        print("Redis PING: OK")
    else:
        print("Redis PING: FAIL")
        return 1

    close_redis_client()
    return 0


if __name__ == "__main__":
    sys.exit(main())
