"""Registry source/view declarations — RG-9.

Declares the role of each registry source within the unified Registry Control
Plane. Old registries are source_adapters; the generated index is a
generated_view. No source is silently deleted or demoted.

This file is the code-level bridge between RG-2 import adapters and the
RG-8 generated registry index.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════
# Source View Model
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RegistrySourceView:
    """Declaration of one registry source's role in the control plane."""

    source_id: str
    path_or_method: str
    role: str  # source_adapter | generated_view | legacy_view
    authoritative_for: tuple[str, ...] = ()
    imported_by: str | None = None
    generated_view_target: str | None = None
    lifecycle_state: str = "active"
    owner: str = "ordivon-core-maintainer"
    current_truth_allowed: bool = False
    notes: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════════
# Registry Source Declarations
# ═══════════════════════════════════════════════════════════════════

REGISTRY_SOURCE_VIEWS: tuple[RegistrySourceView, ...] = (
    RegistrySourceView(
        source_id="document-registry",
        path_or_method="docs/governance/document-registry.jsonl",
        role="source_adapter",
        authoritative_for=("document identity, status, authority, freshness",),
        imported_by="import_document_registry",
        notes="Original document governance registry. Remains primary document authority during transition.",
    ),
    RegistrySourceView(
        source_id="artifact-registry",
        path_or_method="docs/governance/artifact-registry.jsonl",
        role="source_adapter",
        authoritative_for=("artifact identity, classification, criticality",),
        imported_by="import_artifact_registry",
        notes="Original artifact governance registry. artifact_layer indicates structural placement, not authority tier.",
    ),
    RegistrySourceView(
        source_id="checker-registry",
        path_or_method="checkers/*/CHECKER.md + run.py (auto-discovery)",
        role="source_adapter",
        authoritative_for=("checker identity, maturity, usage telemetry",),
        imported_by="import_checker_registry",
        notes="Self-registering checker ecosystem. Auto-discovered via CHECKER.md + run.py.",
    ),
    RegistrySourceView(
        source_id="aux-ledgers",
        path_or_method="docs/governance/*.jsonl (multiple)",
        role="source_adapter",
        authoritative_for=("debt, maturity, policy activation, candidate rules, lessons, telemetry",),
        imported_by="import_aux_ledgers",
        notes="Auxiliary governance ledgers. Each ledger has its own lifecycle and authority.",
    ),
    RegistrySourceView(
        source_id="scanner-surfaces",
        path_or_method="src/ordivon_verify/scanners/ (auto-discovery)",
        role="source_adapter",
        authoritative_for=("skill, memory, trace surfaces (T3 candidate only)",),
        imported_by="import_scanner_surfaces",
        notes="CTTS-3M scanner surfaces. All default to T3_CANDIDATE_PROPOSAL. Not current truth.",
    ),
    RegistrySourceView(
        source_id="generated-registry-index",
        path_or_method="ordivon-verify registry-index (CLI)",
        role="generated_view",
        generated_view_target=".ordivon/registry/generated-registry.json (optional)",
        current_truth_allowed=False,
        notes="RG-8 generated unified registry index. Derived from source adapters. Not source of truth.",
    ),
)


def get_registry_source_views() -> list[dict]:
    """Return all source/view declarations as JSON-serializable dicts."""
    return [
        {
            "source_id": v.source_id,
            "path_or_method": v.path_or_method,
            "role": v.role,
            "authoritative_for": list(v.authoritative_for),
            "imported_by": v.imported_by,
            "generated_view_target": v.generated_view_target,
            "lifecycle_state": v.lifecycle_state,
            "owner": v.owner,
            "current_truth_allowed": v.current_truth_allowed,
            "notes": v.notes,
        }
        for v in REGISTRY_SOURCE_VIEWS
    ]
