from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_delivery_environment_test',ROOT/'scripts/artifact_delivery_environment.py');M=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(M)
WRAP_SPEC=importlib.util.spec_from_file_location('artifact_delivery_python_wrapper_test',ROOT/'scripts/artifact_delivery_python_wrapper.py');W=importlib.util.module_from_spec(WRAP_SPEC);assert WRAP_SPEC and WRAP_SPEC.loader;WRAP_SPEC.loader.exec_module(W)

class ArtifactDeliveryEnvironmentTests(unittest.TestCase):
    def test_lock_is_uv_owned_complete_python_package_closure(self):
        lock=json.loads((ROOT/'artifact-delivery/python-runtime-v1.lock.json').read_text())
        self.assertEqual(lock['pythonRuntime'],'3.14.7');self.assertEqual(lock['pythonPackages']['lxml'],'6.1.3')
        self.assertEqual(lock['pythonPackages']['Pillow'],'12.3.0');self.assertNotIn('vendoredEquipment',lock);self.assertNotIn('hostSystemPackages',lock);self.assertNotIn('hostFencedPackages',lock)
        self.assertEqual(lock['uvProject']['path'],'artifact-delivery/python-uv');self.assertTrue(lock['uvProject']['uvLockSha256'].startswith('sha256:'))
    def test_uv_project_pins_every_accepted_distribution(self):
        lock=M.load_lock();text=(ROOT/'artifact-delivery/python-uv/pyproject.toml').read_text()
        for name,version in lock['pythonPackages'].items():self.assertIn(f'{name}=={version}'.lower(),text.lower())
        uvlock=(ROOT/'artifact-delivery/python-uv/uv.lock').read_text();self.assertIn('lxml',uvlock);self.assertIn('6.1.3',uvlock)
    def test_environment_has_no_isolated_equipment_or_host_libxslt_authority(self):
        source=(ROOT/'scripts/artifact_delivery_environment.py').read_text();wrapper=(ROOT/'scripts/artifact_delivery_python_wrapper.py').read_text()
        self.assertNotIn('isolated-equipment',source);self.assertNotIn('pacman',source);self.assertNotIn('libxslt.so',source);self.assertIn("'--frozen','--offline'",source);self.assertIn('venvTreeDigest',wrapper)
    def test_temporal_no_longer_depends_on_artifact_python_carrier(self):
        retired_consumers=[
            'scripts/artifact_delivery_temporal_support.py',
            'scripts/temporal_artifact_delivery_deploy.py',
            'systemd/ordivon-artifact-temporal-worker.service',
        ]
        stable='/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python'
        for name in retired_consumers:
            text=(ROOT/name).read_text()
            self.assertNotIn('.cache/artifact-delivery-venv',text,name)
            self.assertNotIn(stable,text,name)
        doctor=(ROOT/'scripts/artifact_delivery_toolchain_doctor.py').read_text()
        self.assertNotIn('.cache/artifact-delivery-venv',doctor)
        self.assertIn(stable,doctor)
    def test_published_stable_python_is_wrapper_not_internal_venv_interpreter(self):
        lock=M.load_lock();stable=lock['stablePython'];self.assertTrue(stable.endswith('/current/bin/python'));self.assertNotIn('/.venv/',stable)
        wrapper=(ROOT/'scripts/artifact_delivery_python_wrapper.py').read_text();self.assertIn("'PYTHONDONTWRITEBYTECODE':'1'",wrapper)
    def test_materializer_and_wrapper_share_environment_tree_canonicalization(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'pkg').mkdir();(root/'pkg/data').write_bytes(b'bytes');(root/'python').symlink_to('/bin/sh')
            self.assertEqual(M.tree_digest(root),W.tree_digest(root));first=W.tree_digest(root);(root/'pkg/data').write_bytes(b'drift');self.assertNotEqual(first,W.tree_digest(root))
    def test_generation_spec_binds_uv_and_interpreter_identity(self):
        lock=M.load_lock();project={'project':'/x','pyprojectSha256':'sha256:p','uvLockSha256':'sha256:u'};python={'version':'3.14.7','requestedPath':'/toolchain/python','resolvedPath':'/toolchain/python3.14','sha256':'sha256:i'}
        spec=M.generation_spec(lock,project,python);self.assertEqual(spec['uvLockSha256'],'sha256:u');self.assertEqual(spec['pythonExecutableSha256'],'sha256:i');self.assertEqual(spec['pythonPackages']['lxml'],'6.1.3')
    def test_read_only_tree_changes_mode_before_digest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);f=root/'x';f.write_text('x');f.chmod(0o644);M.make_read_only(root);self.assertEqual(root.stat().st_mode & 0o777,0o555);self.assertEqual(f.stat().st_mode & 0o777,0o444)

if __name__=='__main__':unittest.main()
