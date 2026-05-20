from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "kernel"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


def digest(char: str = "a") -> str:
    return "sha256:" + char * 64


def test_kernel_schemas_are_valid_json_schema_documents() -> None:
    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(schema_path.read_text())
        jsonschema.Draft202012Validator.check_schema(schema)


def test_observed_event_rejects_ai_written_origin() -> None:
    schema = load_schema("observed-event.schema.json")
    forged_event = {
        "eventId": "evt_forged",
        "traceId": "trace_1",
        "source": "ai:self-report",
        "sourceIdentity": "codex",
        "observedSequence": 1,
        "eventType": "RESOURCE_CHANGED",
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:test-1",
        "timestamp": "2026-05-16T00:00:00Z",
        "payloadHash": digest(),
        "prevEventHash": digest("b"),
        "origin": "AI_WRITTEN",
        "status": "Observed",
        "authorityRef": "auth_1",
        "idempotencyKey": "intent_1:obligation_1:record:test-1",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(forged_event, schema)


def test_observed_event_accepts_system_observed_origin() -> None:
    schema = load_schema("observed-event.schema.json")
    observed_event = {
        "eventId": "evt_valid",
        "traceId": "trace_1",
        "source": "adapter:mock-record",
        "sourceIdentity": "system:mock-record-adapter",
        "observedSequence": 1,
        "eventType": "RESOURCE_CHANGED",
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:test-1",
        "timestamp": "2026-05-16T00:00:00Z",
        "payloadHash": digest(),
        "prevEventHash": digest("b"),
        "origin": "SYSTEM_OBSERVED",
        "status": "Observed",
        "authorityRef": "auth_1",
        "idempotencyKey": "intent_1:obligation_1:record:test-1",
    }

    jsonschema.validate(observed_event, schema)


def test_authority_token_requires_single_use_binding() -> None:
    schema = load_schema("authority-token.schema.json")
    token = {
        "jti": "auth_1",
        "kid": "ordivon-test-authority-v1",
        "iss": "ordivon-authority-service",
        "sub": "agent:planner",
        "audience": "adapter:mock-record",
        "intentId": "intent_1",
        "obligationId": "obligation_1",
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:test-1",
        "policyHash": digest(),
        "issuedAt": "2026-05-16T00:00:00Z",
        "notBefore": "2026-05-16T00:00:00Z",
        "expiresAt": "2026-05-16T00:05:00Z",
        "maxUseCount": 2,
        "idempotencyKey": "intent_1:obligation_1:record:test-1",
        "sealRef": "seal_1",
        "signature": "base64-signature-placeholder",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(token, schema)


def test_review_decision_requires_authority_ref() -> None:
    schema = load_schema("review-decision.schema.json")
    review_decision = {
        "decisionId": "review_1",
        "action": "PromoteCandidatePolicy",
        "targetRef": "candidate-policy:1",
        "reviewer": "human:reviewer",
        "createdAt": "2026-05-16T00:00:00Z",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(review_decision, schema)


def test_closure_requires_verification_receipt() -> None:
    schema = load_schema("closure.schema.json")
    closure = {
        "closureId": "closure_1",
        "targetRef": "debt:1",
        "closureReason": "fixed",
        "reopenConditions": ["same mismatch recurs"],
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(closure, schema)


def test_candidate_policy_cannot_claim_active_status() -> None:
    schema = load_schema("candidate-policy.schema.json")
    candidate_policy = {
        "candidatePolicyId": "candidate-policy:1",
        "scope": "new-kernel-bootstrap",
        "ruleText": "deny undeclared mutating actions",
        "evidenceRefs": ["debt:1"],
        "metricsGate": {"minRecurrence": 2},
        "status": "Active",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(candidate_policy, schema)


def test_dogfood_seal_records_critical_bypasses_instead_of_hiding_them() -> None:
    schema = load_schema("dogfood-seal.schema.json")
    dogfood_seal = {
        "sealId": "dogfood-seal:p8",
        "scenarioCount": 1,
        "criticalBypasses": 1,
        "scenarioRefs": ["rt:closure-without-verification"],
        "receiptRefs": ["receipt:rt-closure-without-verification"],
        "issuedAt": "2026-05-16T00:00:00Z",
    }

    jsonschema.validate(dogfood_seal, schema)


def test_red_team_scenario_rejects_self_certifying_blocked_result() -> None:
    schema = load_schema("red-team-scenario.schema.json")
    self_certifying = {
        "scenarioId": "rt:self-certifying",
        "description": "old fixture wrote the result into the input",
        "expectedGate": "Comparator.Over",
        "blocked": True,
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(self_certifying, schema)


def test_red_team_scenario_accepts_attack_input_only() -> None:
    schema = load_schema("red-team-scenario.schema.json")
    scenario = {
        "scenarioId": "rt:duplicate-dispatch",
        "description": "same idempotency key should not dispatch twice",
        "attack": "duplicateDispatch",
        "expectedVerdict": "Over",
    }

    jsonschema.validate(scenario, schema)


def test_policy_schema_rejects_hand_written_active_policy() -> None:
    schema = load_schema("policy.schema.json")
    policy = {
        "policyId": "policy:bad",
        "candidatePolicyId": "candidate-policy:1",
        "policyHash": digest(),
        "scope": "new-kernel-hardening",
        "status": "Active",
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(policy, schema)
