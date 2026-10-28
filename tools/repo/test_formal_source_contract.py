"""Ordivon core Formal source readset is admitted by native root CI.

This checks Git SourceCut and CLI wiring, NOT external theorem prover verdicts.
"""

from __future__ import annotations

import importlib.util
import os
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


def assert_verify_task_executes_exact_formal_entrypoint(command: str) -> None:
    """Check executed verifier behavior, not a brittle shell-script string.

    Root CI substitutes a disposable PATH shim; proof tools are not run.
    A verifier failure cannot be concealed by setup or trailing success.
    """
    with tempfile.TemporaryDirectory(prefix="ordivon-formal-command-") as tmp:
        directory = Path(tmp)
        fake = directory / "python3"
        fake.write_text(
            """#!/bin/sh
printf '%s\\n' "$@" >> "$FORMAL_INVOCATIONS"
printf '%s\\n' "$KANI_HOME" >> "$FORMAL_CACHE_OBSERVED"
exit "$FORMAL_FAKE_RESULT"
""",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        sentinel = str(directory / "caller-kani-cache")
        for returned in (0, 61):
            observations = directory / "calls"
            cache = directory / "cache"
            observations.write_text("")
            cache.write_text("")
            env = dict(os.environ)
            env.update({
                "PATH": str(directory) + os.pathsep + env.get("PATH", ""),
                "FORMAL_INVOCATIONS": str(observations),
                "FORMAL_CACHE_OBSERVED": str(cache),
                "FORMAL_FAKE_RESULT": str(returned),
                "KANI_HOME": sentinel,
            })
            proc = subprocess.run(
                ["bash", "-e", "-c", command], cwd=FORMAL, env=env,
                text=True, capture_output=True, timeout=10,
            )
            if observations.read_text().splitlines() != ["verify.py"]:
                raise AssertionError("formal task did not call exactly one verifier entrypoint")
            if cache.read_text().splitlines() != [sentinel]:
                raise AssertionError("formal task overwrote caller KANI_HOME")
            if (proc.returncode == 0) != (returned == 0):
                raise AssertionError("formal task swallowed verifier failure or failed success")


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
        assert_verify_task_executes_exact_formal_entrypoint(
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

    def test_formal_task_equivalence_accepts_safe_kani_cache_setup(self) -> None:
        assert_verify_task_executes_exact_formal_entrypoint(
            """# Kani cache preparation should not break the real verifier interface
export KANI_HOME="$KANI_HOME"
python3 verify.py"""
        )

    def test_formal_task_equivalence_rejects_false_success_or_wrong_tool(self) -> None:
        for script in (
            "echo python3 verify.py",
            "python3 wrong.py",
            "python3 verify.py --skip-assertions",
            "python3 verify.py || true",
            "python3 verify.py || exit 0",
        ):
            with self.subTest(command=script):
                with self.assertRaises(AssertionError):
                    assert_verify_task_executes_exact_formal_entrypoint(script)

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
