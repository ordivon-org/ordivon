from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any

from ordivon_security_v2.admission import ReplayBinding, canonical_digest
from ordivon_security_v2.effect_execution import (
    EffectExecutionCoordinator,
    EffectExecutionError,
    TransportLost,
    compile_effect_request,
    project_openc2,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64


def proposal(*, request_id="effect-request:test", value="on"):
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-effect-proposal-r1",
        "proposalRef": "proposal:dw07:test",
        "requestId": request_id,
        "caseRef": "case:test",
        "subject": {"subjectRef": "subject:test", "snapshotDigest": D1},
        "effectType": "fixture.set-flag",
        "action": {
            "name": "set",
            "targetRef": "fixture:flag",
            "actuatorRef": "fixture:memory-provider",
            "arguments": {"value": value},
        },
        "effectMetadata": {
            "commitPoint": "provider-write",
            "replayIdentityRef": request_id,
            "reversibility": "REVERSIBLE",
            "compensationRef": "fixture:restore-previous-value",
            "reconciliationOracleRef": "fixture:provider-ledger",
            "blastRadius": "single-in-memory-key",
        },
        "authorityObligation": {
            "id": "authority:dw07-effect-execution",
            "obligationDigest": D2,
        },
    }


def authority_context():
    return {
        "actorId": "actor:dwc-test",
        "authorityId": "range-authority:dwc-test",
        "zoneRef": "zone:fixture",
        "capability": "fixture-write",
    }


def admitted(prepared):
    req = prepared["request"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.range-effect-admission",
        "requestId": req["requestId"],
        "requestDigest": prepared["requestDigest"],
        "actorId": req["actorId"],
        "authorityId": req["authorityId"],
        "authorityDigest": D2,
        "zoneRef": req["zoneRef"],
        "capability": req["capability"],
        "effectType": req["effectType"],
        "admitted": True,
        "reason": "admitted",
    }


@dataclass
class MemoryProvider:
    provider_ref: str = "provider:memory-fixture"
    reconciliation_authoritative: bool = True
    value: str = "off"
    apply_count: int = 0
    records: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    transport_mode: str | None = None

    def reconcile(self, *, request_id, request_digest):
        row = self.records.get((request_id, request_digest))
        return None if row is None else dict(row)

    def apply(self, *, request, request_digest, proposal):
        if self.transport_mode == "before":
            raise TransportLost("before commit")
        self.apply_count += 1
        self.value = proposal["action"]["arguments"]["value"]
        state_digest = canonical_digest({"value": self.value})
        receipt = {
            "schemaVersion": 1,
            "kind": "fixture.provider-receipt",
            "requestId": request["requestId"],
            "requestDigest": request_digest,
            "effectExecuted": True,
            "worldEffectVerified": False,
            "stateDigestAfterWrite": state_digest,
            "providerCommitRef": f"commit:{request['requestId']}",
            "commitPoint": proposal["effectMetadata"]["commitPoint"],
            "replayIdentityRef": proposal["effectMetadata"]["replayIdentityRef"],
            "compensationRef": proposal["effectMetadata"]["compensationRef"],
        }
        self.records[(request["requestId"], request_digest)] = dict(receipt)
        if self.transport_mode == "after":
            raise TransportLost("after commit")
        return receipt


def execute(p=None, provider=None, admission=None, coordinator=None):
    p = p or proposal()
    prepared = compile_effect_request(p, authority_context())
    provider = provider or MemoryProvider()
    coordinator = coordinator or EffectExecutionCoordinator(ReplayBinding())
    decision = admission or admitted(prepared)
    return coordinator.execute(
        proposal=p,
        prepared=prepared,
        admission=decision,
        provider=provider,
    ), prepared, provider, coordinator


class EffectExecutionTests(unittest.TestCase):
    def test_harmless_reversible_commit_is_unverified(self):
        result, _, provider, _ = execute()
        self.assertEqual(result["standing"], "COMMITTED_UNVERIFIED")
        self.assertTrue(result["effectExecuted"])
        self.assertFalse(result["worldEffectVerified"])
        self.assertFalse(result["verifiedProtectionEstablished"])
        self.assertTrue(result["compensationAvailable"])
        self.assertEqual(provider.value, "on")
        self.assertEqual(provider.apply_count, 1)

    def test_exact_replay_reconciles_without_second_apply(self):
        provider = MemoryProvider()
        coordinator = EffectExecutionCoordinator(ReplayBinding())
        first, prepared, _, _ = execute(provider=provider, coordinator=coordinator)
        second = coordinator.execute(
            proposal=proposal(),
            prepared=prepared,
            admission=admitted(prepared),
            provider=provider,
        )
        self.assertEqual(first["standing"], "COMMITTED_UNVERIFIED")
        self.assertEqual(second["standing"], "RECONCILED_COMMITTED_UNVERIFIED")
        self.assertTrue(second["admissionReplayed"])
        self.assertEqual(provider.apply_count, 1)

    def test_changed_content_same_request_identity_fails_closed(self):
        provider = MemoryProvider()
        coordinator = EffectExecutionCoordinator(ReplayBinding())
        execute(provider=provider, coordinator=coordinator)
        p2 = proposal(value="changed")
        prepared2 = compile_effect_request(p2, authority_context())
        with self.assertRaisesRegex(ValueError, "reused with different content"):
            coordinator.execute(
                proposal=p2,
                prepared=prepared2,
                admission=admitted(prepared2),
                provider=provider,
            )
        self.assertEqual(provider.apply_count, 1)

    def test_transport_loss_after_commit_reconciles_without_retry(self):
        provider = MemoryProvider(transport_mode="after")
        result, _, provider, _ = execute(provider=provider)
        self.assertEqual(result["standing"], "TRANSPORT_LOSS_RECONCILED_UNVERIFIED")
        self.assertTrue(result["reconciliationPerformed"])
        self.assertFalse(result["retrySafeAfterReconciliation"])
        self.assertIsNotNone(result["receipt"])
        self.assertEqual(provider.apply_count, 1)

    def test_transport_loss_before_commit_returns_retry_safe_only_after_authoritative_reconcile(self):
        provider = MemoryProvider(
            transport_mode="before", reconciliation_authoritative=True
        )
        result, _, provider, _ = execute(provider=provider)
        self.assertEqual(
            result["standing"], "RETRY_SAFE_AFTER_AUTHORITATIVE_NO_COMMIT"
        )
        self.assertIsNone(result["receipt"])
        self.assertTrue(result["retrySafeAfterReconciliation"])
        self.assertEqual(provider.apply_count, 0)

    def test_non_authoritative_reconciliation_never_declares_retry_safe(self):
        provider = MemoryProvider(
            transport_mode="before", reconciliation_authoritative=False
        )
        result, _, _, _ = execute(provider=provider)
        self.assertEqual(result["standing"], "AMBIGUOUS_RECONCILIATION_REQUIRED")
        self.assertFalse(result["retrySafeAfterReconciliation"])

    def test_rejected_admission_never_calls_provider(self):
        p = proposal()
        prepared = compile_effect_request(p, authority_context())
        decision = admitted(prepared)
        decision["admitted"] = False
        decision["reason"] = "capability-not-granted"
        provider = MemoryProvider()
        result = EffectExecutionCoordinator(ReplayBinding()).execute(
            proposal=p, prepared=prepared, admission=decision, provider=provider
        )
        self.assertEqual(result["standing"], "NOT_ADMITTED")
        self.assertEqual(provider.apply_count, 0)
        self.assertFalse(result["effectExecuted"])

    def test_admission_digest_mismatch_fails_before_provider(self):
        p = proposal()
        prepared = compile_effect_request(p, authority_context())
        decision = admitted(prepared)
        decision["requestDigest"] = D1
        provider = MemoryProvider()
        with self.assertRaisesRegex(EffectExecutionError, "requestDigest"):
            EffectExecutionCoordinator(ReplayBinding()).execute(
                proposal=p, prepared=prepared, admission=decision, provider=provider
            )
        self.assertEqual(provider.apply_count, 0)

    def test_self_verifying_provider_receipt_is_rejected(self):
        class BadProvider(MemoryProvider):
            def apply(self, **kwargs):
                receipt = super().apply(**kwargs)
                receipt["worldEffectVerified"] = True
                return receipt

        with self.assertRaisesRegex(EffectExecutionError, "must not self-claim"):
            execute(provider=BadProvider())

    def test_openc2_projection_is_shape_only(self):
        value = project_openc2(proposal())
        self.assertEqual(value["command"]["action"], "set")
        self.assertEqual(value["command"]["target"], {"target_ref": "fixture:flag"})
        self.assertEqual(
            value["command"]["actuator"], {"actuator_ref": "fixture:memory-provider"}
        )
        self.assertFalse(value["transportPerformed"])
        self.assertFalse(value["authorizationDecisionIncluded"])


if __name__ == "__main__":
    unittest.main()
