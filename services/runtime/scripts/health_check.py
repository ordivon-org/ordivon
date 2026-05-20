#!/usr/bin/env python3
"""Ordivon infrastructure health check — run on schedule to detect service failures.

Usage:
    python3 scripts/health_check.py              # Check and print
    python3 scripts/health_check.py --alert       # Check and alert on failure
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

CHECKS = {
    "postgres": {
        "cmd": ["docker", "exec", "ordivon-pg", "pg_isready", "-U", "ordivon"],
        "timeout": 5,
    },
    "nats": {
        "url": "http://localhost:8222/healthz",
        "expect": "ok",
    },
    "temporal": {
        "host": "localhost",
        "port": 7233,
    },
    "openfga": {
        "url": "http://localhost:8081/healthz",
        "expect": "SERVING",
    },
    "minio": {
        "url": "http://localhost:9000/minio/health/live",
        "timeout": 5,
    },
}


def check_tcp(host: str, port: int, timeout: int = 3) -> bool:
    import socket

    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def check_http(url: str, expect: str = "", timeout: int = 5) -> bool:
    import urllib.request

    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        if expect:
            return expect in resp.read().decode()
        return resp.status == 200
    except Exception:
        return False


def check_docker_exec(cmd: list[str], timeout: int = 5) -> bool:
    import subprocess

    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return proc.returncode == 0
    except Exception:
        return False


def run_checks() -> dict:
    results = {}
    for name, cfg in CHECKS.items():
        if "cmd" in cfg:
            ok = check_docker_exec(cfg["cmd"], cfg.get("timeout", 5))
        elif "url" in cfg:
            ok = check_http(cfg["url"], cfg.get("expect", ""), cfg.get("timeout", 5))
        elif "host" in cfg:
            ok = check_tcp(cfg["host"], cfg["port"], cfg.get("timeout", 3))
        else:
            ok = False
        results[name] = ok

    all_ok = all(results.values())
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_healthy": all_ok,
        "services": results,
        "failed": [k for k, v in results.items() if not v],
    }


def main() -> int:
    alert = "--alert" in sys.argv
    result = run_checks()
    print(json.dumps(result, indent=2))

    if alert and not result["all_healthy"]:
        failed = result["failed"]
        print(f"\n⚠️  ALERT: {len(failed)} services unhealthy: {', '.join(failed)}", file=sys.stderr)
        # Could integrate with Slack/email/webhook here

    return 0 if result["all_healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
