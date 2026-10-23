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


class FormalTraceTests(unittest.TestCase):
    def test_formal_trace_gate_passes_current_runtime_binding(self):
        module = load_module()
        self.assertEqual(module.main(), 0)


    def test_owner_slice_is_owner_scoped(self):
        module = load_module()
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
        alpha = module.owner_slice(text, "impl", "Alpha")
        provider = module.owner_slice(text, "trait", "Provider")
        self.assertIn("fn target", alpha)
        self.assertNotIn("fn other", alpha)
        self.assertIn("fn realize", provider)


    def test_schema_v2_rejects_source_fragment_binding_regression(self):
        module = load_module()
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["contractSeams"][0]["requiredFragments"] = ["implementation detail"]
        errors = module.validate(mutated, invariants)
        self.assertIn("schema v2 must not bind source-code body fragments", errors)


    def test_contract_seam_removal_fails_closed(self):
        module = load_module()
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["contractSeams"] = mutated["contractSeams"][1:]
        errors = module.validate(mutated, invariants)
        self.assertTrue(any("contract seam set drift" in error for error in errors))


    def test_production_realization_seam_is_runtime_dispatch_not_contract_probe(self):
        trace, _ = manifests()
        seam = next(item for item in trace["contractSeams"] if item["id"] == "ExecutionProvider.realize")
        self.assertEqual(seam["owner"], "Runtime")
        self.assertEqual(seam["symbol"], "dispatch_attempt")
        supporting = next(
            item
            for item in trace["supportingContracts"]
            if item["id"] == "ExecutionProvider.assumeGuarantee"
        )
        self.assertEqual(supporting["owner"], "ExecutionProviderSpi")
        self.assertEqual(supporting["symbol"], "realize")


    def test_unknown_proving_target_fails_closed(self):
        module = load_module()
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["provingTests"][0]["proves"].append("Unknown.seam")
        errors = module.validate(mutated, invariants)
        self.assertTrue(any("references unknown target" in error for error in errors))


    def test_proving_test_annotation_belongs_to_exact_function(self):
        module = load_module()
        with tempfile.TemporaryDirectory(prefix="ordivon-formal-trace-", dir=ROOT) as directory:
            source = Path(directory) / "proof.rs"
            source.write_text(
                "#[test]\nfn other_test() {}\nfn claimed_test() {}\n",
                encoding="utf-8",
            )
            errors = module.require_test_symbol(source, "claimed_test")
            self.assertTrue(any("not marked #[test]" in error for error in errors), errors)

            source.write_text(
                '#[test]\n#[cfg(target_os = "linux")]\nfn claimed_test() {}\n',
                encoding="utf-8",
            )
            self.assertEqual(module.require_test_symbol(source, "claimed_test"), [])
