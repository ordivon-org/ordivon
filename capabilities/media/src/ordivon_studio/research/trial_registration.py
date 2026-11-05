"""Typed R6-A research registration, outcome and sealed-seed contracts.

This is a pure specification/validation responsibility; neither search
statistics nor PostgreSQL state is owned here.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .grounded_contracts import canonical_digest

OUTCOME_ROLES = ("primary", "guardrail", "secondary", "exploratory")



def seed_commitment(seed: str) -> str:
    if not isinstance(seed, str) or not seed:
        raise ValueError("seed must be a non-empty string")
    return "sha256:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _strict_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a non-empty trimmed string")
    return value


def validate_registration(value: Mapping[str, Any]) -> dict[str, Any]:
    registration = dict(value)
    if registration.get("schemaVersion") != 1 or registration.get("kind") != "ordivon.studio.creative-alpha-experiment":
        raise ValueError("unsupported Creative Alpha experiment registration")
    _strict_text(registration.get("experimentId"), "experimentId")
    _strict_text(registration.get("hypothesis"), "hypothesis")
    _strict_text(registration.get("observerClass"), "observerClass")
    encounter = registration.get("encounter")
    if not isinstance(encounter, dict) or not encounter:
        raise ValueError("encounter must be a non-empty object")
    outcomes = registration.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise ValueError("outcomes must be a non-empty array")
    seen: set[str] = set()
    primary_count = 0
    for raw in outcomes:
        if not isinstance(raw, dict):
            raise ValueError("outcome must be an object")
        outcome_id = _strict_text(raw.get("outcomeId"), "outcomeId")
        if outcome_id in seen:
            raise ValueError(f"duplicate outcomeId: {outcome_id}")
        seen.add(outcome_id)
        role = raw.get("role")
        if role not in OUTCOME_ROLES:
            raise ValueError(f"unsupported outcome role: {role}")
        primary_count += int(role == "primary")
        _strict_text(raw.get("measure"), "outcome measure")
    if primary_count != 1:
        raise ValueError("exactly one primary outcome is required in R6 v0")
    search = registration.get("search")
    if not isinstance(search, dict):
        raise ValueError("search must be an object")
    if search.get("mode") not in {"static", "adaptive"}:
        raise ValueError("search mode must be static or adaptive")
    budget = search.get("attemptBudget")
    if not isinstance(budget, int) or budget < 2:
        raise ValueError("search attemptBudget must be >= 2")
    _strict_text(search.get("visibleSeed"), "visible search seed")
    stop_rule = registration.get("stopRule")
    if stop_rule != {"kind": "fixed-attempt-budget", "attemptBudget": budget}:
        raise ValueError("R6 v0 requires a fixed attempt-budget stop rule")
    holdout = registration.get("holdout")
    if not isinstance(holdout, dict) or holdout.get("status") != "sealed":
        raise ValueError("holdout must begin sealed")
    commitment = holdout.get("seedCommitment")
    if not isinstance(commitment, str) or not commitment.startswith("sha256:") or len(commitment) != 71:
        raise ValueError("holdout seed commitment must be a SHA-256 identity")
    if "seed" in holdout or "holdoutSeed" in holdout:
        raise ValueError("registration must not contain the holdout seed")
    digest = registration.get("registrationDigest")
    semantic = {key: item for key, item in registration.items() if key != "registrationDigest"}
    expected = canonical_digest(semantic)
    if digest is not None and digest != expected:
        raise ValueError("registration digest mismatch")
    registration["registrationDigest"] = expected
    return registration


def build_null_registration(
    *,
    mode: str,
    attempt_budget: int,
    visible_seed: str,
    holdout_seed_commitment: str,
    experiment_id: str | None = None,
) -> dict[str, Any]:
    experiment_id = experiment_id or f"experiment:studio:r6a:null-search:{mode}"
    registration: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.studio.creative-alpha-experiment",
        "experimentId": experiment_id,
        "hypothesis": (
            "In a universe whose true creative intervention effect is exactly zero, high-budget search can manufacture an impressive visible winner, "
            "but complete search accounting, a replayed search null, and an independently sealed holdout should prevent that winner from becoming Creative Alpha evidence."
        ),
        "observerClass": "synthetic-null-observer",
        "encounter": {
            "kind": "synthetic-controlled-encounter",
            "trueCreativeAlpha": 0.0,
            "interpretation": "The modeled observation is a standardized adaptation-consequence estimate under a known zero-effect data-generating process.",
        },
        "outcomes": [
            {
                "outcomeId": "adaptation-effect-z",
                "role": "primary",
                "measure": "standardized estimated incremental adaptation consequence; higher is the searched direction",
            },
            {
                "outcomeId": "holdout-effect-z",
                "role": "guardrail",
                "measure": "independent standardized effect for the frozen candidate after holdout reveal",
            },
            {
                "outcomeId": "search-corrected-p",
                "role": "secondary",
                "measure": "empirical tail probability of the selected visible statistic under replay of the same full search procedure",
            },
            {
                "outcomeId": "visible-winner-effect",
                "role": "exploratory",
                "measure": "naive selected visible effect retained to expose best-of-N inflation, never as confirmatory evidence",
            },
        ],
        "search": {
            "mode": mode,
            "attemptBudget": int(attempt_budget),
            "visibleSeed": visible_seed,
            "searchIsData": True,
        },
        "stopRule": {"kind": "fixed-attempt-budget", "attemptBudget": int(attempt_budget)},
        "holdout": {
            "status": "sealed",
            "seedCommitment": holdout_seed_commitment,
            "revealLaw": "The raw holdout seed is absent from registration and search execution. It may be supplied only after winner freeze, and any reveal contaminates that holdout for future tuning.",
        },
        "decisionLaw": (
            "A large visible winner is not Creative Alpha. R6-A succeeds when search inflation is visible, search-aware false-positive calibration remains controlled, "
            "and the frozen candidate does not acquire confirmatory support merely from being the best result of the search."
        ),
    }
    registration["registrationDigest"] = canonical_digest(registration)
    return validate_registration(registration)
