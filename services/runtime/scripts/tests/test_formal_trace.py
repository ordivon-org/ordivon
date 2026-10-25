"""Consumer-facing checks for the Runtime TLA+ to Rust trace manifest.

Run by the existing Owner unittest discover entrypoint; no second runner
or LEGO test registry is needed.
"""

import copy
import hashlib
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

    def test_live_attempt_identity_is_required_tlc_obligation(self):
        trace, invariant_manifest = manifests()
        bindings = {entry["id"] for entry in trace["formalSpecification"]["modelBindings"]}
        self.assertIn("RuntimeDispatch.NoDetachedLiveAttempt", bindings)
        self.assertIn("RuntimeDispatch.HeldOrphanIsFenced", bindings)
        witnesses = {target for item in trace["provingTests"] for target in item["proves"]}
        self.assertIn("RuntimeDispatch.NoDetachedLiveAttempt", witnesses)
        self.assertIn("RuntimeDispatch.HeldOrphanIsFenced", witnesses)
        admitted = next(
            entry for entry in trace["provingTests"]
            if entry["id"] == "RuntimeDispatch.parallelAdmissionUnique"
        )
        orphan = next(
            entry for entry in trace["provingTests"]
            if entry["id"] == "RuntimeDispatch.ambiguityHeld"
        )
        self.assertIn("RuntimeDispatch.NoDetachedLiveAttempt", admitted["proves"])
        self.assertIn("RuntimeDispatch.HeldOrphanIsFenced", orphan["proves"])
        self.assertNotIn("RuntimeDispatch.NoDetachedLiveAttempt", orphan["proves"])
        self.assertEqual(self.module.validate(trace, invariant_manifest), [])
        modified = copy.deepcopy(trace)
        modified["formalSpecification"]["modelBindings"] = [
            item for item in modified["formalSpecification"]["modelBindings"]
            if item["id"] != "RuntimeDispatch.NoDetachedLiveAttempt"
        ]
        self.assertTrue(any("binding set drift" in err for err in self.module.validate(modified, invariant_manifest)))

        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        checked = {
            row["symbol"]
            for row in trace["formalSpecification"]["modelBindings"]
            if row["kind"] == "invariant"
        }
        weaker_config = config.replace("    HeldOrphanIsFenced\n", "")
        self.assertNotEqual(config, weaker_config)
        self.assertTrue(
            any(
                "HeldOrphanIsFenced" in error
                for error in self.module.check_tlc_config_obligations(weaker_config, checked)
            )
        )

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

    def test_rust_block_comment_cannot_forge_an_always_on_test(self):
        # A textual witness inside a Rust block comment is not compiled or executed.
        for snippet in (
            "/*\n#[test]\nfn fabricated_test() {}\n*/\n",
            "/* outer /* nested */\n#[test]\nfn fabricated_test() {}\n*/\n",
        ):
            with self.subTest(snippet=snippet):
                with tempfile.TemporaryDirectory() as temporary:
                    source = Path(temporary) / "tests.rs"
                    source.write_text(snippet, encoding="utf-8")
                    original_root = self.module.ROOT
                    self.module.ROOT = Path(temporary)
                    try:
                        errors = self.module.require_test_symbol(source, "fabricated_test")
                    finally:
                        self.module.ROOT = original_root
                self.assertTrue(errors, "Comment-only Rust test was accepted as real proof")

    def test_rust_raw_byte_string_cannot_forge_an_always_on_test(self):
        # A raw byte literal can contain unescaped quotes and Rust-looking lines.
        source_text = (
            'const NOTE: &[u8] = br##"literal "interior quote\n'
            '#[test]\nfn fabricated_test() {}\n"##;\n'
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "tests.rs"
            source.write_text(source_text, encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_test_symbol(source, "fabricated_test")
            finally:
                self.module.ROOT = original_root
        self.assertTrue(errors, "Raw byte string was accepted as an executable Rust test")
        self.assertNotIn(
            "fn fabricated_test", self.module._rust_code_only(source_text)
        )

    def test_real_owner_survives_comment_delimiters_inside_string(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "runtime.rs"
            source.write_text(
                'impl Registry { const TEXT: &str = "/* not a comment */"; '
                'fn valid(&self) {} }\n',
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "valid"
                )
            finally:
                self.module.ROOT = original_root
        self.assertEqual(errors, [])

    def test_rust_comment_cannot_forge_a_runtime_owner_method(self):
        # A matching Rust impl may contain unrelated real functions, not a fake method.
        source_text = (
            "impl Registry {\n fn live(&self) {}\n"
            " /* fn forged_dispatch(&self) {} */\n}\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "runtime.rs"
            source.write_text(source_text, encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "forged_dispatch"
                )
            finally:
                self.module.ROOT = original_root
        self.assertTrue(errors, "Comment-only Rust method was accepted as Owner seam")

    def test_rust_comment_cannot_forge_entire_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "runtime.rs"
            source.write_text(
                "/*\nimpl Registry { fn fabricated(&self) {} }\n*/\n",
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "fabricated"
                )
            finally:
                self.module.ROOT = original_root
        self.assertTrue(errors, "Comment-only Rust Owner was accepted as real source")

    def test_conditionally_disabled_rust_tests_are_not_always_on_witnesses(self):
        # Rust cfg(any()) compiles the test out, even with an adjacent #[test].
        # A missing Feature similarly means no test ever ran. Neither is an
        # acceptable always-on proving witness for the Runtime formal model.
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "proof_tests.rs"
            original_root = self.module.ROOT
            self.module.ROOT = Path(temporary)
            try:
                for conditional in (
                    "#[cfg(any())]",
                    '#[cfg(feature = "not_necessarily_enabled")]',
                    "#[cfg_attr(all(), ignore)]",
                ):
                    with self.subTest(conditional=conditional):
                        source.write_text(
                            f"#[test]\n{conditional}\nfn formal_witness() {{}}\n",
                            encoding="utf-8",
                        )
                        errors = self.module.require_test_symbol(source, "formal_witness")
                        self.assertTrue(
                            any("conditionally" in error for error in errors),
                            errors,
                        )
            finally:
                self.module.ROOT = original_root

    def test_disabled_ancestor_module_cannot_be_a_formal_proving_witness(self):
        # Compiler-elided module is not an always-on test, even with #[test].
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "hidden_tests.rs"
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                for gating in ('#[cfg(any())]', '#[cfg(feature = "not_enabled")]'):
                    with self.subTest(gating=gating):
                        source.write_text(
                            f"{gating}\nmod hidden {{\n"
                            "    #[test]\n    fn proof_that_does_not_compile() {}\n"
                            "}\n",
                            encoding="utf-8",
                        )
                        errors = self.module.require_test_symbol(
                            source, "proof_that_does_not_compile"
                        )
                        self.assertTrue(
                            any("ancestor" in error and "conditional" in error for error in errors),
                            f"disabled module falsely admitted as proof: {errors}",
                        )
            finally:
                self.module.ROOT = original_root

    def test_disabled_owner_impl_cannot_be_a_formal_contract_witness(self):
        # Rust cfg(any()) removes the entire impl, despite its textual method.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "owner.rs"
            source.write_text(
                "#[cfg(any())]\nimpl Registry {\n"
                "    fn phantom_dispatch(&self) {}\n"
                "}\n",
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "phantom_dispatch"
                )
            finally:
                self.module.ROOT = original_root
        self.assertTrue(
            any("ancestor" in error and "conditional" in error for error in errors),
            f"compiler-elided impl falsely admitted as Owner contract: {errors}",
        )

    def test_cfg_elided_method_cannot_claim_runtime_owner_contract(self):
        # A real impl may contain only a method removed by rustc cfg handling.
        for attribute in ('#[cfg(any())]', '#[cfg(feature = "nonexistent")]'):
            with self.subTest(attribute=attribute):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    source = root / "runtime.rs"
                    source.write_text(
                        f"impl Registry {{\n  {attribute}\n"
                        "  fn mark_dispatch_issued(&self) {}\n}\n",
                        encoding="utf-8",
                    )
                    old_root = self.module.ROOT
                    self.module.ROOT = root
                    try:
                        errors = self.module.require_owned_method(
                            source, "impl", "Registry", "mark_dispatch_issued"
                        )
                    finally:
                        self.module.ROOT = old_root
                self.assertTrue(
                    errors,
                    f"cfg-elided method falsely admitted as Runtime contract: {attribute}",
                )

    def test_multiline_cfg_before_test_attribute_does_not_forge_a_witness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "tests.rs"
            old_root = self.module.ROOT
            self.module.ROOT = root
            try:
                for gating in (
                    "#[cfg(\n  any()\n)]",
                    "#[cfg_attr(\n  all(),\n  ignore\n)]",
                ):
                    with self.subTest(gating=gating):
                        source.write_text(
                            gating + "\n#[test]\nfn phantom_witness() {}\n",
                            encoding="utf-8",
                        )
                        errors = self.module.require_test_symbol(
                            source, "phantom_witness"
                        )
                        self.assertTrue(
                            errors,
                            f"conditional test falsely admitted as always-on: {gating}",
                        )
            finally:
                self.module.ROOT = old_root

    def test_multiline_cfg_attribute_cannot_promote_method_to_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "runtime.rs"
            source.write_text(
                "impl Registry {\n"
                "  #[cfg(\n"
                "     any()\n"
                "  )]\n"
                "  #[allow(dead_code)]\n"
                "  fn mark_dispatch_issued(&self) {}\n"
                "}\n",
                encoding="utf-8",
            )
            old_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "mark_dispatch_issued"
                )
            finally:
                self.module.ROOT = old_root
        self.assertTrue(errors, "multiline cfg hid method removal from trace gate")

    def test_nested_rust_function_is_not_an_impl_method(self):
        # Rust permits nested functions, but Registry::mark_dispatch_issued
        # does NOT exist here. Textual containment is not an Owner contract.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "runtime.rs"
            source.write_text(
                "impl Registry {\n"
                "  fn helper(&self) {\n"
                "    fn mark_dispatch_issued() {}\n"
                "  }\n"
                "}\n",
                encoding="utf-8",
            )
            old_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "mark_dispatch_issued"
                )
            finally:
                self.module.ROOT = old_root
        self.assertTrue(errors, "nested function falsely admitted as Registry method")
    def test_unexpanded_macro_rules_cannot_forge_a_proving_test(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib.rs").write_text(
                "#[cfg(test)]\nmod tests;\n", encoding="utf-8"
            )
            child = root / "tests.rs"
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                for opening, closing in (("{", "}"), ("(", ")"), ("[", "]")):
                    with self.subTest(delimiter=opening):
                        child.write_text(
                            f"macro_rules! inert {opening}\n"
                            "    () => {\n"
                            "        #[test]\n"
                            "        fn phantom_proof() {}\n"
                            "    };\n"
                            f"{closing}\n",
                            encoding="utf-8",
                        )
                        errors = self.module.require_test_symbol(child, "phantom_proof")
                        self.assertTrue(
                            any("unexpanded macro_rules!" in error for error in errors),
                            f"macro tokens incorrectly granted test proof: {errors}",
                        )
                child.write_text(
                    "macro_rules! inert { () => { #[test] fn fake() {} }; }\n"
                    "#[test]\nfn active_test() {}\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    self.module.require_test_symbol(child, "active_test"), []
                )
            finally:
                self.module.ROOT = original_root

    def test_unexpanded_macro_rules_cannot_forge_an_owner_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "mod.rs").write_text("mod owner;\n", encoding="utf-8")
            child = root / "owner.rs"
            child.write_text(
                "macro_rules! inert {\n"
                "    () => {\n"
                "        impl Registry { fn phantom_owner(&self) {} }\n"
                "    };\n"
                "}\n",
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_owned_method(
                    child, "impl", "Registry", "phantom_owner"
                )
            finally:
                self.module.ROOT = original_root
            self.assertTrue(
                any("unexpanded macro_rules!" in error for error in errors),
                f"macro tokens incorrectly granted owner proof: {errors}",
            )

    def test_external_cfg_disabled_module_cannot_forge_a_proving_test(self):
        # Real rustc --test compiles zero tests when mod tests; is cfg(any()).
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "mod.rs"
            child = root / "tests.rs"
            child.write_text("#[test]\nfn phantom_proof() {}\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                for gate in ('#[cfg(any())]', '#[cfg(feature = "disabled")]'):
                    with self.subTest(gate=gate):
                        parent.write_text(f"{gate}\nmod tests;\n", encoding="utf-8")
                        errors = self.module.require_test_symbol(child, "phantom_proof")
                        self.assertTrue(
                            any("external" in error and "conditional" in error for error in errors),
                            f"cross-file compiler-elided proof falsely admitted: {errors}",
                        )
            finally:
                self.module.ROOT = original_root

    def test_external_cfg_disabled_module_cannot_forge_a_runtime_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "mod.rs").write_text("#[cfg(any())]\nmod owner;\n", encoding="utf-8")
            source = root / "owner.rs"
            source.write_text("impl Registry { fn mark_dispatch_issued(&self) {} }\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_owned_method(
                    source, "impl", "Registry", "mark_dispatch_issued"
                )
            finally:
                self.module.ROOT = original_root
        self.assertTrue(
            any("external" in error and "conditional" in error for error in errors),
            f"cross-file compiler-elided production contract falsely admitted: {errors}",
        )

    def test_conditional_external_include_cannot_forge_owner_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "mod.rs"
            source = root / "owner.rs"
            source.write_text("impl Registry { fn reclaim(&self) {} }\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                parent.write_text('#[cfg(any())]\ninclude!("owner.rs");\n', encoding="utf-8")
                blocked = self.module.require_owned_method(source, "impl", "Registry", "reclaim")
                self.assertTrue(
                    any("conditional" in error and "external" in error for error in blocked),
                    f"disabled include! is not executable owner proof: {blocked}",
                )
                parent.write_text('include!("owner.rs");\n', encoding="utf-8")
                self.assertEqual(
                    self.module.require_owned_method(source, "impl", "Registry", "reclaim"), []
                )
            finally:
                self.module.ROOT = original_root

    def test_external_cfg_test_module_is_admitted_in_native_test_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "mod.rs").write_text("#[cfg(test)]\nmod tests;\n", encoding="utf-8")
            child = root / "tests.rs"
            child.write_text("#[test]\nfn active_test() {}\n", encoding="utf-8")
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_test_symbol(child, "active_test")
            finally:
                self.module.ROOT = original_root
        self.assertEqual(errors, [])

    def test_cfg_test_only_module_is_valid_when_building_native_tests(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "tests.rs"
            source.write_text(
                "#[cfg(test)]\nmod tests {\n"
                "    #[test]\n    fn real_test_witness() {}\n"
                "}\n",
                encoding="utf-8",
            )
            original_root = self.module.ROOT
            self.module.ROOT = root
            try:
                errors = self.module.require_test_symbol(source, "real_test_witness")
            finally:
                self.module.ROOT = original_root
        self.assertEqual(errors, [])

    def test_test_annotation_accepts_adjacent_attributes(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "integration_tests.rs"
            source.write_text("#[test]\n#[allow(dead_code)]\nfn target() {}\n", encoding="utf-8")
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

    def test_formal_binding_cannot_relabel_an_existing_tla_operator(self):
        """A present symbol is not proof that it denotes the declared contract."""
        trace, invariants = manifests()
        aliases = (
            ("RuntimeDispatch.Dispatch", "Admit"),
            ("RuntimeDispatch.AtMostOnceDispatchPerAttempt", "NoUnusedAttemptWasDispatched"),
            ("RuntimeDispatch.AmbiguityRequiresReconciliation", "TerminalAttemptWasDispatched"),
        )
        for binding_id, other_existing_operator in aliases:
            with self.subTest(binding=binding_id, alias=other_existing_operator):
                mutated = copy.deepcopy(trace)
                target = next(
                    item for item in mutated["formalSpecification"]["modelBindings"]
                    if item["id"] == binding_id
                )
                target["symbol"] = other_existing_operator
                errors = self.module.validate(mutated, invariants)
                self.assertTrue(
                    any("formal model binding identity drift" in error for error in errors),
                    errors,
                )

    def test_formal_binding_cannot_retype_a_transition_as_an_invariant(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["modelBindings"][0]["kind"] = "invariant"
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(
            any("formal model binding type drift" in error for error in errors),
            errors,
        )

    def test_no_competing_live_attempts_preserves_always_on_vs_conditional_evidence(self):
        trace, invariants = manifests()
        names = {row["id"] for row in trace["formalSpecification"]["modelBindings"]}
        self.assertIn("RuntimeDispatch.NoCompetingLiveAttempts", names)
        conditional = {row["id"]: row for row in trace["conditionalAcceptanceTests"]}
        self.assertEqual(conditional["RuntimeDispatch.concurrentObservers"]["evidenceMode"], "physical-opt-in")
        self.assertEqual(conditional["RuntimeDispatch.ambiguityNoRedrive"]["evidenceMode"], "physical-opt-in")
        witness = next(row for row in trace["provingTests"] if row["id"] == "RuntimeDispatch.parallelAdmissionUnique")
        self.assertEqual(witness["symbol"], "simultaneous_same_key_creates_one_job_and_one_attempt")
        self.assertIn("RuntimeDispatch.NoCompetingLiveAttempts", witness["proves"])
        self.assertEqual(self.module.validate(trace, invariants), [])

    def test_no_competing_live_attempts_model_binding_cannot_vanish(self):
        trace, invariants = manifests()
        trace["formalSpecification"]["modelBindings"] = [
            row for row in trace["formalSpecification"]["modelBindings"]
            if row["id"] != "RuntimeDispatch.NoCompetingLiveAttempts"
        ]
        errors = self.module.validate(trace, invariants)
        self.assertTrue(any("formal model binding set drift" in error for error in errors))

    def test_removed_formal_model_binding_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated["formalSpecification"]["modelBindings"].pop()
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("formal model binding set drift" in error for error in errors), errors)


    def test_new_model_invariant_cannot_be_claimed_without_a_tlc_check(self):
        # An independently added R2.1 invariant must be checked, not merely
        # named in a proof manifest. No extra schema or proof engine is needed.
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        missing = self.module.check_tlc_config_obligations(
            config, {"NewlyClaimedFormalInvariant"}
        )
        self.assertTrue(
            any("NewlyClaimedFormalInvariant" in error for error in missing),
            missing,
        )

    def test_runtime_model_check_explores_two_explicit_retries(self):
        """An exact hashed two-Attempt source alone cannot qualify consecutive retries."""
        trace, invariants = manifests()
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        self.assertIn("Attempts = {A1, A2, A3}", config)
        downgraded = config.replace("Attempts = {A1, A2, A3}", "Attempts = {A1, A2}")
        self.assertNotEqual(downgraded, config)
        self.assertTrue(any(
            "at least three distinct Attempts" in error
            for error in self.module.check_tlc_config_obligations(downgraded)
        ))
        self.assertEqual(self.module.validate(trace, invariants), [])

    def test_tlc_checker_obligations_survive_source_digest_refresh(self):
        # Hash/currentness alone is not evidence that the model checker
        # actually checked the safety/liveness claim on the same source cut.
        trace, invariants = manifests()
        actual = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        mutations = {
            "lost_safety": actual.replace("    AtMostOnceDispatchPerAttempt\n", ""),
            "lost_progress": actual.replace("    ProgressToFirstDecision\n", ""),
            "lost_fairness": actual.replace("SPECIFICATION FairSpec", "SPECIFICATION Spec"),
            "lost_retry_capacity": actual.replace("Attempts = {A1, A2, A3}", "Attempts = {A1}"),
            "lost_second_retry_capacity": actual.replace("Attempts = {A1, A2, A3}", "Attempts = {A1, A2}"),
            "vacuous_type_constraint": actual.replace(
                "CHECK_DEADLOCK FALSE", "CONSTRAINT TypeOK\nCHECK_DEADLOCK FALSE"
            ),
        }
        for variant, content in mutations.items():
            self.assertNotEqual(actual, content, variant)
            with self.subTest(variant=variant):
                with tempfile.TemporaryDirectory(dir=ROOT / "formal", prefix="model-cut-") as temp:
                    alternative = Path(temp) / "RuntimeDispatchR1.cfg"
                    alternative.write_text(content, encoding="utf-8")
                    fresh = copy.deepcopy(trace)
                    fresh["formalSpecification"]["configPath"] = str(alternative.relative_to(ROOT))
                    fresh["formalSpecification"]["configSha256"] = hashlib.sha256(
                        alternative.read_bytes()
                    ).hexdigest()
                    errors = self.module.validate(fresh, invariants)
                    self.assertTrue(
                        any("TLC config" in error for error in errors),
                        f"source-bound {variant} was accepted without proof: {errors}",
                    )

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

    def test_runtime_formal_manifest_inputs_must_not_be_source_aliases(self):
        """A formal proof manifest or invariant file cannot redirect within Owner."""
        for attribute in ("TRACE", "INVARIANTS"):
            with self.subTest(source=attribute):
                with tempfile.TemporaryDirectory(dir=ROOT / "formal") as folder:
                    link = Path(folder) / "redirected-input.json"
                    link.symlink_to(getattr(self.module, attribute))
                    original = getattr(self.module, attribute)
                    setattr(self.module, attribute, link)
                    try:
                        self.assertEqual(self.module.main(), 1)
                    finally:
                        setattr(self.module, attribute, original)

    def test_runtime_formal_same_owner_symlink_sources_are_not_proof(self):
        """Even same-owner symlinks are aliases, not exact source-cut witnesses."""
        trace, invariants = manifests()
        with tempfile.TemporaryDirectory(dir=ROOT / "formal") as folder:
            temp = Path(folder)
            model = temp / "model.tla"
            config = temp / "model.cfg"
            model.symlink_to(ROOT / "formal/RuntimeDispatchR1.tla")
            config.symlink_to(ROOT / "formal/RuntimeDispatchR1.cfg")
            mutated = copy.deepcopy(trace)
            mutated["formalSpecification"]["modulePath"] = str(model.relative_to(ROOT))
            mutated["formalSpecification"]["configPath"] = str(config.relative_to(ROOT))
            errors = self.module.validate(mutated, invariants)
            self.assertGreaterEqual(
                sum("is not an exact Runtime source" in e for e in errors),
                2,
                errors,
            )

    def test_runtime_proving_test_same_owner_symlink_is_not_its_own_witness(self):
        trace, _ = manifests()
        witness = trace["provingTests"][0]
        real = ROOT / witness["path"]
        with tempfile.TemporaryDirectory(dir=ROOT / "formal") as folder:
            alias = Path(folder) / "alias_proof.rs"
            alias.symlink_to(real)
            errors = self.module.require_test_symbol(alias, witness["symbol"])
            self.assertTrue(
                any("is not an exact Runtime source" in error for error in errors),
                errors,
            )

    def test_runtime_seam_same_owner_symlink_is_not_its_own_witness(self):
        trace, _ = manifests()
        seam = trace["contractSeams"][0]
        real = ROOT / seam["path"]
        with tempfile.TemporaryDirectory(dir=ROOT / "formal") as folder:
            alias = Path(folder) / "alias_contract.rs"
            alias.symlink_to(real)
            errors = self.module.require_owned_method(
                alias, seam["ownerKind"], seam["owner"], seam["symbol"]
            )
            self.assertTrue(
                any("is not an exact Runtime source" in error for error in errors),
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
