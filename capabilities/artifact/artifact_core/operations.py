from __future__ import annotations

from dataclasses import dataclass

from .bindings import CapabilityBinding, CapabilityBindingRegistry
from .contracts import FileCommitment
from .profiles import ProfileRecord, ProfileRegistry


@dataclass(frozen=True)
class OperationPlan:
    operation: str
    profile: ProfileRecord
    binding: CapabilityBinding
    subject: FileCommitment
    object_contract: FileCommitment | None


class OperationPlanner:
    def __init__(
        self,
        profile_registry: ProfileRegistry,
        binding_registry: CapabilityBindingRegistry,
    ) -> None:
        self.profile_registry = profile_registry
        self.binding_registry = binding_registry

    def plan_verify(
        self,
        *,
        profile_id: str,
        subject: FileCommitment,
        object_contract: FileCommitment | None,
    ) -> OperationPlan:
        profile = self.profile_registry.resolve(profile_id)
        binding = self.binding_registry.resolve(profile_id, "verify")
        subject.verify()
        if binding.object_contract_required and object_contract is None:
            raise ValueError(f"Artifact profile requires an object contract: {profile_id}")
        if object_contract is not None:
            object_contract.verify()
        return OperationPlan(
            operation="verify",
            profile=profile,
            binding=binding,
            subject=subject,
            object_contract=object_contract,
        )
