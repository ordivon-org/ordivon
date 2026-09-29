from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r2 import (  # noqa: E402
    EvaluationTargetBinding,
    ModelRequestBinding,
    RealizedTargetBinding,
    TargetBoundObservation,
    diff_target_bindings,
    reconcile_realization,
)


D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64
D6 = "sha256:" + "6" * 64
D7 = "sha256:" + "7" * 64
D8 = "sha256:" + "8" * 64


def binding(model: ModelRequestBinding | None = None, **overrides) -> EvaluationTargetBinding:
    values = dict(
        security_subject_ref="security-subject:agent-under-test",
        security_subject_revision="rev-001",
        target_kind="agent",
        model=model or ModelRequestBinding("provider", "model-x", provider_model_revision="model-x-2026-09"),
        harness_revision="harness-rev-001",
        harness_config_digest=D1,
        instruction_bundle_digest=D2,
        tool_catalog_digest=D3,
        authority_surface_digest=D4,
        monitor_bundle_digest=D5,
        environment_digest=D6,
        adapter_id="adapter.test",
        adapter_revision="adapter-rev-001",
        generation={"temperature": 0.0, "max_tokens": 2048, "reasoning_effort": "fixed"},
    )
    values.update(overrides)
    return EvaluationTargetBinding(**values)


class EvaluationTargetBindingTests(unittest.TestCase):
    def test_generation_key_order_does_not_change_identity(self) -> None:
        first = binding(generation={"temperature": 0.0, "max_tokens": 2048})
        second = binding(generation={"max_tokens": 2048, "temperature": 0.0})
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.generation_digest, second.generation_digest)

    def test_instruction_change_creates_new_target_binding(self) -> None:
        first = binding()
        second = binding(instruction_bundle_digest=D7)
        diff = diff_target_bindings(first, second)
        self.assertFalse(diff.same_target_binding)
        self.assertEqual(diff.changed_fields, ("instructionBundleDigest",))

    def test_tool_catalog_and_authority_are_independent_dimensions(self) -> None:
        base = binding()
        tool_change = binding(tool_catalog_digest=D7)
        authority_change = binding(authority_surface_digest=D8)
        self.assertEqual(diff_target_bindings(base, tool_change).changed_fields, ("toolCatalogDigest",))
        self.assertEqual(diff_target_bindings(base, authority_change).changed_fields, ("authoritySurfaceDigest",))
        self.assertNotEqual(tool_change.digest, authority_change.digest)

    def test_monitor_change_is_part_of_target_identity(self) -> None:
        base = binding()
        changed = binding(monitor_bundle_digest=D8)
        self.assertEqual(diff_target_bindings(base, changed).changed_fields, ("monitorBundleDigest",))

    def test_security_subject_revision_is_required(self) -> None:
        with self.assertRaises(ValueError):
            binding(security_subject_revision="")

    def test_malformed_digest_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            binding(tool_catalog_digest="sha256:not-a-digest")

    def test_model_artifact_digest_is_strongest_pre_run_binding(self) -> None:
        model = ModelRequestBinding("local", "open-model", model_artifact_digest=D7)
        self.assertEqual(model.pre_run_identity_strength, "content_digest")

    def test_provider_revision_is_not_called_byte_exact(self) -> None:
        model = ModelRequestBinding("provider", "closed-model", provider_model_revision="2026-09-01")
        self.assertEqual(model.pre_run_identity_strength, "provider_revision")

    def test_alias_only_is_explicitly_request_only(self) -> None:
        model = ModelRequestBinding("provider", "model-latest")
        self.assertEqual(model.pre_run_identity_strength, "request_only")

    def test_realized_binding_requires_evidence_digest(self) -> None:
        req = binding()
        with self.assertRaises(ValueError):
            RealizedTargetBinding(req.digest, "model-x", "missing")

    def test_realized_identity_strength_is_conservative(self) -> None:
        req = binding()
        artifact = RealizedTargetBinding(req.digest, "model-x", D1, model_artifact_digest=D7)
        revision = RealizedTargetBinding(req.digest, "model-x", D1, provider_model_revision="rev-2")
        observed = RealizedTargetBinding(req.digest, "model-x", D1, provider_system_fingerprint="fp_fixture")
        opaque = RealizedTargetBinding(req.digest, "model-x", D1)
        self.assertEqual(artifact.identity_strength, "content_digest")
        self.assertEqual(revision.identity_strength, "provider_revision")
        self.assertEqual(observed.identity_strength, "provider_observation")
        self.assertEqual(opaque.identity_strength, "request_only")
        self.assertIn("not_byte_exact", observed.claim_scope)
        self.assertIn("no_realized_model_revision_claim", opaque.claim_scope)

    def test_exact_artifact_request_fails_closed_on_realization_drift(self) -> None:
        req = binding(model=ModelRequestBinding("local", "open-model", model_artifact_digest=D7))
        realized = RealizedTargetBinding(req.digest, "open-model", D1, model_artifact_digest=D8)
        with self.assertRaises(ValueError):
            reconcile_realization(req, realized)

    def test_exact_artifact_request_requires_artifact_in_realization(self) -> None:
        req = binding(model=ModelRequestBinding("local", "open-model", model_artifact_digest=D7))
        realized = RealizedTargetBinding(req.digest, "open-model", D1)
        with self.assertRaises(ValueError):
            reconcile_realization(req, realized)

    def test_provider_revision_request_fails_closed_on_revision_drift(self) -> None:
        req = binding(model=ModelRequestBinding("provider", "closed-model", provider_model_revision="rev-a"))
        realized = RealizedTargetBinding(req.digest, "closed-model", D1, provider_model_revision="rev-b")
        with self.assertRaises(ValueError):
            reconcile_realization(req, realized)

    def test_request_only_binding_can_gain_stronger_realization_evidence(self) -> None:
        req = binding(model=ModelRequestBinding("provider", "model-latest"))
        realized = RealizedTargetBinding(req.digest, "model-2026-09", D1, provider_model_revision="rev-observed")
        self.assertIs(reconcile_realization(req, realized), realized)
        self.assertEqual(realized.identity_strength, "provider_revision")

    def test_realization_cannot_attach_to_different_requested_binding(self) -> None:
        first = binding(instruction_bundle_digest=D2)
        second = binding(instruction_bundle_digest=D7)
        realized = RealizedTargetBinding(first.digest, "model-x", D1, provider_model_revision="model-x-2026-09")
        with self.assertRaises(ValueError):
            reconcile_realization(second, realized)

    def test_observation_is_bound_to_realized_target(self) -> None:
        req = binding()
        realized = RealizedTargetBinding(req.digest, "model-x", D1, provider_model_revision="model-x-2026-09")
        reconcile_realization(req, realized)
        observation = TargetBoundObservation(realized.digest, D2, D3, D4, D5)
        observation.require_target(realized)
        self.assertEqual(observation.to_dict()["realizedTargetDigest"], realized.digest)

    def test_observation_rejects_target_drift(self) -> None:
        first = binding(instruction_bundle_digest=D2)
        second = binding(instruction_bundle_digest=D7)
        realized_first = RealizedTargetBinding(first.digest, "model-x", D1, provider_model_revision="model-x-2026-09")
        realized_second = RealizedTargetBinding(second.digest, "model-x", D1, provider_model_revision="model-x-2026-09")
        observation = TargetBoundObservation(realized_first.digest, D2, D3, D4, D5)
        with self.assertRaises(ValueError):
            observation.require_target(realized_second)

    def test_observation_requires_digest_bound_provider_artifact(self) -> None:
        req = binding()
        realized = RealizedTargetBinding(req.digest, "model-x", D1, provider_model_revision="model-x-2026-09")
        with self.assertRaises(ValueError):
            TargetBoundObservation(realized.digest, D2, "provider-artifact", D4, D5)

    def test_adapter_revision_change_is_not_exact_replay(self) -> None:
        first = binding()
        second = binding(adapter_revision="adapter-rev-002")
        self.assertEqual(diff_target_bindings(first, second).changed_fields, ("adapterRevision",))

    def test_target_ref_is_digest_addressed(self) -> None:
        value = binding()
        self.assertEqual(value.target_ref, "eval-target:" + value.digest.removeprefix("sha256:"))

    def test_generation_configuration_must_be_json(self) -> None:
        with self.assertRaises(ValueError):
            binding(generation={"bad": {1, 2, 3}})


if __name__ == "__main__":
    unittest.main()
