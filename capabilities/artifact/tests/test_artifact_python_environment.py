from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_python_environment_test',ROOT/'scripts/artifact_python_environment.py');M=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(M)
WRAP_SPEC=importlib.util.spec_from_file_location('artifact_python_wrapper_test',ROOT/'scripts/artifact_python_wrapper.py');W=importlib.util.module_from_spec(WRAP_SPEC);assert WRAP_SPEC and WRAP_SPEC.loader;WRAP_SPEC.loader.exec_module(W)

class ArtifactDeliveryEnvironmentTests(unittest.TestCase):
    def test_mise_tool_resolution_uses_selected_path_not_system_bin(self):
        # A GitHub runner may install mise outside /usr/bin. Do not bind to
        # the local machine's binary layout when selecting locked owner tools.
        with patch.object(M.shutil, 'which', return_value='/opt/toolchain/bin/mise') as which:
            with patch.object(M.subprocess, 'run') as execute:
                execute.return_value.returncode = 0
                execute.return_value.stdout = '/bin/sh\n'
                result = M.selected_owner_tool('uv', 'ARTIFACT_TEST_NONEXISTENT_OVERRIDE')
        which.assert_called_once_with('mise')
        self.assertEqual(result, Path('/bin/sh'))
        command = execute.call_args.args[0]
        self.assertEqual(command[0], '/opt/toolchain/bin/mise')
        self.assertEqual(command[1:], ['-C', str(ROOT), 'which', 'uv'])

    def test_mise_absence_fails_closed_without_spawning(self):
        with patch.object(M.shutil, 'which', return_value=None):
            with patch.object(M.subprocess, 'run') as execute:
                with self.assertRaisesRegex(RuntimeError, 'mise executable unavailable'):
                    M.selected_owner_tool('uv', 'ARTIFACT_TEST_NONEXISTENT_OVERRIDE')
                execute.assert_not_called()

    def test_apply_fence_uses_canonical_monorepo_artifact_owner(self):
        self.assertEqual(M.MAIN, Path("/root/projects/ordivon/capabilities/artifact"))

    def test_lock_is_uv_owned_complete_python_package_closure(self):
        lock=json.loads((ROOT/'artifact-delivery/artifact-python-runtime-v1.lock.json').read_text())
        self.assertEqual(lock['pythonRuntime'],'3.15.1');self.assertEqual(lock['pythonPackages']['lxml'],'6.1.3')
        self.assertEqual(lock['pythonPackages']['Pillow'],'12.3.0');self.assertNotIn('vendoredEquipment',lock);self.assertNotIn('hostSystemPackages',lock);self.assertNotIn('hostFencedPackages',lock)
        self.assertEqual(lock['uvProject']['path'],'artifact-delivery/python-uv');self.assertTrue(lock['uvProject']['uvLockSha256'].startswith('sha256:'))
    def test_uv_project_pins_every_accepted_distribution(self):
        lock=M.load_lock();text=(ROOT/'artifact-delivery/python-uv/pyproject.toml').read_text()
        for name,version in lock['pythonPackages'].items():self.assertIn(f'{name}=={version}'.lower(),text.lower())
        uvlock=(ROOT/'artifact-delivery/python-uv/uv.lock').read_text();self.assertIn('lxml',uvlock);self.assertIn('6.1.3',uvlock)
    def test_environment_has_no_isolated_equipment_or_host_libxslt_authority(self):
        source=(ROOT/'scripts/artifact_python_environment.py').read_text();wrapper=(ROOT/'scripts/artifact_python_wrapper.py').read_text()
        self.assertNotIn('isolated-equipment',source);self.assertNotIn('pacman',source);self.assertNotIn('libxslt.so',source);self.assertIn("'--frozen','--offline'",source);self.assertIn('venvTreeDigest',wrapper)
    def test_artifact_worker_and_tools_share_one_artifact_python_carrier(self):
        stable='/root/.local/share/ordivon-workstation/artifact-python-v1/current/bin/python'
        consumers=[
            'scripts/artifact_delivery_toolchain_doctor.py',
            'scripts/artifact_agent_surface.py',
            'scripts/artifact_temporal_deploy.py',
            'systemd/ordivon-artifact-temporal-worker.service',
        ]
        for name in consumers:
            text=(ROOT/name).read_text()
            self.assertNotIn('.cache/artifact-delivery-venv',text,name)
            self.assertIn(stable,text,name)
        lock=M.load_lock()
        self.assertEqual(lock['pythonPackages']['temporalio'],'1.32.0')
        self.assertEqual(lock['pythonPackages']['nexus-rpc'],'1.4.0')
        self.assertEqual(lock['pythonPackages']['protobuf'],'7.36.2')
        self.assertEqual(lock['pythonPackages']['types-protobuf'],'7.35.1.20260906')
    def test_published_stable_python_is_wrapper_not_internal_venv_interpreter(self):
        lock=M.load_lock();stable=lock['stablePython'];self.assertTrue(stable.endswith('/current/bin/python'));self.assertNotIn('/.venv/',stable)
        wrapper=(ROOT/'scripts/artifact_python_wrapper.py').read_text();self.assertIn("'PYTHONDONTWRITEBYTECODE':'1'",wrapper)
    def test_materializer_and_wrapper_share_environment_tree_canonicalization(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pkg').mkdir();(root/'pkg/data').write_bytes(b'bytes');(root/'python').symlink_to('/bin/sh')
            self.assertEqual(M.tree_digest(root),W.tree_digest(root));first=W.tree_digest(root);(root/'pkg/data').write_bytes(b'drift');self.assertNotEqual(first,W.tree_digest(root))
    def test_generation_spec_binds_uv_and_interpreter_identity(self):
        lock=M.load_lock();project={'project':'/x','pyprojectSha256':'sha256:p','uvLockSha256':'sha256:u'};python={'version':'3.15.1','requestedPath':'/toolchain/python','resolvedPath':'/toolchain/python3.15','sha256':'sha256:i'}
        spec=M.generation_spec(lock,project,python);self.assertEqual(spec['uvLockSha256'],'sha256:u');self.assertEqual(spec['pythonExecutableSha256'],'sha256:i');self.assertEqual(spec['pythonPackages']['lxml'],'6.1.3');self.assertEqual(spec['pythonPackages']['temporalio'],'1.32.0')
    def test_read_only_tree_changes_mode_before_digest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'x';f.write_text('x');f.chmod(0o644);M.make_read_only(root);self.assertEqual(root.stat().st_mode & 0o777,0o555);self.assertEqual(f.stat().st_mode & 0o777,0o444)


    def test_generation_interpreter_is_pinned_and_survives_source_drift(self):
        # Local-main historical candidate b066c82: the published generation
        # must not depend on mutable external mise executable bytes.
        import hashlib
        with tempfile.TemporaryDirectory(prefix="artifact-python-generation-") as temp:
            root = Path(temp)
            source = root / "external-mise-python"
            source.write_bytes(b"python-v1")
            source.chmod(0o755)
            venv = root / ".venv"
            (venv / "bin").mkdir(parents=True)
            (venv / "bin/python").symlink_to(source)
            (venv / "bin/python3").symlink_to("python")
            identity = {
                "resolvedPath": str(source.resolve()),
                "sha256": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
            }
            selected = M.pin_interpreter_in_venv(venv, identity)
            self.assertEqual(selected, venv / "bin/python")
            self.assertFalse(selected.is_symlink())
            self.assertEqual(selected.read_bytes(), b"python-v1")
            digest = M.tree_digest(venv)
            source.write_bytes(b"python-v2")
            self.assertEqual(selected.read_bytes(), b"python-v1")
            self.assertEqual(M.tree_digest(venv), digest)
            self.assertEqual((venv / "bin/python3").resolve(), selected.resolve())

    def test_generation_interpreter_rejects_wrong_source_hash(self):
        with tempfile.TemporaryDirectory(prefix="artifact-python-source-drift-") as temp:
            root = Path(temp)
            source = root / "source"
            source.write_bytes(b"tampered")
            venv = root / ".venv"
            (venv / "bin").mkdir(parents=True)
            target = venv / "bin/python"
            target.symlink_to(source)
            with self.assertRaisesRegex(RuntimeError, "interpreter.*drift"):
                M.pin_interpreter_in_venv(
                    venv, {"resolvedPath": str(source), "sha256": "sha256:" + "0" * 64}
                )
            self.assertTrue(target.is_symlink())

    def test_actual_artifact_wrapper_refuses_external_python_for_local_generation(self):
        # Black-box wrapper test: a marker alone cannot turn an external
        # interpreter symlink into generation-owned immutable executable bytes.
        import shutil
        import subprocess
        with tempfile.TemporaryDirectory(prefix="artifact-wrapper-placement-") as temp:
            generation = Path(temp) / "generation"
            (generation / "bin").mkdir(parents=True)
            (generation / ".venv/bin").mkdir(parents=True)
            wrapper = generation / "bin/python"
            shutil.copy2(ROOT / "scripts/artifact_python_wrapper.py", wrapper)
            wrapper.chmod(0o755)
            (generation / ".venv/bin/python").symlink_to("/bin/sh")
            binding = {
                "schemaVersion": 1,
                "kind": "artifact-python-generation-binding",
                "wrapperSha256": "sha256:" + M.sha(wrapper),
                "venvTreeDigest": W.tree_digest(generation / ".venv"),
                "pythonExecutableSha256": "sha256:" + M.sha(Path("/bin/sh").resolve()),
                "interpreterPlacement": "generation-local-executable-copy-v1",
            }
            (generation / "binding.json").write_text(json.dumps(binding))
            result = subprocess.run(
                [str(wrapper), "-c", "print(123)"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 126, result.stderr)
            self.assertIn("placement drift", result.stderr)


if __name__=='__main__':unittest.main()
