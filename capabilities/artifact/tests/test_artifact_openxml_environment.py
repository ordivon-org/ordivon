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
        import xml.etree.ElementTree as ET
        lock=M.load_lock()
        self.assertEqual(lock['methodId'],'artifact.openxml.conformance.v1')
        project=ET.parse(ROOT/lock['sourceProject']).getroot()
        self.assertEqual(lock['targetFramework'],project.findtext('.//TargetFramework'))
        self.assertEqual(lock['targetFramework'],'net'+lock['dotnetPolicy']['sdkMajorMinor'])
        self.assertTrue(lock['nixDotnet']['expectedSdkVersion'].startswith(lock['dotnetPolicy']['sdkMajorMinor']+'.'))
        self.assertEqual(set(lock['nixDotnet']),{'flake','package','expectedSdkVersion'})
        packages={row['id']:row for row in lock['nugetPackages']}
        direct={row.attrib['Include']:row.attrib['Version'] for row in project.findall('.//PackageReference')}
        self.assertEqual(direct['DocumentFormat.OpenXml'],packages['DocumentFormat.OpenXml']['version'])
        self.assertEqual(packages['DocumentFormat.OpenXml']['version'],packages['DocumentFormat.OpenXml.Framework']['version'])
        support={row['id']:row for row in lock['sdkRestoreSupportPackages']}
        self.assertIn('Microsoft.AspNetCore.App.Ref',support)
        self.assertFalse(set(packages)&set(support))
        self.assertIn('System.IO.Packaging',packages)
        for row in [*packages.values(),*support.values()]:
            self.assertRegex(row['nupkgSha256'],r'^[a-f0-9]{64}$')
    def test_openxml_reconstruction_uses_artifact_owned_nix_not_isolated_equipment(self):
        source=(ROOT/'scripts/artifact_openxml_environment.py').read_text()
        wrapper=(ROOT/'scripts/artifact_openxml_dotnet_wrapper.py').read_text()
        flake=(ROOT/'artifact-delivery/openxml-nix/flake.nix').read_text()
        self.assertNotIn('isolated-equipment',source)
        self.assertNotIn('equipment_status',source)
        self.assertIn('nix_dotnet_status',source)
        self.assertIn('pkgs.dotnet-sdk_10',flake)
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
        # A single Nix authority, with the revision, NAR and content digest
        # derived atomically. The method lock stores only the SDK constraint.
        self.assertNotIn('nixpkgsRevision',sdk)
        self.assertNotIn('nixpkgsNarHash',sdk)
        self.assertNotIn('flakeLockSha256',sdk)
        authority=M.nix_source_cut(flake_path)
        self.assertEqual(authority['nixpkgsRevision'],flake['rev'])
        self.assertEqual(authority['nixpkgsNarHash'],flake['narHash'])
        self.assertEqual(authority['flakeLockSha256'],'sha256:'+hashlib.sha256(raw).hexdigest())

    def test_outdated_nix_sdk_cannot_be_published_even_when_flake_identity_matches(self):
        # A different SDK cannot inherit the selected exact generation claim;
        # refuse before any publication or path-info success.
        lock = json.loads(
            (ROOT / 'artifact-delivery/openxml-runtime-v1.lock.json').read_text()
        )
        def probe(cmd, **_kwargs):
            if 'build' in cmd:
                return subprocess.CompletedProcess(cmd, 0, '/nix/store/mock-dotnet-10.0.403\n', '')
            if cmd[-1] == '--version':
                return subprocess.CompletedProcess(cmd, 0, '10.0.403\n', '')
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

    def test_updated_nixpkgs_source_is_derived_without_second_lock_edit(self):
        lock=M.load_lock()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            flake_dir=root/'artifact-delivery/openxml-nix'
            flake_dir.mkdir(parents=True)
            data=json.loads((ROOT/'artifact-delivery/openxml-nix/flake.lock').read_text())
            data['nodes']['nixpkgs']['locked']['rev']='a'*40
            path=flake_dir/'flake.lock'
            path.write_text(json.dumps(data))
            def probe(cmd,**_kwargs):
                if 'build' in cmd:
                    self.assertTrue(cmd[-1].endswith('#dotnet-sdk^out'),cmd)
                    return subprocess.CompletedProcess(cmd,0,'/nix/store/example-dotnet\n','')
                if cmd[-1]=='--version':return subprocess.CompletedProcess(cmd,0,lock['nixDotnet']['expectedSdkVersion']+'\n','')
                if 'path-info' in cmd:return subprocess.CompletedProcess(cmd,0,json.dumps({'/nix/store/example-dotnet':{'narHash':'sha256-example'}}),'')
                raise AssertionError('unexpected provider operation')
            with (
                patch.object(M,'ROOT',root),
                patch.object(M,'NIX_FLAKE',flake_dir),
                patch.object(M,'NIX',Path(__file__).resolve()),
                patch.object(M,'run',side_effect=probe),
            ):
                receipt=M.nix_dotnet_status(lock)
            self.assertEqual(receipt['nixpkgsRevision'],'a'*40)
            self.assertEqual(receipt['flakeLockSha256'],'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest())

    def test_nix_source_mutation_during_build_fails_closed(self):
        lock=M.load_lock()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);flake_dir=root/'artifact-delivery/openxml-nix'
            flake_dir.mkdir(parents=True)
            path=flake_dir/'flake.lock'
            original=json.loads((ROOT/'artifact-delivery/openxml-nix/flake.lock').read_text())
            path.write_text(json.dumps(original))
            def mutate_on_build(cmd,**_kwargs):
                if 'build' in cmd:
                    changed=json.loads(path.read_text())
                    changed['nodes']['nixpkgs']['locked']['rev']='b'*40
                    path.write_text(json.dumps(changed))
                    return subprocess.CompletedProcess(cmd,0,'/nix/store/example-dotnet\\n','')
                raise AssertionError('drift must be detected before dotnet/provenance probes')
            with (
                patch.object(M,'ROOT',root),
                patch.object(M,'NIX_FLAKE',flake_dir),
                patch.object(M,'NIX',Path(__file__).resolve()),
                patch.object(M,'run',side_effect=mutate_on_build),
            ):
                with self.assertRaisesRegex(RuntimeError,'changed during build'):
                    M.nix_dotnet_status(lock)

    def test_untrusted_nixpkgs_source_is_rejected_before_build(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'flake.lock'
            data=json.loads((ROOT/'artifact-delivery/openxml-nix/flake.lock').read_text())
            data['nodes']['nixpkgs']['locked']['url']='https://example.invalid/untrusted'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(RuntimeError,'upstream authority drift'):
                M.nix_source_cut(path)
            path.unlink()
            path.symlink_to(ROOT/'artifact-delivery/openxml-nix/flake.lock')
            with self.assertRaisesRegex(RuntimeError,'alias'):
                M.nix_source_cut(path)

    def test_generation_spec_binds_nix_store_and_nar_identity(self):
        lock=json.loads((ROOT/'artifact-delivery/openxml-runtime-v1.lock.json').read_text())
        source=M.nix_source_cut(ROOT/'artifact-delivery/openxml-nix/flake.lock')
        dotnet={'storePath':'/nix/store/example-dotnet','narHash':'sha256-example','flakeLockSha256':source['flakeLockSha256'],'nixpkgsRevision':source['nixpkgsRevision'],'observedSdkVersion':'10.0.404'}
        with patch.object(M,'source_digests',return_value={'sourceProject':'sha256:p','sourceProgram':'sha256:s'}):
            spec=M.generation_spec(lock,dotnet,[])
        self.assertEqual(spec['dotnetNixStorePath'],'/nix/store/example-dotnet')
        self.assertEqual(spec['dotnetNixNarHash'],'sha256-example')
        self.assertEqual(spec['observedDotnetSdk'],'10.0.404')

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


class OpenXmlGenerationRetentionTests(unittest.TestCase):
    def test_apply_build_is_rooted_until_generation_publication(self):
        lock = M.load_lock()
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            lock["stableRoot"] = str(base)
            store = "/nix/store/fixture-dotnet"
            events = []

            def resolve(_lock, *, out_link=None):
                self.assertIsNotNone(out_link)
                self.assertTrue(out_link.parent.is_dir())
                out_link.symlink_to(store)
                events.append("build-root")
                return {"storePath": store}

            def build(_base, _lock, _dotnet, _nuget):
                self.assertEqual(events, ["build-root"])
                generation = base / "generations" / "fixture"
                generation.mkdir(parents=True)
                events.append("generation")
                return "fixture", generation, {"dotnetNixStorePath": store}

            def evidence(_validator):
                self.assertEqual(events, ["build-root", "generation"])
                self.assertTrue(any(base.glob(".build-root-*/dotnet")))
                events.append("corpus")
                return {k: "fixture" for k in (
                    "corpusId", "corpusResultDigest", "standing", "ivvStanding", "methodPromotion",
                )}

            def retain(generation, expected_store):
                self.assertEqual(events, ["build-root", "generation", "corpus"])
                self.assertTrue(any(base.glob(".build-root-*/dotnet")))
                self.assertEqual(expected_store, store)
                self.assertFalse((base / "current").exists())
                (generation / "dotnet-gc-root").symlink_to(store)
                events.append("retained")

            with (
                patch.object(M, "MAIN", M.ROOT),
                patch.object(M, "load_lock", return_value=lock),
                patch.object(M, "nix_dotnet_status", side_effect=resolve),
                patch.object(M, "nuget_sources", return_value=[]),
                patch.object(M, "build_generation", side_effect=build),
                patch.object(M, "verify_external_evidence", side_effect=evidence),
                patch.object(M, "register_generation_gc_root", side_effect=retain, create=True),
                patch.object(M, "status", return_value={"ready": True, "generationId": "fixture"}),
            ):
                M.apply()
            self.assertEqual(events, ["build-root", "generation", "corpus", "retained"])
            self.assertEqual((base / "current").resolve(), base / "generations" / "fixture")
            self.assertFalse(any(base.glob(".build-root-*")))


    def test_status_rejects_unregistered_generation_before_running_sdk(self):
        lock = M.load_lock()
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            generation = base / "generations" / "fixture"
            generation.mkdir(parents=True)
            (generation / "binding.json").write_text(json.dumps({
                "dotnetNixStorePath": "/nix/store/fixture",
                "observedDotnetSdk": "10.0.404",
            }))
            (base / "current").symlink_to(generation)
            (generation / "dotnet-gc-root").symlink_to("/nix/store/fixture")
            with (
                patch.object(M, "load_lock", return_value=lock),
                patch.object(M, "gc_root_registered", return_value=False),
                patch.object(M, "run") as run,
            ):
                status = M.status(base)
            self.assertFalse(status["ready"])
            self.assertFalse(status["gcRootRegistered"])
            self.assertIn("GC root", status["error"])
            run.assert_not_called()

    def test_failed_root_registration_preserves_previous_current(self):
        lock = M.load_lock()
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            lock["stableRoot"] = str(base)
            old = base / "generations" / "old"
            old.mkdir(parents=True)
            (base / "current").symlink_to(old)
            new = base / "generations" / "new"
            new.mkdir()
            store = "/nix/store/fixture"

            def resolve(_lock, *, out_link):
                out_link.symlink_to(store)
                return {"storePath": store}

            with (
                patch.object(M, "MAIN", M.ROOT),
                patch.object(M, "load_lock", return_value=lock),
                patch.object(M, "nix_dotnet_status", side_effect=resolve),
                patch.object(M, "nuget_sources", return_value=[]),
                patch.object(M, "build_generation", return_value=(
                    "new", new, {"dotnetNixStorePath": store},
                )),
                patch.object(M, "verify_external_evidence"),
                patch.object(M, "register_generation_gc_root", side_effect=RuntimeError("root failed")),
            ):
                with self.assertRaisesRegex(RuntimeError, "root failed"):
                    M.apply()
            self.assertEqual((base / "current").resolve(), old)
            self.assertFalse(any(base.glob(".build-root-*")))


if __name__ == "__main__":
    unittest.main()
