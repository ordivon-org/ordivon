#!/usr/bin/env python3
"""Bounded observational distinguishability oracle for Capability Science R1.

This is deliberately not a universal contextual-equivalence checker. It compares exact
canonical observations over an explicit finite context universe and emits concrete witnesses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _observation(item: dict[str, Any], context_id: str) -> Any:
    observations = item.get("observations")
    if not isinstance(observations, dict) or context_id not in observations:
        raise ValueError(f"{item.get('capabilityId', '<unknown>')} missing context {context_id}")
    return observations[context_id]


def distinguishing_witness(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    observation_policy_ref: str,
    contexts: list[str],
) -> dict[str, Any] | None:
    """Return the first deterministic distinguishing witness, or None if not distinguished in the supplied bounded contexts."""
    for context_id in contexts:
        candidate_observation = _observation(candidate, context_id)
        baseline_observation = _observation(baseline, context_id)
        if canonical_bytes(candidate_observation) == canonical_bytes(baseline_observation):
            continue
        witness_seed = {
            "candidate": candidate["capabilityId"],
            "baseline": baseline["capabilityId"],
            "policy": observation_policy_ref,
            "context": context_id,
            "candidateObservation": candidate_observation,
            "baselineObservation": baseline_observation,
        }
        evidence_refs = sorted(
            set(candidate.get("evidenceRefs", [])) | set(baseline.get("evidenceRefs", []))
        )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.capability-novelty-witness-v1",
            "witnessId": "witness:" + sha256_ref(witness_seed).split(":", 1)[1][:24],
            "candidateCapabilityId": candidate["capabilityId"],
            "baselineCapabilityId": baseline["capabilityId"],
            "observationPolicyRef": observation_policy_ref,
            "contextId": context_id,
            "candidateObservation": candidate_observation,
            "baselineObservation": baseline_observation,
            "candidateObservationDigest": sha256_ref(candidate_observation),
            "baselineObservationDigest": sha256_ref(baseline_observation),
            "verdict": "DISTINGUISHABLE_WITHIN_POLICY",
            "boundedComparison": True,
            "evidenceRefs": evidence_refs or ["evidence:synthetic-fixture"],
            "nonClaims": [
                "This witness is relative to the explicit finite observation policy.",
                "This witness does not establish universal contextual inequivalence.",
                "This witness grants no authority or execution permission.",
            ],
        }
    return None


def novelty_report(document: dict[str, Any]) -> dict[str, Any]:
    policy = document.get("observationPolicy")
    if not isinstance(policy, dict):
        raise ValueError("observationPolicy must be an object")
    policy_id = policy.get("policyId")
    contexts = policy.get("contexts")
    if not isinstance(policy_id, str) or not policy_id:
        raise ValueError("observationPolicy.policyId is required")
    if not isinstance(contexts, list) or not contexts or not all(isinstance(v, str) and v for v in contexts):
        raise ValueError("observationPolicy.contexts must be a non-empty string array")

    candidate = document.get("candidate")
    library = document.get("library")
    if not isinstance(candidate, dict) or not isinstance(candidate.get("capabilityId"), str):
        raise ValueError("candidate.capabilityId is required")
    if not isinstance(library, list) or not library:
        raise ValueError("library must be non-empty")

    # Observation-policy completeness is a precondition for any novelty verdict. Validate the
    # entire supplied universe before allowing an early distinguishing witness to short-circuit.
    for context_id in contexts:
        _observation(candidate, context_id)
    for baseline in library:
        if not isinstance(baseline, dict) or not isinstance(baseline.get("capabilityId"), str):
            raise ValueError("each library entry requires capabilityId")
        for context_id in contexts:
            _observation(baseline, context_id)

    witnesses: list[dict[str, Any]] = []
    not_distinguished_from: list[str] = []
    for baseline in library:
        witness = distinguishing_witness(candidate, baseline, policy_id, contexts)
        if witness is None:
            not_distinguished_from.append(baseline["capabilityId"])
        else:
            witnesses.append(witness)

    if not_distinguished_from:
        verdict = "NOVELTY_NOT_ESTABLISHED"
    elif len(witnesses) == len(library):
        verdict = "CERTIFIED_NOVEL_WITHIN_BOUNDED_POLICY"
    else:
        verdict = "UNKNOWN"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capability-novelty-report-r1",
        "candidateCapabilityId": candidate["capabilityId"],
        "observationPolicyRef": policy_id,
        "comparedBaselineCount": len(library),
        "verdict": verdict,
        "notDistinguishedFromWithinPolicy": sorted(not_distinguished_from),
        "witnesses": witnesses,
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "nonClaims": [
            "The report is complete only for the supplied finite baseline library and observation contexts.",
            "Failure to distinguish is not a proof of universal contextual equivalence.",
            "Embedding or lexical distance is not used as semantic authority.",
            "No permission, execution authority, or domain acceptance follows from novelty.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    report = novelty_report(document)
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
