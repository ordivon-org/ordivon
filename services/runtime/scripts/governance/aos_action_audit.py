#!/usr/bin/env python3
"""Audit AIActionDeclaration vs ObservedAction conformance."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

from jsonschema import Draft202012Validator

import observe_action


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "docs/governance/schemas/action-conformance-rules.json"
DECL_SCHEMA = ROOT / "schemas/governance/ai-action-declaration.schema.json"
OBS_SCHEMA = ROOT / "schemas/governance/observed-action.schema.json"
AUDIT_SCHEMA = ROOT / "schemas/governance/conformance-audit.schema.json"
FINDINGS_LEDGER = ROOT / "docs/governance/action-conformance-findings.jsonl"
AUDIT_RECEIPTS = ROOT / "receipts/governance/action-audits"
AUDIT_SCHEMA_VERSION = "aos-conformance-audit-v0.1"
AUDIT_CREATED_BY = "scripts/governance/aos_action_audit.py"
ACTION_CLASSES = {
    "READ_RESOURCE",
    "CALL_TOOL_READONLY",
    "CALL_TOOL_MUTATING",
    "SEND_MESSAGE",
    "STATE_TRANSITION",
}
VERDICT_TO_RESULT = {
    "ExactMatch": "MATCH",
    "Under": "MISMATCH",
    "Over": "MISMATCH",
    "Mis": "MISMATCH",
    "Unverifiable": "UNKNOWN",
    "DeclarationInvalid": "MISMATCH",
    "SystemError": "UNKNOWN",
}

NOT_JUDGED = [
    "output quality",
    "AI intent",
    "evidence sufficiency",
    "authorization",
    "semantic correctness",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def object_hash(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def validate_with_schema(obj: dict, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    return [f"{schema_path.name}: {err.message}" for err in sorted(validator.iter_errors(obj), key=lambda e: e.path)]


def path_matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        clean = pattern.rstrip("/")
        if any(ch in clean for ch in "*?[]"):
            if fnmatch(path, clean):
                return True
        elif path == clean or path.startswith(clean + "/"):
            return True
    return False


def all_changed_paths(observed: dict) -> set[str]:
    return (
        set(observed.get("observed_files_added", []))
        | set(observed.get("observed_files_modified", []))
        | set(observed.get("observed_files_deleted", []))
    )


def finding(finding_type: str, description: str, declared=None, observed=None, affected_paths=None) -> dict:
    return {
        "finding_type": finding_type,
        "description": description,
        "declared": declared,
        "observed": observed,
        "affected_paths": sorted(affected_paths or []),
    }


def legacy_result_for(verdict: str, review_required: list[str]) -> str:
    if verdict == "ExactMatch" and review_required:
        return "REVIEW_REQUIRED"
    return VERDICT_TO_RESULT[verdict]


def observed_boundary_errors(declaration: dict, observed: dict) -> list[str]:
    errors: list[str] = []
    if observed.get("origin") != "SYSTEM_OBSERVED":
        errors.append(f"observed_origin_not_system_observed:{observed.get('origin')}")
    if observed.get("source_declaration_ref") != declaration.get("object_id"):
        errors.append("observed_source_declaration_ref_mismatch")

    producer_values = [
        str(observed.get("created_by", "")).lower(),
        str((observed.get("provenance") or {}).get("collector", "")).lower(),
    ]
    forbidden_producers = ("ai_agent", "ai-written", "ai_written", "codex", "llm")
    for value in producer_values:
        if any(marker in value for marker in forbidden_producers):
            errors.append(f"observed_created_by_untrusted:{value}")

    for source in observed.get("observation_sources", []):
        lowered = str(source).lower()
        if "ai_written" in lowered or "ai self-report" in lowered or "llm self-report" in lowered:
            errors.append(f"observed_source_untrusted:{source}")
    return sorted(set(errors))


def declaration_consistency_errors(declaration: dict, rules: dict) -> list[str]:
    errors: list[str] = []
    action_class = declaration.get("action_class")
    if action_class not in ACTION_CLASSES:
        errors.append(f"action_class_invalid:{action_class}")

    known_actions = rules.get("action_types") or {}
    declared_action = declaration.get("declared_action")
    if declared_action not in known_actions:
        errors.append(f"declared_action_not_in_registry:{declared_action}")
    elif known_actions[declared_action].get("action_class") != action_class:
        errors.append(
            f"action_class_mismatch:{declared_action}:"
            f"{action_class}!={known_actions[declared_action].get('action_class')}"
        )

    spec = declaration.get("action_spec") or {}
    cardinality = spec.get("cardinality") or {}
    if cardinality.get("max", 0) < cardinality.get("min", 0):
        errors.append("action_spec_cardinality_max_lt_min")
    for target in spec.get("target") or []:
        if target not in declaration.get("declared_scope", []):
            errors.append(f"action_spec_target_outside_declared_scope:{target}")
    return errors


def compute_verdict(
    declaration_errors: list[str],
    observed_errors: list[str],
    missing_required_observation: bool,
    findings: list[dict],
) -> str:
    if declaration_errors:
        return "DeclarationInvalid"
    if observed_errors:
        return "SystemError"
    if missing_required_observation:
        return "Unverifiable"

    finding_types = {item.get("finding_type") for item in findings}
    has_out_of_scope = "SCOPE_MISMATCH" in finding_types
    has_missing_output = "EXPECTED_OUTPUT_MISSING" in finding_types
    has_forbidden = "FORBIDDEN_ACTION" in finding_types
    has_action_mismatch = "ACTION_MISMATCH" in finding_types

    if has_forbidden or has_action_mismatch or (has_out_of_scope and has_missing_output):
        return "Mis"
    if has_out_of_scope:
        return "Over"
    if has_missing_output:
        return "Under"
    return "ExactMatch"


def scan_receipt_authorization(receipt_paths: list[str]) -> tuple[bool, list[str]]:
    structured_forbidden = False
    review_required: list[str] = []
    terms = ["authorized", "approved", "approval granted", "safe to execute"]
    for rel in receipt_paths:
        path = ROOT / rel
        if not path.exists() or not path.is_file():
            continue
        raw = path.read_text(errors="ignore")
        try:
            data = json.loads(raw)
            auth = data.get("authorization")
            if isinstance(auth, dict) and auth.get("status") == "approved":
                structured_forbidden = True
        except json.JSONDecodeError:
            pass
        lowered = raw.lower()
        if any(term in lowered for term in terms):
            review_required.append(f"authorization_language:{rel}")
    return structured_forbidden, review_required


def registry_entry_present(declaration: dict, observed: dict, changed_paths: set[str]) -> bool:
    if observed.get("observed_registry_entries"):
        return True
    if "docs/governance/document-registry.jsonl" not in changed_paths:
        return False
    scope = declaration.get("declared_scope", [])
    registry_path = ROOT / "docs/governance/document-registry.jsonl"
    if not registry_path.exists():
        return False
    for line in registry_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if path_matches(row.get("path", ""), scope):
            return True
    return False


def debt_closed(observed: dict) -> bool:
    for transition in observed.get("observed_debt_transitions", []):
        if transition.get("to_status") == "CLOSED":
            return True
    return False


def evaluate(
    declaration: dict,
    observed: dict,
    declaration_schema_errors: list[str] | None = None,
    observed_schema_errors: list[str] | None = None,
) -> dict:
    rules = load_json(RULES_PATH)
    changed_paths = all_changed_paths(observed)
    preexisting_overlap = set(observed.get("preexisting_dirty_overlap", []))
    effective_changed = changed_paths - preexisting_overlap

    findings: list[dict] = []
    unknowns = sorted(set(observed.get("unknown_observations", [])))
    review_required: list[str] = []
    declaration_errors = list(declaration_schema_errors or [])
    observed_errors = list(observed_schema_errors or [])
    declaration_errors.extend(declaration_consistency_errors(declaration, rules))
    observed_errors.extend(observed_boundary_errors(declaration, observed))

    missing_required_observation = not observed.get("observation_sources") or any(
        item.startswith("git_diff_unavailable") for item in unknowns
    )

    for error in sorted(set(declaration_errors)):
        findings.append(
            finding(
                "DECLARATION_INVALID",
                "Declaration is not machine-comparable under the v0.1 AOS contract.",
                declared=error,
            )
        )

    for error in sorted(set(observed_errors)):
        findings.append(
            finding(
                "SYSTEM_ERROR",
                "ObservedAction failed the SYSTEM_OBSERVED trust boundary or schema contract.",
                observed=error,
            )
        )

    out_of_scope = [path for path in effective_changed if not path_matches(path, declaration.get("declared_scope", []))]
    if out_of_scope:
        findings.append(
            finding(
                "SCOPE_MISMATCH",
                "Observed changed paths outside declared_scope.",
                declared=declaration.get("declared_scope", []),
                observed=out_of_scope,
                affected_paths=out_of_scope,
            )
        )

    if preexisting_overlap:
        review_required.append(f"preexisting_dirty_overlap:{','.join(sorted(preexisting_overlap))}")

    not_allowed = set(declaration.get("not_allowed", []))
    deleted = set(observed.get("observed_files_deleted", []))

    if "change_ci" in not_allowed:
        ci_paths = [p for p in effective_changed if path_matches(p, [".github/workflows/**", ".github/dependabot.yml"])]
        if ci_paths:
            findings.append(
                finding(
                    "FORBIDDEN_ACTION",
                    "Changed CI files while change_ci is forbidden.",
                    "change_ci",
                    ci_paths,
                    ci_paths,
                )
            )

    if "modify_policy" in not_allowed:
        policy_paths = [
            p
            for p in effective_changed
            if path_matches(p, ["policies/**", "docs/governance/policy-activation-ledger.jsonl"])
        ]
        if policy_paths:
            findings.append(
                finding(
                    "FORBIDDEN_ACTION",
                    "Changed policy files while modify_policy is forbidden.",
                    "modify_policy",
                    policy_paths,
                    policy_paths,
                )
            )

    if "delete_files" in not_allowed and deleted - preexisting_overlap:
        deleted_paths = sorted(deleted - preexisting_overlap)
        findings.append(
            finding(
                "FORBIDDEN_ACTION",
                "Deleted files while delete_files is forbidden.",
                "delete_files",
                deleted_paths,
                deleted_paths,
            )
        )

    if "close_debt" in not_allowed and debt_closed(observed):
        findings.append(
            finding(
                "FORBIDDEN_ACTION", "Observed debt transition to CLOSED while close_debt is forbidden.", "close_debt"
            )
        )

    if "claim_authorization" in not_allowed:
        structured, auth_review = scan_receipt_authorization(observed.get("observed_receipts", []))
        if structured:
            findings.append(
                finding(
                    "FORBIDDEN_ACTION",
                    "Structured receipt claims approved authorization while claim_authorization is forbidden.",
                    "claim_authorization",
                )
            )
        review_required.extend(auth_review)

    expected_outputs = set(declaration.get("expected_outputs", []))
    for expected in sorted(expected_outputs):
        present = True
        if expected == "receipt":
            present = bool(observed.get("observed_receipts"))
        elif expected == "registry_entry":
            present = registry_entry_present(declaration, observed, changed_paths)
        elif expected == "candidate_rule_file":
            present = any(
                path_matches(
                    path, ["docs/governance/candidate-rule-drafts.jsonl", "docs/governance/candidate-rules/**"]
                )
                for path in changed_paths
            )
        elif expected == "conformance_audit_receipt":
            present = any(path_matches(path, ["receipts/governance/action-audits/**"]) for path in changed_paths)
            if not present:
                slug = observe_action.slug_from_object_id(declaration["object_id"])
                present = (AUDIT_RECEIPTS / f"{slug}.json").exists()
        if not present:
            findings.append(
                finding(
                    "EXPECTED_OUTPUT_MISSING",
                    f"Expected output missing: {expected}.",
                    declared=expected,
                    observed=[],
                )
            )

    if missing_required_observation:
        findings.append(
            finding(
                "UNVERIFIABLE",
                "Required observation source is missing or unavailable.",
                observed=unknowns,
            )
        )

    verdict = compute_verdict(
        sorted(set(declaration_errors)),
        sorted(set(observed_errors)),
        missing_required_observation,
        findings,
    )
    result = legacy_result_for(verdict, review_required)

    slug = observe_action.slug_from_object_id(declaration["object_id"])
    now = datetime.now(timezone.utc).isoformat()
    audit = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "object_id": f"aos:actions:ConformanceAudit:{slug}",
        "object_kind": "ConformanceAudit",
        "origin": "SYSTEM_DERIVED",
        "created_at": now,
        "created_by": AUDIT_CREATED_BY,
        "provenance": {
            "input_refs": [declaration.get("object_id", ""), observed.get("object_id", "")],
            "collector": AUDIT_CREATED_BY,
            "digest": object_hash({"declaration": declaration, "observed": observed}),
            "signature_refs": [],
        },
        "state": "ISSUED",
        "declaration_ref": declaration["object_id"],
        "observed_action_ref": observed["object_id"],
        "verdict": verdict,
        "result": result,
        "findings": findings,
        "unknowns": unknowns,
        "review_required": sorted(set(review_required)),
        "not_judged": NOT_JUDGED,
        "audited_at": now,
    }
    return audit


def append_findings(audit: dict) -> None:
    if not audit.get("findings"):
        return
    FINDINGS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = set()
    if FINDINGS_LEDGER.exists():
        for line in FINDINGS_LEDGER.read_text().splitlines():
            if not line.strip():
                continue
            try:
                existing_ids.add(json.loads(line).get("finding_id"))
            except json.JSONDecodeError:
                continue
    with FINDINGS_LEDGER.open("a") as handle:
        for idx, item in enumerate(audit["findings"], start=1):
            finding_id = f"{audit['object_id']}:{idx:03d}"
            if finding_id in existing_ids:
                continue
            row = {
                "finding_id": finding_id,
                "audit_ref": audit["object_id"],
                "declaration_ref": audit["declaration_ref"],
                "verdict": audit["verdict"],
                "result": audit["result"],
                **item,
                "recorded_at": audit.get("audited_at"),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_receipt(audit: dict) -> Path:
    AUDIT_RECEIPTS.mkdir(parents=True, exist_ok=True)
    slug = observe_action.slug_from_object_id(audit["declaration_ref"])
    path = AUDIT_RECEIPTS / f"{slug}.json"
    receipt = {
        "schema_version": audit["schema_version"],
        "receipt_id": f"action-audit-{slug}",
        "audit_ref": audit["object_id"],
        "declaration_ref": audit["declaration_ref"],
        "observed_action_ref": audit["observed_action_ref"],
        "origin": "SYSTEM_DERIVED",
        "created_at": audit["created_at"],
        "created_by": AUDIT_CREATED_BY,
        "provenance": audit["provenance"],
        "state": "ISSUED",
        "verdict": audit["verdict"],
        "result": audit["result"],
        "findings": audit["findings"],
        "unknowns": audit["unknowns"],
        "review_required": audit["review_required"],
        "not_judged": audit["not_judged"],
        "authorization": {
            "status": "not_requested",
            "rationale": (
                "Receipt is evidence, not authorization. ExactMatch does not authorize merge, release, deploy, "
                "policy activation, broker writes, live trading, or any external action."
            ),
        },
        "written_at": audit.get("audited_at"),
    }
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit AIActionDeclaration vs ObservedAction")
    parser.add_argument("--declaration", required=True, help="Path to AIActionDeclaration object")
    parser.add_argument("--observed", help="Path to ObservedAction object; if omitted, observe current repo state")
    parser.add_argument("--write-receipt", action="store_true", help="Write audit receipt and findings ledger")
    parser.add_argument("--json", action="store_true", help="Print JSON audit")
    args = parser.parse_args()

    declaration = load_json(Path(args.declaration))
    observed = (
        load_json(Path(args.observed)) if args.observed else observe_action.build_observation(Path(args.declaration))
    )

    declaration_errors = validate_with_schema(declaration, DECL_SCHEMA)
    observed_errors = validate_with_schema(observed, OBS_SCHEMA)
    audit = evaluate(declaration, observed, declaration_errors, observed_errors)
    errors = validate_with_schema(audit, AUDIT_SCHEMA)
    if errors:
        for error in errors:
            print(f"  ✗ {error}", file=sys.stderr)
        sys.exit(1)

    receipt_path = None
    if args.write_receipt:
        receipt_path = write_receipt(audit)
        append_findings(audit)

    if args.json:
        print(json.dumps(audit, indent=2, ensure_ascii=False))
    else:
        print(f"{audit['verdict']} ({audit['result']}): {len(audit['findings'])} finding(s)")
        if receipt_path:
            print(f"Receipt: {receipt_path.relative_to(ROOT)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
