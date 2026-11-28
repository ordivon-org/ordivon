"""Pure source binding for declared CI economic annotations.

This checks representation and context, not the truth of a causal assertion.
Neither a reference string nor an authority name is an independent attestation.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

ECONOMIC_OUTCOMES = {
    "UNCLASSIFIED",
    "USEFUL",
    "SAVED_WORK",
    "AVOIDABLE_WASTE",
    "FAILED_PRODUCTIVELY",
    "INFRA_FAILURE",
    "DUPLICATED",
    "SUPERSEDED",
    "NO_EXECUTION",
    "PENDING",
}


def bind_annotation(annotation: Any, expected: dict[str, Any], *, status: Any) -> dict[str, Any]:
    required = {
        "schemaVersion", "kind", "runId", "headSha", "event", "attempt",
        "providerConclusion", "economicOutcome", "reason", "evidenceRefs",
        "annotationAuthority", "timestamp",
    }
    if not isinstance(annotation, dict) or set(annotation) != required:
        raise ValueError("malformed economic annotation")
    if type(annotation["schemaVersion"]) is not int or annotation["schemaVersion"] != 1 or annotation["kind"] != "ordivon.ci-economic-annotation":
        raise ValueError("unsupported economic annotation identity")
    for key, value in expected.items():
        if key not in annotation or type(annotation[key]) is not type(value) or annotation[key] != value:
            raise ValueError(f"economic annotation does not bind observed {key}")
    if any(type(annotation[k]) is not int or annotation[k] < 1 for k in ("runId", "attempt")):
        raise ValueError("invalid economic annotation native identity")
    if not isinstance(annotation["headSha"], str) or not re.fullmatch(r"[0-9a-f]{40}", annotation["headSha"]):
        raise ValueError("invalid economic annotation source identity")
    if not all(isinstance(annotation[k], str) and annotation[k].strip()
               for k in ("event", "reason", "annotationAuthority", "timestamp")):
        raise ValueError("invalid economic annotation metadata")
    if annotation["providerConclusion"] is not None and not isinstance(annotation["providerConclusion"], str):
        raise ValueError("invalid provider conclusion")
    timestamp = datetime.fromisoformat(annotation["timestamp"].replace("Z", "+00:00"))
    if timestamp.utcoffset() is None:
        raise ValueError("economic annotation timestamp must have offset")
    refs = annotation["evidenceRefs"]
    if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref.strip() for ref in refs) or len(set(refs)) != len(refs):
        raise ValueError("economic annotation lacks declared evidence references")
    outcome = annotation["economicOutcome"]
    if not isinstance(outcome, str) or outcome not in ECONOMIC_OUTCOMES:
        raise ValueError("invalid economic annotation outcome")
    if status != "completed" and outcome not in {"PENDING", "UNCLASSIFIED"}:
        raise ValueError("nonterminal workflow attempt cannot have a final economic outcome")
    return {**annotation, "evidenceRefs": list(refs)}
