
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

from artifact_verification.tool_identity import assess_native_tool_paths

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_software_release',ROOT/'scripts/artifact_software_release.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/software-release-oci-image-smoke-r1.json'
GO=Path('/opt/ordivon/external/go/1.26.6/bin/go')
NEGATIVE_FIXTURES=ROOT/'tests/fixtures/software-release'


def run(cmd,**kw): return subprocess.run(cmd,capture_output=True,**kw)
def build_layout(root:Path, *, stdout_text='ordivon-artifact-software-release-r1', secret=False, entrypoint='/app')->Path:
    src=root/'src'; src.mkdir()
    extra='\nvar embeddedSecret = "AKIAIOSFODNN7EXAMPLE"\n' if secret else ''
    (src/'main.go').write_text('package main\nimport "fmt"\n'+extra+'func main(){fmt.Println("'+stdout_text+'") }\n')
    env=os.environ.copy(); env.update({'GOROOT':'/opt/ordivon/external/go/1.26.6','PATH':'/opt/ordivon/external/go/1.26.6/bin:'+env['PATH'],'CGO_ENABLED':'0','GOOS':'linux','GOARCH':'amd64'})
    p=run([str(GO),'build','-trimpath','-ldflags=-s -w -buildid=','-o',str(src/'app'),str(src/'main.go')],env=env)
    if p.returncode: raise RuntimeError((p.stdout+p.stderr).decode())
    return package_layout(root, src, entrypoint=entrypoint)


def package_layout(root: Path, src: Path, *, entrypoint: str = "/app") -> Path:
    (src / "Containerfile").write_text(
        'FROM scratch\nCOPY app /app\nENTRYPOINT ["' + entrypoint + '"]\n'
    )
    tag = "localhost/ordivon/software-release-test:" + next(tempfile._get_candidate_names())
    p = run(["/usr/bin/podman", "build", "--network", "host", "--format", "oci",
             "--timestamp", "0", "-t", tag, "-f", str(src / "Containerfile"), str(src)])
    if p.returncode:
        raise RuntimeError((p.stdout + p.stderr).decode())
    try:
        layout = root / "oci"
        layout.mkdir()
        p = run(["/usr/bin/skopeo", "copy", "containers-storage:" + tag,
                 "oci:" + str(layout) + ":release"])
        if p.returncode:
            raise RuntimeError((p.stdout + p.stderr).decode())
        return layout
    finally:
        run(["/usr/bin/podman", "rmi", "-f", tag])



class SoftwareReleaseTests(unittest.TestCase):
    def require_tools(self, *, builder=True):
        tools = (MODULE.SKOPEO,MODULE.PODMAN,MODULE.SYFT,MODULE.TRIVY)
        for p in (*tools, GO) if builder else tools:
            if not p.is_file(): self.skipTest(f'missing tool {p}')

    @pytest.mark.integration
    def test_frozen_database_binding_matches(self):
        db = MODULE.TRIVY_DB_ROOT / "cache/db"
        if not (db / "trivy.db").is_file() or not (db / "metadata.json").is_file():
            self.skipTest("frozen Trivy database not materialized")
        b = json.loads((ROOT / "artifact-delivery/shadow-bindings/software-release-oci-image-local-r1.json").read_text())
        self.assertEqual(hashlib.sha256((db / "trivy.db").read_bytes()).hexdigest(),
                         b["bindings"]["security"]["dbSha256"])
        self.assertEqual(hashlib.sha256((db / "trivy.db").read_bytes()).hexdigest(),
                         MODULE.EXPECTED_DB_SHA)
        self.assertEqual(hashlib.sha256((db / "metadata.json").read_bytes()).hexdigest(),
                         MODULE.EXPECTED_DB_META_SHA)

    def assert_current_tool_identity(self, result):
        tools = result["tools"]
        self.assertEqual(set(tools), {"skopeo", "podman", "syft", "trivy"})
        assessment = assess_native_tool_paths({"tools": tools})
        self.assertEqual(assessment["status"], "OBSERVED_POSTRUN_CONSISTENT", assessment)
        self.assertFalse(assessment["dependenciesComplete"])
        tampered = {name: dict(fact) for name, fact in tools.items()}
        tampered["skopeo"]["sha256"] = "0" * 64
        self.assertTrue(assess_native_tool_paths({"tools": tampered})["rejected"])

    @pytest.mark.integration
    def test_valid_oci_release_passes(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); v=MODULE.verify_oci(layout,BASE,root/'e')
            self.assertEqual(v['status'],'PASS',v); self.assertEqual(v['vulnerabilityScan']['vulnerabilityCount'],0); self.assertEqual(v['secretScan']['secretCount'],0)
            self.assert_current_tool_identity(v)

    @pytest.mark.integration
    def test_valid_oci_does_not_launder_wrong_manifest_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); c=json.loads(BASE.read_text()); c['image']['manifestDigest']='sha256:'+'0'*64; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertIn('OCI manifest digest differs from object contract',v['failures'])

    @pytest.mark.integration
    def test_tampered_layer_fails_descriptor_integrity(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); idx=json.loads((layout/'index.json').read_text()); man=layout/'blobs/sha256'/idx['manifests'][0]['digest'].split(':')[1]; m=json.loads(man.read_text()); layer=layout/'blobs/sha256'/m['layers'][0]['digest'].split(':')[1]; data=bytearray(layer.read_bytes()); data[len(data)//2]^=0x55; layer.write_bytes(data); v=MODULE.verify_oci(layout,BASE,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertTrue(any('blob digest mismatch' in x for x in v['failures']),v)

    @pytest.mark.integration
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

    @pytest.mark.integration
    def test_vulnerable_go1265_fixture_fails_frozen_db_policy(self):
        self.require_tools(builder=False)
        # The immutable negative-control input deliberately retains old Go
        # bytes. Production Go may roll freely; never rebuild with /usr/bin/go.
        manifest = json.loads((NEGATIVE_FIXTURES / "go1265-negative.json").read_text())
        fixture = manifest["fixture"]
        compressed = (NEGATIVE_FIXTURES / fixture["file"]).read_bytes()
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), fixture["compressedSha256"])
        payload = gzip.decompress(compressed)
        self.assertEqual(len(payload), fixture["size"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), fixture["sha256"])
        source = manifest["source"]
        self.assertEqual(hashlib.sha256((NEGATIVE_FIXTURES / source["file"]).read_bytes()).hexdigest(),
                         source["sha256"])
        self.assertEqual(manifest["observedNegativeControl"]["dbSha256"], MODULE.EXPECTED_DB_SHA)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            src = root / "src"
            src.mkdir()
            app = src / "app"
            app.write_bytes(payload)
            app.chmod(0o755)
            layout = package_layout(root, src)
            c = json.loads(BASE.read_text())
            idx = json.loads((layout / "index.json").read_text())
            c["image"]["manifestDigest"] = idx["manifests"][0]["digest"]
            c["image"]["expectedFiles"][0]["sha256"] = fixture["sha256"]
            c["sbom"]["requiredPackages"][0]["version"] = manifest["build"]["goVersion"]
            cp = root / "contract.json"
            cp.write_text(json.dumps(c))
            v = MODULE.verify_oci(layout, cp, root / "evidence")
            self.assertEqual(v["status"], "FAIL", v)
            for gate in ("ociIdentity", "platformConfig", "rootfsReadback", "sbom",
                         "secretScan", "runtimeReadback"):
                self.assertEqual(v[gate]["status"], "PASS", (gate, v))
            self.assertGreater(v["vulnerabilityScan"]["vulnerabilityCount"], 0)
            self.assertEqual(v["failures"], ["vulnerability count exceeds object contract maximum"])
            self.assert_current_tool_identity(v)

    @pytest.mark.integration
    def test_runtime_mismatch_fails_after_static_gates_pass(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root,stdout_text='different-output'); c=json.loads(BASE.read_text()); idx=json.loads((layout/'index.json').read_text()); c['image']['manifestDigest']=idx['manifests'][0]['digest']; c['image']['expectedFiles'][0]['sha256']=hashlib.sha256((root/'src/app').read_bytes()).hexdigest(); c['sbom']['requiredPackages'][0]['version']='go1.26.6'; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertEqual(v['vulnerabilityScan']['status'],'PASS'); self.assertIn('runtime stdout differs from contract',v['failures'])

    @pytest.mark.integration
    def test_contract_rejects_non_linux_platform_before_external_evidence(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); layout=build_layout(root); c=json.loads(BASE.read_text()); c['image']['os']='windows'; cp=root/'c.json'; cp.write_text(json.dumps(c)); v=MODULE.verify_oci(layout,cp,root/'e')
            self.assertEqual(v['status'],'FAIL'); self.assertTrue(any('software-release contract schema invalid' in x for x in v['failures'])); self.assertNotIn('ociIdentity',v)

if __name__=='__main__': unittest.main()
