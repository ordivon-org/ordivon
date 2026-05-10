"""Ordivon Registry Control Plane — unified object model for all governed artifacts.

This package defines the RegistryObject model, authority/lifecycle enums,
invariant validators, and import adapters that convert existing registry
sources into RegistryObject instances.

DO NOT import metabolic models here.  The two planes coexist during RG-1/RG-2.
"""

from ordivon_verify.registry.adapters import (
    RegistryImportResult,
    import_all_registry_sources,
    import_artifact_registry,
    import_aux_ledgers,
    import_checker_registry,
    import_document_registry,
    import_scanner_surfaces,
)
from ordivon_verify.registry.reconciler import (
    ReconcileResult,
    ReconcileSummary,
    reconcile_imported_sources,
    reconcile_registry_objects,
)
from ordivon_verify.registry.models import (
    ACTIVE_LIFECYCLE_STATES,
    AuthorityTier,
    DECISION_AUTHORITY_TIERS,
    LifecycleState,
    REGISTRY_INVARIANTS,
    RegistryFinding,
    RegistryFindingStatus,
    RegistryKind,
    RegistryObject,
    TERMINAL_LIFECYCLE_STATES,
    invariant_active_t0_requires_owner,
    invariant_archive_snapshot_not_current_truth,
    invariant_config_surface_not_current_truth,
    invariant_current_truth_allowed_restricted,
    invariant_generated_not_source_truth,
    invariant_generated_requires_generated_from,
    invariant_legacy_scope_requires_legacy_lifecycle,
    invariant_policy_activation_requires_target,
    invariant_tombstone_requires_reason,
    validate_registry_object,
)

__all__ = [
    # Adapters
    "RegistryImportResult",
    "import_all_registry_sources",
    "import_artifact_registry",
    "import_aux_ledgers",
    "import_checker_registry",
    "import_document_registry",
    "import_scanner_surfaces",
    # Reconciler
    "ReconcileResult",
    "ReconcileSummary",
    "reconcile_imported_sources",
    "reconcile_registry_objects",
    # Enums
    "AuthorityTier",
    "DECISION_AUTHORITY_TIERS",
    "ACTIVE_LIFECYCLE_STATES",
    "LifecycleState",
    "RegistryFindingStatus",
    "RegistryKind",
    "TERMINAL_LIFECYCLE_STATES",
    # Core model
    "RegistryFinding",
    "RegistryObject",
    "REGISTRY_INVARIANTS",
    # Invariants
    "invariant_active_t0_requires_owner",
    "invariant_archive_snapshot_not_current_truth",
    "invariant_config_surface_not_current_truth",
    "invariant_current_truth_allowed_restricted",
    "invariant_generated_not_source_truth",
    "invariant_generated_requires_generated_from",
    "invariant_legacy_scope_requires_legacy_lifecycle",
    "invariant_policy_activation_requires_target",
    "invariant_tombstone_requires_reason",
    "validate_registry_object",
]
