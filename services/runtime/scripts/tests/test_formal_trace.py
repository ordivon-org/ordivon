"""Consumer-facing checks for the Runtime TLA+ to Rust trace manifest.

Run by the existing Owner unittest discover entrypoint; no second runner
or LEGO test registry is needed.
"""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/verify_formal_trace.py"
TRACE = ROOT / "formal/RuntimeDispatchR1.trace-r1.json"
INVARIANTS = ROOT / "planning/invariants-r1.json"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_formal_trace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def manifests():
    return (
        json.loads(TRACE.read_text(encoding="utf-8")),
        json.loads(INVARIANTS.read_text(encoding="utf-8")),
    )


class FormalTraceContractTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_formal_trace_gate_passes_current_runtime_binding(self):
        self.assertEqual(self.module.main(), 0)

    def test_owner_slice_is_owner_scoped(self):
        text = """impl Alpha {
    fn target() {}
}
impl Beta {
    fn other() {}
}
trait Provider {
    fn realize(&self);
}
"""
        alpha = self.module.owner_slice(text, "impl", "Alpha")
        provider = self.module.owner_slice(text, "trait", "Provider")
        self.assertIn("fn target", alpha)
        self.assertNotIn("fn other", alpha)
        self.assertIn("fn realize", provider)

    def test_schema_v2_rejects_source_fragment_binding_regression(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["contractSeams"][0]["requiredFragments"] = ["implementation detail"]
        errors = self.module.validate(mutated, invariants)
        self.assertIn("schema v2 must not bind source-code body fragments", errors)

    def test_contract_seam_removal_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["contractSeams"] = mutated["contractSeams"][1:]
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("contract seam set drift" in error for error in errors))

    def test_production_realization_seam_is_runtime_dispatch_not_contract_probe(self):
        trace, _ = manifests()
        seam = next(item for item in trace["contractSeams"] if item["id"] == "ExecutionProvider.realize")
        self.assertEqual(seam["owner"], "Runtime")
        self.assertEqual(seam["symbol"], "dispatch_attempt")
        supporting = next(
            item for item in trace["supportingContracts"] if item["id"] == "ExecutionProvider.assumeGuarantee"
        )
        self.assertEqual(supporting["owner"], "ExecutionProviderSpi")
        self.assertEqual(supporting["symbol"], "realize")

    def test_unknown_proving_target_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["provingTests"][0]["proves"].append("Unknown.seam")
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("references unknown target" in error for error in errors))

    def test_test_annotation_is_bound_to_exact_function(self):
        # An earlier Rust test attribute may not certify this unannotated function.
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "integration_tests.rs"
            source.write_text("#[test]\nfn existing_test() {}\nfn target() {}\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_test_symbol(source, "target")
            finally:
                self.module.ROOT = original_root
        self.assertTrue(any("is not marked #[test]" in error for error in errors))

    def test_ignored_integration_cannot_claim_always_on_proving_test(self):
        # A source symbol is not executed evidence when Rust marks it ignored.
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "integration_tests.rs"
            source.write_text(
                '#[test]\n#[ignore = "requires root and cgroup"]\nfn target() {}\n',
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_test_symbol(source, "target")
            finally:
                self.module.ROOT = original_root
        self.assertTrue(any("ignored" in error for error in errors), errors)

    def test_test_annotation_accepts_adjacent_attributes(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "integration_tests.rs"
            source.write_text("#[test]\n#[cfg(unix)]\nfn target() {}\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_test_symbol(source, "target")
            finally:
                self.module.ROOT = original_root
        self.assertEqual(errors, [])


    def test_physical_witness_must_be_explicitly_ignored(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["conditionalAcceptanceTests"][0]["symbol"] = "orphaned_terminal_keeps_capacity_reserved"
        mutated["conditionalAcceptanceTests"][0]["path"] = "crates/ordivon-runtime-core/src/runtime/tests.rs"
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("not an explicitly ignored" in error for error in errors), errors)

    def test_missing_conditional_physical_witness_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated.pop("conditionalAcceptanceTests")
        errors = self.module.validate(mutated, invariants)
        self.assertIn("conditional acceptance test set drift", errors)

    def test_conditional_evidence_cannot_replace_always_on_oracle(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["provingTests"][0]["path"] = "crates/ordivon-runtime-core/src/runtime/integration_tests.rs"
        mutated["provingTests"][0]["symbol"] = "runtime_two_observers_do_not_race_dispatch_of_one_accepted_attempt"
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("ignored, not an always-on" in error for error in errors), errors)

    def test_changed_formal_model_digest_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["moduleSha256"] = "0" * 64
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("formal source drift" in error for error in errors), errors)

    def test_terminal_evidence_math_kernel_has_one_native_owner_witness(self):
        """R2.1 consumer seam: terminal standing requires committed physical evidence."""
        trace, invariants = manifests()
        bindings = {item["id"] for item in trace["formalSpecification"]["modelBindings"]}
        self.assertIn("RuntimeDispatch.TerminalEvidenceIsCommitted", bindings)
        terminal = next(
            item for item in trace["provingTests"]
            if item["id"] == "RuntimeDispatch.terminalEvidence"
        )
        self.assertEqual(
            terminal["path"],
            "crates/ordivon-runtime-core/src/runtime/job_attempt_state.rs",
        )
        self.assertEqual(
            terminal["symbol"],
            "terminal_evidence_requires_result_finish_matching_resolution_and_no_current_attempt",
        )
        self.assertIn("RuntimeDispatch.TerminalEvidenceIsCommitted", terminal["proves"])
        self.assertEqual(self.module.validate(trace, invariants), [])

    def test_terminal_evidence_proof_cannot_be_dropped_without_rejection(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["modelBindings"] = [
            row for row in mutated["formalSpecification"]["modelBindings"]
            if row["id"] != "RuntimeDispatch.TerminalEvidenceIsCommitted"
        ]
        self.assertTrue(any(
            "formal model binding set drift" in error
            for error in self.module.validate(mutated, invariants)
        ))
        mutated = copy.deepcopy(trace)
        mutated["provingTests"] = [
            row for row in mutated["provingTests"]
            if row["id"] != "RuntimeDispatch.terminalEvidence"
        ]
        self.assertTrue(any(
            "proving test set drift" in error
            for error in self.module.validate(mutated, invariants)
        ))

    def test_removed_formal_model_binding_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["modelBindings"].pop()
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("formal model binding set drift" in error for error in errors), errors)


    def test_erasing_all_runtime_invariant_bindings_is_rejected(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["runtimeInvariantBindings"] = []
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("Runtime invariant binding set drift" in error for error in errors), errors)

    def test_erasing_one_runtime_invariant_binding_is_rejected(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["runtimeInvariantBindings"].pop()
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("Runtime invariant binding set drift" in error for error in errors), errors)

    def test_formal_runtime_proof_cannot_import_foreign_owner_rust_test(self):
        # A syntactically valid #[test] outside Runtime is not Runtime evidence.
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as foreign:
            test = Path(foreign) / "external_proof.rs"
            test.write_text("#[test]\nfn foreign_proof() {}\n", encoding="utf-8")
            relative = "../" + str(test.relative_to(ROOT.parent))
            trace, invariants = manifests()
            original = trace["runtimeInvariantBindings"][0]["requiredProofRefs"][0]
            replacement = f"{relative}::foreign_proof"
            trace["runtimeInvariantBindings"][0]["requiredProofRefs"] = [replacement]
            entry = next(row for row in invariants["invariants"] if row["id"] == "I05")
            entry["proof"] = [
                replacement if ref == original else ref for ref in entry["proof"]
            ]
            errors = self.module.validate(trace, invariants)
            self.assertTrue(any("escapes Runtime source" in error for error in errors), errors)

    def test_formal_runtime_seam_cannot_import_foreign_owner_impl(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as foreign:
            source = Path(foreign) / "foreign_impl.rs"
            source.write_text("impl Foreign { fn fake_owner_method() {} }\n", encoding="utf-8")
            relative = "../" + str(source.relative_to(ROOT.parent))
            trace, invariants = manifests()
            seam = trace["contractSeams"][0]
            seam.update(path=relative, ownerKind="impl", owner="Foreign", symbol="fake_owner_method")
            errors = self.module.validate(trace, invariants)
            self.assertTrue(any("escapes Runtime source" in error for error in errors), errors)

    def test_formal_tla_module_and_config_must_be_runtime_owned(self):
        # Byte-for-byte identical TLA material in another Owner does not
        # establish the scoped Runtime model source identity.
        trace, invariants = manifests()
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as foreign:
            for filename, field in (
                ("RuntimeDispatchR1.tla", "modulePath"),
                ("RuntimeDispatchR1.cfg", "configPath"),
            ):
                external = Path(foreign) / filename
                external.write_bytes((ROOT / "formal" / filename).read_bytes())
                trace["formalSpecification"][field] = "../" + str(external.relative_to(ROOT.parent))
            errors = self.module.validate(trace, invariants)
            self.assertTrue(
                sum("formal source escapes Runtime source" in error for error in errors) == 2,
                errors,
            )

    def test_formal_runtime_test_symlink_cannot_leave_owner(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as foreign:
            target = Path(foreign) / "foreign_proof.rs"
            target.write_text("#[test]\nfn foreign_proof() {}\n", encoding="utf-8")
            with tempfile.TemporaryDirectory(dir=ROOT) as local:
                link = Path(local) / "outside.rs"
                link.symlink_to(target)
                errors = self.module.require_test_symbol(link, "foreign_proof")
                self.assertTrue(any("escapes Runtime source" in error for error in errors), errors)

    def test_empty_proof_references_cannot_vacuously_pass(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["runtimeInvariantBindings"][0]["requiredProofRefs"] = []
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("has no required proof references" in error for error in errors), errors)


    def test_ignored_physical_proof_ref_cannot_claim_always_on_invariant(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["runtimeInvariantBindings"][0]["requiredProofRefs"] = [
            "crates/ordivon-runtime-core/src/runtime/integration_tests.rs::runtime_two_observers_do_not_race_dispatch_of_one_accepted_attempt"
        ]
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(
            any("ignored, not an always-on proving test" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
