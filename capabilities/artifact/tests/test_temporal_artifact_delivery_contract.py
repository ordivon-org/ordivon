from __future__ import annotations
import ast,hashlib,importlib.util,json,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SUPPORT=ROOT/'scripts/artifact_delivery_temporal_support.py'
def load_support():
    spec=importlib.util.spec_from_file_location('artifact_delivery_temporal_support_test',SUPPORT);m=importlib.util.module_from_spec(spec);assert spec.loader is not None;spec.loader.exec_module(m);return m
class TemporalArtifactDeliveryContractTests(unittest.TestCase):
    def test_workflow_effect_boundary(self):
        path=ROOT/'scripts/temporal_artifact_delivery.py';text=path.read_text();tree=ast.parse(text);self.assertIn('@workflow.defn(name=ARTIFACT_DELIVERY_WORKFLOW)',text);self.assertIn('@workflow.signal(name=TRUST_MATERIAL_SIGNAL)',text);self.assertIn('await workflow.wait_condition',text);self.assertIn('retry_policy=RECEIPT_FENCED_RETRY',text)
        for node in ast.walk(tree):
            if isinstance(node,ast.ClassDef) and node.name=='ArtifactDeliveryWorkflow':
                seg=ast.get_source_segment(text,node) or ''
                for forbidden in ('subprocess.','Path(','open(','read_text(','write_text('):self.assertNotIn(forbidden,seg)
    def test_temporal_sdk_pin(self):self.assertEqual((ROOT/'config/artifact-delivery-temporal-requirements.txt').read_text().strip(),'temporalio==1.32.0')
    def test_launcher_duplicate_policy(self):
        text=(ROOT/'scripts/temporal_artifact_delivery_launch.py').read_text();self.assertIn('WorkflowIDReusePolicy.REJECT_DUPLICATE',text);self.assertIn('WorkflowIDConflictPolicy.FAIL',text);self.assertIn('signal-trust',text)
    def test_receipt_fence_replays_same_build(self):
        m=load_support()
        with tempfile.TemporaryDirectory() as d:
            ex=m.ReceiptFencedArtifactExecutor(Path(d)/'state');req=ROOT/'artifact-delivery/examples/presentation-native-smoke-request-r1.json';v={'operationId':'test/build/same','request':{'path':str(req),'sha256':hashlib.sha256(req.read_bytes()).hexdigest()}};a=ex.build(v);b=ex.build(v);self.assertFalse(a['replayed']);self.assertTrue(b['replayed']);self.assertEqual(a['roles']['artifact']['sha256'],b['roles']['artifact']['sha256']);self.assertEqual(a['roles']['artifact']['path'],b['roles']['artifact']['path'])
    def test_receipt_fence_rejects_operation_id_collision(self):
        m=load_support()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ex=m.ReceiptFencedArtifactExecutor(root/'state');req=ROOT/'artifact-delivery/examples/presentation-native-smoke-request-r1.json';v={'operationId':'test/build/collision','request':{'path':str(req),'sha256':hashlib.sha256(req.read_bytes()).hexdigest()}};ex.build(v);copy=root/'different.json';copy.write_text(req.read_text().replace('presentation-native-smoke-r1','presentation-native-smoke-r2'));bad={'operationId':'test/build/collision','request':{'path':str(copy),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest()}}
            with self.assertRaisesRegex(RuntimeError,'different immutable inputs'):ex.build(bad)
    def test_cli_failure_diagnostics_preserve_stdout_only_structured_error(self):
        m=load_support()
        proc=subprocess.CompletedProcess([],1,stdout='{"status":"FAIL","failures":["Python jsonschema package is not installed"]}\n',stderr='')
        message=m.ReceiptFencedArtifactExecutor._cli_failure_message('build-request',proc)
        self.assertIn('exit=1',message)
        self.assertIn('stdout=',message)
        self.assertIn('jsonschema package is not installed',message)

    def test_launcher_rejects_secret_before_temporal_signal(self):
        m=load_support()
        with self.assertRaisesRegex(ValueError,'unsupported fields'):
            m.validate_public_trust_material_envelope({'trustPolicy':{},'bundles':{},'signerIds':{},'privateKey':'forbidden'})
        good={'trustPolicy':{'path':'/tmp/policy.json','sha256':'a'*64},'bundles':{'structural':{'path':'/tmp/structural.sigstore.json','sha256':'b'*64}},'signerIds':{'structural':'release-signer'}}
        self.assertIs(m.validate_public_trust_material_envelope(good),good)

    def test_abandoned_operation_without_receipt_is_rebuilt(self):
        m=load_support()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);state=root/'state';ex=m.ReceiptFencedArtifactExecutor(state);req=ROOT/'artifact-delivery/examples/presentation-native-smoke-request-r1.json';oid='test/build/abandoned';key=m._operation_key('build',oid);abandoned=state/'operations'/'build'/key;abandoned.mkdir(parents=True);(abandoned/'partial.bin').write_bytes(b'partial');value={'operationId':oid,'request':{'path':str(req),'sha256':hashlib.sha256(req.read_bytes()).hexdigest()}};result=ex.build(value);self.assertFalse(result['replayed']);self.assertFalse((abandoned/'partial.bin').exists());self.assertTrue((abandoned/'activity-receipt.json').is_file())

    def test_committed_output_drift_fails_closed(self):
        m=load_support()
        with tempfile.TemporaryDirectory() as d:
            ex=m.ReceiptFencedArtifactExecutor(Path(d)/'state');req=ROOT/'artifact-delivery/examples/presentation-native-smoke-request-r1.json';value={'operationId':'test/build/drift','request':{'path':str(req),'sha256':hashlib.sha256(req.read_bytes()).hexdigest()}};result=ex.build(value);artifact=Path(result['roles']['artifact']['path']);artifact.write_bytes(artifact.read_bytes()+b'drift')
            with self.assertRaisesRegex(RuntimeError,'committed operation output drift'):ex.build(value)

    def test_package_activity_uses_oci_layout_and_receipt_fences_every_blob(self):
        m=load_support()
        spec=importlib.util.spec_from_file_location('artifact_delivery',ROOT/'scripts/artifact_delivery.py'); ad=importlib.util.module_from_spec(spec); spec.loader.exec_module(ad)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); ex=m.ReceiptFencedArtifactExecutor(root/'state')
            profile=json.loads((ROOT/'artifact-delivery/examples/pdu-sdu-presentation-r1.json').read_text()); profile.pop('$schema',None); profile['id']='temporal-oci-package-test-r1'; profile.pop('companions',None)
            for gate in list(profile['gates']): profile['gates'][gate]=False
            for gate in ('profileSchema','structural','semantic'): profile['gates'][gate]=True
            profile_path=root/'profile.json'; profile_path.write_text(json.dumps(profile))
            pptx=root/'artifact.pptx'; built=ad.build_presentation_source(ROOT/'artifact-delivery/examples/presentation-native-smoke-source-r1.json',ROOT/'artifact-delivery/examples/pdu-sdu-presentation-r1.json',pptx); self.assertEqual(built['status'],'PASS')
            verify_dir=root/'verify'; verified=ad.execute_verify_stage(profile_path,pptx,verify_dir); self.assertTrue(verified['profileVerificationComplete'])
            report=root/'verify-stage.json'; ad.write_json(report,verified)
            fact=lambda q:{'path':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'name':q.name,'size':q.stat().st_size}
            value={'operationId':'test/package/oci','profile':fact(profile_path),'artifact':fact(pptx),'verifyReport':fact(report),'allowLocalUnsignedDevelopment':True}
            first=ex.package(value); second=ex.package(value)
            self.assertFalse(first['replayed']); self.assertTrue(second['replayed'])
            self.assertEqual(first['metadata']['trustStanding'],'LOCAL_UNSIGNED_DEVELOPMENT'); self.assertFalse(first['metadata']['releaseReady']); self.assertEqual(first['metadata']['referrerCount'],4)
            blob_roles=sorted(k for k in first['roles'] if k.startswith('ociBlob:')); self.assertTrue(blob_roles)
            self.assertIn('ociLayoutIndex',first['roles']); self.assertIn('ociLayoutMarker',first['roles'])
            package_root=Path(first['packageDirectory']).parent; self.assertFalse((package_root/'package-index.json').exists()); self.assertFalse((package_root/'release-manifest.json').exists())
            victim=Path(first['roles'][blob_roles[0]]['path']); victim.write_bytes(victim.read_bytes()+b'drift')
            with self.assertRaisesRegex(RuntimeError,'committed operation output drift'): ex.package(value)

    def test_deployment_is_main_source_fenced_and_hardened(self):
        deploy=(ROOT/'scripts/temporal_artifact_delivery_deploy.py').read_text();unit=(ROOT/'systemd/ordivon-artifact-temporal-worker.service').read_text();self.assertIn("MAIN=Path('/root/projects/ordivon-artifact-v2')",deploy);self.assertIn("main_source=ROOT.resolve()==MAIN.resolve()",deploy);self.assertIn("if not current['applyEligible']",deploy);self.assertIn('artifact_python_probe()',deploy);self.assertIn("artifact_python['ready']",deploy);self.assertIn('ProtectSystem=strict',unit);self.assertIn('NoNewPrivileges=true',unit);self.assertIn('ReadWritePaths=/root/.local/state/ordivon-workstation/artifact-delivery-temporal',unit)

    def test_trust_material_rejects_secret_fields(self):
        m=load_support()
        with tempfile.TemporaryDirectory() as d:
            ex=m.ReceiptFencedArtifactExecutor(Path(d)/'state')
            with self.assertRaisesRegex(RuntimeError,'unsupported fields'):ex._validate_trust_material({'trustPolicy':{},'bundles':{},'signerIds':{},'privateKey':'forbidden'})
if __name__=='__main__':unittest.main()
