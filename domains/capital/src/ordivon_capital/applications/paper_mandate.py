"""Validate a caller-declared Paper spending mandate without PG or provider side effects."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from ..governance.policy_decision import PolicyDecisionError, enforce_non_live
from ..portfolio.strategic_contribution import plan_strategic_contribution


def admit_paper_mandate(
    path: Path, *, symbol: str, horizon: int, buys_minor: int,
    starting_cash: int, protected_cash: int,
) -> dict:
    """Compose existing Portfolio capital-plan and Governance nonlive gates.

    A caller-declared Paper portfolio label is NOT a real broker principal.
    The repo's actual policy source, not an input file provided by the
    caller, decides whether NON_LIVE effects are currently permitted.
    """
    raw = path.read_bytes()
    mandate = json.loads(raw)
    expected = {
        "schemaVersion", "kind", "portfolioRef", "lane",
        "externalFinancialWritesAllowed", "maxHorizonSessions",
        "allocationRequest",
    }
    if (
        type(mandate) is not dict or set(mandate) != expected
        or type(mandate["schemaVersion"]) is not int
        or mandate["schemaVersion"] != 1
        or mandate["kind"] != "ordivon.finance.portfolio.paper-simulation-mandate"
        or mandate["lane"] != "NON_LIVE"
        or mandate["externalFinancialWritesAllowed"] is not False
        or type(mandate["maxHorizonSessions"]) is not int
        or mandate["maxHorizonSessions"] not in (5, 20)
        or horizon > mandate["maxHorizonSessions"]
        or type(mandate["portfolioRef"]) is not str
        or re.fullmatch(r"paper-[a-z0-9][a-z0-9-]{2,47}", mandate["portfolioRef"]) is None
    ):
        raise ValueError("Paper portfolio mandate is not simulation-only or in scope")
    # Existing Portfolio makes a projection, never investment advice or
    # execution permission. The amount is the maximum simulated sleeve,
    # not an additional deposit to the initial Paper cash.
    plan = plan_strategic_contribution(mandate["allocationRequest"])
    if (
        plan["standing"] != "READ_ONLY_PROJECTION"
        or plan["executionAuthorized"] is not False
        or plan["currency"] != "USD"
        or mandate["allocationRequest"]["cashMinor"] != starting_cash
        or plan["protectedReserveMinor"] != protected_cash
        or plan["contributionMinor"] != starting_cash - protected_cash
        or plan["allocationsMinor"].get(symbol, 0) < buys_minor
    ):
        raise ValueError("Paper fill exceeds the caller-declared Portfolio capital envelope")
    # Reuse the current repo's sole Governance decision point; no new
    # authorization system and no user-supplied policy override.
    repo = Path(__file__).resolve().parents[3]
    try:
        gate = enforce_non_live(repo, repo / "config/execution_policy.json")
    except PolicyDecisionError as exc:
        raise ValueError("current Governance policy denied Paper nonlive effects") from exc
    if (
        gate["standing"] != "NON_LIVE_POLICY_ALLOWED"
        or gate["externalFinancialWritesAllowed"] is not False
        or gate["allowExternalWrite"] is not False
    ):
        raise ValueError("current Governance policy does not allow Paper nonlive effects")
    return {
        "paper_portfolio_ref": mandate["portfolioRef"],
        "paper_mandate_sha256": hashlib.sha256(raw).hexdigest(),
        "nonlive_policy_standing": gate["standing"],
        "portfolio_plan_standing": plan["standing"],
    }
