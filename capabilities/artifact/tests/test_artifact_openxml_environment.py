from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('openxml_env',ROOT/'scripts/artifact_openxml_environment.py');M=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(M)
class ArtifactOpenXmlEnvironmentTests(unittest.TestCase):
    def test_apply_fence_uses_canonical_monorepo_artifact_owner(self):
        self.assertEqual(M.MAIN, Path("/root/projects/ordivon/capabilities/artifact"))

    def test_lock_separates_method_package_and_sdk_restore_support(self):
        lock=json.loads((ROOT/'artifact-delivery/openxml-runtime-v1.lock.json').read_text())
        self.assertEqual(lock['methodId'],'artifact.openxml.conformance.v1')
        self.assertEqual(lock['targetFramework'],'net8.0')
        self.assertEqual(lock['dotnetPolicy']['sdkMajorMinor'],'8.0')
        self.assertNotIn('equipment',lock)
        self.assertEqual(lock['nixDotnet']['expectedSdkVersion'],'8.0.426')
        self.assertEqual(lock['nixDotnet']['nixpkgsRevision'],json.loads((ROOT/'artifact-delivery/openxml-nix/flake.lock').read_text())['nodes']['nixpkgs']['locked']['rev'])
        self.assertEqual([(x['id'],x['version']) for x in lock['nugetPackages']],[('DocumentFormat.OpenXml','3.5.1'),('DocumentFormat.OpenXml.Framework','3.5.1'),('System.IO.Packaging','8.0.1')])
        self.assertEqual(lock['sdkRestoreSupportPackages'][0]['id'],'Microsoft.AspNetCore.App.Ref')
    def test_openxml_reconstruction_uses_artifact_owned_nix_not_isolated_equipment(self):
        source=(ROOT/'scripts/artifact_openxml_environment.py').read_text()
        wrapper=(ROOT/'scripts/artifact_openxml_dotnet_wrapper.py').read_text()
        flake=(ROOT/'artifact-delivery/openxml-nix/flake.nix').read_text()
        self.assertNotIn('isolated-equipment',source)
        self.assertNotIn('equipment_status',source)
        self.assertIn('nix_dotnet_status',source)
        self.assertIn('pkgs.dotnet-sdk_8',flake)
        self.assertIn('dotnetNixStorePath',wrapper)

    def test_nix_and_artifact_openxml_lock_share_exact_source_identity(self):
        # Consumer-driven lock invariant: one exact flake source cut, not two
        # independently mutable revision / NAR / byte-digest authorities.
        flake_path = ROOT / 'artifact-delivery/openxml-nix/flake.lock'
        raw = flake_path.read_bytes()
        flake = json.loads(raw)['nodes']['nixpkgs']['locked']
        sdk = json.loads(
            (ROOT / 'artifact-delivery/openxml-runtime-v1.lock.json').read_text()
        )['nixDotnet']
        self.assertEqual(sdk['nixpkgsRevision'], flake['rev'])
        self.assertEqual(sdk['nixpkgsNarHash'], flake['narHash'])
        self.assertEqual(
            sdk['flakeLockSha256'],
            'sha256:' + hashlib.sha256(raw).hexdigest(),
        )

    def test_outdated_nix_sdk_cannot_be_published_even_when_flake_identity_matches(self):
        # The official Nixpkgs 26.05 and unstable SDK providers still resolve
        # 8.0.425. That is not an acceptable substitute for security-patched
        # upstream 8.0.426; refuse before any publication or path-info success.
        lock = json.loads(
            (ROOT / 'artifact-delivery/openxml-runtime-v1.lock.json').read_text()
        )
        def probe(cmd, **_kwargs):
            if 'build' in cmd:
                return subprocess.CompletedProcess(cmd, 0, '/nix/store/mock-dotnet-8.0.425\n', '')
            if cmd[-1] == '--version':
                return subprocess.CompletedProcess(cmd, 0, '8.0.425\n', '')
            raise AssertionError('unpatched SDK reached unsafe downstream step')
        # The checkout-only CI runner need not install physical Nix. Bind the
        # executable presence check to an existing fixture path; mock only
        # the transport outputs. Live Nix acceptance is proved separately.
        with (
            patch.object(M, 'NIX', Path(__file__).resolve()),
            patch.object(M, 'run', side_effect=probe),
        ):
            with self.assertRaisesRegex(RuntimeError, 'Nix SDK drift'):
                M.nix_dotnet_status(lock)

    def test_generation_spec_binds_nix_store_and_nar_identity(self):
        lock=json.loads((ROOT/'artifact-delivery/openxml-runtime-v1.lock.json').read_text())
        dotnet={'storePath':'/nix/store/example-dotnet','narHash':'sha256-example','flakeLockSha256':lock['nixDotnet']['flakeLockSha256'],'nixpkgsRevision':lock['nixDotnet']['nixpkgsRevision'],'observedSdkVersion':'8.0.426'}
        with patch.object(M,'source_digests',return_value={'sourceProject':'sha256:p','sourceProgram':'sha256:s'}):
            spec=M.generation_spec(lock,dotnet,[])
        self.assertEqual(spec['dotnetNixStorePath'],'/nix/store/example-dotnet')
        self.assertEqual(spec['dotnetNixNarHash'],'sha256-example')
        self.assertEqual(spec['observedDotnetSdk'],'8.0.426')

    def test_production_defaults_use_managed_openxml_carrier(self):
        doctor=(ROOT/'scripts/artifact_delivery_toolchain_doctor.py').read_text()
        toolchain=(ROOT/'artifact_verifiers/openxml/toolchain.py').read_text()
        self.assertNotIn('.cache/dotnet/dotnet',doctor)
        self.assertNotIn('openxml-validator/bin/Release/net8.0/ArtifactOpenXmlValidator.dll',doctor)
        self.assertIn('artifact-openxml-v1/current/bin/validate-openxml',toolchain)
        self.assertIn('OPENXML_LOCK',doctor)
    def test_external_evidence_prepublication_gate_requires_bounded_pass_without_ivv_claim(self):
        payload={
            'methodId':'artifact.openxml.conformance.v1',
            'standing':'PASS_BOUNDED_EXTERNAL_EVIDENCE',
            'methodPromotion':'GRADUATED_BOUNDED_STRUCTURAL_GATE',
            'ivvStanding':'NOT_CLAIMED',
            'corpusDigestMatchesFreeze':True,
        }
        completed=subprocess.CompletedProcess(['python'],0,json.dumps(payload),'')
        with patch.object(M,'run',return_value=completed):
            self.assertEqual(M.verify_external_evidence(Path('/tmp/validator'))['standing'],'PASS_BOUNDED_EXTERNAL_EVIDENCE')
        payload['corpusDigestMatchesFreeze']=False
        completed=subprocess.CompletedProcess(['python'],0,json.dumps(payload),'')
        with patch.object(M,'run',return_value=completed):
            with self.assertRaisesRegex(RuntimeError,'corpus digest drift'):
                M.verify_external_evidence(Path('/tmp/validator'))

    def test_apply_runs_external_evidence_before_current_publication(self):
        source=(ROOT/'scripts/artifact_openxml_environment.py').read_text()
        gate=source.index("external_evidence=verify_external_evidence(final/'bin/validate-openxml')")
        publish=source.index("os.symlink(Path('generations')/gid,tmp)")
        self.assertLess(gate,publish)

    def test_tree_digest_detects_bytes_and_unsafe_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a').write_bytes(b'one');first=M.tree_digest(root);(root/'a').write_bytes(b'two');self.assertNotEqual(first,M.tree_digest(root));(root/'escape').symlink_to('/etc/passwd')
            with self.assertRaisesRegex(RuntimeError,'unsafe generation symlink'):M.tree_digest(root)
if __name__=='__main__':unittest.main()
