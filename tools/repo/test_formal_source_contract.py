"""Ordivon core Formal source readset is admitted by native root CI.

This checks Git SourceCut and CLI wiring, NOT external theorem prover verdicts.
"""

from __future__ import annotations

import importlib.util
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
    if not commands or commands[-1] != "python3 verify.py":
        raise ValueError("Formal task must end with the native verifier call")
    if commands.count("python3 verify.py") != 1:
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
            "python3 verify.py\n"
        )
        _verify_formal_task_behavior("python3 verify.py")
        _verify_formal_task_behavior(peer_task)

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
