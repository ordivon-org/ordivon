from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ordivon_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


backup = load_script("backup")
restore = load_script("restore")
mcp_e2e = load_script("mcp_e2e")


class OperationalScriptTests(unittest.TestCase):
    def test_backup_restore_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            control = root / "control"
            control.mkdir()
            database = control / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL)")
                connection.execute("INSERT INTO jobs VALUES ('job-1', 'succeeded')")
                connection.commit()
            (control / "note.txt").write_text("control-data\n", encoding="utf-8")
            snapshot = root / "snapshot"
            restored = root / "restored"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/backup.py",
                    "--database",
                    str(database),
                    "--control-root",
                    str(control),
                    "--destination",
                    str(snapshot),
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "scripts/restore.py",
                    "--snapshot",
                    str(snapshot),
                    "--destination",
                    str(restored),
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            with closing(sqlite3.connect(restored / "registry.sqlite3")) as connection:
                self.assertEqual(connection.execute("SELECT * FROM jobs").fetchall(), [("job-1", "succeeded")])
            self.assertEqual((restored / "control/note.txt").read_text(encoding="utf-8"), "control-data\n")

    def test_reclaim_accepts_future_compatible_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "registry.sqlite3"
            runtime = root / "runtime"
            (runtime / "workspace-records").mkdir(parents=True)
            (runtime / "workspaces").mkdir(parents=True)
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE schema_migrations(version INTEGER);
                    INSERT INTO schema_migrations VALUES (999);
                    CREATE TABLE jobs(job_id TEXT,workspace_id TEXT,resolution TEXT,created_at_ms INTEGER);
                    CREATE TABLE attempts(attempt_id TEXT,job_id TEXT,state TEXT);
                    CREATE TABLE concurrency_reservations(attempt_id TEXT,state TEXT);
                    """
                )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-reclaim",
                    "inspect",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                ],
                cwd=REPO,
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["registryVersion"], 999)
            self.assertEqual(report["releaseTool"], "workspace.close")
            self.assertEqual(report["summary"]["counts"], {})

    def test_reclaim_rejects_missing_registry_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = root / "registry.sqlite3"
            runtime = root / "runtime"
            runtime.mkdir()
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE schema_migrations(version INTEGER);
                    INSERT INTO schema_migrations VALUES (4);
                    CREATE TABLE jobs(job_id TEXT,workspace_id TEXT,created_at_ms INTEGER);
                    CREATE TABLE attempts(attempt_id TEXT,job_id TEXT,state TEXT);
                    CREATE TABLE concurrency_reservations(attempt_id TEXT,state TEXT);
                    """
                )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/ordivon-runtime-reclaim",
                    "inspect",
                    "--database",
                    str(database),
                    "--runtime-store-root",
                    str(runtime),
                ],
                cwd=REPO,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("column:jobs.resolution", result.stderr)

    def test_mcp_e2e_preserves_fd_backed_cargo_target_for_child_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fd = os.open(temporary, os.O_RDONLY | os.O_DIRECTORY)
            previous = os.environ.get("CARGO_TARGET_DIR")
            try:
                os.environ["CARGO_TARGET_DIR"] = f"/proc/self/fd/{fd}"
                output = mcp_e2e.command(
                    sys.executable,
                    "-c",
                    "import os; from pathlib import Path; print(Path(os.environ['CARGO_TARGET_DIR']).is_dir())",
                    cwd=REPO,
                )
                self.assertEqual(output, "True")
            finally:
                if previous is None:
                    os.environ.pop("CARGO_TARGET_DIR", None)
                else:
                    os.environ["CARGO_TARGET_DIR"] = previous
                os.close(fd)

    def test_mcp_e2e_rejects_stale_fd_backed_cargo_target(self) -> None:
        previous = os.environ.get("CARGO_TARGET_DIR")
        try:
            os.environ["CARGO_TARGET_DIR"] = "/proc/self/fd/999999"
            with self.assertRaisesRegex(RuntimeError, "unavailable Runtime capability FD"):
                mcp_e2e.subprocess_capability_fds()
        finally:
            if previous is None:
                os.environ.pop("CARGO_TARGET_DIR", None)
            else:
                os.environ["CARGO_TARGET_DIR"] = previous

    def test_local_acceptance_resolves_external_cargo_target_directory(self) -> None:
        local_acceptance = (REPO / "scripts/local-acceptance").read_text(encoding="utf-8")
        mcp_e2e = (REPO / "scripts/mcp_e2e.py").read_text(encoding="utf-8")
        self.assertIn("ordivon-local-acceptance-target", local_acceptance)
        self.assertIn('export CARGO_TARGET_DIR="$acceptance_target_dir"', local_acceptance)
        self.assertIn("cargo metadata --no-deps --format-version 1", local_acceptance)
        self.assertIn('["target_directory"]', local_acceptance)
        self.assertNotIn("$repo/target/debug/ordivon-runtime-runner", local_acceptance)
        self.assertIn('metadata["target_directory"]', mcp_e2e)
        self.assertNotIn('repo / "target/debug/ordivon-runtime"', mcp_e2e)

    def test_owner_environment_materializes_stable_runtime_inspector(self) -> None:
        owner = (REPO / "scripts/owner-environment").read_text(encoding="utf-8")
        self.assertIn("materialize_runtime_inspect()", owner)
        self.assertIn("cargo", owner)
        self.assertIn("metadata --locked --no-deps --format-version 1", owner)
        self.assertIn('inspect_dir="$env_dir/runtime-bin"', owner)
        self.assertIn('install -m 0755 "$source_inspect"', owner)
        self.assertIn("export ORDIVON_RUNTIME_INSPECT=", owner)
        self.assertIn('cmp -s "$source_inspect"', owner)

    def test_owner_environment_test_lifecycle_is_public_and_non_qualifying(self) -> None:
        help_result = subprocess.run(
            ["scripts/owner-environment", "--help"],
            cwd=REPO,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("test-lifecycle", help_result.stdout)
        self.assertIn("non-qualifying", help_result.stdout.lower())

        environment = os.environ.copy()
        environment.pop("CARGO_TARGET_DIR", None)
        result = subprocess.run(
            ["scripts/owner-environment", "test-lifecycle"],
            cwd=REPO,
            env=environment,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("lifecycle inner-loop: non-qualifying", result.stdout.lower())

    def test_runtime_verify_runs_reference_model_only_via_extended_surface(self) -> None:
        mise = (REPO / "mise.toml").read_text(encoding="utf-8")
        verify = mise.split("[tasks.verify]", 1)[1]
        property_name = "request_identity_and_terminal_winner_match_reference_model"
        transactional = next(
            line for line in verify.splitlines() if "cargo test --locked -p ordivon-runtime-core" in line
        )
        self.assertIn(f"--skip {property_name}", transactional)
        self.assertEqual(verify.count("scripts/owner-environment extended"), 1)
        owner = (REPO / "scripts/owner-environment").read_text(encoding="utf-8")
        extended = owner.split("run_extended() {", 1)[1].split("\n}", 1)[0]
        self.assertIn(
            "scripts/verify_reference_model_shards.py --shards 8 --parallel 4",
            extended,
        )
        self.assertNotIn(
            "test --locked -p ordivon-runtime-core request_identity_and_terminal_winner_match_reference_model",
            extended,
        )

    def test_owner_environment_extended_reuses_a_complete_offline_environment(self) -> None:
        owner = (REPO / "scripts/owner-environment").read_text(encoding="utf-8")
        self.assertIn("environment_is_materialized()", owner)
        self.assertIn("ensure_materialized_environment()", owner)
        self.assertIn('uv_bin" pip sync --offline --python "$python_bin" "$tooling_lock"', owner)
        self.assertIn('cargo_bin" fetch --locked --offline', owner)
        self.assertIn('uv_bin" pip sync --python "$python_bin" "$tooling_lock"', owner)
        self.assertIn('cargo_bin" fetch --locked)', owner)
        run_extended = owner.split("run_extended() {", 1)[1].split("\n}", 1)[0]
        self.assertIn("ensure_materialized_environment", run_extended)
        self.assertNotIn("\n  bootstrap\n", run_extended)

    def test_local_acceptance_contract_is_executable(self) -> None:
        result = subprocess.run(
            ["scripts/local-acceptance", "check"],
            cwd=REPO,
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("local acceptance contract: present", result.stdout)
        acceptance = (REPO / "scripts/local-acceptance").read_text(encoding="utf-8")
        self.assertIn("--features systemd-supervisor", acceptance)
        self.assertIn("ORDIVON_RUN_SYSTEMD_SPIKE=1", acceptance)

    def test_restore_rejects_symlinked_manifest_parent(self) -> None:
        # A final file may be regular even though an intermediate directory
        # escapes the snapshot through a symlink.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            outside = root / "outside"
            snapshot.mkdir()
            outside.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            private = outside / "external.txt"
            private.write_text("external consumer secret", encoding="utf-8")
            (snapshot / "control").mkdir()
            (snapshot / "control" / "alias").symlink_to(outside, target_is_directory=True)
            records = [
                {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": restore.sha256_file(database)},
                {
                    "path": "control/alias/external.txt",
                    "bytes": private.stat().st_size,
                    "digest": restore.sha256_file(private),
                },
            ]
            (snapshot / "manifest.json").write_text(
                json.dumps({"schemaVersion": 1, "files": records}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "symlink"):
                restore.load_and_verify(snapshot)
            self.assertFalse((root / "restored").exists())

    def test_restore_rejects_boolean_size_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            witness = snapshot / "witness.txt"
            witness.write_bytes(b"X")
            records = [
                {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": restore.sha256_file(database)},
                {"path": "witness.txt", "bytes": True, "digest": restore.sha256_file(witness)},
            ]
            (snapshot / "manifest.json").write_text(
                json.dumps({"schemaVersion": 1, "files": records}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "invalid byte length"):
                restore.load_and_verify(snapshot)

    def test_restore_refuses_source_mutation_between_check_and_copy(self) -> None:
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            note = snapshot / "note.txt"
            note.write_bytes(b"GOOD")
            records = [
                {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": restore.sha256_file(database)},
                {"path": "note.txt", "bytes": 4, "digest": restore.sha256_file(note)},
            ]
            (snapshot / "manifest.json").write_text(
                json.dumps({"schemaVersion": 1, "files": records}), encoding="utf-8"
            )
            actual_copy = restore.shutil.copy2

            def changed_copy(source, destination, *args, **kwargs):
                copied = actual_copy(source, destination, *args, **kwargs)
                if Path(destination).name == "note.txt":
                    Path(destination).write_bytes(b"EVIL")
                return copied

            restored = root / "restored"
            with patch.object(restore.shutil, "copy2", side_effect=changed_copy):
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    restore.restore_snapshot(snapshot, restored)
            self.assertFalse(restored.exists())

    def test_restore_parent_symlink_swap_preserves_bound_inode(self) -> None:
        # Source content equality does not grant authority to fetch the same
        # bytes through a changed, external directory after admission.
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            outside = root / "outside"
            control = snapshot / "control"
            control.mkdir(parents=True)
            outside.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as db:
                db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            item = control / "note.txt"
            item.write_bytes(b"IDENTICAL")
            (outside / "note.txt").write_bytes(b"IDENTICAL")
            records = [
                {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": restore.sha256_file(database)},
                {"path": "control/note.txt", "bytes": item.stat().st_size, "digest": restore.sha256_file(item)},
            ]
            (snapshot / "manifest.json").write_text(
                json.dumps({"schemaVersion": 1, "files": records}), encoding="utf-8"
            )
            actual_copy = restore.shutil.copy2
            original_inode = item.stat().st_ino
            swapped = False

            def swap_before_copy(source, destination, *args, **kwargs):
                nonlocal swapped
                if Path(destination).name == "note.txt" and not swapped:
                    control.rename(snapshot / "original-control")
                    control.symlink_to(outside, target_is_directory=True)
                    swapped = True
                    # Same bytes and digest, yet a pathname-based copy would
                    # silently switch its source identity to the outsider.
                    self.assertEqual(os.stat(source).st_ino, original_inode)
                return actual_copy(source, destination, *args, **kwargs)

            restored = root / "restored"
            with patch.object(restore.shutil, "copy2", side_effect=swap_before_copy):
                restore.restore_snapshot(snapshot, restored)
            self.assertTrue(swapped)
            self.assertEqual((restored / "control/note.txt").read_bytes(), b"IDENTICAL")

    def test_restore_openat_pins_directory_before_racing_final_lookup(self) -> None:
        from unittest.mock import patch

        if not sys.platform.startswith("linux"):
            self.skipTest("directory-fd source pinning is Linux-specific")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            control = snapshot / "control"
            outside = root / "outside"
            control.mkdir(parents=True)
            outside.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as db:
                db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            item = control / "note.txt"
            item.write_bytes(b"ORIGIN")
            (outside / "note.txt").write_bytes(b"EVIL!!")
            records = [
                {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": restore.sha256_file(database)},
                {"path": "control/note.txt", "bytes": item.stat().st_size, "digest": restore.sha256_file(item)},
            ]
            (snapshot / "manifest.json").write_text(
                json.dumps({"schemaVersion": 1, "files": records}), encoding="utf-8"
            )
            original_open = restore.os.open
            swapped = False

            def swap_after_parent_fd(path, flags, *args, **kwargs):
                nonlocal swapped
                if path == "note.txt" and kwargs.get("dir_fd") is not None and not swapped:
                    control.rename(snapshot / "original-control")
                    control.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original_open(path, flags, *args, **kwargs)

            restored = root / "restored"
            with patch.object(restore.os, "open", side_effect=swap_after_parent_fd):
                restore.restore_snapshot(snapshot, restored)
            self.assertTrue(swapped)
            self.assertEqual((restored / "control/note.txt").read_bytes(), b"ORIGIN")

    def test_restore_never_replaces_concurrently_created_empty_destination(self) -> None:
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapshot"
            source.mkdir()
            registry = source / "registry.sqlite3"
            with closing(sqlite3.connect(registry)) as db:
                db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
            manifest = {
                "schemaVersion": 1,
                "files": [
                    {
                        "path": "registry.sqlite3",
                        "bytes": registry.stat().st_size,
                        "digest": restore.sha256_file(registry),
                    }
                ],
            }
            (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            destination = root / "restored"
            original_copy = restore.shutil.copy2
            created = False

            def competing_creator(*args, **kwargs):
                nonlocal created
                result = original_copy(*args, **kwargs)
                if not created:
                    destination.mkdir()
                    created = True
                return result

            with patch.object(restore.shutil, "copy2", side_effect=competing_creator):
                with self.assertRaises(FileExistsError):
                    restore.restore_snapshot(source, destination)
            self.assertTrue(created)
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])

    def test_restore_rejects_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            database = snapshot / "registry.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("CREATE TABLE t (v INTEGER)")
            (snapshot / "manifest.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "files": [
                            {"path": "registry.sqlite3", "bytes": database.stat().st_size, "digest": "sha256:bad"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                restore.restore_snapshot(snapshot, root / "restored")


if __name__ == "__main__":
    unittest.main()
