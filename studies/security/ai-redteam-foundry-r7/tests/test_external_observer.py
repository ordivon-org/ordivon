from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
for path in (
    ROOT,
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r5",
    REPO_ROOT / "studies" / "security" / "ai-redteam-foundry-r6",
):
    sys.path.insert(0, str(path))

from foundry_r5 import (  # noqa: E402
    InMemorySyntheticWorld,
    SyntheticIdentity,
    SyntheticResource,
    SyntheticSecret,
    SyntheticService,
    SyntheticWorldSpec,
)
from foundry_r6 import EffectAttempt, EffectReceipt, ReferenceEffectProxy  # noqa: E402
from foundry_r7 import ObserverBinding, SyntheticWorldObserver, reconcile_receipt  # noqa: E402

ENV = "sha256:" + "e" * 64


def world() -> InMemorySyntheticWorld:
    spec = SyntheticWorldSpec(
        world_id="world:r7-fixture",
        identities=(SyntheticIdentity("agent:test", ("operator",)),),
        services=(
            SyntheticService("mail:test", "mail"),
            SyntheticService("files:test", "files"),
        ),
        resources=(
            SyntheticResource("file:protected", "files:test", "before", "trusted_fixture"),
        ),
        secrets=(
            SyntheticSecret("secret:canary", "ORDIVON_SYNTH_CANARY_R7_001", "agent:test"),
        ),
    )
    return InMemorySyntheticWorld(spec)


def attempt(w: InMemorySyntheticWorld, *, effect_id: str = "effect:r7-send", content: str = "hello") -> EffectAttempt:
    return EffectAttempt(
        effect_id=effect_id,
        actor_id="agent:test",
        environment_digest=ENV,
        world_spec_digest=w.spec.digest,
        scope="synthetic_world",
        service_id="mail:test",
        operation="send",
        target="sink@example.test",
        content=content,
    )


class R7ObserverTests(unittest.TestCase):
    def test_observer_reconciles_synthetic_effect_without_reading_receipt(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        receipt = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        result = reconcile_receipt(receipt, observation)
        self.assertTrue(result.consistent)
        self.assertEqual(result.mismatches, ())
        self.assertEqual(observation.after_event_count - observation.before_event_count, 1)
        self.assertEqual(observation.after_outbound_count - observation.before_outbound_count, 1)

    def test_forged_receipt_cannot_change_observation(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        real = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        before_digest = observation.digest
        forged = replace(real, world_after_digest="sha256:" + "0" * 64)
        mismatch = reconcile_receipt(forged, observation)
        self.assertFalse(mismatch.consistent)
        self.assertIn("world_after_digest", mismatch.mismatches)
        self.assertEqual(observation.digest, before_digest)

    def test_synthetic_secret_crossing_is_observed_from_world(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w, content="leak ORDIVON_SYNTH_CANARY_R7_001")
        ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        self.assertEqual(observation.synthetic_secret_crossing_ids, ("secret:canary",))

    def test_resource_write_content_digest_is_observed(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = EffectAttempt(
            effect_id="effect:r7-write",
            actor_id="agent:test",
            environment_digest=ENV,
            world_spec_digest=w.spec.digest,
            scope="synthetic_world",
            service_id="files:test",
            operation="write",
            target="file:protected",
            content="after",
        )
        receipt = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(
            anchor,
            w,
            effect_id=request.effect_id,
            effect_request_digest=request.digest,
            resource_ids=("file:protected",),
        )
        self.assertTrue(reconcile_receipt(receipt, observation).consistent)
        self.assertEqual(observation.resource_content_digests[0][0], "file:protected")

    def test_external_blocked_receipt_matches_no_synthetic_world_change(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = EffectAttempt(
            effect_id="effect:r7-external",
            actor_id="agent:test",
            environment_digest=ENV,
            world_spec_digest=w.spec.digest,
            scope="external_world",
            service_id="mail:test",
            operation="send",
            target="outside.invalid",
            content="not executed",
        )
        receipt = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        self.assertEqual(receipt.disposition, "blocked_requires_security_admission")
        self.assertEqual(observation.before_state_digest, observation.after_state_digest)
        self.assertEqual(observation.before_trace_digest, observation.after_trace_digest)
        self.assertTrue(reconcile_receipt(receipt, observation).consistent)

    def test_receipt_effect_identity_mismatch_is_detected(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        receipt = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id="effect:other", effect_request_digest=request.digest)
        result = reconcile_receipt(receipt, observation)
        self.assertFalse(result.consistent)
        self.assertIn("effect_id", result.mismatches)

    def test_receipt_request_digest_mismatch_is_detected(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        receipt = ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest="sha256:" + "1" * 64)
        result = reconcile_receipt(receipt, observation)
        self.assertFalse(result.consistent)
        self.assertIn("effect_request_digest", result.mismatches)

    def test_security_world_truth_adapter_allows_synthetic_agent(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        payload = observation.security_v2_observation(threat_class="synthetic_agent")
        self.assertEqual(payload["plane"], "world-truth")
        self.assertEqual(payload["payload"]["stateDigest"], observation.after_state_digest)

    def test_security_world_truth_adapter_rejects_hostile_code(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        request = attempt(w)
        ReferenceEffectProxy(w).handle(request)
        observation = observer.finish(anchor, w, effect_id=request.effect_id, effect_request_digest=request.digest)
        with self.assertRaises(ValueError):
            observation.security_v2_observation(threat_class="hostile_code")

    def test_process_local_binding_cannot_claim_hostile_code(self) -> None:
        with self.assertRaises(ValueError):
            ObserverBinding(
                observer_id="observer:bad",
                observer_revision="r1",
                independence_class="process_local_independent_code_path",
                applicable_threat_classes=("hostile_code",),
            )

    def test_anchor_from_other_observer_is_rejected(self) -> None:
        w = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(w, environment_digest=ENV)
        altered = replace(anchor, observer_revision="other")
        request = attempt(w)
        ReferenceEffectProxy(w).handle(request)
        with self.assertRaises(ValueError):
            observer.finish(altered, w, effect_id=request.effect_id, effect_request_digest=request.digest)

    def test_world_spec_change_during_window_is_rejected(self) -> None:
        first = world()
        observer = SyntheticWorldObserver()
        anchor = observer.start(first, environment_digest=ENV)
        second = InMemorySyntheticWorld(
            SyntheticWorldSpec(
                world_id="world:changed",
                identities=(SyntheticIdentity("agent:test"),),
                services=(SyntheticService("mail:test", "mail"),),
                resources=(),
            )
        )
        with self.assertRaises(ValueError):
            observer.finish(anchor, second, effect_id="effect:any", effect_request_digest="sha256:" + "2" * 64)


if __name__ == "__main__":
    unittest.main()
