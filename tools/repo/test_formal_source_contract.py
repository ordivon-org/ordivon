"""Ordivon core Formal source readset is admitted by native root CI.

This checks Git SourceCut and CLI wiring, NOT external theorem prover verdicts.
"""

from __future__ import annotations

import importlib.util
import os
import shlex
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
FORMAL = ROOT / "tools/formal"
SPEC = importlib.util.spec_from_file_location(
    "ordivon_core_formal_source_contract", FORMAL / "verify.py"
)
assert SPEC is not None and SPEC.loader is not None
formal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(formal)


def _verify_formal_task_behavior(run: str) -> None:
    """Accept bounded shell setup, but require one real final verifier call.

    A source contract is the invoked verifier and absence of unexpected
    side-effects, not equality of the entire implementation's shell string.
    This is a source-level admission check, not proof of deployed semantics.
    """
    if not isinstance(run, str):
        raise ValueError("Formal task must be a shell string")
    commands = [
        line.strip() for line in run.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not commands or commands[-1] != "python3 -I verify.py":
        raise ValueError("Formal task requires isolated native verifier call")
    if commands.count("python3 -I verify.py") != 1:
        raise ValueError("Formal task must invoke the verifier exactly once")
    for line in commands[:-1]:
        # A shell status or appended action is not an equivalent environment
        # setup. Only explicit Kani-home initialization and strict shell flags
        # are admitted without a separate consumer requalification.
        if any(token in line for token in (";", "&", "|", "`", "$(", ">", "<", "\\")):
            raise ValueError("Formal task setup contains a shell control effect")
        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            raise ValueError("Formal task setup shell syntax is invalid") from exc
        if tokens == ["set", "-euo", "pipefail"]:
            continue
        if (len(tokens) == 2 and tokens[0] == "export"
                and tokens[1].startswith("KANI_HOME=")
                and tokens[1] != "KANI_HOME="):
            continue
        raise ValueError("Unexpected executable or environment change before verifier")


class FormalSourceConsumerContractTests(unittest.TestCase):
    def test_native_formal_cli_is_reachable_from_root_mise(self) -> None:
        root = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        formal_tasks = tomllib.loads(
            (FORMAL / "mise.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            root["tasks"]["formal:verify"]["run"],
            "cd tools/formal && mise run verify",
        )
        _verify_formal_task_behavior(formal_tasks["tasks"]["verify"]["run"])
        ci_script = root["tasks"]["repo:ci"]["run"]
        self.assertIn(
            "python3 -m unittest tools/repo/test_formal_source_contract.py",
            ci_script,
        )
        # Repo CI performs a bounded source admission, not the entire
        # opt-in toolchain: never fake Lean/Z3/Kani proof success.
        self.assertNotIn("mise run formal:verify", ci_script)

    def test_formal_consumer_allows_real_kani_cache_prelude_without_skipping_proof(self) -> None:
        """A KANI_HOME setup is not a different proof interface."""
        peer_task = (
            "# Isolate Kani's potentially broken shared cache\n"
            'export KANI_HOME="${KANI_HOME:-${HOME}/.cache/ordivon/kani}"\n'
            "python3 -I verify.py\n"
        )
        _verify_formal_task_behavior("python3 -I verify.py")
        _verify_formal_task_behavior(peer_task)

    def test_loader_trace_can_fake_zero_exit_without_executing_proof(self) -> None:
        """An unchanged real ELF executable can report rc0 without running its code."""
        import os
        import sys

        with tempfile.TemporaryDirectory(prefix="ordivon-formal-elf-loader-") as tmp:
            receipt = Path(tmp) / "executed"
            command = [sys.executable, "-I", "-c",
                       "from pathlib import Path; Path(" + repr(str(receipt)) +
                       ").write_text('executed')"]
            # Direct positive oracle *would* misclassify a loader listing
            # as a successful process exit; its intended effect never ran.
            trace_env = {**os.environ, "LD_TRACE_LOADED_OBJECTS": "1"}
            observed = subprocess.run(
                command, env=trace_env, capture_output=True, text=True, timeout=8,
            )
            self.assertEqual(observed.returncode, 0)
            self.assertFalse(receipt.exists(), "code unexpectedly ran under loader trace")
            with patch.dict(os.environ, {"LD_TRACE_LOADED_OBJECTS": "1"}):
                with self.assertRaisesRegex(ValueError, "loader|LD_"):
                    formal.run("model positive probe", command, expected_rc=0)
            self.assertFalse(receipt.exists())

    def test_formal_run_rejects_loader_in_explicit_child_overlay(self) -> None:
        """Named child overlays must not bypass the parent LD_* admission."""
        import sys

        with tempfile.TemporaryDirectory(prefix="ordivon-formal-loader-overlay-") as tmp:
            marker = Path(tmp) / "executed"
            command = [sys.executable, "-I", "-c",
                       "from pathlib import Path; Path(" + repr(str(marker)) +
                       ").write_text('executed')"]
            with self.assertRaisesRegex(ValueError, "loader|LD_"):
                formal.run(
                    "positive child", command, expected_rc=0,
                    env_overlay={"LD_TRACE_LOADED_OBJECTS": "1"},
                )
            self.assertFalse(marker.exists())

    def test_formal_proof_rejects_loader_overrides_before_source_or_tools(self) -> None:
        """No formal proof receipt may issue under ambient LD_* overrides."""
        for variable in ("LD_PRELOAD", "LD_LIBRARY_PATH",
                         "LD_AUDIT", "LD_TRACE_LOADED_OBJECTS"):
            with self.subTest(variable=variable):
                with patch.dict(os.environ, {variable: "/tmp/untrusted-loader-input"}):
                    with patch.object(formal, "qualified_source_cut") as source:
                        with self.assertRaisesRegex(ValueError, "loader|LD_"):
                            formal.main()
                        source.assert_not_called()

    def test_formal_task_excludes_untracked_python_module_shadow(self) -> None:
        """Real root->mise child command must not load forged imports from CWD or PYTHONPATH."""
        import os

        run = tomllib.loads((FORMAL / "mise.toml").read_text(encoding="utf-8"))[
            "tasks"
        ]["verify"]["run"]
        with tempfile.TemporaryDirectory(prefix="ordivon-formal-py-import-") as temp:
            root = Path(temp)
            poison = root / "external-imports"
            poison.mkdir()
            (root / "json.py").write_text(
                "raise RuntimeError('UNTRACKED_CWD_IMPORT_EXECUTED')\n",
                encoding="utf-8",
            )
            (poison / "json.py").write_text(
                "raise RuntimeError('UNTRACKED_PYTHONPATH_IMPORT_EXECUTED')\n",
                encoding="utf-8",
            )
            receipt = root / "verified.json"
            (root / "verify.py").write_text(
                "import json, os, sys\n"
                "assert sys.flags.isolated == 1, 'native verifier is not Python isolated'\n"
                "with open(os.environ['FORMAL_IMPORT_RECEIPT'], 'w') as f:\n"
                "    f.write(json.dumps({'isolated': True}))\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["bash", "-euo", "pipefail", "-c", run],
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(poison),
                     "FORMAL_IMPORT_RECEIPT": str(receipt)},
                capture_output=True, text=True, timeout=8,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(receipt.read_text(), '{"isolated": true}')

    def test_direct_nonisolated_verifier_fails_before_untrusted_import(self) -> None:
        """Direct invocation bypassing mise must fail before any PYTHONPATH import."""
        import os
        import sys

        with tempfile.TemporaryDirectory(prefix="ordivon-direct-import-gate-") as tmp:
            poison = Path(tmp)
            marker = poison / "imported-marker"
            (poison / "json.py").write_text(
                "import os\n"
                "open(os.environ['FORMAL_IMPORT_MARKER'], 'w').close()\n"
                "raise RuntimeError('FORGED_JSON_MODULE_EXECUTED')\n",
                encoding="utf-8",
            )
            attempt = subprocess.run(
                [sys.executable, str(FORMAL / "verify.py")],
                cwd=ROOT, capture_output=True, text=True, timeout=8,
                env={**os.environ, "PYTHONPATH": str(poison),
                     "FORMAL_IMPORT_MARKER": str(marker)},
            )
            self.assertNotEqual(attempt.returncode, 0)
            self.assertIn("requires Python -I", attempt.stderr + attempt.stdout)
            self.assertFalse(marker.exists(), "module was imported before fail-closed preflight")

    def test_formal_source_contract_rejects_nonisolated_runner(self) -> None:
        with self.assertRaisesRegex(ValueError, "isolated|native verifier"):
            _verify_formal_task_behavior("python3 verify.py")

    def test_formal_child_contract_has_nonvacuous_execution_receipts(self) -> None:
        """R2.1 bounded executable A/G seam; lexical admission is not execution."""
        import os

        commands = (
            tomllib.loads((FORMAL / "mise.toml").read_text(encoding="utf-8"))[
                "tasks"
            ]["verify"]["run"],
            '# Prepare only the native optional Kani cache\n'
            'export KANI_HOME="${KANI_HOME:-${HOME}/.cache/ordivon/kani}"\n'
            'python3 -I verify.py',
        )
        with tempfile.TemporaryDirectory(prefix="ordivon-formal-behavior-") as tmp:
            root = Path(tmp).resolve()
            (root / "verify.py").write_text(
                "import os, pathlib, sys\n"
                "with pathlib.Path(os.environ['FORMAL_RECEIPT']).open('a') as receipt:\n"
                "    receipt.write(os.environ['KANI_HOME'] + '\\n')\n"
                "raise SystemExit(int(os.environ['FORMAL_TEST_EXIT']))\n",
                encoding="utf-8",
            )
            receipt = root / "execution-receipt.txt"
            fixed_cache = root / "caller-selected-kani"
            environment = {
                **os.environ,
                "KANI_HOME": str(fixed_cache),
                "FORMAL_RECEIPT": str(receipt),
            }
            for command in commands:
                _verify_formal_task_behavior(command)
                for exit_code in (0, 37):
                    with self.subTest(command=command, exit_code=exit_code):
                        receipt.unlink(missing_ok=True)
                        result = subprocess.run(
                            ["bash", "-euo", "pipefail", "-c", command],
                            cwd=root,
                            env={**environment, "FORMAL_TEST_EXIT": str(exit_code)},
                            capture_output=True,
                            text=True,
                            timeout=8,
                        )
                        self.assertEqual(result.returncode, exit_code, result.stderr)
                        self.assertTrue(receipt.exists(), "zero executed verifiers")
                        self.assertEqual(
                            receipt.read_text(encoding="utf-8").splitlines(),
                            [str(fixed_cache)],
                            "zero/multiple executions or caller environment changed",
                        )

        for false_positive in (
            "exit 0\npython3 verify.py",
            "python3 verify.py\npython3 verify.py",
            "python3 verify.py || true",
        ):
            with self.subTest(false_positive=false_positive):
                with self.assertRaises(ValueError):
                    _verify_formal_task_behavior(false_positive)

    def test_formal_consumer_rejects_skip_duplicate_or_extra_effects(self) -> None:
        malformed = (
            "",
            "export KANI_HOME=/tmp/safe",
            "python3 -c 'print(1)'",
            "python3 verify.py\npython3 verify.py",
            "python3 verify.py\necho done",
            "echo launch\npython3 verify.py",
            "export FORMAL_SKIP_PROOFS=1\npython3 verify.py",
            "export KANI_HOME=/tmp/safe; true\npython3 verify.py",
            "export KANI_HOME=$(echo bad)\npython3 verify.py",
            "set -euo pipefail\npython3 verify.py | cat",
            "export KANI_HOME=/tmp/safe && false\npython3 verify.py",
        )
        for candidate in malformed:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    _verify_formal_task_behavior(candidate)

    def test_root_protected_ci_runs_formal_task_for_changed_proof_sources(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn(
            "from affected_owners import requires_core_formal_verification",
            workflow,
        )
        self.assertIn("formal=%s", workflow)
        self.assertIn("\"$GITHUB_OUTPUT\"", workflow)
        self.assertIn("if: steps.affected.outputs.formal == 'true'", workflow)
        self.assertIn("mise run formal:verify", workflow)
        self.assertIn("KANI_HOME:", workflow)
        self.assertIn("mise install", workflow)

    def test_selected_formal_verus_rustup_toolchain_is_provisioned(self) -> None:
        """Cold Linux CI must establish Verus's pinned rustup toolchain."""
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        step = workflow.split(
            "      - name: Verify changed core Formal source\n", 1
        )[1].split(
            "      - name: Runtime supply-chain policy\n", 1
        )[0]
        runtime = tomllib.loads(
            (ROOT / "services/runtime/mise.toml").read_text(encoding="utf-8")
        )
        version = runtime["tools"]["rust"]["version"]
        admission = f"rustup toolchain install {version} --profile minimal"
        self.assertIn(admission, step)
        self.assertLess(step.index(admission), step.index("mise run formal:verify"))
        self.assertIn("KANI_HOME:", step)

    def test_timeout_source_anchor_reader_rejects_changed_explicit_syntax(self) -> None:
        """Anchor observation rejects changed syntax without proving code semantics."""
        qualified = formal.qualified_timeout_adapter_fragment()
        self.assertIs(qualified["sourceAstAnchorsObserved"], True)
        self.assertIs(qualified["codeFragmentRefined"], False)
        self.assertEqual(qualified["sourceRefinementStanding"], "UNKNOWN")
        self.assertIs(qualified["runtimeRustRefined"], False)
        target = ROOT / "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
        source = target.read_text(encoding="utf-8")
        originals = {
            "default": (
                "self.gateway_grant.max_timeout_ms if timeout is None else timeout"
                if "self.gateway_grant.max_timeout_ms if timeout is None else timeout" in source
                else "return grant if requested is None else requested"
            ),
            "projection": 'gateway_args["timeoutMs"] = execution["timeoutMs"]',
            "guard": "timeout > self.gateway_grant.max_timeout_ms",
            "presence": 'if "timeoutMs" in call.arguments and (',
        }
        revisions = {
            "default": (
                "None if timeout is None else timeout"
                if originals["default"].startswith("self.gateway_grant")
                else "return None if requested is None else requested"
            ),
            "projection": 'gateway_args["timeoutMs"] = None',
            "guard": "timeout > 900_000",
            "presence": "if timeout is not None and (",
        }
        real_read = Path.read_text
        for name, original in originals.items():
            with self.subTest(semantic_mutation=name):
                self.assertIn(original, source)
                changed = source.replace(original, revisions[name], 1)

                def simulated_source_read(path, *args, **kwargs):
                    if path == target:
                        return changed
                    return real_read(path, *args, **kwargs)

                with patch.object(Path, "read_text", simulated_source_read):
                    with self.assertRaisesRegex(ValueError, "timeout|admission"):
                        formal.qualified_timeout_adapter_fragment()

    def test_partial_ast_source_anchors_must_not_promise_semantic_refinement(self) -> None:
        """A remaining pre-projection rebind keeps source refinement UNKNOWN."""
        baseline = formal.qualified_timeout_adapter_fragment()
        self.assertIs(baseline["sourceAstAnchorsObserved"], True)
        self.assertEqual(
            baseline["effectFrameObserved"],
            "exact_post_projection_return_and_immediate_gateway_dispatch",
        )
        self.assertIs(baseline["codeFragmentRefined"], False)
        self.assertEqual(baseline["sourceRefinementStanding"], "UNKNOWN")

        target = ROOT / "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
        source = target.read_text(encoding="utf-8")
        before = '        execution["timeoutMs"] = _forward_granted_timeout(\n'
        self.assertEqual(source.count(before), 1)
        mutant = source.replace(before, '        timeout = None\n' + before, 1)
        compile(mutant, str(target), "exec")

        actual_read = Path.read_text

        def read_with_mutant(path, *args, **kwargs):
            if path == target:
                return mutant
            return actual_read(path, *args, **kwargs)

        with patch.object(Path, "read_text", read_with_mutant):
            outcome = formal.qualified_timeout_adapter_fragment()
        self.assertIs(outcome["sourceAstAnchorsObserved"], True)
        self.assertIs(outcome["codeFragmentRefined"], False)
        self.assertEqual(outcome["sourceRefinementStanding"], "UNKNOWN")

    def test_timeout_source_observation_rejects_post_projection_effect_mutations(self) -> None:
        """Exact observed frame rejects caller/Gateway mutations before handoff."""
        target = ROOT / "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
        original = target.read_text(encoding="utf-8")
        variants = (
            (
                "caller-update",
                '        return (\n            "workspace.exec",',
                '        execution.update({"timeoutMs": self.gateway_grant.max_timeout_ms + 1})\n'
                '        return (\n            "workspace.exec",',
            ),
            (
                "caller-alias",
                '        return (\n            "workspace.exec",',
                '        alias = execution\n'
                '        alias.update({"timeoutMs": self.gateway_grant.max_timeout_ms + 1})\n'
                '        return (\n            "workspace.exec",',
            ),
            (
                "gateway-update",
                '        receipt = self._call("execution.submit", gateway_args)',
                '        gateway_args.update({"timeoutMs": 900000})\n'
                '        receipt = self._call("execution.submit", gateway_args)',
            ),
            (
                "gateway-alias",
                '        receipt = self._call("execution.submit", gateway_args)',
                '        alias = gateway_args\n'
                '        alias["timeoutMs"] = 900000\n'
                '        receipt = self._call("execution.submit", gateway_args)',
            ),
        )
        actual_read = Path.read_text
        for label, old, new in variants:
            with self.subTest(label=label):
                self.assertIn(old, original)
                mutant = original.replace(old, new, 1)
                compile(mutant, str(target), "exec")

                def read_with_mutant(path, *args, **kwargs):
                    if path == target:
                        return mutant
                    return actual_read(path, *args, **kwargs)

                with patch.object(Path, "read_text", read_with_mutant):
                    with self.assertRaisesRegex(ValueError, "timeout|frame|effect|projection"):
                        formal.qualified_timeout_adapter_fragment()

    def test_exact_git_source_readset_is_qualified(self) -> None:
        current = formal.qualified_source_cut()
        self.assertEqual(
            current["gitHead"],
            subprocess.check_output(
                ["git", "--no-replace-objects", "rev-parse", "HEAD^{commit}"],
                text=True, cwd=ROOT,
            ).strip(),
        )
        self.assertEqual(set(current["sourceBlobs"]), set(formal.SOURCE_FILES))
        # The source-scoped Formal proof now binds the actual Harness
        # execution adapter as well as ten existing proof/toolchain inputs.
        self.assertEqual(len(current["sourceBlobs"]), 11)
        for relative, oid in current["sourceBlobs"].items():
            self.assertEqual(
                oid,
                subprocess.check_output(
                    ["git", "--no-replace-objects", "rev-parse",
                     f"HEAD:{relative}"],
                    cwd=ROOT, text=True,
                ).strip(),
            )

    def test_formal_ci_selection_covers_every_declared_source_cut_input(self) -> None:
        # No parallel dependency registry: the existing proof producer owns
        # SOURCE_FILES and the existing Git selector must cover each input.
        from tools.repo.affected_owners import requires_core_formal_verification

        for source in formal.SOURCE_FILES:
            with self.subTest(source=source):
                self.assertTrue(requires_core_formal_verification((source,)))

    def test_formal_exact_source_cut_ignores_inherited_foreign_git_store(self) -> None:
        # Executed proof-input readset must not resolve a different Git repo
        # when invoked by an Agent with ambient GIT_DIR/object-store settings.
        with tempfile.TemporaryDirectory(prefix="ordivon-formal-two-repos-") as temp:
            root = Path(temp)
            real, foreign = root / "real", root / "foreign"
            for repo in (real, foreign):
                repo.mkdir()
                for args in (
                    ("init", "-q"),
                    ("config", "user.name", "Formal CDC"),
                    ("config", "user.email", "formal-env@example.invalid"),
                ):
                    subprocess.run(["git", "-C", str(repo), *args], check=True)
                (repo / "source.lean").write_text(
                    "def identity (n : Nat) := n\n", encoding="utf-8",
                )
                if repo == foreign:
                    (repo / "unrelated.txt").write_text(
                        "foreign commit identity\n", encoding="utf-8",
                    )
                subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "commit", "-qm", "source"], check=True
                )
            # The dangerous case is identical declared proof blobs under
            # different Git HEAD identities. A mismatching blob can fail via
            # hash validation without exercising the foreign-HEAD flaw.
            def git(repo: Path, *args: str) -> str:
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args], text=True,
                ).strip()

            self.assertNotEqual(git(real, "rev-parse", "HEAD"),
                                git(foreign, "rev-parse", "HEAD"))
            self.assertEqual(git(real, "rev-parse", "HEAD:source.lean"),
                             git(foreign, "rev-parse", "HEAD:source.lean"))
            with patch.object(formal, "REPO", real), patch.object(
                formal, "SOURCE_FILES", ("source.lean",)
            ):
                expected = formal.qualified_source_cut()
                for override in (
                    {"GIT_DIR": str(foreign / ".git")},
                    {"GIT_OBJECT_DIRECTORY": str(foreign / ".git" / "objects")},
                    {"GIT_ALTERNATE_OBJECT_DIRECTORIES":
                     str(foreign / ".git" / "objects")},
                ):
                    with self.subTest(override=tuple(override)):
                        with patch.dict(os.environ, override):
                            self.assertEqual(formal.qualified_source_cut(), expected)

    def test_formal_sourcecut_does_not_use_untrusted_path_git(self) -> None:
        """A PATH Git wrapper cannot manufacture a foreign HEAD for equal proof blobs."""
        with tempfile.TemporaryDirectory(prefix="ordivon-formal-git-path-") as temp:
            root = Path(temp)
            real, foreign, bin_dir = root / "real", root / "foreign", root / "bin"
            for repo in (real, foreign):
                repo.mkdir()
                for args in (
                    ("init", "-q"),
                    ("config", "user.name", "Formal PATH CDC"),
                    ("config", "user.email", "git-path@example.invalid"),
                ):
                    subprocess.run(["/usr/bin/git", "-C", str(repo), *args], check=True)
                (repo / "proof.lean").write_text("def same := true\n", encoding="utf-8")
                if repo == foreign:
                    (repo / "other.txt").write_text("different HEAD\n", encoding="utf-8")
                subprocess.run(["/usr/bin/git", "-C", str(repo), "add", "."], check=True)
                subprocess.run(["/usr/bin/git", "-C", str(repo), "commit", "-qm", "fixture"],
                               check=True)
            bin_dir.mkdir()
            wrapper = bin_dir / "git"
            wrapper.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "args = sys.argv[1:]\n"
                "if '-C' in args and any(x in args for x in ('rev-parse', 'ls-tree')):\n"
                "    args[args.index('-C') + 1] = os.environ['FORMAL_FOREIGN_ROOT']\n"
                "os.execv('/usr/bin/git', ['/usr/bin/git', *args])\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            with patch.object(formal, "REPO", real), patch.object(
                formal, "SOURCE_FILES", ("proof.lean",)
            ):
                expected = formal.qualified_source_cut()
                foreign_head = subprocess.check_output(
                    ["/usr/bin/git", "-C", str(foreign), "rev-parse", "HEAD"],
                    text=True,
                ).strip()
                self.assertNotEqual(expected["gitHead"], foreign_head)
                with patch.dict(os.environ, {
                    "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
                    "FORMAL_FOREIGN_ROOT": str(foreign),
                }):
                    actual = formal.qualified_source_cut()
                self.assertEqual(actual, expected, "foreign Git CLI reselected by PATH")

    def test_source_cut_rejects_modified_untracked_and_symlink_inputs(self) -> None:
        def git(cwd: Path, *args: str) -> str:
            return subprocess.check_output(
                ["git", "--no-replace-objects", *args],
                cwd=cwd, text=True, stderr=subprocess.PIPE,
            ).strip()

        with tempfile.TemporaryDirectory(prefix="ordivon-formal-source-") as temp:
            root = Path(temp)
            git(root, "init", "-q")
            git(root, "config", "user.name", "Formal Test")
            git(root, "config", "user.email", "formal-test@invalid.example")
            source = root / "source.lean"
            source.write_text("def identity (n : Nat) := n\n", encoding="utf-8")
            git(root, "add", "source.lean")
            git(root, "commit", "-qm", "immutable formal input")
            with patch.object(formal, "REPO", root), patch.object(
                formal, "SOURCE_FILES", ("source.lean",)
            ):
                evidence = formal.qualified_source_cut()
                self.assertEqual(set(evidence["sourceBlobs"]), {"source.lean"})
                source.write_text("def identity (n : Nat) := n + 1\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "differs from SourceCut"):
                    formal.qualified_source_cut()
                source.write_text("def identity (n : Nat) := n\n", encoding="utf-8")
                self.assertEqual(evidence, formal.qualified_source_cut())
                untracked = root / "new-proof.lean"
                untracked.write_text("def x := 1\n", encoding="utf-8")
                with patch.object(formal, "SOURCE_FILES", ("new-proof.lean",)):
                    with self.assertRaisesRegex(ValueError, "nonregular or untracked"):
                        formal.qualified_source_cut()
                source.unlink()
                source.symlink_to(untracked)
                with self.assertRaisesRegex(ValueError, "missing or nonregular"):
                    formal.qualified_source_cut()


if __name__ == "__main__":
    unittest.main()
