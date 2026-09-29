"""Thin Artifact semantic kernel.

This package owns cross-family identity, profile resolution, capability bindings,
and operation planning. Family mechanics and external effects remain delegated.
"""

from .bindings import CapabilityBinding, CapabilityBindingRegistry
from .contracts import FileCommitment
from .operations import OperationPlan, OperationPlanner
from .profiles import ProfileRecord, ProfileRegistry
from .standing import derive_standing_decision, required_claim_keys

__all__ = [
    "CapabilityBinding",
    "CapabilityBindingRegistry",
    "FileCommitment",
    "OperationPlan",
    "OperationPlanner",
    "ProfileRecord",
    "ProfileRegistry",
    "derive_standing_decision",
    "required_claim_keys",
]
