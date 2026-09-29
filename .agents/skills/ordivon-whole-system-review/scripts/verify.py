from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "assets" / "review-record.schema.json"
VALID_FIXTURE = ROOT / "fixtures" / "valid-review-record.json"
INVALID_FIXTURE = ROOT / "fixtures" / "invalid-realized-without-proof.json"
SKILL_PATH = ROOT / "SKILL.md"

RUN_PROOF = {"LIVE_OWNER_RECEIPT", "EXECUTED_VERIFICATION"}
DISPOSITIONS = {
    "ARCHITECTURE_DECISION",
    "FITNESS_FUNCTION",
    "OPERATIONAL_CONTROL",
    "REDESIGN",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(record: dict) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [e.message for e in sorted(validator.iter_errors(record), key=lambda e: list(e.path))]


def semantic_errors(record: dict) -> list[str]:
    errors: list[str] = []
    evidence = {item["evidenceId"]: item for item in record.get("evidence", [])}
    finding_ids = {item["findingId"] for item in record.get("findings", [])}

    def require_refs(refs: list[str], owner: str) -> list[dict]:
        resolved = []
        for ref in refs:
            if ref not in evidence:
                errors.append(f"{owner} references missing evidence {ref}")
            else:
                resolved.append(evidence[ref])
        return resolved

    for surface in record.get("systemSurface", []):
        require_refs(surface.get("evidenceRefs", []), f"surface:{surface.get('id')}")

    for capability in record.get("capabilities", []):
        resolved = require_refs(
            capability.get("evidenceRefs", []),
            f"capability:{capability.get('capability')}",
        )
        if capability.get("state") == "REALIZED" and not any(
            item.get("type") in RUN_PROOF for item in resolved
        ):
            errors.append(
                f"REALIZED capability lacks live/executed proof: {capability.get('capability')}"
            )

    for finding in record.get("findings", []):
        require_refs(finding.get("evidenceRefs", []), f"finding:{finding.get('findingId')}")

    for theme in record.get("riskThemes", []):
        for ref in theme.get("findingRefs", []):
            if ref not in finding_ids:
                errors.append(f"riskTheme:{theme.get('themeId')} references missing finding {ref}")

    for item in record.get("recurringFindingDispositions", []):
        if item.get("findingRef") not in finding_ids:
            errors.append(f"disposition references missing finding {item.get('findingRef')}")
        if item.get("disposition") not in DISPOSITIONS:
            errors.append(f"invalid disposition {item.get('disposition')}")

    source = record.get("sourceBoundary", {})
    if source.get("censusConfidence") != "HIGH" and not source.get("limitations"):
        errors.append("non-HIGH census confidence requires at least one limitation")

    return errors


def verify_skill_text() -> list[str]:
    text = SKILL_PATH.read_text(encoding="utf-8")
    required = [
        "Current truth before narrative",
        "Full surface, adaptive depth",
        "REALIZED",
        "LATENT",
        "BLOCKED",
        "DEGRADED",
        "RETIRED",
        "references/ledger-contract.md",
        "assets/review-record.schema.json",
        "Completion gate",
    ]
    return [f"SKILL.md missing required contract text: {needle}" for needle in required if needle not in text]


def verify() -> list[str]:
    errors = verify_skill_text()

    valid = load_json(VALID_FIXTURE)
    errors.extend(f"valid fixture schema: {e}" for e in schema_errors(valid))
    errors.extend(f"valid fixture semantic: {e}" for e in semantic_errors(valid))

    invalid = load_json(INVALID_FIXTURE)
    invalid_schema = schema_errors(invalid)
    if invalid_schema:
        errors.extend(f"invalid fixture unexpectedly fails structural schema: {e}" for e in invalid_schema)
    invalid_semantic = semantic_errors(invalid)
    if not any("REALIZED capability lacks live/executed proof" in e for e in invalid_semantic):
        errors.append("invalid fixture did not trigger REALIZED proof invariant")

    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("whole-system-review skill verification: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
