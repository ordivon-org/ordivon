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


def _validate_native_formal_task(run: str) -> None:
    """Check a bounded executable interface, not a frozen mise implementation."""
    commands = [
        line.strip() for line in run.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not commands or commands[-1] != "python3 verify.py":
        raise ValueError("Formal task must invoke the existing verify.py entrypoint")
    setup = commands[:-1]
    if len(setup) > 1:
        raise ValueError("Formal task has unexpected setup commands")
    if setup:
        step = setup[0]
        if not step.startswith("export KANI_HOME="):
            raise ValueError("Formal task may only prepare the Kani cache")
        # Shell command injection and unrelated side effects are not part of
        # this narrow task interface. Dynamic tests below check the value
        # passed to the real shell, not the exact export syntax.
        if any(token in step for token in (";", "&&", "||", "|", "`", "$(")):
            raise ValueError("Formal Kani cache setup contains shell side effects")
    if commands.count("python3 verify.py") != 1:
        raise ValueError("Formal task invokes verifier more than once")


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
        task_run = formal_tasks["tasks"]["verify"]["run"]
        _validate_native_formal_task(task_run)
        # Executable composition check: use a PATH-shadowed python3 recorder
        # to test only routing and environment, never pretend the full
        # Lean/SMT/Kani proof suite ran.
        with tempfile.TemporaryDirectory(prefix="formal-cli-contract-") as td:
            folder = Path(td)
            shim = folder / "python3"
            shim.write_text(
                '#!/bin/sh\n'
                'printf "%s\\n" "$#" "$1" "${KANI_HOME-UNSET}" >> "$FORMAL_TASK_LOG"\n',
                encoding="utf-8",
            )
            shim.chmod(0o755)
            out = folder / "observed"
            for override in (None, str(folder / "caller-owned-kani")):
                out.write_text("", encoding="utf-8")
                env = dict(os.environ)
                env.update({
                    "HOME": str(folder),
                    "FORMAL_TASK_LOG": str(out),
                    "PATH": str(folder) + os.pathsep + os.environ.get("PATH", ""),
                })
                env.pop("KANI_HOME", None)
                if override is not None:
                    env["KANI_HOME"] = override
                subprocess.run(
                    ["bash", "-e", "-c", task_run], cwd=FORMAL, env=env,
                    check=True, capture_output=True, text=True, timeout=12,
                )
                fields = out.read_text(encoding="utf-8").splitlines()
                self.assertEqual(fields[:2], ["1", "verify.py"])
                self.assertEqual(len(fields), 3, "verifier executed more than once")
                if override is not None:
                    self.assertEqual(fields[2], override)
                elif "export KANI_HOME=" in task_run:
                    self.assertEqual(fields[2], str(folder / ".cache/ordivon/kani"))
                else:
                    self.assertEqual(fields[2], "UNSET")
        ci_script = root["tasks"]["repo:ci"]["run"]
        self.assertIn(
            "python3 -m unittest tools/repo/test_formal_source_contract.py",
            ci_script,
        )
        # Repo CI performs a bounded source admission, not the entire
        # opt-in toolchain: never fake Lean/Z3/Kani proof success.
        self.assertNotIn("mise run formal:verify", ci_script)

    def test_formal_task_rejects_incorrect_or_side_effecting_wrappers(self) -> None:
        for script in (
            "python3 random_verifier.py",
            "python3 verify.py\npython3 verify.py",
            "export KANI_HOME=/tmp/x; rm -rf /tmp/y\npython3 verify.py",
            "export PATH=/tmp/untrusted\npython3 verify.py",
        ):
            with self.subTest(script=script), self.assertRaises(ValueError):
                _validate_native_formal_task(script)

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
