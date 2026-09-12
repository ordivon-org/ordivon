import hashlib,importlib.util,json,os,subprocess,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_software_release',ROOT/'scripts/artifact_software_release.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/software-release-oci-image-smoke-r1.json'
GO=Path('/opt/ordivon/external/go/1.26.6/bin/go')


def run(cmd,**kw): return subprocess.run(cmd,capture_output=True,**kw)
def build_layout(root:Path, *, stdout_text='ordivon-artifact-software-release-r1', secret=False, entrypoint='/app')->Path:
    src=root/'src'; src.mkdir()
    extra='\nvar embeddedSecret = "AKIAIOSFODNN7EXAMPLE"\n' if secret else ''
    (src/'main.go').write_text('package main\nimport "fmt"\n'+extra+'func main(){fmt.Println("'+stdout_text+'") }\n')
    env=os.environ.copy(); env.update({'GOROOT':'/opt/ordivon/external/go/1.26.6','PATH':'/opt/ordivon/external/go/1.26.6/bin:'+env['PATH'],'CGO_ENABLED':'0','GOOS':'linux','GOARCH':'amd64'})
    p=run([str(GO),'build','-trimpath','-ldflags=-s -w -buildid=','-o',str(src/'app'),str(src/'main.go')],env=env)
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode())
    ep=entrypoint
    (src/'Containerfile').write_text('FROM scratch\nCOPY app /app\nENTRYPOINT ["'+ep+'"]\n')
    tag='localhost/ordivon/software-release-test:'+next(tempfile._get_candidate_names())
    p=run(['/usr/bin/podman','build','--network','host','--format','oci','--timestamp','0','-t',tag,'-f',str(src/'Containerfile'),str(src)])
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode())
    layout=root/'oci'; layout.mkdir(); p=run(['/usr/bin/skopeo','copy','containers-storage:'+tag,'oci:'+str(layout)+':release'])
    run(['/usr/bin/podman','rmi','-f',tag])
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode())
    return layout


class SoftwareReleaseTests(unittest.TestCase):
    def require_tools(self):
        for p in (MODULE.SKOPEO,MODULE.PODMAN,MODULE.SYFT,MODULE.TRIVY,GO):
            if not p.is_file(): self.skipTest(f'missing tool {p}')

    def test_local_binding_digests_match(self):
        b=json.loads((ROOT/'artifact-delivery/shadow-bindings/software-release-oci-image-local-r1.json').read_text())
        checks=[('/usr/bin/skopeo',b['bindings']['ociTransport']['binarySha256']),('/usr/bin/podman',b['bindings']['runtimeReadback']['binarySha256']),('/usr/bin/syft',b['bindings']['sbom']['binarySha256']),('/usr/bin/trivy',b['bindings']['security']['binarySha256'])]
        for path,want in checks: self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),want,path)
        self.assertEqual(hashlib.sha256((MODULE.TRIVY_DB_ROOT/'cache/db/trivy.db').read_bytes()).hexdigest(),b['bindings']['security']['dbSha256'])

    def test_valid_oci_release_passes(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); v=MODULE.verify_oci(layout,BASE,root/'e')
            self.assertEqual(v['status'],'PASS',v); self.assertEqual(v['vulnerabilityScan']['vulnerabilityCount'],0); self.assertEqual(v['secretScan']['secretCount'],0)

    def test_valid_oci_does_not_launder_wrong_manifest_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); c=json.loads(BASE.read_text()); c['image']['manifestDigest']='sha256:'+'0'*64; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertIn('OCI manifest digest differs from object contract',v['failures'])

    def test_tampered_layer_fails_descriptor_integrity(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); idx=json.loads((layout/'index.json').read_text()); man=layout/'blobs/sha256'/idx['manifests'][0]['digest'].split(':')[1]; m=json.loads(man.read_text()); layer=layout/'blobs/sha256'/m['layers'][0]['digest'].split(':')[1]; data=bytearray(layer.read_bytes()); data[len(data)//2]^=0x55; layer.write_bytes(data); v=MODULE.verify_oci(layout,BASE,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertTrue(any('blob digest mismatch' in x for x in v['failures']),v)

    def test_wrong_entrypoint_contract_fails_config_even_if_image_valid(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); c=json.loads(BASE.read_text()); c['image']['entrypoint']=['/wrong']; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertIn('OCI entrypoint differs from contract',v['failures'])

    def test_synthetic_trivy_secret_report_exceeds_zero_policy(self):
        report={'Results':[{'Target':'fixture.txt','Secrets':[{'RuleID':'synthetic-rule'}]}]}
        count,failures=MODULE.scan_count_policy(report,'Secrets',0,'secret')
        self.assertEqual(count,1)
        self.assertEqual(failures,['secret count exceeds object contract maximum'])

    def test_vulnerable_go125_build_fails_frozen_db_policy(self):
        self.require_tools()
        # Current host Go 1.26.5 is intentionally retained as a negative-control builder; verifier itself does not build.
        host=Path('/usr/bin/go')
        if not host.is_file(): self.skipTest('host negative-control Go unavailable')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); src=root/'src'; src.mkdir(); (src/'main.go').write_text('package main\nimport "fmt"\nfunc main(){fmt.Println("ordivon-artifact-software-release-r1")}\n')
            env=os.environ.copy(); env.update({'CGO_ENABLED':'0','GOOS':'linux','GOARCH':'amd64'}); p=run([str(host),'build','-trimpath','-ldflags=-s -w -buildid=','-o',str(src/'app'),str(src/'main.go')],env=env); self.assertEqual(p.returncode,0,(p.stdout+p.stderr).decode())
            (src/'Containerfile').write_text('FROM scratch\nCOPY app /app\nENTRYPOINT ["/app"]\n'); tag='localhost/ordivon/software-release-test:oldgo-'+next(tempfile._get_candidate_names()); p=run(['/usr/bin/podman','build','--network','host','--format','oci','--timestamp','0','-t',tag,'-f',str(src/'Containerfile'),str(src)]); self.assertEqual(p.returncode,0,(p.stdout+p.stderr).decode()); layout=root/'oci'; layout.mkdir(); p=run(['/usr/bin/skopeo','copy','containers-storage:'+tag,'oci:'+str(layout)+':release']); run(['/usr/bin/podman','rmi','-f',tag]); self.assertEqual(p.returncode,0,(p.stdout+p.stderr).decode())
            c=json.loads(BASE.read_text()); idx=json.loads((layout/'index.json').read_text()); c['image']['manifestDigest']=idx['manifests'][0]['digest']; c['image']['expectedFiles'][0]['sha256']=hashlib.sha256((src/'app').read_bytes()).hexdigest(); c['sbom']['requiredPackages'][0]['version']='go1.26.5-X:nodwarf5'; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertGreater(v['vulnerabilityScan']['vulnerabilityCount'],0); self.assertIn('vulnerability count exceeds object contract maximum',v['failures'])

    def test_runtime_mismatch_fails_after_static_gates_pass(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root,stdout_text='different-output'); c=json.loads(BASE.read_text()); idx=json.loads((layout/'index.json').read_text()); c['image']['manifestDigest']=idx['manifests'][0]['digest']; c['image']['expectedFiles'][0]['sha256']=hashlib.sha256((root/'src/app').read_bytes()).hexdigest(); c['sbom']['requiredPackages'][0]['version']='go1.26.6'; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['vulnerabilityScan']['status'],'PASS'); self.assertIn('runtime stdout differs from contract',v['failures'])

    def test_contract_rejects_non_linux_platform_before_external_evidence(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); c=json.loads(BASE.read_text()); c['image']['os']='windows'; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertTrue(any('software-release contract schema invalid' in x for x in v['failures'])); self.assertNotIn('ociIdentity',v)

if __name__=='__main__': unittest.main()
