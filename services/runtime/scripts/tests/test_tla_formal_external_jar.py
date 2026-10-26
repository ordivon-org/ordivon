"""Cold-workspace contract tests for pinned TLA+ tools using the owner-native unittest runner.

No network or host-global installs. A fake Java process observes jar selection;
real TLC checking remains a separate formal-model verification obligation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tla-formal"
ENV_JAR = "ORDIVON_TLA_TOOLS_JAR"


class TlaFormalExternalJarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ordivon-tla-toolchain-")
        self.addCleanup(self.temp.cleanup)
        self.tmp = Path(self.temp.name)
        root = self.tmp / "runtime"
        scripts = root / "scripts"
        formal = root / "formal"
        scripts.mkdir(parents=True)
        formal.mkdir()
        self.script = scripts / "tla-formal"
        shutil.copyfile(SCRIPT, self.script)
        payload = b"tla-locked-test-carrier"
        self.external = self.tmp / "external tools.jar"
        self.external.write_bytes(payload)
        (formal / "toolchain.lock.json").write_text(
            json.dumps({
                "version": "fixture",
                "url": "https://invalid.example/never-fetch",
                "upstreamSha1": hashlib.sha1(payload).hexdigest(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "cacheRelativePath": "target/formal-tools/pinned.jar",
            }), encoding="utf-8",
        )
        (formal / "RuntimeDispatchR1.tla").write_text(
            "---- MODULE RuntimeDispatchR1 ----\n====", encoding="utf-8"
        )
        (formal / "RuntimeDispatchR1.cfg").write_text(
            "SPECIFICATION Spec\n", encoding="utf-8"
        )
        binary = self.tmp / "bin"
        binary.mkdir()
        self.java_log = self.tmp / "java-args.log"
        fake_java = binary / "java"
        fake_java.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$@" >> "$JAVA_ARGS_LOG"\n',
            encoding="utf-8",
        )
        fake_java.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": str(binary) + os.pathsep + os.environ["PATH"],
            "JAVA_ARGS_LOG": str(self.java_log),
        }
        self.env.pop(ENV_JAR, None)
        self.cache = root / "target/formal-tools/pinned.jar"

    def invoke(self, command="verify", jar=None, env=None):
        environ = dict(self.env if env is None else env)
        if jar is not None:
            environ[ENV_JAR] = str(jar)
        return subprocess.run(
            ["bash", str(self.script), command],
            env=environ, capture_output=True, text=True, timeout=15,
        )

    def test_pg_cutover_parity_distinguishes_content_from_revision(self):
        model = (
            SCRIPT.parent.parent / "formal/RuntimePgCutoverR1.tla"
        ).read_text(encoding="utf-8")
        cfg = (
            SCRIPT.parent.parent / "formal/RuntimePgCutoverR1.cfg"
        ).read_text(encoding="utf-8")
        runner = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("sqliteContent", model)
        self.assertIn("pgContent", model)
        self.assertIn("pgContent = sqliteContent", model)
        self.assertIn("VerifiedContentWasFrozen", model)
        self.assertIn("VerifiedContentWasFrozen", cfg)
        self.assertIn("TLC PostgreSQL content parity negative control PASS", runner)

    def test_windows_first_pg_order_needs_owner_receipt_and_falsifiers(self):
        model = (SCRIPT.parent.parent / "formal/RuntimeWindowsFirstPgR1.tla").read_text(
            encoding="utf-8"
        )
        cfg = (SCRIPT.parent.parent / "formal/RuntimeWindowsFirstPgR1.cfg").read_text(
            encoding="utf-8"
        )
        runner = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("WindowsBeforeLinuxPg", model)
        self.assertIn("WindowsBeforeLinuxPg", cfg)
        self.assertIn("windowsReceipt", model)
        self.assertIn(r'linux \in {"sqlite", "staged"}', model)
        self.assertIn("check_windows_first_pg_order", runner)
        self.assertIn("check_windows_first_pg_falsifiers", runner)
        self.assertIn("stale-Windows-receipt rollback rejected PASS", runner)
        self.assertIn("Linux-premature-promotion rejected PASS", runner)

    def test_external_digest_locked_jar_works_without_workspace_cache(self):
        self.assertFalse(self.cache.exists())
        result = self.invoke(jar=self.external)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertFalse(self.cache.exists())

    def test_external_check_invokes_java_using_exact_path(self):
        result = self.invoke(command="check", jar=self.external)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = self.java_log.read_text(encoding="utf-8")
        # Every invoked parser/model checker must bind the exact locked JAR.
        # New source-bound models add invocations: a hard-coded total such as
        # four silently turns a valid new verifier into an unrelated CI FAIL.
        args = observed.splitlines()
        modes = [arg for arg in args if arg in ("tla2sany.SANY", "tlc2.TLC")]
        classpaths = [
            args[index + 1]
            for index, arg in enumerate(args[:-1])
            if arg == "-cp"
        ]
        self.assertGreaterEqual(len(modes), 4)
        self.assertEqual(len(classpaths), len(modes))
        self.assertEqual(classpaths, [str(self.external)] * len(modes))
        self.assertGreaterEqual(modes.count("tla2sany.SANY"), 2)
        self.assertGreaterEqual(modes.count("tlc2.TLC"), 2)
        self.assertIn("RuntimeDispatchR1.tla", observed)
        self.assertIn("RuntimePgCutoverR1.tla", observed)
        self.assertIn("RuntimeWindowsFirstPgR1.tla", observed)
        self.assertIn("WorkspaceConsumerCloseR1.tla", observed)

    def test_scoped_dispatch_only_calls_pinned_tlc_and_sany(self):
        result = self.invoke(command="check-dispatch", jar=self.external)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = self.java_log.read_text(encoding="utf-8")
        self.assertEqual(observed.count("tla2sany.SANY"), 1)
        self.assertEqual(observed.count("tlc2.TLC"), 1)
        self.assertEqual(observed.count(str(self.external)), 2)
        self.assertIn("RuntimeDispatchR1.tla", observed)
        self.assertIn("RuntimeDispatchR1.cfg", observed)
        for unrelated in (
            "RuntimePgCutoverR1.tla",
            "RuntimeWindowsFirstPgR1.tla",
            "WorkspaceConsumerCloseR1.tla",
        ):
            self.assertNotIn(unrelated, observed)

    def test_falsifier_must_see_named_invariant_counterexample_not_just_java_failure(self):
        # A fake Java process returns success without a counterexample; the
        # formal Owner gate must reject it rather than count a mere process exit.
        (self.script.parent.parent / "formal/RuntimeDispatchR1.tla").write_text(
            "---- MODULE RuntimeDispatchR1 ----\n"
            "Next ==\n"
            "    \\/ AdmitExplicitRetry\n"
            "====\n", encoding="utf-8"
        )
        result = self.invoke(command="falsify", jar=self.external)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("counterexample", result.stderr.lower())
        self.assertIn("NoCompetingLiveAttempts", result.stderr)

    def test_falsifier_rejects_non_tlc_tool_failure_with_forged_violation_text(self):
        """A failing Java launcher printing invariant names is not a TLC counterexample."""
        shutil.copyfile(
            SCRIPT.parent.parent / "formal/RuntimeDispatchR1.tla",
            self.script.parent.parent / "formal/RuntimeDispatchR1.tla",
        )
        java = self.tmp / "bin/java"
        java.write_text(
            "#!/bin/sh\n"
            "echo 'Invariant NoCompetingLiveAttempts is violated'\n"
            "echo 'Invariant MatchingResultRequiredForTerminal is violated'\n"
            "exit 1\n",
            encoding="utf-8",
        )
        java.chmod(0o755)
        result = self.invoke(command="falsify", jar=self.external)
        self.assertNotEqual(
            result.returncode, 0,
            "a non-TLC launcher failure forged both named counterexamples",
        )
        self.assertIn("negative control FAILED", result.stderr)

    def test_falsifier_rejects_name_only_without_a_real_state_trace(self):
        """Even TLC's expected error status plus matching text cannot forge a trace."""
        shutil.copyfile(
            SCRIPT.parent.parent / "formal/RuntimeDispatchR1.tla",
            self.script.parent.parent / "formal/RuntimeDispatchR1.tla",
        )
        java = self.tmp / "bin/java"
        java.write_text(
            "#!/bin/sh\n"
            "echo 'Error: Invariant NoCompetingLiveAttempts is violated.'\n"
            "echo 'Error: Invariant MatchingResultRequiredForTerminal is violated.'\n"
            "exit 12\n",
            encoding="utf-8",
        )
        java.chmod(0o755)
        result = self.invoke(command="falsify", jar=self.external)
        self.assertNotEqual(
            result.returncode, 0, "an invariant label without a state trace was admitted"
        )
        self.assertIn("negative control FAILED", result.stderr)

    def test_digest_mismatch_fails_closed(self):
        bad = self.tmp / "tampered.jar"
        bad.write_bytes(self.external.read_bytes() + b"-changed")
        result = self.invoke(jar=bad)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            "digest" in result.stderr.lower() or "sha" in result.stderr.lower()
        )

    def test_relative_external_path_rejected(self):
        self.assertNotEqual(self.invoke(jar="relative.jar").returncode, 0)

    def test_empty_external_path_rejected(self):
        self.assertNotEqual(self.invoke(jar="").returncode, 0)

    def test_external_symlink_rejected(self):
        alias = self.tmp / "alias.jar"
        alias.symlink_to(self.external)
        self.assertNotEqual(self.invoke(jar=alias).returncode, 0)

    def test_default_local_cache_still_works(self):
        self.cache.parent.mkdir(parents=True)
        self.cache.write_bytes(self.external.read_bytes())
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_default_cache_fails_without_network(self):
        self.assertFalse(self.cache.exists())
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertIn("missing", result.stderr.lower())
        self.assertFalse(self.java_log.exists())

    def test_bad_external_override_never_falls_back_to_local_cache(self):
        self.cache.parent.mkdir(parents=True)
        self.cache.write_bytes(self.external.read_bytes())
        invalid = self.tmp / "wrong.jar"
        invalid.write_bytes(b"incorrect")
        result = self.invoke(jar=invalid)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("digest mismatch", result.stderr.lower())

    def test_external_override_does_not_redirect_bootstrap_target(self):
        fake_curl = Path(self.env["PATH"].split(os.pathsep)[0]) / "curl"
        fake_curl.write_text(
            '#!/bin/sh\n'
            'while [ "$#" -gt 0 ]; do\n'
            '  if [ "$1" = "-o" ]; then shift; cp "$BOOTSTRAP_FIXTURE" "$1"; exit $?; fi\n'
            '  shift\n'
            'done\n'
            'exit 2\n',
            encoding="utf-8",
        )
        fake_curl.chmod(0o755)
        original = self.external.read_bytes()
        env = dict(self.env)
        env["BOOTSTRAP_FIXTURE"] = str(self.external)
        env[ENV_JAR] = str(self.tmp / "other-external.jar")
        result = self.invoke(command="bootstrap", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cache.read_bytes(), original)
        self.assertEqual(self.external.read_bytes(), original)
        self.assertFalse(Path(env[ENV_JAR]).exists())


if __name__ == "__main__":
    unittest.main()
