#!/usr/bin/env python3
"""Resolve the thinnest admitted web/GUI provider from explicit task needs.

This module deliberately does not classify natural language. The Agent/caller owns semantic
interpretation; this resolver owns only deterministic route ordering plus current local capability
census. Documentation is never treated as availability truth.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROFILE_PATH = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "web-interaction-r1.json"
)
BROWSER_USE_CONFIG = Path("/etc/ordivon/browser-use-browserless.json")
BROWSER_USE_ACTION = Path(
    "/opt/ordivon/agent-automation/current/scripts/browser_use_browserless.py"
)
PLAYWRIGHT_BINDING = Path("/root/tools/bin/playwright-cli-binding")


@dataclass(frozen=True, slots=True)
class TaskNeeds:
    native_provider_available: bool = False
    requires_interaction: bool = False
    deterministic_browser_flow: bool = False
    site_scale_web_acquisition: bool = False
    adaptive_browser_reasoning: bool = False
    requires_desktop_gui: bool = False

    def __post_init__(self) -> None:
        if self.requires_desktop_gui and not self.requires_interaction:
            raise ValueError("desktop GUI work implies interaction")
        if self.deterministic_browser_flow and not self.requires_interaction:
            raise ValueError("deterministic browser flow implies interaction")
        if self.adaptive_browser_reasoning and not self.requires_interaction:
            raise ValueError("adaptive browser reasoning implies interaction")
        if self.deterministic_browser_flow and self.adaptive_browser_reasoning:
            raise ValueError("browser flow cannot be both deterministic and adaptive")
        if self.site_scale_web_acquisition and self.requires_interaction:
            raise ValueError(
                "site-scale acquisition and interactive operation are distinct primary intents"
            )


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


def _usable(
    route: str, availability: dict[str, dict[str, Any]], *, caller_bound: set[str]
) -> bool:
    state = availability[route]["state"]
    return state == "available" or route in caller_bound


def resolve(
    needs: TaskNeeds, *, caller_available: tuple[str, ...] = ()
) -> dict[str, Any]:
    availability = census()
    caller_bound = set(caller_available)
    unknown = sorted(
        caller_bound - {"native_connector", "playwright", "computer_use", "firecrawl"}
    )
    if unknown:
        raise ValueError(
            f"caller availability contains unknown/non-caller provider classes: {unknown}"
        )

    considered: list[dict[str, str]] = []

    def consider(route: str, adequate: bool, reason: str) -> str | None:
        if not adequate:
            considered.append(
                {"route": route, "standing": "not_adequate", "reason": reason}
            )
            return None
        if _usable(route, availability, caller_bound=caller_bound):
            considered.append(
                {"route": route, "standing": "selected", "reason": reason}
            )
            return route
        considered.append(
            {
                "route": route,
                "standing": "not_available",
                "reason": availability[route]["reason"],
            }
        )
        return None

    selected: str | None = None
    if needs.native_provider_available:
        selected = consider(
            "native_connector",
            True,
            "caller reports a direct native capability that satisfies the task",
        )
    if selected is None and needs.requires_desktop_gui:
        selected = consider(
            "computer_use",
            True,
            "task requires desktop/native GUI beyond browser semantics",
        )
    elif selected is None and not needs.requires_interaction:
        if needs.site_scale_web_acquisition:
            selected = consider(
                "firecrawl", True, "site-scale web acquisition is the primary intent"
            )
        else:
            selected = consider(
                "direct_http", True, "no interactive browser semantics are required"
            )
    elif selected is None:
        if needs.deterministic_browser_flow:
            selected = consider(
                "playwright", True, "browser flow is known/deterministic"
            )
        elif needs.adaptive_browser_reasoning or not needs.deterministic_browser_flow:
            selected = consider(
                "browser_use",
                True,
                "browser action choice must adapt to current page state",
            )
        if selected is None and needs.deterministic_browser_flow:
            selected = consider(
                "browser_use",
                True,
                "generic deterministic browser adapter is unavailable; adaptive browser provider can still execute the flow",
            )

    standing = "ROUTED" if selected is not None else "NO_ADMITTED_PROVIDER"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.web-interaction-route-decision",
        "standing": standing,
        "selectedRoute": selected,
        "needs": asdict(needs),
        "callerAvailable": sorted(caller_bound),
        "considered": considered,
        "availability": availability,
        "semanticSelector": "agent_or_caller",
        "executionAuthority": "selected_provider",
        "completionAuthority": "owning_domain",
    }


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--census",
        action="store_true",
        help="print current provider-class availability only",
    )
    p.add_argument("--native-provider-available", action="store_true")
    p.add_argument("--requires-interaction", action="store_true")
    p.add_argument("--deterministic-browser-flow", action="store_true")
    p.add_argument("--site-scale-web-acquisition", action="store_true")
    p.add_argument("--adaptive-browser-reasoning", action="store_true")
    p.add_argument("--requires-desktop-gui", action="store_true")
    p.add_argument("--caller-available", action="append", default=[])
    return p


def main() -> int:
    args = _parser().parse_args()
    if args.census:
        print(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ordivon.web-provider-census",
                    "providers": census(),
                },
                sort_keys=True,
            )
        )
        return 0
    decision = resolve(
        TaskNeeds(
            native_provider_available=args.native_provider_available,
            requires_interaction=args.requires_interaction,
            deterministic_browser_flow=args.deterministic_browser_flow,
            site_scale_web_acquisition=args.site_scale_web_acquisition,
            adaptive_browser_reasoning=args.adaptive_browser_reasoning,
            requires_desktop_gui=args.requires_desktop_gui,
        ),
        caller_available=tuple(args.caller_available),
    )
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["standing"] == "ROUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
