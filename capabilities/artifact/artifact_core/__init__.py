"""Thin Artifact semantic kernel.

This package owns cross-family identity, profile resolution, capability bindings,
and bounded standing. Family mechanics and external effects remain delegated.
"""

from .bindings import CapabilityBinding, CapabilityBindingRegistry
from .contracts import FileCommitment
from .profiles import ProfileRecord, ProfileRegistry

__all__ = [
    "CapabilityBinding",
    "CapabilityBindingRegistry",
    "FileCommitment",
    "ProfileRecord",
    "ProfileRegistry",
]
