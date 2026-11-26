"""Native Git and pure projection tests for immutable deployment preparation."""
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "artifact_temporal_immutable_deploy", ROOT / "scripts/artifact_temporal_deploy.py"
)
assert SPEC and SPEC.loader
DEPLOY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEPLOY)


class ImmutableDeploymentTests(unittest.TestCase):
    def test_native_git_tree_rejects_byte_mode_membership_and_symlink_drift(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(object_format=fmt), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                repo = root / "repo"
                repo.mkdir()
                git = ["/usr/bin/git", "-C", str(repo)]
                env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
                def run(*args):
                    return subprocess.check_output([*git, *args], env=env, stderr=subprocess.PIPE)
                run("init", "--object-format="+fmt)
                run("config", "user.name", "Fixture")
                run("config", "user.email", "fixture@example.invalid")
                source = repo / "capabilities/artifact"
                source.mkdir(parents=True)
                (source / "a").write_text("exact")
                (source / "b").write_text("executable")
                (source / "b").chmod(0o755)
                run("add", ".")
                run("commit", "-m", "fixture")
                commit = run("rev-parse", "HEAD").decode().strip()
                candidate = root / "candidate"
                shutil.copytree(source, candidate)
                self.assertEqual(DEPLOY.qualify_source_tree(repo, commit, candidate), 2)
                self.assertEqual(DEPLOY.qualify_source_tree(source, commit, candidate), 2)
                with self.assertRaisesRegex(RuntimeError, "exact Git commit"):
                    DEPLOY.qualify_source_tree(repo, "HEAD", candidate)
                (candidate / "a").write_text("mutated")
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    DEPLOY.qualify_source_tree(repo, commit, candidate)
                (candidate / "a").write_text("exact")
                (candidate / "b").chmod(0o644)
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    DEPLOY.qualify_source_tree(repo, commit, candidate)
                (candidate / "b").chmod(0o755)
                (candidate / "extra").touch()
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    DEPLOY.qualify_source_tree(repo, commit, candidate)
                (candidate / "extra").unlink()
                (candidate / "a").unlink()
                with self.assertRaisesRegex(RuntimeError, "differs"):
                    DEPLOY.qualify_source_tree(repo, commit, candidate)
                (candidate / "a").symlink_to(source / "a")
                with self.assertRaisesRegex(RuntimeError, "symlink"):
                    DEPLOY.qualify_source_tree(repo, commit, candidate)

    def test_unit_projection_preserves_every_unrelated_byte(self):
        template = DEPLOY.SOURCE_UNIT.read_text()
        source = Path("/nix/store/example-artifact")
        carrier = Path("/opt/generations/example/bin/python")
        unit = DEPLOY.render_immutable_unit(template, source, carrier)
        self.assertIn("WorkingDirectory="+str(source), unit)
        self.assertIn("ExecStart="+str(carrier)+" "+str(source/"scripts/artifact_temporal_worker.py"), unit)
        restored = unit.replace(str(source), str(DEPLOY.MAIN)).replace(str(carrier), str(DEPLOY.TEMPORAL_PY))
        self.assertEqual(template, restored)
        with self.assertRaisesRegex(RuntimeError, "unsupported"):
            DEPLOY.render_immutable_unit(template, Path("/nix/store/bad name"), carrier)
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            DEPLOY.render_immutable_unit(template+"\nExecStart=/bin/false\n", source, carrier)
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            DEPLOY.render_immutable_unit(template+"\nWorkingDirectory=/tmp\n", source, carrier)

    def test_prepare_rejects_non_store_source_before_external_lookup(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError, "direct native Nix"):
                DEPLOY.prepare_immutable("0"*40, Path(d), Path(d)/"root")


if __name__ == "__main__":
    unittest.main()
