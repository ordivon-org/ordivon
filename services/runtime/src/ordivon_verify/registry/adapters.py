"""Registry import adapters — convert existing registry data into RegistryObject.

Each importer reads one source (document-registry, artifact-registry, checker
packages, aux ledgers, scanner surfaces) and returns a RegistryImportResult
with RegistryObject instances and any import findings.

Importers are READ-ONLY. They never mutate source files, never create missing
files, and never fix RG-0 debts. Bad rows produce RegistryFinding objects,
not crashes.

RG-3 will use these imported objects for cross-registry reconciliation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ordivon_verify.registry.models import (
    AuthorityTier,
    DECISION_AUTHORITY_TIERS,
    LifecycleState,
    RegistryFinding,
    RegistryFindingStatus,
    RegistryKind,
    RegistryObject,
)


# ═══════════════════════════════════════════════════════════════════
# Import Result
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RegistryImportResult:
    """Result of importing one registry source."""

    source_name: str
    source_path: str | None
    objects: tuple[RegistryObject, ...] = ()
    findings: tuple[RegistryFinding, ...] = ()

    @property
    def object_count(self) -> int:
        return len(self.objects)

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def blocked_count(self) -> int:
        return sum(1 for f in self.findings if f.status == RegistryFindingStatus.BLOCKED)

    @property
    def degraded_count(self) -> int:
        return sum(1 for f in self.findings if f.status == RegistryFindingStatus.DEGRADED)


# ── Helpers ────────────────────────────────────────────────────────


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file into a list of dicts. Returns empty list on any error."""
    if not path.exists():
        return []
    entries = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except (OSError, IOError):
        pass
    return entries


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════════
# Document Registry Importer
# ═══════════════════════════════════════════════════════════════════

# Known generated manifests — these should map to kind=generated_view.
_GENERATED_MANIFEST_PATHS = frozenset({
    "docs/governance/verification-gate-manifest.json",
    "docs/governance/checker-coverage-manifest.json",
})


def import_document_registry(root: Path) -> RegistryImportResult:
    """Import document-registry.jsonl entries into RegistryObject instances.

    Mapping:
        .jsonl governance files  → kind=ledger
        doc_type=schema          → kind=schema
        known generated manifests → kind=generated_view
        otherwise                → kind=document
    """
    source_path = root / "docs" / "governance" / "document-registry.jsonl"
    if not source_path.exists():
        return RegistryImportResult(
            source_name="document-registry",
            source_path=str(source_path),
            findings=(
                RegistryFinding(
                    finding_id="IMPORT-DR-MISSING",
                    object_id="document-registry",
                    status=RegistryFindingStatus.BLOCKED,
                    invariant="import-source-exists",
                    message="document-registry.jsonl not found",
                    repair_action="Verify the file exists.",
                ),
            ),
        )

    rows = _read_jsonl(source_path)
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    for i, row in enumerate(rows, 1):
        doc_id = row.get("doc_id", f"dr-row-{i}")
        path_str = row.get("path", "")
        doc_type = row.get("doc_type", "")
        authority = row.get("authority", "")
        status = row.get("status", "")

        # Determine kind
        if path_str in _GENERATED_MANIFEST_PATHS:
            kind = RegistryKind.GENERATED_VIEW
            generated = True
        elif doc_type == "schema":
            kind = RegistryKind.SCHEMA
            generated = False
        elif path_str.endswith(".jsonl"):
            kind = RegistryKind.LEDGER
            generated = False
        else:
            kind = RegistryKind.DOCUMENT
            generated = False

        # Authority tier mapping
        authority_map = {
            "source_of_truth": AuthorityTier.T0_SOURCE_OF_TRUTH,
            "current_status": AuthorityTier.T1_CURRENT_STATUS,
            "supporting_evidence": AuthorityTier.T2_SUPPORTING_EVIDENCE,
            "proposal": AuthorityTier.T3_CANDIDATE_PROPOSAL,
            "historical_record": AuthorityTier.T4_ARCHIVE_HISTORICAL,
            "archive": AuthorityTier.T4_ARCHIVE_HISTORICAL,
            "example": AuthorityTier.T3_CANDIDATE_PROPOSAL,
        }
        authority_tier = authority_map.get(authority, AuthorityTier.T2_SUPPORTING_EVIDENCE)

        # Lifecycle mapping
        lifecycle_map = {
            "current": LifecycleState.ACTIVE,
            "accepted": LifecycleState.ACTIVE,
            "implemented": LifecycleState.ACTIVE,
            "closed": LifecycleState.ARCHIVED,
            "deferred": LifecycleState.DRAFT,
            "superseded": LifecycleState.TOMBSTONED,
            "archived": LifecycleState.ARCHIVED,
            "stale": LifecycleState.DEPRECATED,
            "draft": LifecycleState.DRAFT,
            "proposed": LifecycleState.CANDIDATE,
        }
        lifecycle_state = lifecycle_map.get(status, LifecycleState.DRAFT)

        # current_truth_allowed: DGP-2 hardened
        # Archived/tombstoned objects cannot be current truth
        is_decision = authority_tier in DECISION_AUTHORITY_TIERS
        if generated or lifecycle_state in (
            LifecycleState.ARCHIVED,
            LifecycleState.TOMBSTONED,
            LifecycleState.OUT_OF_SCOPE,
            LifecycleState.DEPRECATED,
        ):
            current_truth_allowed = False
        else:
            current_truth_allowed = is_decision

        # Build object
        try:
            obj = RegistryObject(
                registry_id=f"dr:{doc_id}",
                kind=kind,
                path=path_str if path_str else None,
                title=row.get("title"),
                authority_tier=authority_tier,
                lifecycle_state=lifecycle_state,
                current_truth_allowed=current_truth_allowed,
                owner=row.get("owner"),
                source_registry="document-registry",
                generated=generated,
                generated_from=tuple(row.get("related_ledgers", [])) if generated else (),
                last_verified=row.get("last_verified"),
                ttl_days=row.get("stale_after_days"),
                supersedes=tuple(),  # doc-registry has supersedes as string list
                superseded_by=row.get("superseded_by"),
                policy_refs=tuple(),
                evidence_refs=tuple(),
                receipt_refs=tuple(row.get("related_receipts", [])),
                notes=row.get("notes"),
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-DR-ROW-{i}",
                    object_id=doc_id,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Row {i}: failed to construct RegistryObject: {e}",
                    repair_action="Fix the row data.",
                )
            )

    return RegistryImportResult(
        source_name="document-registry",
        source_path=str(source_path),
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Artifact Registry Importer
# ═══════════════════════════════════════════════════════════════════


def import_artifact_registry(root: Path) -> RegistryImportResult:
    """Import artifact-registry.jsonl entries into RegistryObject instances.

    All entries map to kind=artifact by default. Classification metadata
    (artifact_class, artifact_criticality, artifact_layer) is preserved
    in notes.
    """
    source_path = root / "docs" / "governance" / "artifact-registry.jsonl"
    if not source_path.exists():
        return RegistryImportResult(
            source_name="artifact-registry",
            source_path=str(source_path),
            findings=(
                RegistryFinding(
                    finding_id="IMPORT-AR-MISSING",
                    object_id="artifact-registry",
                    status=RegistryFindingStatus.BLOCKED,
                    invariant="import-source-exists",
                    message="artifact-registry.jsonl not found",
                    repair_action="Verify the file exists.",
                ),
            ),
        )

    rows = _read_jsonl(source_path)
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    # RG-10 hardened: artifact_layer indicates structural placement, NOT authority.
    # L3_CANON / L1_TRUTH must not auto-elevate to T0_SOURCE_OF_TRUTH.
    # Authority over-elevation is detected separately by the reconciler.
    layer_tier_map = {
        "L_CHECKER": AuthorityTier.T1_CURRENT_STATUS,
        "L3_CANON": AuthorityTier.T2_SUPPORTING_EVIDENCE,
        "L2_EVIDENCE": AuthorityTier.T2_SUPPORTING_EVIDENCE,
        "L4_PRODUCT": AuthorityTier.T2_SUPPORTING_EVIDENCE,
        "L1_TRUTH": AuthorityTier.T1_CURRENT_STATUS,
    }

    for i, row in enumerate(rows, 1):
        aid = row.get("artifact_id", f"ar-row-{i}")
        path_str = row.get("path", "")
        aclass = row.get("artifact_class", "")
        acrit = row.get("artifact_criticality", "")
        alayer = row.get("artifact_layer", "")

        authority_tier = layer_tier_map.get(alayer, AuthorityTier.T3_CANDIDATE_PROPOSAL)

        # Determine lifecycle from status field
        status = row.get("status", "registered")
        if status == "registered":
            lifecycle_state = LifecycleState.ACTIVE
        elif status == "deprecated":
            lifecycle_state = LifecycleState.DEPRECATED
        elif status == "archived":
            lifecycle_state = LifecycleState.ARCHIVED
        else:
            lifecycle_state = LifecycleState.ACTIVE

        notes_parts = [row.get("notes", "").strip()]
        if aclass:
            notes_parts.append(f"artifact_class={aclass}")
        if acrit:
            notes_parts.append(f"artifact_criticality={acrit}")
        if alayer:
            notes_parts.append(f"artifact_layer={alayer}")
        notes = "; ".join(p for p in notes_parts if p).strip() or None

        try:
            obj = RegistryObject(
                registry_id=f"ar:{aid}",
                kind=RegistryKind.ARTIFACT,
                path=path_str if path_str else None,
                title=row.get("artifact_id"),
                authority_tier=authority_tier,
                lifecycle_state=lifecycle_state,
                current_truth_allowed=(authority_tier in DECISION_AUTHORITY_TIERS),
                source_registry="artifact-registry",
                generated=False,
                last_verified=row.get("last_verified"),
                ttl_days=row.get("stale_after_days"),
                notes=notes,
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-AR-ROW-{i}",
                    object_id=aid,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Row {i}: failed to construct RegistryObject: {e}",
                    repair_action="Fix the row data.",
                )
            )

    return RegistryImportResult(
        source_name="artifact-registry",
        source_path=str(source_path),
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Checker Registry Importer
# ═══════════════════════════════════════════════════════════════════


def import_checker_registry(root: Path) -> RegistryImportResult:
    """Import checker packages from checkers/*/CHECKER.md + run.py.

    Also reads checker-maturity-ledger for lifecycle state.
    Sidecar files (.bundled_manifest, .usage.json) are NOT imported
    as independent objects — they are evidence references.
    """
    checkers_dir = root / "checkers"
    if not checkers_dir.exists():
        return RegistryImportResult(
            source_name="checker-registry",
            source_path=str(checkers_dir),
            findings=(
                RegistryFinding(
                    finding_id="IMPORT-CR-MISSING",
                    object_id="checker-registry",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-source-exists",
                    message="checkers/ directory not found",
                    repair_action="Verify the directory exists.",
                ),
            ),
        )

    # Load maturity ledger for lifecycle context
    maturity_path = root / "docs" / "governance" / "checker-maturity-ledger.jsonl"
    maturity: dict[str, dict] = {}
    for row in _read_jsonl(maturity_path):
        cid = row.get("checker_id", "")
        if cid:
            maturity[cid] = row

    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    for checker_dir in sorted(checkers_dir.iterdir()):
        if not checker_dir.is_dir():
            continue
        if checker_dir.name.startswith("."):
            continue

        gate_id = checker_dir.name
        checker_md = checker_dir / "CHECKER.md"
        run_py = checker_dir / "run.py"

        if not checker_md.exists() and not run_py.exists():
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-CR-MISSING-CHECKER-{gate_id}",
                    object_id=f"checker:{gate_id}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-checker-complete",
                    message=f"Checker '{gate_id}' has no CHECKER.md or run.py",
                    repair_action="Add CHECKER.md + run.py or archive the directory.",
                )
            )
            continue

        # Determine lifecycle from maturity ledger
        mat = maturity.get(gate_id)
        if mat:
            mat_status = mat.get("maturity", "")
            maturity_map = {
                "draft": LifecycleState.DRAFT,
                "shadow_tested": LifecycleState.CANDIDATE,
                "red_teamed": LifecycleState.CANDIDATE,
                "active": LifecycleState.ACTIVE,
            }
            lifecycle_state = maturity_map.get(mat_status, LifecycleState.ACTIVE)
        else:
            # Grandfathered: no maturity record = de facto active
            lifecycle_state = LifecycleState.ACTIVE

        rel_path = str(checker_dir.relative_to(root))

        try:
            obj = RegistryObject(
                registry_id=f"checker:{gate_id}",
                kind=RegistryKind.CHECKER,
                path=f"{rel_path}/",
                title=gate_id.replace("-", " ").title(),
                authority_tier=AuthorityTier.T1_CURRENT_STATUS,  # checkers ARE governance authority
                lifecycle_state=lifecycle_state,
                current_truth_allowed=False,  # checkers produce findings, not truth
                source_registry="checker-registry",
                discovered_by="checker-registry-auto-discovery",
                generated=False,
                last_verified=_now_iso(),
                notes=f"Checker package at {rel_path}",
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-CR-FAIL-{gate_id}",
                    object_id=f"checker:{gate_id}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Checker '{gate_id}': {e}",
                    repair_action="Fix the checker package.",
                )
            )

    return RegistryImportResult(
        source_name="checker-registry",
        source_path=str(checkers_dir),
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Auxiliary Ledgers Importer
# ═══════════════════════════════════════════════════════════════════

_AUX_LEDGER_FILES = [
    "verification-debt-ledger.jsonl",
    "checker-maturity-ledger.jsonl",
    "policy-activation-ledger.jsonl",
    "candidate-rule-drafts.jsonl",
    "lesson-ledger.jsonl",
    "shadow-evaluation-log.jsonl",
    "entropy-telemetry.jsonl",
    "agent-native-evidence-redteam.jsonl",
    "registry-degraded-lifecycle.jsonl",
    "ownership-manifest.jsonl",
    "external-benchmark-source-registry.jsonl",
    "lesson-extraction-log.jsonl",
]

_AUX_GENERATED_LEDGERS = frozenset({
    "shadow-evaluation-log.jsonl",
    "entropy-telemetry.jsonl",
    "lesson-extraction-log.jsonl",
})


def import_aux_ledgers(root: Path) -> RegistryImportResult:
    """Import auxiliary governance ledgers from docs/governance/.

    Each JSONL ledger becomes a RegistryObject. Missing ledgers that are
    referenced in code/docs are noted as findings but NOT created.

    Ownership-manifest entries are not expanded to individual ownership_rule
    objects in RG-2 — that's deferred to RG-5 (Legacy Scope Manifest).
    """
    gov_dir = root / "docs" / "governance"
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    for filename in _AUX_LEDGER_FILES:
        filepath = gov_dir / filename
        source_name = f"aux-ledger:{filename}"

        if not filepath.exists():
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-AUX-MISSING-{filename}",
                    object_id=source_name,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-source-exists",
                    message=f"Aux ledger '{filename}' not found — may be referenced but absent",
                    repair_action=f"Create {filename} if needed, or remove dangling references.",
                )
            )
            continue

        row_count = len(_read_jsonl(filepath))
        is_generated = filename in _AUX_GENERATED_LEDGERS

        # Map to kind based on filename patterns
        if "ownership" in filename:
            kind = RegistryKind.OWNERSHIP_RULE
        elif "candidate" in filename and "rule" in filename:
            kind = RegistryKind.LEDGER  # candidate-rule-drafts, not policy-activation
        elif "entropy" in filename:
            kind = RegistryKind.LEDGER
        elif "shadow" in filename:
            kind = RegistryKind.LEDGER
        elif "benchmark" in filename:
            kind = RegistryKind.LEDGER
        else:
            kind = RegistryKind.LEDGER

        try:
            obj = RegistryObject(
                registry_id=f"aux:{filename}",
                kind=kind,
                path=str(filepath.relative_to(root)),
                title=filename.replace("-", " ").replace(".jsonl", "").title(),
                authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
                lifecycle_state=LifecycleState.GENERATED if is_generated else LifecycleState.ACTIVE,
                current_truth_allowed=False,
                source_registry="aux-ledgers",
                generated=is_generated,
                generated_from=() if not is_generated else (),
                last_verified=_now_iso(),
                notes=f"Aux governance ledger. {row_count} entries. {'GENERATED — not source of truth.' if is_generated else ''}",
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-AUX-FAIL-{filename}",
                    object_id=source_name,
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Failed to import {filename}: {e}",
                    repair_action="Fix the file or remove it.",
                )
            )

    return RegistryImportResult(
        source_name="aux-ledgers",
        source_path=str(gov_dir),
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Scanner Surfaces Importer
# ═══════════════════════════════════════════════════════════════════


def import_scanner_surfaces(root: Path) -> RegistryImportResult:
    """Import CTTS-3M scanner surfaces (skill/memory/trace).

    Attempts to use the metabolic discovery module if available; falls back
    to explicit scanner module presence detection.

    All scanner surfaces default to T3_CANDIDATE_PROPOSAL and
    current_truth_allowed=False — per CTTS-3M invariants.
    """
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    # Check if scanner modules exist (lightweight fallback)
    scanner_dir = root / "src" / "ordivon_verify" / "scanners"
    scanner_modules = [
        ("skill_boundary", "Skill/Tool Surface Scanner"),
        ("memory_hygiene", "Memory/Content Surface Scanner"),
        ("trace_evidence", "Trace Evidence Scanner"),
    ]

    for mod_name, display_name in scanner_modules:
        mod_path = scanner_dir / f"{mod_name}.py"
        if not mod_path.exists():
            continue

        try:
            obj = RegistryObject(
                registry_id=f"scanner:{mod_name}",
                kind=RegistryKind.SCANNER_SURFACE,
                path=str(mod_path.relative_to(root)),
                title=display_name,
                authority_tier=AuthorityTier.T3_CANDIDATE_PROPOSAL,
                lifecycle_state=LifecycleState.CANDIDATE,
                current_truth_allowed=False,
                source_registry="scanner-surfaces",
                discovered_by=f"ctts-3m-{mod_name}",
                generated=False,
                last_verified=_now_iso(),
                notes=f"CTTS-3M {mod_name} scanner surface. T3 candidate — not current truth. See CTTS-3M closure seal.",
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-SCN-FAIL-{mod_name}",
                    object_id=f"scanner:{mod_name}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Failed to import scanner {mod_name}: {e}",
                    repair_action="Fix scanner module.",
                )
            )

    return RegistryImportResult(
        source_name="scanner-surfaces",
        source_path=str(scanner_dir) if scanner_dir.exists() else None,
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Import All
# ═══════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════
# Config Surface Importer (RG-13)
# ═══════════════════════════════════════════════════════════════════

_CONFIG_FILES = (
    "pyproject.toml",
    "package.json",
    "pnpm-workspace.yaml",
    "docker-compose.yml",
    "Makefile",
    ".env.example",
)


def import_config_surfaces(root: Path) -> RegistryImportResult:
    """Import known project config files as RegistryObject(kind=config_surface).

    Config surfaces are T2 supporting evidence by default — they affect
    behavior but are not source_of_truth.
    """
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    for cf in _CONFIG_FILES:
        fp = root / cf
        if not fp.exists():
            continue
        try:
            obj = RegistryObject(
                registry_id=f"config:{cf}",
                kind=RegistryKind.CONFIG_SURFACE,
                path=cf,
                title=f"Config: {cf}",
                authority_tier=AuthorityTier.T2_SUPPORTING_EVIDENCE,
                lifecycle_state=LifecycleState.ACTIVE,
                current_truth_allowed=False,
                source_registry="config-surfaces",
                generated=False,
                last_verified=_now_iso(),
                notes="Project config surface. Affects build/test/runtime behavior. Not source of truth.",
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-CFG-FAIL-{cf}",
                    object_id=f"config:{cf}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Failed to import config {cf}: {e}",
                    repair_action="Fix config file or remove it.",
                )
            )

    return RegistryImportResult(
        source_name="config-surfaces",
        source_path=str(root),
        objects=tuple(objects),
        findings=tuple(findings),
    )


# ═══════════════════════════════════════════════════════════════════
# Legacy Scope Importer (RG-14)
# ═══════════════════════════════════════════════════════════════════


def import_legacy_scopes(root: Path) -> RegistryImportResult:
    """Import legacy scope manifest entries as RegistryObject(kind=legacy_scope).

    Reads docs/governance/legacy-scope-manifest-rg-14.jsonl if present.
    Falls back to empty if file not found (legacy scope not yet declared).
    """
    manifest_path = root / "docs" / "governance" / "legacy-scope-manifest-rg-14.jsonl"
    rows = _read_jsonl(manifest_path)
    objects: list[RegistryObject] = []
    findings: list[RegistryFinding] = []

    for row in rows:
        sid = row.get("scope_id", "?")
        pp = row.get("path_pattern", "")
        try:
            obj = RegistryObject(
                registry_id=f"legacy:{sid}",
                kind=RegistryKind.LEGACY_SCOPE,
                path=pp,
                title=f"Legacy: {pp}",
                authority_tier=AuthorityTier.T6_OUT_OF_SCOPE,
                lifecycle_state=LifecycleState.LEGACY_INACTIVE,
                current_truth_allowed=False,
                source_registry="legacy-scope-manifest",
                generated=False,
                last_verified=_now_iso(),
                notes=row.get("notes", f"Legacy scope: {pp}"),
            )
            objects.append(obj)
        except Exception as e:
            findings.append(
                RegistryFinding(
                    finding_id=f"IMPORT-LEGACY-FAIL-{sid}",
                    object_id=f"legacy:{sid}",
                    status=RegistryFindingStatus.DEGRADED,
                    invariant="import-row-valid",
                    message=f"Failed to import legacy scope {sid}: {e}",
                    repair_action="Fix the scope record.",
                )
            )

    return RegistryImportResult(
        source_name="legacy-scope-manifest",
        source_path=str(manifest_path) if manifest_path.exists() else None,
        objects=tuple(objects),
        findings=tuple(findings),
    )


def import_all_registry_sources(root: Path | None = None) -> dict[str, RegistryImportResult]:
    """Import all registry sources into a single dictionary.

    Returns {source_name: RegistryImportResult}.
    Does NOT write a generated index — that's RG-8.
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]  # registry/ → ordivon_verify/ → src/ → root

    results: dict[str, RegistryImportResult] = {}

    importers = [
        ("document-registry", import_document_registry),
        ("artifact-registry", import_artifact_registry),
        ("checker-registry", import_checker_registry),
        ("aux-ledgers", import_aux_ledgers),
        ("scanner-surfaces", import_scanner_surfaces),
        ("config-surfaces", import_config_surfaces),
        ("legacy-scope-manifest", import_legacy_scopes),
    ]

    for name, importer_fn in importers:
        try:
            results[name] = importer_fn(root)
        except Exception as e:
            results[name] = RegistryImportResult(
                source_name=name,
                source_path=None,
                findings=(
                    RegistryFinding(
                        finding_id=f"IMPORT-ALL-FAIL-{name}",
                        object_id=name,
                        status=RegistryFindingStatus.BLOCKED,
                        invariant="import-source-available",
                        message=f"Importer '{name}' crashed: {e}",
                        repair_action="Fix the importer or source data.",
                    ),
                ),
            )

    return results
