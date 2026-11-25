"""Bounded search for a distinct exact canonical witness, not policy mutation.

The caller owns the numerical search budget in r. The original solver policy
and its evidence remain unchanged. Every repaired witness must pass the same
exact verifier; contraction is a proposal heuristic, not a feasibility proof.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any

from .canonical_caps import CapMethod, validate_cap_method
from .information_tree import MultistageProblem, ValidatedInformationTree, validate_information_tree
from .optimality_evidence import (
    OptimalityEvidence,
    certify_canonical_gap,
    freeze_dual_proposal,
    proof_dual_dimensions,
    proof_methods,
    verify_canonical_gap_claim,
)
from .policy_contract import AlgebraicPolicyError, finite_economic_number

# Finite search over binary64 resolution near the original solution.
# These are numerical search coordinates, never economic risk constraints.
_CONTRACTION_EXPONENTS = (52, 48, 44, 40)


@dataclass(frozen=True)
class WitnessRepair:
    standing: str
    reason: str
    problem_sha256: str
    source_policy_sha256: str
    max_change_r: float
    source_evidence: OptimalityEvidence
    repaired_policy: dict[str, tuple[float, ...]] | None = None
    repaired_policy_sha256: str | None = None
    max_observed_change_r: float | None = None
    contraction_exponent: int | None = None
    canonical_evidence: OptimalityEvidence | None = None


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def _problem_digest(problem: MultistageProblem) -> str:
    raw = asdict(problem)
    raw["nodes"] = sorted(raw["nodes"], key=lambda n: (n["t"], n["id"]))
    return _digest(raw)


def _validate_source(
    problem: MultistageProblem, source: dict[str, tuple[float, ...]]
) -> ValidatedInformationTree:
    tree = validate_information_tree(problem)
    if not isinstance(source, dict) or set(source) != {n.id for n in tree.decision}:
        raise AlgebraicPolicyError("repair requires complete original risky policy")
    if any(
        not isinstance(row, tuple)
        or len(row) != tree.asset_count
        or any(not finite_economic_number(v) for v in row)
        for row in source.values()
    ):
        raise AlgebraicPolicyError("repair requires finite aligned risky positions")
    return tree


def _candidate(source: dict[str, tuple[float, ...]], exponent: int):
    scale = 1.0 - 2.0 ** (-exponent)
    return {key: tuple(max(0.0, value) * scale for value in row) for key, row in source.items()}


def _delta(source, candidate) -> Fraction:
    return max(
        abs(Fraction(a) - Fraction(b))
        for key, row in source.items()
        for a, b in zip(row, candidate[key], strict=True)
    )


def _outward(value: Fraction) -> float:
    f = float(value)
    return math.nextafter(f, math.inf) if Fraction(f) < value else f


def repair_canonical_witness(
    problem: MultistageProblem,
    source: dict[str, tuple[float, ...]],
    inequality_multipliers: Any,
    equality_multipliers: Any,
    numerical_estimate: float,
    *,
    max_change_r: float,
    cap_method: CapMethod = "LEGACY_V1",
) -> WitnessRepair:
    """Return a separately identified witness or UNKNOWN, within a caller budget."""
    validate_cap_method(cap_method)
    if not finite_economic_number(max_change_r) or max_change_r < 0:
        raise AlgebraicPolicyError("finite nonnegative repair budget required")
    if not finite_economic_number(numerical_estimate) or numerical_estimate < 0:
        raise AlgebraicPolicyError("finite nonnegative numerical estimate required")
    tree = _validate_source(problem, source)
    dimensions = proof_dual_dimensions(tree)
    proposal = (
        None
        if dimensions is None
        else freeze_dual_proposal(inequality_multipliers, equality_multipliers, dimensions)
    )
    y, lam = (
        ((), ())
        if proposal is None
        else (
            proposal.inequality_marginals,
            proposal.equality_marginals,
        )
    )
    original = certify_canonical_gap(
        problem, source, y, lam, numerical_estimate, cap_method=cap_method
    )
    problem_id, source_id = _problem_digest(problem), _digest(source)

    def unknown(reason: str):
        return WitnessRepair("UNKNOWN", reason, problem_id, source_id, max_change_r, original)

    if original.reason != "INEXACT_WITNESS":
        return unknown("SOURCE_NOT_REPAIRABLE")
    if proposal is None:
        return unknown("MALFORMED_DUAL_PROPOSAL")
    for exponent in _CONTRACTION_EXPONENTS:
        candidate = _candidate(source, exponent)
        change = _delta(source, candidate)
        if not 0 < change <= Fraction(max_change_r):
            continue
        evidence = certify_canonical_gap(
            problem, candidate, y, lam, numerical_estimate, cap_method=cap_method
        )
        if evidence.certified_canonical_gap_upper is not None:
            return WitnessRepair(
                "VERIFIED_DISTINCT_CANONICAL_WITNESS",
                "EXACT_REPLAY_WITHIN_EXPLICIT_BUDGET",
                problem_id,
                source_id,
                max_change_r,
                original,
                candidate,
                _digest(candidate),
                _outward(change),
                exponent,
                evidence,
            )
    return unknown("NO_CERTIFIED_WITNESS_WITHIN_SEARCH_BUDGET")


def verify_repaired_witness(
    problem: MultistageProblem,
    source: dict[str, tuple[float, ...]],
    claim: WitnessRepair,
) -> bool:
    """Verify the receipt from its original contract and policy; no optimizer."""
    if (
        not isinstance(claim, WitnessRepair)
        or claim.standing != "VERIFIED_DISTINCT_CANONICAL_WITNESS"
        or not isinstance(claim.canonical_evidence, OptimalityEvidence)
        or not isinstance(claim.source_evidence, OptimalityEvidence)
    ):
        return False
    methods = proof_methods(claim.canonical_evidence.reason)
    proposal = claim.canonical_evidence.dual_proposal
    if methods is None or proposal is None:
        return False
    try:
        _validate_source(problem, source)
        if (
            not finite_economic_number(claim.max_change_r)
            or claim.max_change_r < 0
            or claim.contraction_exponent not in _CONTRACTION_EXPONENTS
        ):
            return False
        candidate = _candidate(source, claim.contraction_exponent)
        delta = _delta(source, candidate)
        if not 0 < delta <= Fraction(claim.max_change_r):
            return False
        original = certify_canonical_gap(
            problem,
            source,
            proposal.inequality_marginals,
            proposal.equality_marginals,
            claim.source_evidence.numerical_tangent_gap_estimate,
            cap_method=methods[1],
        )
        if original.reason != "INEXACT_WITNESS" or original != claim.source_evidence:
            return False
        if (
            claim.canonical_evidence.numerical_tangent_gap_estimate
            != original.numerical_tangent_gap_estimate
        ):
            return False
        if not verify_canonical_gap_claim(problem, candidate, claim.canonical_evidence):
            return False
        expected = WitnessRepair(
            "VERIFIED_DISTINCT_CANONICAL_WITNESS",
            "EXACT_REPLAY_WITHIN_EXPLICIT_BUDGET",
            _problem_digest(problem),
            _digest(source),
            claim.max_change_r,
            original,
            candidate,
            _digest(candidate),
            _outward(delta),
            claim.contraction_exponent,
            claim.canonical_evidence,
        )
        return claim == expected
    except ValueError, TypeError, OverflowError, KeyError:
        return False
