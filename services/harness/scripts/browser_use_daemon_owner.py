#!/usr/bin/env python3
"""Own one Browser Use daemon outside Runtime Attempt cgroups.

The systemd unit owns daemon lifetime. Browserless remains the Chromium owner.
This wrapper resolves the configured Browserless endpoint, activates it when
needed, constructs the token-bearing CDP WebSocket only in process memory, and
execs the Browser Use daemon from the configured uv tool environment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from browserless_substrate import BrowserlessPool

DAEMON_NAME_RE = re.compile(r"^ordivon-bu-[0-9a-f]{24}$")
DEFAULT_CONFIG = Path("/etc/ordivon/browser-use-browserless.json")


def load_config(path: Path) -> tuple[dict, BrowserlessPool]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("kind") != "ordivon.browser-use-browserless-pool":
        raise RuntimeError("Browser Use config kind mismatch")
    pool = BrowserlessPool.from_dict(value.get("browserSubstrate"))
    return value, pool


def select_endpoint(pool: BrowserlessPool, endpoint_id: str):
    rows = [row for row in pool.endpoints if row.endpoint_id == endpoint_id]
    if len(rows) != 1:
        raise RuntimeError("endpoint-id must resolve exactly once")
    return rows[0]


def browser_use_python(executable: str) -> str:
    path = Path(executable)
    candidate = path.parent / "python"
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise RuntimeError("Browser Use Python executable is unavailable")
    return str(candidate)


def daemon_env(daemon_name: str, *, cdp_ws: str | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["BU_NAME"] = daemon_name
    env["BH_OPEN_LIVE_URL"] = "0"
    env["BH_TAB_MARKER"] = "0"
    if cdp_ws is not None:
        env["BU_CDP_WS"] = cdp_ws
    else:
        env.pop("BU_CDP_WS", None)
        env.pop("BU_CDP_URL", None)
    return env


def start(config: Path, daemon_name: str, endpoint_id: str) -> None:
    value, pool = load_config(config)
    endpoint = select_endpoint(pool, endpoint_id)
    lifecycle = endpoint.ensure_active(start_timeout_seconds=20.0)
    if lifecycle.get("healthy") is not True:
        raise RuntimeError(
            "Browserless on-demand activation failed: "
            + str(lifecycle.get("detail") or lifecycle.get("status") or "unhealthy")
        )
    executable = str(value.get("browserUseExecutable") or "")
    python = browser_use_python(executable)
    cdp_ws = endpoint.authenticated_operator_connection_endpoint(timeout_ms=300_000)
    os.execve(
        python,
        [python, "-m", "browser_harness.daemon"],
        daemon_env(daemon_name, cdp_ws=cdp_ws),
    )


def stop(config: Path, daemon_name: str) -> int:
    value, _pool = load_config(config)
    executable = str(value.get("browserUseExecutable") or "")
    if not executable.startswith("/") or not Path(executable).is_file():
        return 0
    proc = subprocess.run(
        [executable, "--reload"],
        text=True,
        capture_output=True,
        env=daemon_env(daemon_name),
        timeout=15,
        check=False,
    )
    # systemd will still converge the service process if Browser Use reports an
    # already-absent daemon. Stop must remain idempotent.
    return 0 if proc.returncode in {0, 1} else int(proc.returncode)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--daemon-name", required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--stop", action="store_true")
    return p


def main() -> int:
    a = parser().parse_args()
    if not DAEMON_NAME_RE.fullmatch(a.daemon_name):
        raise SystemExit("invalid Browser Use daemon name")
    if a.stop:
        return stop(a.config, a.daemon_name)
    start(a.config, a.daemon_name, a.endpoint_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
