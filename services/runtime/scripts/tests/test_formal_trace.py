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


    def test_changed_formal_model_digest_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["moduleSha256"] = "0" * 64
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("formal source drift" in error for error in errors), errors)

    def test_removed_formal_model_binding_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["modelBindings"].pop()
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("formal model binding set drift" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
