#!/usr/bin/env python3
"""Social Fabric R3: OPA-backed quorum-policy shadow and commitment projection."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

if __package__:
    from .social_fabric_coordination_r2 import compile_coordination_projection
    from .social_fabric_r1 import SocialFabricError, canonical_digest
else:
    from social_fabric_coordination_r2 import compile_coordination_projection
    from social_fabric_r1 import SocialFabricError, canonical_digest

POLICY_KIND = "ordivon.social-fabric-commitment-policy"
PROJECTION_KIND = "ordivon.social-fabric-commitment-projection"

_POLICY_KEYS = {
    "schemaVersion",
    "kind",
    "policyId",
    "candidateSubjectPrefixes",
    "requiredSupportRoles",
    "requiredCandidateEvidencePrefixes",
    "blockingDamageReasonCodes",
    "blockingModulatoryDimensions",
}


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SocialFabricError(f"{label} must be non-empty")
    return value


def _unique_strings(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise SocialFabricError(f"{label} must be a list")
    if not allow_empty and not value:
        raise SocialFabricError(f"{label} must be non-empty")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise SocialFabricError(f"{label}[{index}] must be non-empty")
        if item in seen:
            raise SocialFabricError(f"{label} contains duplicate value: {item}")
        seen.add(item)
        result.append(item)
    return result


def validate_policy(policy: dict[str, Any]) -> None:
    if set(policy) != _POLICY_KEYS:
        unknown = sorted(set(policy) - _POLICY_KEYS)
        missing = sorted(_POLICY_KEYS - set(policy))
        raise SocialFabricError(
            f"commitment policy fields mismatch: unknown={unknown} missing={missing}"
        )
    if policy.get("schemaVersion") != 1:
        raise SocialFabricError("unsupported commitment policy schemaVersion")
    if policy.get("kind") != POLICY_KIND:
        raise SocialFabricError("unsupported commitment policy kind")
    _nonempty(policy.get("policyId"), "policyId")
    _unique_strings(
        policy.get("candidateSubjectPrefixes"),
        "candidateSubjectPrefixes",
        allow_empty=False,
    )
    for field in (
        "requiredSupportRoles",
        "requiredCandidateEvidencePrefixes",
        "blockingDamageReasonCodes",
        "blockingModulatoryDimensions",
    ):
        _unique_strings(policy.get(field), field)


def _opa_decision(
    opa_executable: str,
    rego_path: Path,
    policy_input: dict[str, Any],
) -> dict[str, Any]:
    executable = shutil.which(opa_executable)
    if executable is None:
        raise SocialFabricError(f"OPA executable not found: {opa_executable}")
    completed = subprocess.run(
        [
            executable,
            "eval",
            "--format=json",
            "--data",
            str(rego_path),
            "--stdin-input",
            "data.ordivon.social_commitment_r3.decision",
        ],
        input=json.dumps(policy_input, ensure_ascii=False, sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SocialFabricError(
            f"OPA evaluation failed rc={completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        envelope = json.loads(completed.stdout)
        value = envelope["result"][0]["expressions"][0]["value"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise SocialFabricError(
            "OPA returned an unreadable decision envelope"
        ) from error
    if not isinstance(value, dict):
        raise SocialFabricError("OPA decision must be an object")
    if not isinstance(value.get("satisfied"), bool):
        raise SocialFabricError("OPA decision.satisfied must be boolean")
    if value.get("effectAuthorityGranted") is not False:
        raise SocialFabricError("OPA policy must not grant EffectAuthority")
    if value.get("externalEffectPerformed") is not False:
        raise SocialFabricError("OPA policy must not claim an external effect")
    unmet = value.get("unmet")
    if not isinstance(unmet, list):
        raise SocialFabricError("OPA decision.unmet must be a list")
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(unmet):
        if not isinstance(item, dict):
            raise SocialFabricError(f"OPA decision.unmet[{index}] must be an object")
        code = _nonempty(item.get("code"), f"OPA decision.unmet[{index}].code")
        raw_value = item.get("value")
        if not isinstance(raw_value, str):
            raise SocialFabricError(
                f"OPA decision.unmet[{index}].value must be a string"
            )
        normalized.append({"code": code, "value": raw_value})
    normalized.sort(key=lambda row: (row["code"], row["value"]))
    return {
        "satisfied": value["satisfied"],
        "unmet": normalized,
        "effectAuthorityGranted": False,
        "externalEffectPerformed": False,
    }


def _event_map(cut: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = cut.get("events")
    if not isinstance(raw, list):
        raise SocialFabricError("events must be a list")
    return {
        event["id"]: event
        for event in raw
        if isinstance(event, dict) and isinstance(event.get("id"), str)
    }


def _applicable(subject: str, prefixes: list[str]) -> bool:
    return any(subject.startswith(prefix) for prefix in prefixes)


def compile_commitment_projection(
    cut: dict[str, Any],
    policy: dict[str, Any],
    *,
    rego_path: Path,
    opa_executable: str = "opa",
) -> dict[str, Any]:
    validate_policy(policy)
    coordination = compile_coordination_projection(cut)
    events = _event_map(cut)

    active_damage = sorted(
        {
            events[event_id]["data"]["reasonCode"]
            for event_id in coordination["damageSignals"]
        }
    )
    active_modulatory = sorted(
        {
            events[event_id]["data"]["dimension"]
            for event_id in coordination["modulatorySignals"]
        }
    )

    decisions: list[dict[str, Any]] = []
    prefixes = policy["candidateSubjectPrefixes"]
    opa_policy = {
        key: policy[key]
        for key in (
            "requiredSupportRoles",
            "requiredCandidateEvidencePrefixes",
            "blockingDamageReasonCodes",
            "blockingModulatoryDimensions",
        )
    }

    for standing in coordination["candidateStanding"]:
        if not _applicable(standing["subject"], prefixes):
            continue
        candidate_event = events[standing["candidateEventId"]]
        support_roles: set[str] = set()
        support_bindings: list[dict[str, Any]] = []
        for support_id in standing["supportEventIds"]:
            support = events[support_id]
            role = support["data"].get("role")
            evidence_refs = support["data"].get("evidenceRefs", [])
            counted = isinstance(role, str) and bool(role) and bool(evidence_refs)
            if counted:
                support_roles.add(role)
            support_bindings.append(
                {
                    "eventId": support_id,
                    "role": role if isinstance(role, str) else None,
                    "evidenceRefs": sorted(evidence_refs),
                    "countsForRoleRequirement": counted,
                }
            )

        candidate_input = {
            "standing": standing["state"],
            "supportRoles": sorted(support_roles),
            "candidateEvidenceRefs": sorted(
                candidate_event["data"].get("evidenceRefs", [])
            ),
            "activeDamageReasonCodes": active_damage,
            "activeModulatoryDimensions": active_modulatory,
        }
        policy_input = {"policy": opa_policy, "candidate": candidate_input}
        opa = _opa_decision(opa_executable, rego_path, policy_input)
        decisions.append(
            {
                "candidateEventId": standing["candidateEventId"],
                "subject": standing["subject"],
                "satisfied": opa["satisfied"],
                "unmet": opa["unmet"],
                "supportBindings": sorted(
                    support_bindings, key=lambda row: row["eventId"]
                ),
                "policyInputDigest": canonical_digest(policy_input),
                "policyDecisionDigest": canonical_digest(opa),
                "truthBoundary": (
                    "OPA policy satisfaction is a shadow coordination fact only; "
                    "it does not grant execution, priority, a resource lease, or EffectAuthority."
                ),
            }
        )

    decisions.sort(key=lambda row: row["candidateEventId"])
    satisfied_ids = sorted(
        row["candidateEventId"] for row in decisions if row["satisfied"]
    )
    if not decisions:
        state = "NOT_APPLICABLE"
    elif not satisfied_ids:
        state = "NOT_READY"
    elif len(satisfied_ids) == 1:
        state = "READY_SHADOW"
    else:
        state = "AMBIGUOUS_MULTIPLE_READY"

    commitment: dict[str, Any] = {
        "state": state,
        "policySatisfiedCandidateIds": satisfied_ids,
        "effectAuthorityGranted": False,
        "externalEffectPerformed": False,
        "requiresOwnerBinding": True,
        "truthBoundary": (
            "SF42 is an explainable shadow commitment projection. Natural effect owners "
            "must separately establish any enforceable lease, admission, or external effect."
        ),
    }
    if state == "READY_SHADOW":
        commitment["soleSatisfiedCandidateEventId"] = satisfied_ids[0]

    result = {
        "schemaVersion": 1,
        "kind": PROJECTION_KIND,
        "truthRole": "rebuildable-shadow-commitment-projection",
        "observedAt": coordination["observedAt"],
        "sourceCutDigest": coordination["sourceCutDigest"],
        "coordinationProjectionDigest": coordination["projectionDigest"],
        "policyId": policy["policyId"],
        "policyDigest": canonical_digest(policy),
        "candidateDecisions": decisions,
        "commitmentProjection": commitment,
        "nonClaims": [
            "OPA policy satisfaction is not execution authorization.",
            "Required support roles are set membership requirements, not votes.",
            "Duplicate supporters or support counts do not increase standing.",
            "Multiple satisfied candidates are reported as ambiguous and are never tie-broken.",
            "READY_SHADOW does not mint a resource lease or EffectAuthority.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=("current", "decisions"))
    parser.add_argument("--cut", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--rego", type=Path, required=True)
    parser.add_argument("--opa", default="opa")
    args = parser.parse_args()

    cut = json.loads(args.cut.read_text(encoding="utf-8"))
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    if not isinstance(cut, dict) or not isinstance(policy, dict):
        raise SocialFabricError("cut and policy must be JSON objects")
    projection = compile_commitment_projection(
        cut,
        policy,
        rego_path=args.rego,
        opa_executable=args.opa,
    )
    if args.view == "current":
        output: Any = projection
    else:
        output = {
            "schemaVersion": 1,
            "kind": "ordivon.social-fabric-commitment-decisions",
            "observedAt": projection["observedAt"],
            "policyId": projection["policyId"],
            "policyDigest": projection["policyDigest"],
            "items": projection["candidateDecisions"],
        }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
