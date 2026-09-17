"""Thin Artifact semantic kernel.

This package owns cross-family identity, profile resolution, capability bindings,
and operation planning. Family mechanics and external effects remain delegated.
"""

from .contracts import FileCommitment
from .profiles import ProfileRecord, ProfileRegistry
from .bindings import CapabilityBinding, CapabilityBindingRegistry
from .operations import OperationPlan, OperationPlanner

__all__ = [
    "CapabilityBinding",
    "CapabilityBindingRegistry",
    "FileCommitment",
    "OperationPlan",
    "OperationPlanner",
    "ProfileRecord",
    "ProfileRegistry",
]
