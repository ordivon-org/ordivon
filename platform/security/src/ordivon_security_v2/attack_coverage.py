from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping
from typing import Any

_DW01_KIND = "ordivon.security.dwc-subject-exposure-snapshot"
_DW02_KIND = "ordivon.security.threat-applicability-fusion"
_FLOW_KIND = "ordivon.security.dwc-attack-flow-reference"
_IMPLEMENTATION = {"IMPLEMENTED", "NOT_IMPLEMENTED", "UNKNOWN"}
_OBSERVATION = {"OBSERVED", "NO_OBSERVATION_WITH_COVERAGE", "UNKNOWN"}
_EFFECTIVENESS = {"VERIFIED_EFFECTIVE", "VERIFIED_INEFFECTIVE", "UNKNOWN"}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value


def _texts(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    rows = [_text(item, f"{label} item") for item in value]
    if nonempty and not rows:
        raise ValueError(f"{label} must not be empty")
    if len(rows) != len(set(rows)):
        raise ValueError(f"{label} must not contain duplicates")
    return sorted(rows)


def _subject_binding(subject: Mapping[str, object]) -> dict[str, str]:
    if _text(subject.get("kind"), "subject.kind") != _DW01_KIND:
        raise ValueError(f"subject.kind must be {_DW01_KIND}")
    snapshot_digest = _text(subject.get("snapshotDigest"), "subject.snapshotDigest")
    if not snapshot_digest.startswith("sha256:") or len(snapshot_digest) != 71:
        raise ValueError("subject.snapshotDigest must be sha256:<64 hex>")
    evidence_ref = _text(subject.get("evidenceRef"), "subject.evidenceRef")
    if evidence_ref != f"dwc-subject-exposure:{snapshot_digest}":
        raise ValueError("subject.evidenceRef does not bind snapshotDigest")
    return {
        "caseRef": _text(subject.get("caseRef"), "subject.caseRef"),
        "epochRef": _text(subject.get("epochRef"), "subject.epochRef"),
        "subjectRef": _text(subject.get("subjectRef"), "subject.subjectRef"),
        "snapshotDigest": snapshot_digest,
        "evidenceRef": evidence_ref,
    }


def _validate_dw02(
    applicability: Mapping[str, object], subject_binding: Mapping[str, str]
) -> dict[str, object]:
    if _text(applicability.get("kind"), "applicability.kind") != _DW02_KIND:
        raise ValueError(f"applicability.kind must be {_DW02_KIND}")
    bound = applicability.get("subject")
    if not isinstance(bound, Mapping):
        raise ValueError("applicability.subject must be an object")
    observed = {
        "caseRef": _text(bound.get("caseRef"), "applicability.subject.caseRef"),
        "epochRef": _text(bound.get("epochRef"), "applicability.subject.epochRef"),
        "subjectRef": _text(bound.get("subjectRef"), "applicability.subject.subjectRef"),
        "snapshotDigest": _text(
            bound.get("snapshotDigest"), "applicability.subject.snapshotDigest"
        ),
        "evidenceRef": _text(bound.get("evidenceRef"), "applicability.subject.evidenceRef"),
    }
    if observed != dict(subject_binding):
        raise ValueError("DW02 subject binding does not match DW01 subject")
    claim = _text(applicability.get("claim"), "applicability.claim")
    if claim not in {"AFFECTED", "NOT_AFFECTED", "UNDER_INVESTIGATION"}:
        raise ValueError("unsupported applicability.claim")
    return {
        "vulnerabilityRef": _text(
            applicability.get("vulnerabilityRef"), "applicability.vulnerabilityRef"
        ),
        "claim": claim,
        "currentness": applicability.get("currentness", {}),
        "threatSignals": applicability.get("threatSignals", {}),
    }


def _validate_flow(
    flow: Mapping[str, object], subject_binding: Mapping[str, str]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], list[str], list[str]]:
    if _text(flow.get("kind"), "flow.kind") != _FLOW_KIND:
        raise ValueError(f"flow.kind must be {_FLOW_KIND}")
    _text(flow.get("flowRef"), "flow.flowRef")
    _text(flow.get("sourceRef"), "flow.sourceRef")
    _text(flow.get("sourceDigest"), "flow.sourceDigest")
    _text(flow.get("attackFlowVersion"), "flow.attackFlowVersion")

    binding = flow.get("subjectBinding")
    if not isinstance(binding, Mapping):
        raise ValueError("flow.subjectBinding must be an object")
    observed = {
        "caseRef": _text(binding.get("caseRef"), "flow.subjectBinding.caseRef"),
        "epochRef": _text(binding.get("epochRef"), "flow.subjectBinding.epochRef"),
        "subjectRef": _text(binding.get("subjectRef"), "flow.subjectBinding.subjectRef"),
        "snapshotDigest": _text(
            binding.get("snapshotDigest"), "flow.subjectBinding.snapshotDigest"
        ),
        "evidenceRef": _text(binding.get("evidenceRef"), "flow.subjectBinding.evidenceRef"),
    }
    if observed != dict(subject_binding):
        raise ValueError("Attack Flow subject binding does not match DW01 subject")

    raw_actions = flow.get("actions")
    if not isinstance(raw_actions, list) or not raw_actions:
        raise ValueError("flow.actions must be a non-empty array")
    actions: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_actions):
        if not isinstance(raw, Mapping):
            raise ValueError(f"flow.actions[{index}] must be an object")
        action_ref = _text(raw.get("actionRef"), f"flow.actions[{index}].actionRef")
        if action_ref in actions:
            raise ValueError(f"duplicate actionRef: {action_ref}")
        actions[action_ref] = {
            "actionRef": action_ref,
            "techniqueRef": _text(
                raw.get("techniqueRef"), f"flow.actions[{index}].techniqueRef"
            ),
            "name": _text(raw.get("name"), f"flow.actions[{index}].name"),
            "sourceRefs": _texts(
                raw.get("sourceRefs", []), f"flow.actions[{index}].sourceRefs", nonempty=True
            ),
            "evidenceRefs": _texts(
                raw.get("evidenceRefs", []), f"flow.actions[{index}].evidenceRefs"
            ),
        }

    raw_edges = flow.get("edges")
    if not isinstance(raw_edges, list):
        raise ValueError("flow.edges must be an array")
    edges: list[dict[str, str]] = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {action_ref: 0 for action_ref in actions}
    for index, raw in enumerate(raw_edges):
        if not isinstance(raw, Mapping):
            raise ValueError(f"flow.edges[{index}] must be an object")
        source = _text(raw.get("fromActionRef"), f"flow.edges[{index}].fromActionRef")
        target = _text(raw.get("toActionRef"), f"flow.edges[{index}].toActionRef")
        relation = _text(raw.get("relation"), f"flow.edges[{index}].relation")
        if source not in actions or target not in actions:
            raise ValueError(f"dangling attack-flow edge: {source}->{target}")
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1
        edges.append(
            {
                "fromActionRef": source,
                "toActionRef": target,
                "relation": relation,
            }
        )

    queue = deque(sorted(ref for ref, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in sorted(adjacency[source]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(actions):
        raise ValueError("attack-flow graph is cyclic")

    entries = _texts(flow.get("entryActionRefs"), "flow.entryActionRefs", nonempty=True)
    objectives = _texts(
        flow.get("objectiveActionRefs"), "flow.objectiveActionRefs", nonempty=True
    )
    unknown = (set(entries) | set(objectives)) - set(actions)
    if unknown:
        raise ValueError(f"entry/objective references unknown actions: {sorted(unknown)}")
    return actions, edges, entries, objectives


def _all_paths(
    actions: Mapping[str, object],
    edges: list[dict[str, str]],
    entries: list[str],
    objectives: list[str],
    *,
    max_paths: int = 4096,
) -> list[list[str]]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["fromActionRef"]].append(edge["toActionRef"])
    for source in adjacency:
        adjacency[source].sort()

    objective_set = set(objectives)
    paths: list[list[str]] = []
    stack: list[tuple[str, list[str]]] = [
        (entry, [entry]) for entry in reversed(sorted(entries))
    ]
    while stack:
        node, path = stack.pop()
        if node in objective_set:
            paths.append(path)
            if len(paths) > max_paths:
                raise ValueError("attack-flow path expansion exceeds qualification bound")
            continue
        for target in reversed(adjacency.get(node, [])):
            if target in path:
                raise ValueError("attack-flow path unexpectedly revisits an action")
            stack.append((target, [*path, target]))
    if not paths:
        raise ValueError("no entry-to-objective path exists")
    return sorted(paths)


def _validate_control(
    raw: Mapping[str, object], action_refs: set[str], index: int
) -> dict[str, Any]:
    control_ref = _text(raw.get("controlRef"), f"controls[{index}].controlRef")
    mapped_actions = _texts(
        raw.get("mappedActionRefs"), f"controls[{index}].mappedActionRefs", nonempty=True
    )
    unknown = set(mapped_actions) - action_refs
    if unknown:
        raise ValueError(f"{control_ref} maps unknown actions: {sorted(unknown)}")

    attack_refs = _texts(
        raw.get("attackMitigationRefs", []),
        f"controls[{index}].attackMitigationRefs",
    )
    d3fend_refs = _texts(
        raw.get("d3fendRefs", []), f"controls[{index}].d3fendRefs"
    )
    detection_refs = _texts(
        raw.get("detectionStrategyRefs", []),
        f"controls[{index}].detectionStrategyRefs",
    )
    if not attack_refs and not d3fend_refs and not detection_refs:
        raise ValueError(f"{control_ref} requires at least one external defensive reference")

    mapping_evidence = _texts(
        raw.get("mappingEvidenceRefs", []),
        f"controls[{index}].mappingEvidenceRefs",
        nonempty=True,
    )

    implementation = _text(
        raw.get("implementationStanding"), f"controls[{index}].implementationStanding"
    )
    observation = _text(
        raw.get("observationStanding"), f"controls[{index}].observationStanding"
    )
    effectiveness = _text(
        raw.get("effectivenessStanding"), f"controls[{index}].effectivenessStanding"
    )
    if implementation not in _IMPLEMENTATION:
        raise ValueError(f"{control_ref} has invalid implementationStanding")
    if observation not in _OBSERVATION:
        raise ValueError(f"{control_ref} has invalid observationStanding")
    if effectiveness not in _EFFECTIVENESS:
        raise ValueError(f"{control_ref} has invalid effectivenessStanding")

    implementation_evidence = _texts(
        raw.get("implementationEvidenceRefs", []),
        f"controls[{index}].implementationEvidenceRefs",
    )
    observation_evidence = _texts(
        raw.get("observationEvidenceRefs", []),
        f"controls[{index}].observationEvidenceRefs",
    )
    effectiveness_evidence = _texts(
        raw.get("effectivenessEvidenceRefs", []),
        f"controls[{index}].effectivenessEvidenceRefs",
    )
    if implementation != "UNKNOWN" and not implementation_evidence:
        raise ValueError(f"{control_ref} non-UNKNOWN implementation requires evidence")
    if observation != "UNKNOWN" and not observation_evidence:
        raise ValueError(f"{control_ref} non-UNKNOWN observation requires evidence")
    if effectiveness != "UNKNOWN" and not effectiveness_evidence:
        raise ValueError(f"{control_ref} non-UNKNOWN effectiveness requires evidence")

    if effectiveness == "VERIFIED_EFFECTIVE" and implementation != "IMPLEMENTED":
        raise ValueError(f"{control_ref} cannot be VERIFIED_EFFECTIVE without IMPLEMENTED")
    if effectiveness == "VERIFIED_INEFFECTIVE" and implementation != "IMPLEMENTED":
        raise ValueError(f"{control_ref} cannot be VERIFIED_INEFFECTIVE without IMPLEMENTED")

    return {
        "controlRef": control_ref,
        "ownerRef": _text(raw.get("ownerRef"), f"controls[{index}].ownerRef"),
        "mappedActionRefs": mapped_actions,
        "attackMitigationRefs": attack_refs,
        "d3fendRefs": d3fend_refs,
        "detectionStrategyRefs": detection_refs,
        "mappingEvidenceRefs": mapping_evidence,
        "implementationStanding": implementation,
        "implementationEvidenceRefs": implementation_evidence,
        "observationStanding": observation,
        "observationEvidenceRefs": observation_evidence,
        "effectivenessStanding": effectiveness,
        "effectivenessEvidenceRefs": effectiveness_evidence,
    }


def project_attack_coverage(
    *,
    subject: Mapping[str, object],
    applicability: Mapping[str, object],
    flow: Mapping[str, object],
    controls: list[Mapping[str, object]],
) -> dict[str, Any]:
    """
    Project task-local attack-flow/control coverage without authorizing or executing controls.

    External ATT&CK / Attack Flow / D3FEND references remain authoritative for their own
    vocabularies. Local implementation, observation, and consequence evidence remain separate.
    """
    subject_binding = _subject_binding(subject)
    dw02 = _validate_dw02(applicability, subject_binding)
    actions, edges, entries, objectives = _validate_flow(flow, subject_binding)

    normalized_controls: list[dict[str, Any]] = []
    seen_controls: set[str] = set()
    for index, raw in enumerate(controls):
        item = _validate_control(raw, set(actions), index)
        if item["controlRef"] in seen_controls:
            raise ValueError(f"duplicate controlRef: {item['controlRef']}")
        seen_controls.add(item["controlRef"])
        normalized_controls.append(item)

    paths = _all_paths(actions, edges, entries, objectives)
    common_actions = set(paths[0])
    for path in paths[1:]:
        common_actions &= set(path)

    by_action: dict[str, dict[str, list[str]]] = {
        action_ref: {
            "mappedControlRefs": [],
            "implementedControlRefs": [],
            "observedControlRefs": [],
            "verifiedEffectiveControlRefs": [],
            "verifiedIneffectiveControlRefs": [],
        }
        for action_ref in actions
    }
    for control in normalized_controls:
        for action_ref in control["mappedActionRefs"]:
            row = by_action[action_ref]
            row["mappedControlRefs"].append(control["controlRef"])
            if control["implementationStanding"] == "IMPLEMENTED":
                row["implementedControlRefs"].append(control["controlRef"])
            if control["observationStanding"] == "OBSERVED":
                row["observedControlRefs"].append(control["controlRef"])
            if control["effectivenessStanding"] == "VERIFIED_EFFECTIVE":
                row["verifiedEffectiveControlRefs"].append(control["controlRef"])
            if control["effectivenessStanding"] == "VERIFIED_INEFFECTIVE":
                row["verifiedIneffectiveControlRefs"].append(control["controlRef"])

    for row in by_action.values():
        for key in row:
            row[key] = sorted(row[key])

    structural_cuts = sorted(common_actions)
    verified_effective_at_cuts = sorted(
        action_ref
        for action_ref in structural_cuts
        if by_action[action_ref]["verifiedEffectiveControlRefs"]
    )

    path_projection: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        mapped = sorted(
            {
                ref
                for action_ref in path
                for ref in by_action[action_ref]["mappedControlRefs"]
            }
        )
        implemented = sorted(
            {
                ref
                for action_ref in path
                for ref in by_action[action_ref]["implementedControlRefs"]
            }
        )
        observed = sorted(
            {
                ref
                for action_ref in path
                for ref in by_action[action_ref]["observedControlRefs"]
            }
        )
        effective = sorted(
            {
                ref
                for action_ref in path
                for ref in by_action[action_ref]["verifiedEffectiveControlRefs"]
            }
        )
        ineffective = sorted(
            {
                ref
                for action_ref in path
                for ref in by_action[action_ref]["verifiedIneffectiveControlRefs"]
            }
        )
        path_projection.append(
            {
                "pathRef": f"path:{index}",
                "actionRefs": path,
                "mappedControlRefs": mapped,
                "implementedControlRefs": implemented,
                "observedControlRefs": observed,
                "verifiedEffectiveControlRefs": effective,
                "verifiedIneffectiveControlRefs": ineffective,
                "verifiedEffectiveControlPresent": bool(effective),
            }
        )

    validation_candidates = sorted(
        control["controlRef"]
        for control in normalized_controls
        if control["implementationStanding"] == "IMPLEMENTED"
        and control["effectivenessStanding"] == "UNKNOWN"
        and bool(set(control["mappedActionRefs"]) & common_actions)
    )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-attack-coverage-projection",
        "caseRef": subject_binding["caseRef"],
        "epochRef": subject_binding["epochRef"],
        "subject": dict(subject_binding),
        "vulnerabilityRef": dw02["vulnerabilityRef"],
        "applicabilityClaim": dw02["claim"],
        "flow": {
            "flowRef": flow["flowRef"],
            "sourceRef": flow["sourceRef"],
            "sourceDigest": flow["sourceDigest"],
            "attackFlowVersion": flow["attackFlowVersion"],
            "entryActionRefs": entries,
            "objectiveActionRefs": objectives,
        },
        "actions": [actions[key] for key in sorted(actions)],
        "edges": sorted(
            edges,
            key=lambda row: (
                row["fromActionRef"],
                row["toActionRef"],
                row["relation"],
            ),
        ),
        "controls": sorted(normalized_controls, key=lambda row: row["controlRef"]),
        "coverageByAction": {
            action_ref: by_action[action_ref] for action_ref in sorted(by_action)
        },
        "paths": path_projection,
        "structuralCutActionRefs": structural_cuts,
        "verifiedEffectiveAtStructuralCutActionRefs": verified_effective_at_cuts,
        "gaps": {
            "unmappedActionRefs": sorted(
                ref for ref, row in by_action.items() if not row["mappedControlRefs"]
            ),
            "mappedButNotImplementedActionRefs": sorted(
                ref
                for ref, row in by_action.items()
                if row["mappedControlRefs"] and not row["implementedControlRefs"]
            ),
            "implementedButUnobservedActionRefs": sorted(
                ref
                for ref, row in by_action.items()
                if row["implementedControlRefs"] and not row["observedControlRefs"]
            ),
            "implementedButEffectivenessUnknownActionRefs": sorted(
                ref
                for ref, row in by_action.items()
                if row["implementedControlRefs"]
                and not row["verifiedEffectiveControlRefs"]
                and not row["verifiedIneffectiveControlRefs"]
            ),
        },
        "authorizedValidationCandidateControlRefs": validation_candidates,
        "validationStanding": (
            "OPTIONAL_MAY_CHANGE_DOWNSTREAM_DECISION"
            if validation_candidates
            else "NOT_TRIGGERED_BY_DW04"
        ),
        "authorityGranted": False,
        "effectExecuted": False,
        "verifiedProtectionEstablished": False,
        "domainAcceptanceEstablished": False,
        "truthBoundary": (
            "DW04 is a task-local structural and evidence-state projection. Attack Flow, "
            "ATT&CK, and D3FEND remain external vocabularies. A mapped control is not proof "
            "of local implementation; implementation is not observation; observation is not "
            "verified effectiveness; verified effectiveness at one action is not a global "
            "protection verdict. Structural cuts are graph properties, not recommendations "
            "or effect authority. DW05 validation is only a candidate when additional "
            "authorized isolated evidence could change downstream planning."
        ),
    }
