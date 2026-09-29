from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from foundry_r4 import (  # noqa: E402
    ExperimentEnvironmentSpec,
    IsolationVector,
    ResourceBudget,
    SandboxProviderBinding,
    SandboxRealizationReceipt,
    admit_environment,
    canonical_digest,
    reconcile_realization,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64
D6 = "sha256:" + "6" * 64
D7 = "sha256:" + "7" * 64


def provider(kind: str = "libvirt-qemu-kvm") -> SandboxProviderBinding:
    return SandboxProviderBinding(
        provider_id="sandbox-provider:local-libvirt",
        provider_revision="libvirt-contract-r1",
        provider_kind=kind,
        provider_evidence_digest=D7,
    )


def budget(*, network: int = 1_000_000) -> ResourceBudget:
    return ResourceBudget(
        max_wall_seconds=300,
        max_cpu_seconds=240,
        max_memory_mib=2048,
        max_disk_mib=4096,
        max_processes=256,
        max_network_bytes=network,
    )


def hostile_isolation(**overrides) -> IsolationVector:
    values = dict(
        process="vm",
        kernel="separate_guest_kernel",
        filesystem="disposable_overlay",
        network="simulated_internet",
        credentials="synthetic_only",
        devices="explicit_allowlist",
        external_effects="policy_proxy",
        lifecycle="disposable",
        observer="independent",
    )
    values.update(overrides)
    return IsolationVector(**values)


def spec(*, threat_class: str = "hostile_code", isolation: IsolationVector | None = None, resource_budget: ResourceBudget | None = None) -> ExperimentEnvironmentSpec:
    return ExperimentEnvironmentSpec(
        environment_id="environment:test-r4",
        threat_class=threat_class,
        base_image_digest=D1,
        synthetic_world_digest=D2,
        tool_surface_digest=D3,
        observer_spec_digest=D4,
        isolation=isolation or hostile_isolation(),
        budget=resource_budget or budget(),
        provider=provider(),
    )


class SandboxContractTests(unittest.TestCase):
    def test_hostile_vm_profile_is_admitted(self) -> None:
        admission = admit_environment(spec())
        self.assertTrue(admission.admitted)
        self.assertEqual(admission.reasons, ())
        self.assertIn("kernel=separate_guest_kernel", admission.required_dimensions)

    def test_runtime_contained_local_shape_is_not_hostile_sandbox(self) -> None:
        contained = IsolationVector(
            process="separate_process_tree",
            kernel="shared",
            filesystem="restricted_host",
            network="none",
            credentials="none",
            devices="explicit_allowlist",
            external_effects="none",
            lifecycle="resettable",
            observer="same_trust_domain",
        )
        admission = admit_environment(spec(isolation=contained, resource_budget=budget(network=0)))
        self.assertFalse(admission.admitted)
        joined = " ".join(admission.reasons)
        self.assertIn("VM process boundary", joined)
        self.assertIn("separate guest kernel", joined)
        self.assertIn("disposable filesystem overlay", joined)
        self.assertIn("cannot self-verify experiment consequences", joined)

    def test_container_shared_kernel_is_not_hostile_sandbox(self) -> None:
        container = hostile_isolation(process="container", kernel="shared")
        admission = admit_environment(spec(isolation=container))
        self.assertFalse(admission.admitted)
        self.assertIn("hostile code requires a VM process boundary", admission.reasons)
        self.assertIn("hostile code requires a separate guest kernel", admission.reasons)

    def test_hostile_full_egress_is_rejected(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(network="full_egress")))
        self.assertFalse(admission.admitted)
        self.assertIn("hostile code cannot have unrestricted network egress", admission.reasons)

    def test_hostile_host_credentials_are_rejected(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(credentials="host_ambient")))
        self.assertFalse(admission.admitted)
        self.assertIn("hostile code cannot receive host/provider credentials", admission.reasons)

    def test_hostile_provider_credentials_are_rejected(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(credentials="provider_scoped")))
        self.assertFalse(admission.admitted)

    def test_hostile_direct_open_world_effects_are_rejected(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(external_effects="direct_open_world")))
        self.assertFalse(admission.admitted)
        self.assertIn("hostile code external effects must be absent, synthetic, or mediated", admission.reasons)

    def test_hostile_self_reported_observer_is_rejected(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(observer="self_reported")))
        self.assertFalse(admission.admitted)
        self.assertIn("hostile code cannot self-verify experiment consequences", admission.reasons)

    def test_network_enabled_hostile_environment_requires_positive_byte_budget(self) -> None:
        admission = admit_environment(spec(resource_budget=budget(network=0)))
        self.assertFalse(admission.admitted)
        self.assertIn("network-enabled hostile experiment requires an explicit positive network-byte budget", admission.reasons)

    def test_network_none_allows_zero_network_budget(self) -> None:
        admission = admit_environment(spec(isolation=hostile_isolation(network="none"), resource_budget=budget(network=0)))
        self.assertTrue(admission.admitted)

    def test_semantic_only_requires_no_external_effect_surface(self) -> None:
        safe = IsolationVector(
            process="same_process",
            kernel="shared",
            filesystem="restricted_host",
            network="allowlist_egress",
            credentials="provider_scoped",
            devices="none",
            external_effects="none",
            lifecycle="persistent",
            observer="independent",
        )
        self.assertTrue(admit_environment(spec(threat_class="semantic_only", isolation=safe)).admitted)
        unsafe = replace(safe, external_effects="direct_open_world")
        self.assertFalse(admit_environment(spec(threat_class="semantic_only", isolation=unsafe)).admitted)

    def test_synthetic_agent_rejects_real_credentials_and_open_world_effects(self) -> None:
        synthetic = IsolationVector(
            process="separate_process_tree",
            kernel="shared",
            filesystem="synthetic",
            network="simulated_internet",
            credentials="synthetic_only",
            devices="none",
            external_effects="synthetic_only",
            lifecycle="resettable",
            observer="independent",
        )
        self.assertTrue(admit_environment(spec(threat_class="synthetic_agent", isolation=synthetic)).admitted)
        self.assertFalse(admit_environment(spec(threat_class="synthetic_agent", isolation=replace(synthetic, credentials="provider_scoped"))).admitted)
        self.assertFalse(admit_environment(spec(threat_class="synthetic_agent", isolation=replace(synthetic, external_effects="direct_open_world"))).admitted)

    def test_environment_digest_changes_when_isolation_changes(self) -> None:
        first = spec()
        second = spec(isolation=hostile_isolation(network="none"))
        self.assertNotEqual(first.digest, second.digest)

    def test_environment_digest_changes_when_budget_changes(self) -> None:
        first = spec()
        second = spec(resource_budget=replace(budget(), max_memory_mib=4096))
        self.assertNotEqual(first.digest, second.digest)

    def test_malformed_subject_digest_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            ExperimentEnvironmentSpec(
                environment_id="environment:bad",
                threat_class="hostile_code",
                base_image_digest="not-a-digest",
                synthetic_world_digest=D2,
                tool_surface_digest=D3,
                observer_spec_digest=D4,
                isolation=hostile_isolation(),
                budget=budget(),
                provider=provider(),
            )

    def test_realization_reconciles_exact_environment(self) -> None:
        requested = spec()
        receipt = SandboxRealizationReceipt(
            requested_environment_digest=requested.digest,
            realized_provider_id=requested.provider.provider_id,
            realized_provider_revision=requested.provider.provider_revision,
            realized_base_image_digest=requested.base_image_digest,
            realized_isolation_digest=canonical_digest(requested.isolation.to_dict()),
            realization_evidence_digest=D5,
            disposable_instance_id="vm:fixture-001",
        )
        self.assertIs(reconcile_realization(requested, receipt), receipt)

    def test_realization_fails_on_provider_drift(self) -> None:
        requested = spec()
        receipt = SandboxRealizationReceipt(
            requested_environment_digest=requested.digest,
            realized_provider_id="sandbox-provider:other",
            realized_provider_revision=requested.provider.provider_revision,
            realized_base_image_digest=requested.base_image_digest,
            realized_isolation_digest=canonical_digest(requested.isolation.to_dict()),
            realization_evidence_digest=D5,
            disposable_instance_id="vm:fixture-001",
        )
        with self.assertRaises(ValueError):
            reconcile_realization(requested, receipt)

    def test_realization_fails_on_image_drift(self) -> None:
        requested = spec()
        receipt = SandboxRealizationReceipt(
            requested_environment_digest=requested.digest,
            realized_provider_id=requested.provider.provider_id,
            realized_provider_revision=requested.provider.provider_revision,
            realized_base_image_digest=D6,
            realized_isolation_digest=canonical_digest(requested.isolation.to_dict()),
            realization_evidence_digest=D5,
            disposable_instance_id="vm:fixture-001",
        )
        with self.assertRaises(ValueError):
            reconcile_realization(requested, receipt)

    def test_realization_fails_on_isolation_drift(self) -> None:
        requested = spec()
        receipt = SandboxRealizationReceipt(
            requested_environment_digest=requested.digest,
            realized_provider_id=requested.provider.provider_id,
            realized_provider_revision=requested.provider.provider_revision,
            realized_base_image_digest=requested.base_image_digest,
            realized_isolation_digest=canonical_digest(hostile_isolation(network="none").to_dict()),
            realization_evidence_digest=D5,
            disposable_instance_id="vm:fixture-001",
        )
        with self.assertRaises(ValueError):
            reconcile_realization(requested, receipt)

    def test_rejected_environment_cannot_be_realized(self) -> None:
        requested = spec(isolation=hostile_isolation(kernel="shared"))
        receipt = SandboxRealizationReceipt(
            requested_environment_digest=requested.digest,
            realized_provider_id=requested.provider.provider_id,
            realized_provider_revision=requested.provider.provider_revision,
            realized_base_image_digest=requested.base_image_digest,
            realized_isolation_digest=canonical_digest(requested.isolation.to_dict()),
            realization_evidence_digest=D5,
            disposable_instance_id="vm:fixture-001",
        )
        with self.assertRaises(ValueError):
            reconcile_realization(requested, receipt)


if __name__ == "__main__":
    unittest.main()
