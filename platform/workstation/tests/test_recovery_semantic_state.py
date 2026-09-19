from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("backup_semantic_state", ROOT / "recovery" / "backup_semantic_state.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SemanticBackupGitAuthorityTests(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> str:
        proc = subprocess.run(
            ["/usr/bin/git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout.strip()

    def test_dirty_worktree_does_not_block_committed_ref_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo = root / "repo"
            repo.mkdir()
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.email", "workstation-test@example.invalid")
            self._git(repo, "config", "user.name", "Workstation Test")
            (repo / "tracked.txt").write_text("committed\n")
            self._git(repo, "add", "tracked.txt")
            self._git(repo, "commit", "-q", "-m", "seed")
            head = self._git(repo, "rev-parse", "HEAD")

            # Legitimate owner continuity remains uncommitted. That does not change
            # committed Git ref authority and therefore must not block its backup.
            (repo / "tracked.txt").write_text("uncommitted owner work\n")
            (repo / "untracked.txt").write_text("also uncommitted\n")

            target = root / "repo.bundle"
            record = MODULE.create_git_bundle(repo, target)

            self.assertFalse(record["clean"])
            self.assertEqual(record["head"], head)
            self.assertTrue(record["status"])
            self.assertGreater(record["bundleBytes"], 0)
            self.assertGreaterEqual(record["bundleRefs"], 1)
            self.assertEqual(MODULE.sha256_file(target), record["bundleSha256"])

    def test_git_ref_digest_is_independent_of_worktree_dirtiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw) / "repo"
            repo.mkdir()
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.email", "workstation-test@example.invalid")
            self._git(repo, "config", "user.name", "Workstation Test")
            (repo / "tracked.txt").write_text("committed\n")
            self._git(repo, "add", "tracked.txt")
            self._git(repo, "commit", "-q", "-m", "seed")

            clean = MODULE.git_record(repo)
            (repo / "tracked.txt").write_text("dirty\n")
            dirty = MODULE.git_record(repo)

            self.assertTrue(clean["clean"])
            self.assertFalse(dirty["clean"])
            self.assertEqual(clean["head"], dirty["head"])
            self.assertEqual(clean["refsDigest"], dirty["refsDigest"])

    def test_semantic_retention_ignores_random_staging_path_identity(self) -> None:
        command = MODULE.semantic_retention_command()
        self.assertIn("--group-by", command)
        group_index = command.index("--group-by")
        self.assertEqual(command[group_index + 1], "host,tags")
        keep_index = command.index("--keep-last")
        self.assertEqual(command[keep_index + 1], str(MODULE.REC["retain_semantic_snapshots"]))
        self.assertIn("--prune", command)

    def test_existing_repository_unlocks_stale_locks_before_config_probe(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repository = root / "semantic"
            repository.mkdir()
            (repository / "config").write_bytes(b"restic-config")
            password = root / "password"
            password.write_text("secret\n")
            calls: list[list[str]] = []

            def fake_checked(args, *, env=None, timeout=60):
                calls.append(list(args))
                return ""

            with mock.patch.dict(
                MODULE.REC,
                {
                    "semantic_repository": str(repository),
                    "restic_password_file": str(password),
                },
                clear=False,
            ), mock.patch.object(MODULE, "require_mount"), mock.patch.object(
                MODULE, "checked", side_effect=fake_checked
            ):
                MODULE.ensure_repository({})

            self.assertEqual(calls[0], MODULE.restic_command("unlock"))
            self.assertEqual(calls[1], MODULE.restic_command("cat", "config"))
            self.assertNotIn("--remove-all", calls[0])

    def test_semantic_staging_parent_is_private_contract_selected_node_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw) / "semantic-stage"
            with mock.patch.dict(MODULE.REC, {"semantic_staging_parent": str(parent)}, clear=False):
                observed = MODULE.semantic_staging_parent()
            self.assertEqual(observed, parent)
            self.assertTrue(parent.is_dir())
            self.assertEqual(parent.stat().st_mode & 0o777, 0o700)

    def test_node_incident_history_has_narrow_semantic_recovery_custody(self) -> None:
        direct = set(MODULE.REC["semantic_direct_paths"])
        self.assertIn("/root/.local/state/ordivon-workstation/node-snapshot-baseline.json", direct)
        self.assertIn("/root/.local/state/ordivon-workstation/node-generation-history", direct)
        self.assertIn("/root/.local/state/ordivon-workstation/node-incidents", direct)
        self.assertNotIn("/root/.local/state/ordivon-workstation", direct)

    def test_direct_path_witness_selects_exact_bounded_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "state"
            root.mkdir()
            (root / "large.bin").write_bytes(b"x" * (MODULE.DIRECT_WITNESS_MAX_BYTES + 1))
            nested = root / "a"
            nested.mkdir()
            witness_file = nested / "proof.json"
            witness_file.write_bytes(b'{"proof":1}\n')

            witness = MODULE.select_direct_path_witness(root)

            self.assertEqual(witness["root"], str(root))
            self.assertEqual(witness["witnessPath"], str(witness_file))
            self.assertEqual(witness["bytes"], witness_file.stat().st_size)
            self.assertEqual(witness["sha256"], MODULE.sha256_file(witness_file))
            self.assertEqual(witness["kind"], "directory-file")

    def test_snapshot_witness_verification_requires_exact_readback_bytes(self) -> None:
        proof = b"proof\n"
        witness = {
            "root": "/state",
            "witnessPath": "/state/proof.json",
            "bytes": len(proof),
            "sha256": __import__("hashlib").sha256(proof).hexdigest(),
            "kind": "directory-file",
        }
        with mock.patch.object(MODULE, "checked_bytes", return_value=proof) as dumped:
            verified = MODULE.verify_snapshot_witness({}, "snapshot-1", witness)
        self.assertEqual(verified["witnessPath"], witness["witnessPath"])
        self.assertEqual(verified["bytes"], len(proof))
        self.assertTrue(verified["digestMatches"])
        dumped.assert_called_once()

        with mock.patch.object(MODULE, "checked_bytes", return_value=b"wrong\n"):
            with self.assertRaisesRegex(RuntimeError, "direct-path witness readback mismatch"):
                MODULE.verify_snapshot_witness({}, "snapshot-1", witness)

    def test_restore_test_separates_declared_direct_roots_from_verified_readbacks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temp_root = Path(raw)
            witnesses = [
                {
                    "root": path,
                    "witnessPath": path + "/proof.json",
                    "bytes": 1,
                    "sha256": "x" * 64,
                    "kind": "directory-file",
                }
                for path in MODULE.REC["semantic_direct_paths"]
            ]
            manifest = {"git": [], "sqlite": [], "directWitnesses": witnesses}

            def fake_checked(args, *, env=None, timeout=60):
                self.assertIn("restore", args)
                target = Path(args[args.index("--target") + 1])
                restored = target / "semantic-recovery"
                restored.mkdir(parents=True)
                (restored / "manifest.json").write_text(__import__("json").dumps(manifest))
                return ""

            metadata = {
                "paths": ["/tmp/stage/semantic-recovery", *MODULE.REC["semantic_direct_paths"]]
            }
            with mock.patch.object(MODULE, "restic_env", return_value={}), \
                 mock.patch.object(MODULE, "ensure_repository"), \
                 mock.patch.object(MODULE, "snapshot_metadata", return_value=metadata), \
                 mock.patch.object(MODULE, "checked", side_effect=fake_checked), \
                 mock.patch.object(MODULE, "verify_snapshot_witness", return_value={"digestMatches": True}) as verify, \
                 mock.patch.dict(MODULE.REC, {"semantic_receipt": str(temp_root / "absent-receipt.json")}, clear=False):
                result = MODULE.restore_test("snapshot-1")

            self.assertEqual(result["directRootsDeclared"], len(witnesses))
            self.assertEqual(result["directWitnessesVerified"], len(witnesses))
            self.assertNotIn("directPathsVerified", result)
            self.assertEqual(verify.call_count, len(witnesses))

    def test_operation_lock_serializes_apply_check_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            lock_path = str(Path(raw) / "semantic.lock")
            with MODULE.OperationLock("apply", lock_path):
                with self.assertRaises(MODULE.RecoveryOperationBusy) as caught:
                    with MODULE.OperationLock("check", lock_path):
                        pass
            self.assertEqual(caught.exception.operation, "check")
            self.assertEqual(caught.exception.holder["operation"], "apply")
            self.assertEqual(caught.exception.holder["pid"], __import__("os").getpid())

    def test_apply_contention_is_visible_deferred_without_claiming_effect(self) -> None:
        busy = MODULE.RecoveryOperationBusy("apply", {"pid": 123, "operation": "restore-test"})
        with mock.patch.object(MODULE, "apply", side_effect=busy), \
             mock.patch.object(MODULE, "write_attempt") as write_attempt, \
             mock.patch.object(MODULE.os.sys, "argv", ["backup_semantic_state.py", "--apply"]), \
             mock.patch("builtins.print") as output:
            rc = MODULE.main()
        self.assertEqual(rc, 0)
        attempt = write_attempt.call_args.args[0]
        self.assertEqual(attempt["status"], "deferred")
        self.assertFalse(attempt["effectAttempted"])
        self.assertEqual(attempt["reason"], "semantic-recovery-operation-busy")
        self.assertEqual(attempt["holder"]["operation"], "restore-test")
        self.assertTrue(output.called)

    def test_read_only_contention_does_not_mutate_backup_attempt_standing(self) -> None:
        busy = MODULE.RecoveryOperationBusy("check", {"pid": 456, "operation": "apply"})
        with mock.patch.object(MODULE, "repository_check", side_effect=busy), \
             mock.patch.object(MODULE, "write_attempt") as write_attempt, \
             mock.patch.object(MODULE.os.sys, "argv", ["backup_semantic_state.py", "--check"]), \
             mock.patch("builtins.print"):
            rc = MODULE.main()
        self.assertEqual(rc, 0)
        write_attempt.assert_not_called()



if __name__ == "__main__":
    unittest.main()
