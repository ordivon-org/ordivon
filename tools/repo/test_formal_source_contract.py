"""Ordivon core Formal source readset is admitted by native root CI.

This checks Git SourceCut and CLI wiring, NOT external theorem prover verdicts.
"""

from __future__ import annotations

import importlib.util
import re
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


class FormalSourceConsumerContractTests(unittest.TestCase):
    def _assert_native_formal_task_calls_original_verifier(self, script: str) -> None:
        # Bound allowed setup to declarative environment preparation, not
        # arbitrary shell commands or a different formal checker. This tests
        # the consumer contract rather than the incidental TOML run string.
        commands = [
            line.strip() for line in script.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(commands)
        self.assertEqual(commands[-1], "python3 verify.py")
        self.assertEqual(commands.count("python3 verify.py"), 1)
        for command in commands[:-1]:
            self.assertTrue(
                command == "set -euo pipefail"
                or re.fullmatch(r'export KANI_HOME="[A-Za-z0-9_/${}:.~+-]+"', command),
                f"unapproved pre-verifier shell command: {command!r}",
            )

    def test_no_extra_effect_or_false_verifier_after_environment_setup(self) -> None:
        for script in (
            "python3 verify.py\npython3 unapproved.py",
            "python3 other.py",
            "echo skip\npython3 verify.py",
            'export KANI_HOME="$(touch /tmp/unapproved)"\npython3 verify.py',
            "python3 verify.py; true",
            "python3 verify.py\npython3 verify.py",
        ):
            with self.subTest(script=script), self.assertRaises(AssertionError):
                self._assert_native_formal_task_calls_original_verifier(script)

    def test_native_formal_cli_is_reachable_from_root_mise(self) -> None:
        root = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        formal_tasks = tomllib.loads(
            (FORMAL / "mise.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            root["tasks"]["formal:verify"]["run"],
            "cd tools/formal && mise run verify",
        )
        self._assert_native_formal_task_calls_original_verifier(
            formal_tasks["tasks"]["verify"]["run"]
        )
        ci_script = root["tasks"]["repo:ci"]["run"]
        self.assertIn(
            "python3 -m unittest tools/repo/test_formal_source_contract.py",
            ci_script,
        )
        # Repo CI performs a bounded source admission, not the entire
        # opt-in toolchain: never fake Lean/Z3/Kani proof success.
        self.assertNotIn("mise run formal:verify", ci_script)

    def test_peer_kani_environment_prelude_preserves_real_formal_consumer(self) -> None:
        # Peer PR #1082 adds a correct Kani cache environment prelude. It may
        # not remove or replace the native proof checker selected by root CI.
        peer_prelude = (
            "# Kani cache is deliberately separate from the shared home\n"
            'export KANI_HOME="${KANI_HOME:-${HOME}/.cache/ordivon/kani}"\n'
            "python3 verify.py\n"
        )
        original = Path.read_text
        child_path = FORMAL / "mise.toml"

        def compatible_formal_source(path: Path, *args, **kwargs) -> str:
            text = original(path, *args, **kwargs)
            if path == child_path:
                old = 'run = "python3 verify.py"'
                self.assertEqual(text.count(old), 1)
                return text.replace(
                    old,
                    'run = """\n' + peer_prelude + '"""',
                    1,
                )
            return text

        with patch.object(Path, "read_text", autospec=True,
                          side_effect=compatible_formal_source):
            self.test_native_formal_cli_is_reachable_from_root_mise()

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
        self.assertEqual(len(current["sourceBlobs"]), 10)
        for relative, oid in current["sourceBlobs"].items():
            self.assertEqual(
                oid,
                subprocess.check_output(
                    ["git", "--no-replace-objects", "rev-parse",
                     f"HEAD:{relative}"],
                    cwd=ROOT, text=True,
                ).strip(),
            )

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
