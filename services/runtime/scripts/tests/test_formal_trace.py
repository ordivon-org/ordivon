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
            entry for entry in trace["provingTests"] if entry["id"] == "RuntimeDispatch.parallelAdmissionUnique"
        )
        orphan = next(entry for entry in trace["provingTests"] if entry["id"] == "RuntimeDispatch.ambiguityHeld")
        self.assertIn("RuntimeDispatch.NoDetachedLiveAttempt", admitted["proves"])
        self.assertIn("RuntimeDispatch.HeldOrphanIsFenced", orphan["proves"])
        self.assertNotIn("RuntimeDispatch.NoDetachedLiveAttempt", orphan["proves"])
        self.assertEqual(self.module.validate(trace, invariant_manifest), [])
        modified = copy.deepcopy(trace)
        modified["formalSpecification"]["modelBindings"] = [
            item
            for item in modified["formalSpecification"]["modelBindings"]
            if item["id"] != "RuntimeDispatch.NoDetachedLiveAttempt"
        ]
        self.assertTrue(any("binding set drift" in err for err in self.module.validate(modified, invariant_manifest)))

        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        checked = {row["symbol"] for row in trace["formalSpecification"]["modelBindings"] if row["kind"] == "invariant"}
        weaker_config = config.replace("    HeldOrphanIsFenced\n", "")
        self.assertNotEqual(config, weaker_config)
        self.assertTrue(
            any(
                "HeldOrphanIsFenced" in error
                for error in self.module.check_tlc_config_obligations(weaker_config, checked)
            )
        )

    def test_formal_trace_gate_passes_current_runtime_binding(self):
        # The full native execution is independently covered by Cargo jobs.
        # This unit test checks the source/schema driver only.
        from unittest.mock import patch

        with patch.object(self.module, "qualify_native_witnesses", return_value={}):
            self.assertEqual(self.module.main(), 0)

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

    def test_physical_witness_must_be_explicitly_ignored(self):
        trace, _ = manifests()
        witness = copy.deepcopy(trace["conditionalAcceptanceTests"][0])
        name = "runtime::integration_tests::" + witness["symbol"]
        self.assertEqual(self.module._require_native_test_role(witness, {name}, {name}, require_ignored=True), name)
        witness["path"] = "crates/ordivon-runtime-core/src/runtime/tests.rs"
        witness["symbol"] = "orphaned_terminal_keeps_capacity_reserved"
        always_on = "runtime::tests::orphaned_terminal_keeps_capacity_reserved"
        with self.assertRaisesRegex(ValueError, "invalid ignored/always-on"):
            self.module._require_native_test_role(
                witness,
                {always_on},
                set(),
                require_ignored=True,
            )

    def test_missing_conditional_physical_witness_fails_closed(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        mutated.pop("conditionalAcceptanceTests")
        errors = self.module.validate(mutated, invariants)
        self.assertIn("conditional acceptance test set drift", errors)

    def test_conditional_evidence_cannot_replace_always_on_oracle(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        physical = mutated["conditionalAcceptanceTests"][0]
        mutated["provingTests"][0]["path"] = physical["path"]
        mutated["provingTests"][0]["symbol"] = physical["symbol"]
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("conditional opt-in evidence" in e for e in errors), errors)
        native = "runtime::integration_tests::" + physical["symbol"]
        with self.assertRaisesRegex(ValueError, "invalid ignored/always-on"):
            self.module._require_native_test_role(
                mutated["provingTests"][0],
                {native},
                {native},
                require_ignored=False,
            )

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
        terminal = next(item for item in trace["provingTests"] if item["id"] == "RuntimeDispatch.terminalEvidence")
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
            row
            for row in mutated["formalSpecification"]["modelBindings"]
            if row["id"] != "RuntimeDispatch.TerminalEvidenceIsCommitted"
        ]
        self.assertTrue(
            any("formal model binding set drift" in error for error in self.module.validate(mutated, invariants))
        )
        mutated = copy.deepcopy(trace)
        mutated["provingTests"] = [
            row for row in mutated["provingTests"] if row["id"] != "RuntimeDispatch.terminalEvidence"
        ]
        self.assertTrue(any("proving test set drift" in error for error in self.module.validate(mutated, invariants)))

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
                    item for item in mutated["formalSpecification"]["modelBindings"] if item["id"] == binding_id
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
            row
            for row in trace["formalSpecification"]["modelBindings"]
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

    def test_result_provenance_invariants_are_never_dropped_from_tlc_config(self):
        """An RW9 TLC PASS must check matching-result provenance, not only source hashes."""
        trace, _ = manifests()
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        claimed = {row["symbol"] for row in trace["formalSpecification"]["modelBindings"] if row["kind"] == "invariant"}
        for name in (
            "MatchingResultRequiredForTerminal",
            "NoForeignResultIsTerminal",
            "LocalCancellationNeverDispatched",
        ):
            with self.subTest(invariant=name):
                self.assertIn(f"    {name}\n", config)
                downgraded = config.replace(f"    {name}\n", "")
                errors = self.module.check_tlc_config_obligations(downgraded, claimed)
                self.assertTrue(
                    any(name in error for error in errors),
                    f"RW9 missing result-provenance TLC invariant was accepted: {name}, {errors}",
                )

    def test_new_model_invariant_cannot_be_claimed_without_a_tlc_check(self):
        # An independently added R2.1 invariant must be checked, not merely
        # named in a proof manifest. No extra schema or proof engine is needed.
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        missing = self.module.check_tlc_config_obligations(config, {"NewlyClaimedFormalInvariant"})
        self.assertTrue(
            any("NewlyClaimedFormalInvariant" in error for error in missing),
            missing,
        )

    def test_foreign_result_recovery_is_a_checked_tlc_obligation(self):
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        self.assertIn("ForeignResultDoesNotDisableMatchingRecovery", config)
        weakened = config.replace("    ForeignResultDoesNotDisableMatchingRecovery\n", "")
        self.assertNotEqual(weakened, config)
        errors = self.module.check_tlc_config_obligations(weakened)
        self.assertTrue(any("ForeignResultDoesNotDisableMatchingRecovery" in e for e in errors))
        native = (ROOT / "scripts/tla-formal").read_text(encoding="utf-8")
        self.assertIn("check_foreign_result_recovery_counterexample", native)
        self.assertIn("ForeignResultIsUnreachable is violated.", native)
        self.assertIn("ForeignResultDoesNotDisableMatchingRecovery is violated.", native)

    def test_runtime_model_check_explores_two_explicit_retries(self):
        """An exact hashed two-Attempt source alone cannot qualify consecutive retries."""
        trace, invariants = manifests()
        config = (ROOT / "formal/RuntimeDispatchR1.cfg").read_text(encoding="utf-8")
        self.assertIn("Attempts = {A1, A2, A3}", config)
        downgraded = config.replace("Attempts = {A1, A2, A3}", "Attempts = {A1, A2}")
        self.assertNotEqual(downgraded, config)
        self.assertTrue(
            any(
                "at least three distinct Attempts" in error
                for error in self.module.check_tlc_config_obligations(downgraded)
            )
        )
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
                    fresh["formalSpecification"]["configSha256"] = hashlib.sha256(alternative.read_bytes()).hexdigest()
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
            entry["proof"] = [replacement if ref == original else ref for ref in entry["proof"]]
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
            errors = self.module.require_test_source(alias, witness["symbol"])
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
            errors = self.module.require_contract_source(alias, seam["ownerKind"], seam["owner"], seam["symbol"])
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
                errors = self.module.require_test_source(link, "foreign_proof")
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
            any("uses conditional opt-in proof" in error for error in errors),
            errors,
        )

    def test_native_cargo_witness_rejects_hidden_git_index_and_toolchain_changes(self):
        """Source impact and Cargo witness admission share Git source guards."""
        import subprocess

        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            runtime = repo / "services/runtime"
            runtime.mkdir(parents=True)
            source = runtime / "crates/core.rs"
            source.parent.mkdir()
            source.write_text("pub fn sample() {}\n", encoding="utf-8")
            toolchain = repo / "mise.toml"
            toolchain.write_text('[tools]\nrust = "1.99.1"\n', encoding="utf-8")

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True, capture_output=True,
                ).stdout.decode().strip()

            git("init", "-q")
            git("add", ".")
            git("-c", "user.name=FormalTest", "-c",
                "user.email=test@example.invalid", "commit", "-qm", "source")
            expected = git("rev-parse", "HEAD")
            prior = self.module.ROOT
            self.module.ROOT = runtime
            try:
                self.assertEqual(self.module._qualified_native_source_head(), expected)
                for enable, disable in (
                    ("--skip-worktree", "--no-skip-worktree"),
                    ("--assume-unchanged", "--no-assume-unchanged"),
                ):
                    with self.subTest(flag=enable):
                        git("update-index", enable, "--", "services/runtime/crates/core.rs")
                        source.write_text("pub fn hidden_edit() {}\n", encoding="utf-8")
                        self.assertEqual(
                            git("status", "--porcelain", "--", "services/runtime"),
                            "",
                        )
                        # Pre-execution admission fails even before Cargo is run.
                        with self.assertRaisesRegex(ValueError, "unsafe Git index flags"):
                            self.module.qualify_native_witnesses({})
                        source.write_text("pub fn sample() {}\n", encoding="utf-8")
                        git("update-index", disable, "--", "services/runtime/crates/core.rs")

                toolchain.write_text('[tools]\nrust = "9.9.9"\n', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "worktree is dirty"):
                    self.module.qualify_native_witnesses({})
                toolchain.write_text('[tools]\nrust = "1.99.1"\n', encoding="utf-8")
                self.assertEqual(self.module._qualified_native_source_head(), expected)
            finally:
                self.module.ROOT = prior

    def test_native_cargo_witness_missing_git_cut_reports_unknown_before_cargo(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "services/runtime"
            runtime.mkdir(parents=True)
            previous = self.module.ROOT
            self.module.ROOT = runtime
            try:
                with self.assertRaisesRegex(ValueError, "Git SourceCut is unavailable"):
                    self.module.qualify_native_witnesses({})
            finally:
                self.module.ROOT = previous

    def test_native_witness_identity_is_module_and_source_scoped(self):
        trace, _ = manifests()
        witness = trace["provingTests"][0]
        native = "runtime::tests::" + witness["symbol"]
        self.assertEqual(self.module._native_witness_name(witness, {native}), native)
        with self.assertRaisesRegex(ValueError, "not uniquely registered"):
            self.module._native_witness_name(witness, {"unrelated::tests::" + witness["symbol"]})

    def test_native_witness_anti_vacuity_requires_one_executed_pass(self):
        def summary(passed: int, ignored: int, filtered: int) -> str:
            return (
                f"test result: ok. {passed} passed; 0 failed; {ignored} ignored; "
                f"0 measured; {filtered} filtered out; finished in 0.00s"
            )

        self.module._require_exact_native_pass(summary(1, 0, 415))
        for bad in (summary(0, 0, 416), summary(0, 1, 415), summary(2, 0, 414), "test result: FAILED"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    self.module._require_exact_native_pass(bad)

    def test_native_method_contract_manifest_drift_is_rejected(self):
        trace, invariants = manifests()
        changed = copy.deepcopy(trace)
        changed["contractSeams"][0]["symbol"] = "mark_dispatch_from_text_only"
        errors = self.module.validate(changed, invariants)
        self.assertTrue(
            any("native Rust contract seam identity drift" in error for error in errors),
            errors,
        )

    def test_all_four_contracts_bind_only_three_compiler_owned_tests(self):
        trace, _ = manifests()
        seams = [*trace["contractSeams"], *trace["supportingContracts"]]
        self.assertEqual(len(seams), 4)
        names = [self.module.native_contract_expected(seam) for seam in seams]
        self.assertEqual(len(set(names)), 3)
        self.assertTrue(all(name.startswith("runtime::") and "native_formal_" in name for name in names))

    def test_runtime_required_proof_cannot_point_to_undeclared_native_test(self):
        trace, invariants = manifests()
        mutated = copy.deepcopy(trace)
        invariant_id = mutated["runtimeInvariantBindings"][0]["id"]
        foreign = "crates/ordivon-runtime-core/src/runtime/tests.rs::not_a_declared_compiler_test_witness"
        mutated["runtimeInvariantBindings"][0]["requiredProofRefs"] = [foreign]
        for row in invariants["invariants"]:
            if row["id"] == invariant_id:
                row["proof"].append(foreign)
        errors = self.module.validate(mutated, invariants)
        self.assertTrue(any("lacks declared native proving test" in e for e in errors), errors)

    def test_runtime_formal_source_impact_is_selective_for_exact_test_file(self):
        trace, invariants = manifests()
        changed = {"services/runtime/crates/ordivon-runtime-core/src/runtime/execution_provider.rs"}
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        statuses = {row["id"]: row["standing"] for row in result["standingByWitness"]}
        self.assertEqual(statuses["ExecutionProvider.guaranteeNegativeControl"], "RECHECK_REQUIRED")
        self.assertEqual(statuses["RuntimeDispatch.ambiguityHeld"], "UNKNOWN")
        self.assertEqual(result["unindexedRuntimeChanges"], [])
        self.assertIn("not proof PASS", result["nonClaims"][0])

    def test_runtime_formal_indexed_shared_registry_callee_does_not_false_reuse(self):
        trace, invariants = manifests()
        # Actual Rust: runtime/tests.rs::orphaned_terminal_keeps_capacity_reserved
        # calls Registry::commit_terminal, implemented in registry/lifecycle.rs.
        # This path is indexed by registryDispatchCAS but not ambiguityHeld.
        changed = {"services/runtime/crates/ordivon-runtime-core/src/runtime/registry/lifecycle.rs"}
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        statuses = {row["id"]: row["standing"] for row in result["standingByWitness"]}
        self.assertEqual(result["unindexedRuntimeChanges"], [])
        self.assertEqual(statuses["RuntimeDispatch.registryDispatchCAS"], "RECHECK_REQUIRED")
        self.assertEqual(statuses["RuntimeDispatch.ambiguityHeld"], "UNKNOWN")
        self.assertTrue(
            any("shared Rust callees" in note for note in result["nonClaims"]),
            result["nonClaims"],
        )

    def test_runtime_tlc_checker_source_changes_recheck_all_scoped_witnesses(self):
        """A model proof consumes the actual checker path, not only TLA bytes."""
        trace, invariants = manifests()
        for path in (
            "services/runtime/formal/toolchain.lock.json",
            "services/runtime/scripts/tla-formal",
            "services/runtime/scripts/tests/test_tla_formal_external_jar.py",
        ):
            with self.subTest(path=path):
                result = self.module.project_proving_test_source_impact(trace, invariants, {path})
                self.assertEqual(result["unindexedRuntimeChanges"], [])
                self.assertEqual(
                    {row["standing"] for row in result["standingByWitness"]},
                    {"RECHECK_REQUIRED"},
                )
                self.assertTrue(all(row["matchedChangedPaths"] == [path] for row in result["standingByWitness"]))

    def test_runtime_formal_source_impact_model_change_rechecks_all(self):
        trace, invariants = manifests()
        changed = {"services/runtime/formal/RuntimeDispatchR1.tla"}
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        self.assertTrue(result["standingByWitness"])
        self.assertEqual(
            {row["standing"] for row in result["standingByWitness"]},
            {"RECHECK_REQUIRED"},
        )

    def test_runtime_formal_source_impact_unknown_unindexed_change_fails_closed(self):
        trace, invariants = manifests()
        changed = {"services/runtime/crates/ordivon-runtime-core/src/unknown_new_module.rs"}
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        self.assertEqual(result["unindexedRuntimeChanges"], sorted(changed))
        self.assertEqual(
            {row["standing"] for row in result["standingByWitness"]},
            {"UNKNOWN"},
        )

    def test_runtime_formal_source_impact_known_recheck_not_erased_by_unknown(self):
        trace, invariants = manifests()
        changed = {
            "services/runtime/crates/ordivon-runtime-core/src/runtime/execution_provider.rs",
            "services/runtime/Cargo.lock",
        }
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        statuses = {row["id"]: row["standing"] for row in result["standingByWitness"]}
        self.assertEqual(statuses["ExecutionProvider.guaranteeNegativeControl"], "RECHECK_REQUIRED")
        self.assertEqual(statuses["RuntimeDispatch.ambiguityHeld"], "UNKNOWN")

    def test_runtime_formal_source_impact_shared_toolchain_changes_unknown(self):
        """Root build/toolchain inputs can invalidate a local Rust proof witness."""
        trace, invariants = manifests()
        for path in (
            "Cargo.lock",
            "Cargo.toml",
            "rust-toolchain.toml",
            ".cargo/config.toml",
            "mise.toml",
        ):
            with self.subTest(path=path):
                result = self.module.project_proving_test_source_impact(trace, invariants, {path})
                self.assertEqual(
                    {row["standing"] for row in result["standingByWitness"]},
                    {"UNKNOWN"},
                    result,
                )
                self.assertIn(path, result["crosscuttingAssumptionChanges"])

    def test_runtime_formal_source_impact_local_recheck_survives_toolchain_unknown(self):
        trace, invariants = manifests()
        changed = {
            "Cargo.lock",
            "services/runtime/crates/ordivon-runtime-core/src/runtime/execution_provider.rs",
        }
        result = self.module.project_proving_test_source_impact(trace, invariants, changed)
        statuses = {row["id"]: row["standing"] for row in result["standingByWitness"]}
        self.assertEqual(statuses["ExecutionProvider.guaranteeNegativeControl"], "RECHECK_REQUIRED")
        self.assertEqual(statuses["RuntimeDispatch.ambiguityHeld"], "UNKNOWN")

    def test_runtime_formal_source_impact_unrelated_repository_change_only_local_hint(self):
        trace, invariants = manifests()
        result = self.module.project_proving_test_source_impact(trace, invariants, {"README.md"})
        self.assertEqual(
            {row["standing"] for row in result["standingByWitness"]},
            {"REUSE_CANDIDATE"},
        )
        self.assertIn("ONLY", result["scope"])
        self.assertFalse(any("PASS" == row["standing"] for row in result["standingByWitness"]))

    def test_runtime_formal_source_impact_rejects_hidden_dirty_git_index_flags(self):
        import subprocess

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "services/runtime").mkdir(parents=True)
            source = repo / "services/runtime/core.rs"
            original = "pub fn original() {}\\n"
            source.write_text(original, encoding="utf-8")
            # A clean earlier index entry must not mask a later flagged entry
            # when ls-files -z emits multiple NUL-delimited records.
            (repo / "services/runtime/a.rs").write_text("pub fn clean() {}\n", encoding="utf-8")

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                ).stdout

            git("init", "-q")
            git("add", "--", "services/runtime/a.rs", "services/runtime/core.rs")
            git("-c", "user.name=FormalTest", "-c", "user.email=test@example.invalid", "commit", "-qm", "initial")
            commit = git("rev-parse", "HEAD").decode().strip()
            original_root = self.module.ROOT
            self.module.ROOT = repo / "services/runtime"
            try:
                self.assertEqual(self.module._git_source_changes(commit, commit), set())
                for enable, disable in (
                    ("--assume-unchanged", "--no-assume-unchanged"),
                    ("--skip-worktree", "--no-skip-worktree"),
                ):
                    with self.subTest(flag=enable):
                        git("update-index", enable, "--", "services/runtime/core.rs")
                        source.write_text("pub fn tampered() {}\\n", encoding="utf-8")
                        # This is the real Git behavior that invalidated the old
                        # --porcelain-only clean-worktree precondition.
                        self.assertEqual(
                            git("status", "--porcelain", "--untracked-files=normal", "--", "services/runtime"),
                            b"",
                        )
                        with self.assertRaisesRegex(ValueError, "unsafe Git index flags"):
                            self.module._git_source_changes(commit, commit)
                        source.write_text(original, encoding="utf-8")
                        git("update-index", disable, "--", "services/runtime/core.rs")
                self.assertEqual(self.module._git_source_changes(commit, commit), set())
            finally:
                self.module.ROOT = original_root

    def test_runtime_formal_source_impact_rejects_dirty_root_toolchain_and_hidden_flags(self):
        """A clean Runtime subtree is insufficient for a source-bound Rust witness."""
        import subprocess

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "services/runtime").mkdir(parents=True)
            (repo / ".cargo").mkdir()
            (repo / "services/runtime/core.rs").write_text("fn core() {}\n", encoding="utf-8")
            mise = repo / "mise.toml"
            mise_original = '[tools]\npython = "3.15.1"\n'
            mise.write_text(mise_original, encoding="utf-8")
            config = repo / ".cargo/config.toml"
            config.write_text("[build]\n", encoding="utf-8")

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                ).stdout

            git("init", "-q")
            git("add", ".")
            git("-c", "user.name=FormalTest", "-c", "user.email=test@example.invalid", "commit", "-qm", "source-cut")
            commit = git("rev-parse", "HEAD").decode().strip()
            previous_root = self.module.ROOT
            self.module.ROOT = repo / "services/runtime"
            try:
                self.assertEqual(self.module._git_source_changes(commit, commit), set())
                mise.write_text('[tools]\npython = "0.0.0"\n', encoding="utf-8")
                self.assertEqual(git("status", "--porcelain", "--", "services/runtime"), b"")
                with self.assertRaisesRegex(ValueError, "worktree is dirty"):
                    self.module._git_source_changes(commit, commit)
                mise.write_text(mise_original, encoding="utf-8")

                git("update-index", "--skip-worktree", "--", "mise.toml")
                mise.write_text('[tools]\npython = "0.0.0"\n', encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unsafe Git index flags"):
                    self.module._git_source_changes(commit, commit)
                mise.write_text(mise_original, encoding="utf-8")
                git("update-index", "--no-skip-worktree", "--", "mise.toml")

                config.write_text("[build]\nrustflags = []\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "worktree is dirty"):
                    self.module._git_source_changes(commit, commit)
                config.write_text("[build]\n", encoding="utf-8")
                self.assertEqual(self.module._git_source_changes(commit, commit), set())
            finally:
                self.module.ROOT = previous_root

    def test_runtime_formal_git_impact_requires_ancestor_source_cut(self):
        """Divergent PR tip diffs must not count target-only changes as PR impact."""
        import subprocess

        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            source = repo / "services/runtime"
            source.mkdir(parents=True)
            (source / "core.rs").write_text("fn baseline() {}\\n", encoding="utf-8")

            def git(*args):
                return (
                    subprocess.run(
                        ["git", "-C", str(repo), *args],
                        check=True,
                        capture_output=True,
                    )
                    .stdout.decode()
                    .strip()
                )

            def commit(msg):
                git("add", ".")
                git("-c", "user.name=FormalTest", "-c", "user.email=test@example.invalid", "commit", "-qm", msg)
                return git("rev-parse", "HEAD")

            git("init", "-q")
            root = commit("shared base")
            git("checkout", "-qb", "target-main")
            (source / "core.rs").write_text("fn main_only() {}\\n", encoding="utf-8")
            main_tip = commit("main-only Rust change")
            git("checkout", "-qb", "candidate-pr", root)
            (repo / "README.md").write_text("docs-only PR\\n", encoding="utf-8")
            candidate_tip = commit("PR-only docs change")

            original_root = self.module.ROOT
            self.module.ROOT = source
            try:
                self.assertEqual(
                    self.module._git_source_changes(root, candidate_tip),
                    {"README.md"},
                )
                self.assertNotEqual(main_tip, candidate_tip)
                # A direct diff of main vs PR would falsely attribute the
                # main-only changed Rust source to this docs-only PR.
                self.assertIn(
                    "services/runtime/core.rs",
                    git("diff", "--name-only", main_tip, candidate_tip),
                )
                with self.assertRaisesRegex(ValueError, "must be an ancestor"):
                    self.module._git_source_changes(main_tip, candidate_tip)
            finally:
                self.module.ROOT = original_root

    def test_runtime_formal_source_impact_rejects_untrusted_paths_and_git_ref(self):
        trace, invariants = manifests()
        for bad in ("../escape", "/absolute", "services//runtime/file", "services\\runtime\\bad"):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(ValueError, "normalized Git paths"):
                    self.module.project_proving_test_source_impact(trace, invariants, {bad})
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            self.module._git_source_changes("HEAD", "HEAD")


if __name__ == "__main__":
    unittest.main()
