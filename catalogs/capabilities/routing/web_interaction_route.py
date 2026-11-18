#!/usr/bin/env python3
"""Resolve the thinnest admitted web/GUI provider from explicit task needs.

This module deliberately does not classify natural language. The Agent/caller owns semantic
interpretation; this resolver owns only deterministic route ordering plus current local capability
census. Documentation is never treated as availability truth.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

# The current-admission probe is isolated from task semantics. Both call
# modes are real consumers: catalogs.capabilities.routing.web_interaction_route and the direct CLI.
if __package__:
    from .web_provider_census import census
else:
    from web_provider_census import census


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
