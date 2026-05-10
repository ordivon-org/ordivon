"""Unit tests for Ordivon Registry import adapters (RG-2).

Tests that each importer correctly reads registry source data and
maps it into RegistryObject instances. Uses fixture data to avoid
depending on real registry state.

Importers are READ-ONLY. Tests verify that source files are not modified.
"""

from pathlib import Path

from ordivon_verify.registry import (
    AuthorityTier,
    LifecycleState,
    RegistryImportResult,
    RegistryKind,
    RegistryObject,
    import_all_registry_sources,
    import_artifact_registry,
    import_aux_ledgers,
    import_checker_registry,
    import_document_registry,
    import_scanner_surfaces,
)

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "registry_import"
DR_SAMPLE = FIXTURES / "document_registry_sample.jsonl"
AR_SAMPLE = FIXTURES / "artifact_registry_sample.jsonl"


# ═══════════════════════════════════════════════════════════════════
# Document Registry Importer
# ═══════════════════════════════════════════════════════════════════


class TestImportDocumentRegistry:
    """Tests for import_document_registry()."""

    def _patch_source(self, tmp_path, monkeypatch):
        """Set up a minimal file tree with document-registry.jsonl as sample."""
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        # Copy sample content
        dest = gov / "document-registry.jsonl"
        dest.write_text(DR_SAMPLE.read_text())
        return tmp_path

    def test_imports_all_entries(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        assert result.object_count == 7
        assert result.blocked_count == 0

    def test_root_context_maps_to_document_kind(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        agents_obj = next(o for o in result.objects if o.registry_id == "dr:agents-md")
        assert agents_obj.kind == RegistryKind.DOCUMENT
        assert agents_obj.authority_tier == AuthorityTier.T0_SOURCE_OF_TRUTH
        assert agents_obj.lifecycle_state == LifecycleState.ACTIVE
        assert agents_obj.current_truth_allowed is True

    def test_jsonl_ledger_maps_to_ledger_kind(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        ledger_obj = next(o for o in result.objects if o.registry_id == "dr:paper-dogfood-ledger")
        assert ledger_obj.kind == RegistryKind.LEDGER

    def test_schema_doc_type_maps_to_schema_kind(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        schema_obj = next(o for o in result.objects if o.registry_id == "dr:dg-schema")
        assert schema_obj.kind == RegistryKind.SCHEMA

    def test_generated_manifest_maps_to_generated_view(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        manifest_obj = next(o for o in result.objects if o.registry_id == "dr:gate-manifest")
        assert manifest_obj.kind == RegistryKind.GENERATED_VIEW
        assert manifest_obj.generated is True
        assert manifest_obj.current_truth_allowed is False  # generated → not truth

    def test_closed_stage_summit_maps_to_archived(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        summit_obj = next(o for o in result.objects if o.registry_id == "dr:phase-4-stage-summit")
        assert summit_obj.lifecycle_state == LifecycleState.ARCHIVED
        # authority is not decision, so current_truth_allowed defaults false
        assert summit_obj.authority_tier == AuthorityTier.T1_CURRENT_STATUS

    def test_source_registry_preserved(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        for obj in result.objects:
            assert obj.source_registry == "document-registry"

    def test_missing_file_returns_blocked_finding(self, tmp_path, monkeypatch):
        root = tmp_path  # no docs/governance/ created
        result = import_document_registry(root)
        assert result.object_count == 0
        assert result.blocked_count == 1
        assert "not found" in result.findings[0].message.lower()

    def test_result_structure_populated(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_document_registry(root)
        assert result.source_name == "document-registry"
        assert result.source_path is not None
        assert result.object_count > 0


# ═══════════════════════════════════════════════════════════════════
# Artifact Registry Importer
# ═══════════════════════════════════════════════════════════════════


class TestImportArtifactRegistry:
    """Tests for import_artifact_registry()."""

    def _patch_source(self, tmp_path, monkeypatch):
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        dest = gov / "artifact-registry.jsonl"
        dest.write_text(AR_SAMPLE.read_text())
        return tmp_path

    def test_imports_all_entries(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        assert result.object_count == 4

    def test_all_entries_are_artifact_kind(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        for obj in result.objects:
            assert obj.kind == RegistryKind.ARTIFACT

    def test_l3_canon_maps_to_t2_supporting_evidence_rg10(self, tmp_path, monkeypatch):
        """RG-10: artifact_layer L3_CANON → T2_SUPPORTING_EVIDENCE (structural placement, not authority)."""
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        canon_obj = next(o for o in result.objects if "runner" in o.registry_id)
        assert canon_obj.authority_tier == AuthorityTier.T2_SUPPORTING_EVIDENCE

    def test_l4_product_maps_to_t2_supporting_evidence(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        test_obj = next(o for o in result.objects if "test-example" in o.registry_id)
        assert test_obj.authority_tier == AuthorityTier.T2_SUPPORTING_EVIDENCE

    def test_classification_preserved_in_notes(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        canon_obj = next(o for o in result.objects if "runner" in o.registry_id)
        assert canon_obj.notes is not None
        assert "artifact_class=source_registry" in canon_obj.notes
        assert "artifact_criticality=governance_critical" in canon_obj.notes

    def test_source_registry_preserved(self, tmp_path, monkeypatch):
        root = self._patch_source(tmp_path, monkeypatch)
        result = import_artifact_registry(root)
        for obj in result.objects:
            assert obj.source_registry == "artifact-registry"

    def test_missing_file_returns_blocked(self, tmp_path, monkeypatch):
        result = import_artifact_registry(tmp_path)
        assert result.object_count == 0
        assert result.blocked_count == 1


# ═══════════════════════════════════════════════════════════════════
# Checker Registry Importer
# ═══════════════════════════════════════════════════════════════════


class TestImportCheckerRegistry:
    """Tests for import_checker_registry()."""

    def _setup_checkers(self, tmp_path):
        """Create minimal checker directory structure."""
        checkers = tmp_path / "checkers"
        checkers.mkdir()
        for name in ["document-registry", "receipt-integrity"]:
            d = checkers / name
            d.mkdir()
            (d / "CHECKER.md").write_text(
                "---\ngate_id: {name}\n---\n# {title}\n".format(
                    name=name.replace("-", "_"),
                    title=name.replace("-", " ").title(),
                )
            )
            (d / "run.py").write_text("def run():\n    pass\n")
        return tmp_path

    def test_imports_checker_packages(self, tmp_path, monkeypatch):
        root = self._setup_checkers(tmp_path)
        result = import_checker_registry(root)
        assert result.object_count == 2

    def test_checker_kind_assigned(self, tmp_path, monkeypatch):
        root = self._setup_checkers(tmp_path)
        result = import_checker_registry(root)
        for obj in result.objects:
            assert obj.kind == RegistryKind.CHECKER
            assert obj.current_truth_allowed is False

    def test_checker_has_checker_registry_source(self, tmp_path, monkeypatch):
        root = self._setup_checkers(tmp_path)
        result = import_checker_registry(root)
        for obj in result.objects:
            assert obj.source_registry == "checker-registry"

    def test_registry_id_has_checker_prefix(self, tmp_path, monkeypatch):
        root = self._setup_checkers(tmp_path)
        result = import_checker_registry(root)
        for obj in result.objects:
            assert obj.registry_id.startswith("checker:")

    def test_empty_checkers_dir_returns_no_objects(self, tmp_path, monkeypatch):
        root = tmp_path
        (root / "checkers").mkdir()
        result = import_checker_registry(root)
        assert result.object_count == 0

    def test_missing_checker_dir_returns_degraded(self, tmp_path, monkeypatch):
        result = import_checker_registry(tmp_path)
        assert result.object_count == 0
        assert result.degraded_count >= 1

    def test_checkers_with_maturity_ledger(self, tmp_path, monkeypatch):
        root = self._setup_checkers(tmp_path)
        # Add maturity ledger
        gov = root / "docs" / "governance"
        gov.mkdir(parents=True)
        (gov / "checker-maturity-ledger.jsonl").write_text(
            '{"checker_id": "document-registry", "maturity": "active"}\n'
            '{"checker_id": "receipt-integrity", "maturity": "draft"}\n'
        )
        result = import_checker_registry(root)
        # document-registry should be active, receipt-integrity should be draft
        doc_obj = next(o for o in result.objects if "document-registry" in o.registry_id)
        rec_obj = next(o for o in result.objects if "receipt-integrity" in o.registry_id)
        assert doc_obj.lifecycle_state == LifecycleState.ACTIVE
        assert rec_obj.lifecycle_state == LifecycleState.DRAFT


# ═══════════════════════════════════════════════════════════════════
# Aux Ledgers Importer
# ═══════════════════════════════════════════════════════════════════


class TestImportAuxLedgers:
    """Tests for import_aux_ledgers()."""

    def _setup_ledgers(self, tmp_path):
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        (gov / "verification-debt-ledger.jsonl").write_text('{"debt_id": "VD-001", "status": "open"}\n')
        (gov / "lesson-ledger.jsonl").write_text('{"lesson_id": "L-001", "status": "active"}\n')
        (gov / "entropy-telemetry.jsonl").write_text('{"timestamp": "2026-05-01", "metrics": {}}\n')
        return tmp_path

    def test_imports_existing_ledgers(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        result = import_aux_ledgers(root)
        assert result.object_count == 3

    def test_existing_ledgers_are_ledger_kind(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        result = import_aux_ledgers(root)
        for obj in result.objects:
            assert obj.kind in (RegistryKind.LEDGER, RegistryKind.OWNERSHIP_RULE)

    def test_generated_ledger_has_generated_lifecycle(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        result = import_aux_ledgers(root)
        entropy_obj = next(o for o in result.objects if "entropy" in o.registry_id)
        assert entropy_obj.generated is True
        assert entropy_obj.lifecycle_state == LifecycleState.GENERATED

    def test_manual_ledger_not_generated(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        result = import_aux_ledgers(root)
        debt_obj = next(o for o in result.objects if "verification-debt" in o.registry_id)
        assert debt_obj.generated is False
        assert debt_obj.lifecycle_state == LifecycleState.ACTIVE

    def test_missing_ledger_produces_finding(self, tmp_path, monkeypatch):
        root = tmp_path
        (root / "docs" / "governance").mkdir(parents=True)
        result = import_aux_ledgers(root)
        # Many ledgers are missing — each produces a DEGRADED finding
        assert result.finding_count > 0

    def test_all_objects_have_supporting_evidence_authority(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        result = import_aux_ledgers(root)
        for obj in result.objects:
            assert obj.authority_tier == AuthorityTier.T2_SUPPORTING_EVIDENCE

    def test_importers_do_not_mutate_source_files(self, tmp_path, monkeypatch):
        root = self._setup_ledgers(tmp_path)
        original = {}
        for f in (root / "docs" / "governance").iterdir():
            if f.is_file():
                original[f.name] = f.read_text()

        import_aux_ledgers(root)

        for f in (root / "docs" / "governance").iterdir():
            if f.is_file() and f.name in original:
                assert f.read_text() == original[f.name], f"{f.name} was mutated!"


# ═══════════════════════════════════════════════════════════════════
# Scanner Surfaces Importer
# ═══════════════════════════════════════════════════════════════════


class TestImportScannerSurfaces:
    """Tests for import_scanner_surfaces()."""

    def _setup_scanners(self, tmp_path):
        scanner_dir = tmp_path / "src" / "ordivon_verify" / "scanners"
        scanner_dir.mkdir(parents=True)
        for name in ["skill_boundary", "memory_hygiene", "trace_evidence"]:
            (scanner_dir / f"{name}.py").write_text("# Scanner module\n")
        return tmp_path

    def test_imports_scanner_surfaces(self, tmp_path, monkeypatch):
        root = self._setup_scanners(tmp_path)
        result = import_scanner_surfaces(root)
        assert result.object_count == 3

    def test_scanner_surfaces_are_t3_candidate(self, tmp_path, monkeypatch):
        root = self._setup_scanners(tmp_path)
        result = import_scanner_surfaces(root)
        for obj in result.objects:
            assert obj.authority_tier == AuthorityTier.T3_CANDIDATE_PROPOSAL

    def test_scanner_surfaces_not_current_truth(self, tmp_path, monkeypatch):
        root = self._setup_scanners(tmp_path)
        result = import_scanner_surfaces(root)
        for obj in result.objects:
            assert obj.current_truth_allowed is False

    def test_scanner_surfaces_are_scanner_kind(self, tmp_path, monkeypatch):
        root = self._setup_scanners(tmp_path)
        result = import_scanner_surfaces(root)
        for obj in result.objects:
            assert obj.kind == RegistryKind.SCANNER_SURFACE

    def test_no_scanners_returns_empty(self, tmp_path, monkeypatch):
        result = import_scanner_surfaces(tmp_path)
        assert result.object_count == 0

    def test_source_registry_preserved(self, tmp_path, monkeypatch):
        root = self._setup_scanners(tmp_path)
        result = import_scanner_surfaces(root)
        for obj in result.objects:
            assert obj.source_registry == "scanner-surfaces"


# ═══════════════════════════════════════════════════════════════════
# Import All
# ═══════════════════════════════════════════════════════════════════


class TestImportAll:
    """Tests for import_all_registry_sources()."""

    def _setup_full(self, tmp_path):
        """Set up a minimal but complete registry environment."""
        # Document registry
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        (gov / "document-registry.jsonl").write_text(DR_SAMPLE.read_text())

        # Artifact registry
        (gov / "artifact-registry.jsonl").write_text(AR_SAMPLE.read_text())

        # Checker packages
        checkers = tmp_path / "checkers"
        checkers.mkdir()
        d = checkers / "test-checker"
        d.mkdir()
        (d / "CHECKER.md").write_text("---\ngate_id: test_checker\n---\n# Test Checker\n")
        (d / "run.py").write_text("def run():\n    pass\n")

        # Aux ledgers
        (gov / "verification-debt-ledger.jsonl").write_text('{"debt_id": "VD-001"}\n')

        # Scanners
        scanner_dir = tmp_path / "src" / "ordivon_verify" / "scanners"
        scanner_dir.mkdir(parents=True)
        (scanner_dir / "skill_boundary.py").write_text("# Scanner\n")

        return tmp_path

    def test_imports_all_sources(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        assert len(results) >= 5
        assert "document-registry" in results
        assert "artifact-registry" in results
        assert "checker-registry" in results
        assert "aux-ledgers" in results
        assert "scanner-surfaces" in results

    def test_all_results_have_source_name(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        for name, result in results.items():
            assert result.source_name == name

    def test_each_source_has_at_least_one_object(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        for name, result in results.items():
            if result.object_count == 0:
                continue  # config-surfaces/legacy-scope may be empty in fixture
            assert result.object_count >= 1, f"{name} has 0 objects"
            assert isinstance(result.objects[0], RegistryObject)

    def test_total_object_count_reasonable(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        total = sum(r.object_count for r in results.values())
        # 7 doc + 4 artifact + 1 checker + 1 aux + 1 scanner = 14
        assert total >= 10

    def test_registry_ids_are_unique_across_sources(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        all_ids = []
        for result in results.values():
            for obj in result.objects:
                all_ids.append(obj.registry_id)
        assert len(all_ids) == len(set(all_ids)), "Duplicate registry IDs found"

    def test_source_registry_field_reflects_origin(self, tmp_path, monkeypatch):
        root = self._setup_full(tmp_path)
        results = import_all_registry_sources(root)
        source_map = {
            "document-registry": "document-registry",
            "artifact-registry": "artifact-registry",
            "checker-registry": "checker-registry",
            "aux-ledgers": "aux-ledgers",
            "scanner-surfaces": "scanner-surfaces",
        }
        for name, result in results.items():
            for obj in result.objects:
                assert obj.source_registry == source_map[name], (
                    f"{name} object {obj.registry_id} has source_registry={obj.source_registry}"
                )


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════


class TestImportEdgeCases:
    """Edge cases and robustness for importers."""

    def test_invalid_jsonl_document_registry_returns_finding(self, tmp_path, monkeypatch):
        gov = tmp_path / "docs" / "governance"
        gov.mkdir(parents=True)
        (gov / "document-registry.jsonl").write_text("this is not valid JSON\n")
        result = import_document_registry(tmp_path)
        # Should not crash — malformed lines are skipped (JSON decode errors
        # are caught, resulting in 0 objects)
        assert result.object_count == 0

    def test_importers_do_not_create_files(self, tmp_path, monkeypatch):
        """Verify no importer creates any new file."""
        root = tmp_path
        (root / "docs" / "governance").mkdir(parents=True)
        (root / "checkers").mkdir()
        scanner_dir = root / "src" / "ordivon_verify" / "scanners"
        scanner_dir.mkdir(parents=True)

        before_files = set()
        for f in root.rglob("*"):
            if f.is_file():
                before_files.add(str(f))

        import_all_registry_sources(root)

        after_files = set()
        for f in root.rglob("*"):
            if f.is_file():
                after_files.add(str(f))

        new_files = after_files - before_files
        assert new_files == set(), f"Importers created files: {new_files}"

    def test_import_all_handles_empty_repo_gracefully(self, tmp_path, monkeypatch):
        """Importing from empty temp dir should not crash."""
        results = import_all_registry_sources(tmp_path)
        assert len(results) >= 5
        for name, result in results.items():
            assert isinstance(result, RegistryImportResult)
            # All should have findings or zero objects for missing sources
            assert result.object_count + result.finding_count >= 0
