#!/usr/bin/env python3
"""Acceptance for external equivalence provider fit and first constructive lift pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from computational_lift_r3 import lift_pilot


STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[2]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("JSON document must be an object")
    return value


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    provider_path = STUDY / "evidence" / "mcrl2-equivalence-provider-pilot-r3.json"
    provider = load(provider_path)
    require(provider["standing"] == "PASS_BOUNDED_EXTERNAL_EQUIVALENCE_PROVIDER_PILOT", "mCRL2 pilot standing mismatch")
    require(provider["provider"] == "mCRL2", "wrong formal provider")
    require("202607.0" in provider["providerVersion"], "unexpected mCRL2 version")
    require(provider["equivalentCase"]["equivalent"] is True, "equivalent provider case failed")
    require(provider["nonEquivalentCase"]["equivalent"] is False, "non-equivalent provider case failed")
    require(provider["nonEquivalentCase"]["counterexamplePresent"] is True, "non-equivalence must bind counterexample")
    require(provider["counterexampleDigest"], "counterexample digest missing")
    require(provider["permanentDependencyAdmitted"] is False, "provider must remain ephemeral")
    require(provider["semanticAuthorityTransferred"] is False, "provider must not become Ordivon semantic authority")

    lift_result = lift_pilot()
    lift = lift_result["certificate"]
    witness = lift_result["historyDependenceWitness"]
    require(lift["standing"] == "CERTIFIED_LIFT", "lift certificate standing mismatch")
    require(lift["lowerModelClass"] == "L0_STATELESS_RELATION", "lower model mismatch")
    require(lift["higherModelClass"] == "L1_FINITE_STATE_TRANSDUCER", "higher model mismatch")
    require(witness["sameExplicitInput"] == "read", "history witness input mismatch")
    require(witness["observationA"] != witness["observationB"], "history witness does not distinguish")
    require(lift["bounds"]["constructedStateCount"] == 2, "finite-state upper model missing")
    require(lift["universalDecisionProcedureClaimed"] is False, "universal decider claim forbidden")

    checks = [
        "formal:mcrl2-202607.0-external-provider-fit",
        "formal:strong-bisim-equivalent-case-pass",
        "formal:strong-bisim-non-equivalent-case-counterexample-bound",
        "formal:no-permanent-provider-dependency",
        "lift:same-input-history-dependence-witness",
        "lift:two-state-transducer-constructed",
        "lift:l0-to-l1-certified-only",
        "lift:no-universal-decider-claim",
    ]
    tracked = [
        STUDY / "scripts" / "mcrl2_equivalence_adapter_r3.py",
        STUDY / "scripts" / "run_mcrl2_equivalence_pilot_r3.py",
        STUDY / "scripts" / "computational_lift_r3.py",
        STUDY / "scripts" / "check_capability_science_r3.py",
        STUDY / "tests" / "test_formal_backends_r3.py",
        provider_path,
    ]
    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-r3-formal-lift-acceptance",
        "standing": "R3_FORMAL_EQUIVALENCE_AND_L0_L1_LIFT_ACCEPTED_BOUNDED",
        "sourceRevision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "checks": checks,
        "formalProviderPilot": provider,
        "computationalLiftCertificate": lift,
        "computationalLiftEvidence": {
            "historyDependenceWitness": witness,
            "constructedFiniteStateModel": lift_result["constructedFiniteStateModel"],
            "historyDependenceWitnessDigest": lift_result["historyDependenceWitnessDigest"],
            "constructedFiniteStateModelDigest": lift_result["constructedFiniteStateModelDigest"],
        },
        "artifactDigests": {str(path.relative_to(REPO)): digest(path) for path in tracked},
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "nonClaims": [
            "The mCRL2 pilot covers tiny finite examples and does not establish universal contextual equivalence.",
            "The lift certificate covers one explicit L0->L1 synthetic subject only.",
            "No L2+ computational lift is established.",
            "No external provider result grants authority or production standing.",
        ],
    }
    if args.write_evidence:
        output = STUDY / "evidence" / "capability-science-r3-formal-lift.json"
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
