"""Test PostgreSQL physical-test admission through behavior, not source-file positions.

Rust unit tests and the disposable PG18 task own the actual Job, Attempt,
cancel, terminal, and replay correctness claims.  This Python suite verifies
that neither physical lane can run without its explicit isolated-test DSN.
"""

import os
import json
from pathlib import Path
import subprocess
import tomllib
import tempfile
import shlex
import shutil
import unittest


ROOT = Path(__file__).resolve().parents[2]
MISE = ROOT / "mise.toml"


class PgPhysicalVerificationContractTests(unittest.TestCase):
    def _assert_dsn_required(self, *, task: str, variable: str) -> None:
        with MISE.open("rb") as stream:
            command = tomllib.load(stream)["tasks"][task]["run"]

        env = dict(os.environ)
        env.pop(variable, None)
        # This is the real task's bash command, not an AST or a positional
        # source-file regex.  The missing DSN must stop BEFORE any Cargo/PG
        # process is started, regardless of future Rust file organization.
        result = subprocess.run(
            ["bash", "-c", command],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(variable, result.stderr)
        self.assertIn("required", result.stderr)
        self.assertNotIn("Compiling", result.stderr)
        self.assertNotIn("test result:", result.stdout)

    def _run_stub_lane(self, task: str, variable: str, inventory: str,
                       output: str, *, dsn: str = "fixture-only-no-database-contact",
                       exit_code: int = 0) -> subprocess.CompletedProcess[str]:
        """Exercise the real Owner task; Cargo stub cannot reach a database."""
        with MISE.open("rb") as stream:
            command = tomllib.load(stream)["tasks"][task]["run"]
        opposite = ("ORDIVON_PG_STAGE_TEST_DSN" if variable == "ORDIVON_PG_TEST_DSN"
                    else "ORDIVON_PG_TEST_DSN")
        with tempfile.TemporaryDirectory() as temp:
            cargo = Path(temp) / "cargo"
            binary = Path(temp) / "ordivon_runtime_core-fixture"
            artifact = json.dumps({
                "reason": "compiler-artifact",
                "target": {"name": "ordivon_runtime_core", "kind": ["lib"],
                           "src_path": str(ROOT / "crates/ordivon-runtime-core/src/lib.rs")},
                "profile": {"test": True},
                "features": ["postgres-registry-admission", "runtime-contract"],
                "executable": str(binary),
            })
            binary.write_text(
                '#!/bin/sh\n'
                f'[ -n "${variable}" ] && [ -z "${opposite}" ] || exit 97\n'
                'case " $* " in *" --list "*) '
                f'printf "%s\n" {shlex.quote(inventory)};; '
                f'*) printf "%s\n" {shlex.quote(output)}; exit {exit_code};; esac\n',
                encoding="utf-8",
            )
            binary.chmod(0o700)
            cargo.write_text(
                '#!/bin/sh\n'
                f'[ -z "${variable}" ] && [ -z "${opposite}" ] || exit 98\n'
                'case " $* " in *" --no-run "*) '
                f'printf "%s\n" {shlex.quote(artifact)};; *) exit 96;; esac\n',
                encoding="utf-8",
            )
            cargo.chmod(0o700)
            env = {**os.environ, "PATH": temp + os.pathsep + os.environ["PATH"],
                   "CARGO_TARGET_DIR": temp, variable: dsn, opposite: "must-not-reach-child"}
            return subprocess.run(["bash", "-c", command], cwd=ROOT, env=env,
                                  capture_output=True, text=True, timeout=15)

    def test_both_direct_lanes_require_nonempty_exact_executed_inventory(self) -> None:
        for lane, variable, name in (
            ("physical", "ORDIVON_PG_TEST_DSN", "pg18_fixture"),
            ("stage", "ORDIVON_PG_STAGE_TEST_DSN", "historical_pg_stage_is_not_an_admission_authority"),
        ):
            task = f"test:postgres-registry:{lane}"
            qualified = f"module::{name}"
            required = []
            if lane == "physical":
                trace = json.loads((ROOT / "formal/RuntimeDispatchR1.trace-r1.json").read_text())
                required = [
                    row["path"].split("/src/")[1][:-3].replace("/", "::") + "::" + row["symbol"]
                    for row in trace["pgNativeWitnesses"] if row["evidenceMode"] == "physical-opt-in"
                ]
            names = [*required, qualified]
            inventory = "\n".join(f"{case}: test" for case in names) + f"\n{len(names)} tests, 0 benchmarks"
            output = "\n".join(f"test {case} ... ok" for case in names) + f"\ntest result: ok. {len(names)} passed; 0 failed; 0 ignored;"
            for label, listed, observed, code in (
                ("positive", inventory, output, 0),
                ("empty", "0 tests, 0 benchmarks", output, 0),
                ("zero-executed", inventory, "test result: ok. 0 passed; 0 failed; 0 ignored;", 0),
                ("wrong-identity", inventory, output.replace("module::", "other::"), 0),
                ("duplicate", inventory, output + f"\ntest {qualified} ... ok", 0),
                ("native-failed", inventory, output, 101),
            ):
                with self.subTest(lane=lane, case=label):
                    result = self._run_stub_lane(task, variable, listed, observed, exit_code=code)
                    combined = result.stdout + result.stderr
                    if label == "positive":
                        self.assertEqual(result.returncode, 0, combined)
                        self.assertIn(f"{lane.upper()}_PG18_PASS={len(names)}/{len(names)}", combined)
                        if lane == "physical":
                            if "PG_SOURCE_CUT_UNQUALIFIED=1" in result.stdout:
                                self.assertIn("PG_FORMAL_CONDITIONAL_WITNESSES_EXECUTED_UNQUALIFIED_SOURCE=", result.stdout)
                                self.assertNotIn("PG_FORMAL_CONDITIONAL_WITNESSES_PASS=", result.stdout)
                            else:
                                self.assertIn("PG_SOURCE_CUT_OBSERVED=", result.stdout)
                                self.assertIn("PG_FORMAL_CONDITIONAL_WITNESSES_PASS=", result.stdout)
                    else:
                        self.assertNotEqual(result.returncode, 0, combined)
                        self.assertNotIn("_PG18_PASS=", combined)
                        if label == "empty":
                            self.assertIn("inventory", result.stderr.lower())
            if required:
                with self.subTest(lane=lane, case="missing-required-but-green"):
                    remaining = names[1:]
                    listed = "\n".join(f"{case}: test" for case in remaining)
                    observed = "\n".join(f"test {case} ... ok" for case in remaining) + f"\ntest result: ok. {len(remaining)} passed; 0 failed; 0 ignored;"
                    result = self._run_stub_lane(task, variable, listed, observed)
                    self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertNotIn("PHYSICAL_PG18_PASS=", result.stdout)
            with self.subTest(lane=lane, case="blank-dsn"):
                result = self._run_stub_lane(task, variable, inventory, output, dsn="  ")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(variable, result.stderr)

    def test_stage_inventory_and_execution_use_one_compiler_selected_binary(self):
        """The real task must not ask Cargo to rebuild after listing."""
        with MISE.open("rb") as stream:
            command = tomllib.load(stream)["tasks"]["test:postgres-registry:stage"]["run"]
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            binary = temp / "ordivon_runtime_core-fixture"
            cargo = temp / "cargo"
            calls = temp / "cargo-calls"
            identity = "fixture::historical_pg_stage_is_not_an_admission_authority"
            artifact = json.dumps({
                "reason": "compiler-artifact",
                "target": {"name": "ordivon_runtime_core", "kind": ["lib"],
                           "src_path": str(ROOT / "crates/ordivon-runtime-core/src/lib.rs")},
                "profile": {"test": True},
                "features": ["postgres-registry-admission", "runtime-contract"],
                "executable": str(binary),
            })
            listing = f"{identity}: test"
            result = f"test {identity} ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored;"
            binary.write_text(
                "#!/bin/sh\n"
                '[ -n "$ORDIVON_PG_STAGE_TEST_DSN" ] && [ -z "$ORDIVON_PG_TEST_DSN" ] || exit 97\n'
                'case " $* " in *" --list "*) '
                f'printf "%s\n" {shlex.quote(listing)};; '
                f'*) printf "%s\n" {shlex.quote(result)};; esac\n'
            )
            binary.chmod(0o700)
            cargo.write_text(
                "#!/bin/sh\n"
                f'echo call >> {shlex.quote(str(calls))}\n'
                'case " $* " in *" --no-run "*) '
                '[ -z "$ORDIVON_PG_STAGE_TEST_DSN" ] && [ -z "$ORDIVON_PG_TEST_DSN" ] || exit 98; '
                f'printf "%s\n" {shlex.quote(artifact)};; '
                # Old two-Cargo implementation gets a green result despite
                # never selecting a single build artifact.
                f'*" --list "*) printf "%s\n" {shlex.quote(listing)};; '
                f'*) printf "%s\n" {shlex.quote(result)};; esac\n'
            )
            cargo.chmod(0o700)
            env = {**os.environ, "PATH": raw + os.pathsep + os.environ["PATH"],
                   "CARGO_TARGET_DIR": raw, "ORDIVON_PG_STAGE_TEST_DSN": "fixture",
                   "ORDIVON_PG_TEST_DSN": "must-not-reach-child"}
            observed = subprocess.run(["bash", "-c", command], cwd=ROOT, env=env,
                                      capture_output=True, text=True, timeout=15)
            self.assertEqual(observed.returncode, 0, observed.stdout + observed.stderr)
            self.assertEqual(calls.read_text().splitlines(), ["call"])
            # An on-disk executable change during listing cannot qualify.
            binary.write_text(binary.read_text().replace(
                'case " $* " in *" --list "*) ',
                'case " $* " in *" --list "*) echo "# drift" >> "$0"; ',
            ))
            changed = subprocess.run(["bash", "-c", command], cwd=ROOT, env=env,
                                     capture_output=True, text=True, timeout=15)
            self.assertNotEqual(changed.returncode, 0, changed.stdout + changed.stderr)
            self.assertNotIn("STAGE_PG18_PASS=", changed.stdout)
            self.assertIn("artifact", changed.stderr.lower())

    def test_source_observation_is_exact_and_distinguishes_local_execution(self):
        """Run the real stage task against a disposable Git checkout and Cargo stub.

        This challenges source attribution, not database behavior or rustc.
        """
        with MISE.open("rb") as stream:
            command = tomllib.load(stream)["tasks"]["test:postgres-registry:stage"]["run"]
        with tempfile.TemporaryDirectory() as raw:
            temp = Path(raw)
            repo = temp / "repo"
            runtime = repo / "services/runtime"
            scripts = runtime / "scripts"
            scripts.mkdir(parents=True)
            for name in ("pg_disposable_physical.py", "verify_formal_trace.py"):
                shutil.copyfile(ROOT / "scripts" / name, scripts / name)
            source = runtime / "crates/ordivon-runtime-core/src/lib.rs"
            source.parent.mkdir(parents=True)
            source.write_text("// original\n")
            git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args], env=git_env, text=True,
                    stderr=subprocess.PIPE,
                ).strip()

            git("init", "-q")
            git("add", ".")
            git("-c", "user.name=fixture", "-c", "user.email=fixture@example.test",
                "commit", "-qm", "exact cut")
            cut = git("rev-parse", "HEAD")

            cargo = temp / "cargo"
            binary = temp / "ordivon_runtime_core-fixture"
            identity = "fixture::historical_pg_stage_is_not_an_admission_authority"
            artifact = json.dumps({
                "reason": "compiler-artifact",
                "target": {"name": "ordivon_runtime_core", "kind": ["lib"], "src_path": str(source)},
                "profile": {"test": True},
                "features": ["postgres-registry-admission", "runtime-contract"],
                "executable": str(binary),
            })
            # Foreign Git selectors must not reach either native subprocess.
            guard = ('[ -z "${GIT_DIR+x}" ] && [ -z "${GIT_WORK_TREE+x}" ] '
                     '&& [ -z "${GIT_INDEX_FILE+x}" ] || exit 99\n')
            cargo.write_text('#!/bin/sh\n' + guard + f'printf "%s\n" {shlex.quote(artifact)}\n')
            cargo.chmod(0o700)
            binary.write_text(
                '#!/bin/sh\n' + guard +
                'case " $* " in *" --list "*) '
                'if [ "${MUTATE_SOURCE:-0}" = 1 ]; then '
                f'echo "// changed while listing" >> {shlex.quote(str(source))}; fi; '
                f'printf "%s\n" {shlex.quote(identity + ": test")};; '
                f'*) printf "%s\n" {shlex.quote("test " + identity + " ... ok")}; '
                'printf "%s\n" "test result: ok. 1 passed; 0 failed; 0 ignored;";; esac\n'
            )
            binary.chmod(0o700)
            env = {**git_env, "PATH": raw + os.pathsep + os.environ["PATH"],
                   "CARGO_TARGET_DIR": raw, "ORDIVON_PG_STAGE_TEST_DSN": "fixture",
                   "GIT_DIR": str(temp / "foreign"), "GIT_WORK_TREE": str(temp / "foreign"),
                   "GIT_INDEX_FILE": str(temp / "foreign-index"), "PYTHONDONTWRITEBYTECODE": "1"}

            def invoke(**extra):
                return subprocess.run(["bash", "-c", command], cwd=runtime, env={**env, **extra},
                                      capture_output=True, text=True, timeout=15)

            clean = invoke()
            self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
            self.assertIn(f"PG_SOURCE_CUT_OBSERVED={cut}", clean.stdout)
            self.assertIn("STAGE_PG18_PASS=1/1", clean.stdout)

            drift = invoke(MUTATE_SOURCE="1")
            self.assertNotEqual(drift.returncode, 0, drift.stdout + drift.stderr)
            self.assertNotIn("STAGE_PG18_PASS=", drift.stdout)
            self.assertNotIn("PG_SOURCE_CUT_OBSERVED=", drift.stdout)
            self.assertIn("source cut changed", drift.stderr)

            local = invoke()
            self.assertEqual(local.returncode, 0, local.stdout + local.stderr)
            self.assertIn("STAGE_PG18_PASS=1/1", local.stdout)
            self.assertIn("PG_SOURCE_CUT_UNQUALIFIED=1", local.stdout)
            self.assertNotIn("PG_SOURCE_CUT_OBSERVED=", local.stdout)

            git("update-index", "--assume-unchanged",
                "services/runtime/crates/ordivon-runtime-core/src/lib.rs")
            self.assertEqual(git("status", "--porcelain"), "")
            hidden = invoke()
            self.assertEqual(hidden.returncode, 0, hidden.stdout + hidden.stderr)
            self.assertIn("PG_SOURCE_CUT_UNQUALIFIED=1", hidden.stdout)
            self.assertNotIn("PG_SOURCE_CUT_OBSERVED=", hidden.stdout)

    def test_fresh_physical_lane_cannot_run_without_test_dsn(self) -> None:
        self._assert_dsn_required(
            task="test:postgres-registry:physical",
            variable="ORDIVON_PG_TEST_DSN",
        )

    def test_historical_stage_lane_cannot_run_without_stage_dsn(self) -> None:
        self._assert_dsn_required(
            task="test:postgres-registry:stage",
            variable="ORDIVON_PG_STAGE_TEST_DSN",
        )


if __name__ == "__main__":
    unittest.main()
