"""Local provider availability census for web/GUI routing.

Advisory physical observations only: they do not grant provider permission,
make domain decisions, or infer state from provider documentation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

BROWSER_USE_CONFIG = Path("/etc/ordivon/browser-use-browserless.json")


BROWSER_USE_ACTION = Path(
    "/opt/ordivon/agent-automation/current/scripts/browser_use_browserless.py"
)


PLAYWRIGHT_BINDING = Path("/root/tools/bin/playwright-cli-binding")


def _browser_use_health() -> dict[str, Any]:
    if not BROWSER_USE_CONFIG.is_file() or not BROWSER_USE_ACTION.is_file():
        return {
            "state": "unavailable",
            "reason": "isolated Browser Use config/action adapter absent",
        }
    try:
        value = json.loads(BROWSER_USE_CONFIG.read_text(encoding="utf-8"))
        endpoints = value.get("browserSubstrate", {}).get("endpoints", [])
        ids = [row.get("id") for row in endpoints if isinstance(row, dict)]
        if not ids or any(not str(item).startswith("browser-agent-") for item in ids):
            return {
                "state": "unavailable",
                "reason": "Browser Use pool is not isolated browser-agent-*",
            }
    except Exception as exc:  # malformed config is unavailable, not a reason to guess
        return {
            "state": "unavailable",
            "reason": f"Browser Use config invalid: {type(exc).__name__}",
        }
    try:
        proc = subprocess.run(
            [
                "/usr/bin/python3",
                str(BROWSER_USE_ACTION),
                "--session-id",
                "route-census",
                "doctor",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if proc.returncode != 0:
            return {"state": "unavailable", "reason": "Browser Use doctor failed"}
        lines = [
            line for line in proc.stdout.splitlines() if line.strip().startswith("{")
        ]
        doctor = json.loads(lines[-1]) if lines else {}
        healthy = bool(doctor.get("browserlessHealth", {}).get("healthy"))
        if not healthy:
            return {
                "state": "unavailable",
                "reason": "isolated Browserless lane unhealthy",
            }
        return {
            "state": "available",
            "reason": "isolated Browser Use lane healthy",
            "actionAdapter": str(BROWSER_USE_ACTION),
            "endpointId": doctor.get("browserlessEndpointId"),
            "credentialsExposed": bool(doctor.get("credentialsExposed", True)),
            "arbitraryPythonExposed": bool(doctor.get("arbitraryPythonExposed", True)),
        }
    except Exception as exc:
        return {
            "state": "unavailable",
            "reason": f"Browser Use doctor unavailable: {type(exc).__name__}",
        }


def _playwright_health() -> dict[str, Any]:
    if not PLAYWRIGHT_BINDING.is_file() or not os.access(PLAYWRIGHT_BINDING, os.X_OK):
        return {
            "state": "unavailable",
            "reason": "Workstation Playwright CLI binding is absent",
        }
    try:
        proc = subprocess.run(
            [str(PLAYWRIGHT_BINDING), "profile"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "state": "unavailable",
                "reason": "Workstation Playwright CLI binding failed",
            }
        value = json.loads(proc.stdout)
        prefix = value.get("commandPrefix")
        environment = value.get("environment")
        identity = value.get("identity")
        if (
            value.get("state") != "AVAILABLE"
            or not isinstance(prefix, list)
            or len(prefix) != 2
            or not all(isinstance(item, str) and item for item in prefix)
            or not isinstance(environment, dict)
            or not environment.get("PLAYWRIGHT_BROWSERS_PATH")
            or not isinstance(identity, dict)
            or not identity.get("browserExecutableDigest")
            or not identity.get("cliEntrypointDigest")
        ):
            return {
                "state": "unavailable",
                "reason": "Workstation Playwright CLI binding is incomplete",
            }
        return {
            "state": "available",
            "reason": "Microsoft Playwright CLI + exact Workstation Chromium binding available",
            "bindingTool": str(PLAYWRIGHT_BINDING),
            "bindingDigest": value.get("bindingDigest"),
            "commandPrefix": prefix,
            "browserExecutableDigest": identity.get("browserExecutableDigest"),
            "cliEntrypointDigest": identity.get("cliEntrypointDigest"),
        }
    except Exception as exc:
        return {
            "state": "unavailable",
            "reason": f"Playwright CLI binding unavailable: {type(exc).__name__}",
        }


def census() -> dict[str, dict[str, Any]]:
    curl = shutil.which("curl")
    firecrawl = shutil.which("firecrawl") or shutil.which("firecrawl-mcp")
    return {
        "native_connector": {
            "state": "caller_bound",
            "reason": "availability belongs to the current application/plugin/MCP connection set",
        },
        "direct_http": {
            "state": "available" if curl else "unavailable",
            "reason": "curl available"
            if curl
            else "no admitted generic HTTP client found",
            **({"executable": curl} if curl else {}),
        },
        "firecrawl": {
            "state": "available" if firecrawl else "unavailable",
            "reason": "local Firecrawl executable found"
            if firecrawl
            else "studied provider only; no local executable/service admitted",
            **({"executable": firecrawl} if firecrawl else {}),
        },
        "playwright": _playwright_health(),
        "browser_use": _browser_use_health(),
        "computer_use": {
            "state": "caller_bound",
            "reason": "Computer Use availability belongs to the current Agent/application carrier, not local documentation",
        },
    }
