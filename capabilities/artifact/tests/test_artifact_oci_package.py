import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

import artifact_trust.vsa as trust_vsa
from artifact_core.contracts import sha256_file

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_oci_package", ROOT / "scripts/artifact_oci_package.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

DELIVERY_SPEC = importlib.util.spec_from_file_location("artifact_delivery_fixture", ROOT / "scripts/artifact_delivery.py")
DELIVERY = importlib.util.module_from_spec(DELIVERY_SPEC)
assert DELIVERY_SPEC.loader is not None
DELIVERY_SPEC.loader.exec_module(DELIVERY)


class ArtifactOciPackageTests(unittest.TestCase):
    def _profile_and_verified_artifact(self, root: Path):
        profile = json.loads((ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json").read_text())
        profile.pop("$schema", None)
        profile["id"] = "presentation-oci-package-test-r1"
        profile.pop("companions", None)
        for gate in list(profile["gates"]):
            profile["gates"][gate] = False
        for gate in ("profileSchema", "structural", "semantic"):
            profile["gates"][gate] = True
        profile_path = root / "profile.json"
        profile_path.write_text(json.dumps(profile))
        pptx = root / "artifact.pptx"
        built = DELIVERY.build_presentation_source(
            ROOT / "artifact-delivery/examples/presentation-native-smoke-source-r1.json",
            ROOT / "artifact-delivery/examples/pdu-sdu-presentation-r1.json",
            pptx,
        )
        self.assertEqual(built["status"], "PASS", built)
        verify_dir = root / "verify"
        verified = DELIVERY.execute_verify_stage(profile_path, pptx, verify_dir)
        self.assertEqual(verified["status"], "PASS", verified)
        self.assertTrue(verified["profileVerificationComplete"], verified)
        report = root / "verify-stage.json"
        DELIVERY.write_json(report, verified)
        return profile_path, pptx, report, verified

    def test_local_unsigned_uses_oci_layout_and_referrers_without_legacy_package_manifest(self):
        if not MODULE.DEFAULT_ORAS.is_file():
            self.skipTest("ORAS global carrier is unavailable")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, pptx, report, _ = self._profile_and_verified_artifact(root)
            package = root / "package"
            result = MODULE.execute_oci_package_stage(
                profile, pptx, report, package, allow_local_unsigned=True
            )
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["trustStanding"], "LOCAL_UNSIGNED_DEVELOPMENT")
            self.assertFalse(result["releaseReady"])
            self.assertFalse(result["releasePolicy"]["ready"])
            self.assertTrue(result["releasePolicy"]["input"]["local_unsigned"])
            self.assertEqual(result["releasePolicy"]["tool"]["sha256"], "ae0171e1b8cfed38f39c435660924c06a313868dd5d34bf5f5869d6dbe78d21b")
            self.assertEqual(result["oci"]["subject"]["artifactType"], MODULE.RELEASE_ARTIFACT_TYPE)
            self.assertEqual(len(result["oci"]["discover"]["referrers"]), 4)
            self.assertEqual(result["oci"]["manifest"]["layers"][0]["digest"], "sha256:" + hashlib.sha256(pptx.read_bytes()).hexdigest())
            self.assertTrue((package / "layout/index.json").is_file())
            self.assertTrue((package / "layout/oci-layout").is_file())
            self.assertFalse((package / "package-index.json").exists())
            self.assertFalse((package / "release-manifest.json").exists())
            self.assertFalse((package / ".staging").exists())

    def _cosign_material(self, root: Path):
        tool = trust_vsa.cosign_tool_fact()
        if tool.get("status") != "PASS":
            self.skipTest("cosign is not available")
        cosign = Path(tool["path"])
        password = "artifact-e2e-test-only-password"
        env = dict(os.environ)
        env["COSIGN_PASSWORD"] = password
        key_prefix = root / "trusted-signer"
        proc = subprocess.run(
            [str(cosign), "generate-key-pair", "--output-key-prefix", str(key_prefix)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        private_key = Path(str(key_prefix) + ".key")
        public_key = Path(str(key_prefix) + ".pub")
        policy = {
            "policyVersion": 1,
            "id": "test-vsa-trust-r1",
            "acceptedBundleMediaTypes": [trust_vsa.SIGSTORE_BUNDLE_V03],
            "signers": [{
                "id": "release-signer",
                "mode": "public-key",
                "allowedVerifierIds": [trust_vsa.LOCAL_VSA_VERIFIER_ID],
                "requireTransparencyLog": False,
                "publicKey": {"path": public_key.name, "sha256": sha256_file(public_key)},
            }],
        }
        policy_path = root / "vsa-trust-policy.json"
        policy_path.write_text(json.dumps(policy))
        signing_config = root / "private-signing-config.json"
        signing_config.write_text(json.dumps({
            "mediaType": "application/vnd.dev.sigstore.signingconfig.v0.2+json",
            "caUrls": [], "oidcUrls": [], "rekorTlogUrls": [], "tsaUrls": [],
        }))
        return cosign, private_key, policy_path, signing_config, env

    def _sign_vsa(self, cosign: Path, subject: Path, statement: Path, bundle: Path, private_key: Path, signing_config: Path, env):
        proc = subprocess.run(
            [str(cosign), "attest-blob", "--yes", "--signing-config", str(signing_config),
             "--key", str(private_key), "--statement", str(statement), "--bundle", str(bundle), str(subject)],
            env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(bundle.read_text())
        self.assertEqual(value["mediaType"], trust_vsa.SIGSTORE_BUNDLE_V03)

    def test_signed_vsa_package_is_release_ready_and_bundles_are_oci_referrer_layers(self):
        if not MODULE.DEFAULT_ORAS.is_file():
            self.skipTest("ORAS global carrier is unavailable")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, pptx, report, verified = self._profile_and_verified_artifact(root)
            cosign, private_key, policy_path, signing_config, env = self._cosign_material(root)
            bundles = {}
            signers = {}
            for gate, receipt in sorted(verified["receipts"].items()):
                bundle = root / f"{gate}.sigstore.json"
                self._sign_vsa(
                    cosign, pptx, Path(receipt["vsa"]["path"]), bundle,
                    private_key, signing_config, env,
                )
                bundles[gate] = bundle
                signers[gate] = "release-signer"
            package = root / "package"
            result = MODULE.execute_oci_package_stage(
                profile, pptx, report, package,
                allow_local_unsigned=False,
                gate_bundles=bundles,
                trust_policy_path=policy_path,
                signer_ids=signers,
            )
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["trustStanding"], "CRYPTOGRAPHICALLY_VERIFIED")
            self.assertTrue(result["releaseReady"], result)
            self.assertTrue(result["releasePolicy"]["ready"], result["releasePolicy"])
            self.assertEqual(result["releasePolicy"]["input"]["trust_standing"], "CRYPTOGRAPHICALLY_VERIFIED")
            self.assertEqual(result["unresolvedAssemblyGates"], [])
            refs = result["oci"]["discover"]["referrers"]
            gate_refs = [r for r in refs if r.get("artifactType") == MODULE.GATE_ARTIFACT_TYPE]
            self.assertEqual(len(gate_refs), 3)
            for ref in gate_refs:
                manifest = MODULE.run_oras(
                    ["manifest", "fetch", "--oci-layout", f"{(package / 'layout').resolve()}@{ref['digest']}"],
                    cwd=root,
                )
                self.assertEqual(len(manifest["layers"]), 3)
                titles = {x["annotations"]["org.opencontainers.image.title"] for x in manifest["layers"]}
                self.assertEqual(titles, {"raw-evidence.json", "verification-summary.json", "sigstore-bundle.json"})

    def test_opa_release_policy_fails_closed_when_required_fact_is_missing(self):
        base = {
            "package_status": "PASS",
            "local_unsigned": False,
            "trust_standing": "CRYPTOGRAPHICALLY_VERIFIED",
            "subject": {"digest": "sha256:" + "a" * 64},
            "profile": {"id": "test", "sha256": "b" * 64},
            "verification": {"required_gates": ["structural", "semantic"], "passed_gates": ["structural", "semantic"]},
            "assembly": {"required_gates": ["companionPdf"], "satisfied_gates": ["companionPdf"]},
        }
        self.assertTrue(MODULE.evaluate_release_policy(base)["ready"])
        missing_verification = json.loads(json.dumps(base)); missing_verification["verification"]["passed_gates"].remove("semantic")
        self.assertFalse(MODULE.evaluate_release_policy(missing_verification)["ready"])
        missing_assembly = json.loads(json.dumps(base)); missing_assembly["assembly"]["satisfied_gates"] = []
        self.assertFalse(MODULE.evaluate_release_policy(missing_assembly)["ready"])
        local_unsigned = json.loads(json.dumps(base)); local_unsigned["local_unsigned"] = True; local_unsigned["trust_standing"] = "LOCAL_UNSIGNED_DEVELOPMENT"
        self.assertFalse(MODULE.evaluate_release_policy(local_unsigned)["ready"])

    def test_evidence_drift_fails_before_oci_layout_creation(self):
        if not MODULE.DEFAULT_ORAS.is_file():
            self.skipTest("ORAS global carrier is unavailable")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            profile, pptx, report, verified = self._profile_and_verified_artifact(root)
            raw = Path(verified["receipts"]["structural"]["rawEvidence"]["path"])
            raw.write_text(raw.read_text() + " ")
            package = root / "package"
            result = MODULE.execute_oci_package_stage(
                profile, pptx, report, package, allow_local_unsigned=True
            )
            self.assertEqual(result["status"], "FAIL", result)
            self.assertFalse(result["packageCreated"])
            self.assertFalse(package.exists())
            self.assertIn("raw evidence file fact failed: structural", result["failures"])


if __name__ == "__main__":
    unittest.main()
