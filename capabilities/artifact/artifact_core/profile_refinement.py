"""Bounded common-semantic refinement between production v1 and canonical v2.

This intentionally does NOT assert that all v1 policy gates and every v2
evidence claim are equivalent. Only explicitly projected common semantics
may justify a successful refinement observation.
"""
from __future__ import annotations

from typing import Any

FAMILY = {
    "document": "text-document",
    "fixed-view": "fixed-document",
    "archive": "fixed-document",
    "accessible": "fixed-document",
}


def assess_v1_v2_refinement(v1: dict[str, Any], v2: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[str] = []

    def matches(label: str, expected: object, actual: object) -> None:
        if expected != actual or type(expected) is not type(actual):
            mismatches.append(label)

    matches("id", v1.get("id"), v2.get("id"))
    artifact_class = v1.get("artifactClass")
    family = FAMILY.get(artifact_class, artifact_class)
    matches("classification.family", family, v2.get("classification", {}).get("family"))
    construction = v2.get("construction", {})
    for field, source_field in (
        ("authorityMode", "authorityMode"), ("locale", "locale")
    ):
        matches(f"construction.{field}", v1.get(source_field), construction.get(field))

    def output_projection(v1_output: dict[str, Any], role: str) -> dict[str, Any]:
        return {
            "role": role,
            "format": v1_output.get("format"),
            "purpose": v1_output.get("purpose"),
            "required": v1_output.get("required"),
            "editable": v1_output.get("editable"),
        }

    expected_outputs = [
        output_projection(v1.get("primaryOutput", {}), "primary")
    ] + [
        output_projection(output, "companion")
        for output in v1.get("companions", [])
    ]
    actual_outputs = [
        {
            "role": output.get("role"),
            "format": output.get("format", {}).get("name"),
            "purpose": output.get("purpose"),
            "required": output.get("required"),
            "editable": output.get("editable"),
        }
        for output in v2.get("outputs", [])
    ]
    matches("outputs", expected_outputs, actual_outputs)

    # The primary target's identity and its required flag are common facts;
    # other v1 renderer and v2 evidence semantics are not claimed equivalent.
    primary = v1.get("targetRenderer", {})
    authorities = v2.get("targetAuthorities", [])
    matching = [
        item for item in authorities
        if item.get("name") == primary.get("name")
    ]
    if len(matching) != 1:
        mismatches.append("targetAuthorities.primary")
    else:
        matches(
            "targetAuthorities.primary.required",
            primary.get("required"), matching[0].get("required"),
        )

    return {
        "complete": not mismatches,
        "status": "PASS" if not mismatches else "FAIL",
        "mismatches": mismatches,
        "scope": (
            "identity, family, construction, outputs and primary renderer "
            "refinement only; v1 gates vs v2 requiredEvidence and semantic "
            "policies remain unproven and must not be promoted"
        ),
    }
