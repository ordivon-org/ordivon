import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ordivon_security_v2 import (
    build_browser_security_witness_bundle,
    compare_browser_security_pool,
)
from scripts import promote_browser_security_pool_lkg as reseal

HARNESS = "1" * 40
SECURITY = "2" * 40
NETWORK = "sha256:" + "3" * 64
BROWSER_OLD = "sha256:" + "4" * 64
BROWSER_NEW = "sha256:" + "5" * 64


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(carrier: str, *, browser=BROWSER_OLD, public_value="stable", control_version="old"):
    return {
        "schemaVersion": 1,
        "witnessId": f"{carrier}-{control_version}",
        "browserBinaryDigest": browser,
        "controlLayer": {
            "endpointId": carrier,
            "routeFamily": "browserless/chromium",
            "browserVersion": control_version,
        },
        "networkAuthority": {
            "kind": "network-v2",
            "name": "browserless-prod",
            "generationDigest": NETWORK,
            "serviceUnit": "network-v2-browserless.target",
        },
        "readings": [
            {
                "detectorId": "cf04-browser-js-presentation",
                "family": "CF04",
                "detectorVersion": "harness-browser-security-r2",
                "coverage": "test browser presentation",
                "publicObservation": {"value": public_value},
            }
        ],
        "challengeStanding": None,
    }


def bundle(value):
    return build_browser_security_witness_bundle(
        witness_id=value["witnessId"],
        browser_binary_digest=value["browserBinaryDigest"],
        control_layer=value["controlLayer"],
        network_authority=value["networkAuthority"],
        readings=value["readings"],
        challenge_standing=value["challengeStanding"],
    ).to_dict()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


class BrowserSecurityLkgResealTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fixture = self.root / "fixtures/browser-security"
        self.index = self.fixture / "harness-r2-live-lkg-pool-index.json"
        self.run_root = self.root / "run"
        self.run_root.mkdir()
        self.carriers = [f"chatgpt-carrier-{n}" for n in (11, 12, 13)]
        self.old_manifests = {carrier: manifest(carrier) for carrier in self.carriers}
        rows = []
        for carrier in self.carriers:
            suffix = carrier.rsplit("-", 1)[-1]
            mp = self.fixture / f"harness-r2-live-lkg-carrier{suffix}-manifest.json"
            bp = self.fixture / f"harness-r2-live-lkg-carrier{suffix}-bundle.json"
            write_json(mp, self.old_manifests[carrier])
            write_json(bp, bundle(self.old_manifests[carrier]))
            rows.append(
                {
                    "browserBinaryDigest": BROWSER_OLD,
                    "bundle": str(bp.relative_to(self.root)),
                    "bundleSha256": sha(bp),
                    "carrierId": carrier,
                    "challengeStanding": None,
                    "controlLayerEndpointId": carrier,
                    "detectorVersion": "harness-browser-security-r2",
                    "manifest": str(mp.relative_to(self.root)),
                    "manifestSha256": sha(mp),
                    "networkAuthority": self.old_manifests[carrier]["networkAuthority"],
                    "witnessId": self.old_manifests[carrier]["witnessId"],
                }
            )
        write_json(
            self.index,
            {
                "schemaVersion": 1,
                "kind": "ordivon.browser-security-pool-lkg-index",
                "poolId": "browserless-prod-r2-test",
                "standing": "LKG_PER_CARRIER",
                "comparisonLaw": {
                    "sameCarrierCandidateVsSameCarrierLkg": "ALLOWED",
                    "crossCarrierAsSubjectDrift": "FORBIDDEN",
                    "crossCarrierUse": "DESCRIPTIVE_DIFFERENTIAL_ONLY",
                },
                "carriers": rows,
            },
        )
        self.patchers = [
            mock.patch.object(reseal, "ROOT", self.root),
            mock.patch.object(reseal, "FIXTURE_ROOT", self.fixture),
            mock.patch.object(reseal, "POOL_INDEX", self.index),
            mock.patch.object(reseal, "_current_revision", return_value=SECURITY),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.tmp.cleanup()

    def write_run(self, *, browser=BROWSER_NEW, public_value="stable", control_version="new"):
        evidence = []
        pairs = {}
        for carrier in self.carriers:
            candidate = manifest(
                carrier,
                browser=browser,
                public_value=public_value,
                control_version=control_version,
            )
            mp = self.run_root / f"{carrier}-candidate-manifest.json"
            bp = self.run_root / f"{carrier}-candidate-bundle.json"
            write_json(mp, candidate)
            write_json(bp, bundle(candidate))
            evidence.append(
                {
                    "carrierId": carrier,
                    "baselineBundleSha256": "sha256:" + "0" * 64,
                    "candidateManifestSha256": sha(mp),
                    "candidateBundleSha256": sha(bp),
                }
            )
            old_bundle = build_browser_security_witness_bundle(
                witness_id=self.old_manifests[carrier]["witnessId"],
                browser_binary_digest=self.old_manifests[carrier]["browserBinaryDigest"],
                control_layer=self.old_manifests[carrier]["controlLayer"],
                network_authority=self.old_manifests[carrier]["networkAuthority"],
                readings=self.old_manifests[carrier]["readings"],
                challenge_standing=None,
            )
            new_bundle = build_browser_security_witness_bundle(
                witness_id=candidate["witnessId"],
                browser_binary_digest=candidate["browserBinaryDigest"],
                control_layer=candidate["controlLayer"],
                network_authority=candidate["networkAuthority"],
                readings=candidate["readings"],
                challenge_standing=None,
            )
            pairs[carrier] = (old_bundle, new_bundle)
        classification = compare_browser_security_pool(pairs)
        write_json(
            self.run_root / "pool-run-receipt.json",
            {
                "schemaVersion": 1,
                "kind": "ordivon.browser-security-pool-run",
                "runId": "test-run",
                "poolId": "browserless-prod-r2-test",
                "poolIndexSha256": sha(self.index),
                "harnessRevision": HARNESS,
                "securityRevision": SECURITY,
                "carrierEvidence": evidence,
                "classification": classification,
                "providerChallengeVisited": False,
                "providerSendAttempted": False,
            },
        )
        return classification

    def test_reseal_accepts_shared_browser_control_infrastructure_only(self):
        classification = self.write_run()
        self.assertEqual(classification["standing"], "GLOBAL_DRIFT")
        self.assertEqual(
            classification["sharedInfrastructureChanges"], ["browserBinary", "controlLayer"]
        )
        old_sha = sha(self.index)
        result = reseal.reseal(
            self.run_root,
            expected_harness_revision=HARNESS,
            expected_old_index_sha256=old_sha,
            fixture_root=self.fixture,
            index_path=self.index,
        )
        self.assertEqual(result["standing"], "LKG_RESEALED_PENDING_COMMIT")
        self.assertNotEqual(result["newPoolIndexSha256"], old_sha)
        new_index = json.loads(self.index.read_text())
        self.assertEqual(new_index["reseal"]["previousPoolIndexSha256"], old_sha)
        self.assertEqual(new_index["reseal"]["observedStanding"], "GLOBAL_DRIFT")
        self.assertEqual(len(new_index["carriers"]), 3)
        self.assertTrue(all(row["browserBinaryDigest"] == BROWSER_NEW for row in new_index["carriers"]))

    def test_reseal_accepts_no_observed_drift_refresh(self):
        classification = self.write_run(
            browser=BROWSER_OLD, public_value="stable", control_version="old"
        )
        self.assertEqual(classification["standing"], "NO_OBSERVED_DRIFT")
        result = reseal.reseal(
            self.run_root,
            expected_harness_revision=HARNESS,
            expected_old_index_sha256=sha(self.index),
            fixture_root=self.fixture,
            index_path=self.index,
        )
        self.assertEqual(result["observedStanding"], "NO_OBSERVED_DRIFT")

    def test_reseal_rejects_subject_drift(self):
        classification = self.write_run(public_value="changed")
        self.assertEqual(classification["sharedChangedFamilies"], ["CF04"])
        with self.assertRaisesRegex(reseal.ResealError, "subject drift"):
            reseal.reseal(
                self.run_root,
                expected_harness_revision=HARNESS,
                expected_old_index_sha256=sha(self.index),
                fixture_root=self.fixture,
                index_path=self.index,
            )

    def test_reseal_rejects_tampered_candidate_bundle(self):
        self.write_run()
        path = self.run_root / "chatgpt-carrier-11-candidate-bundle.json"
        value = json.loads(path.read_text())
        value["witness"]["witnessId"] = "tampered"
        write_json(path, value)
        receipt = json.loads((self.run_root / "pool-run-receipt.json").read_text())
        for row in receipt["carrierEvidence"]:
            if row["carrierId"] == "chatgpt-carrier-11":
                row["candidateBundleSha256"] = sha(path)
        write_json(self.run_root / "pool-run-receipt.json", receipt)
        with self.assertRaisesRegex(reseal.ResealError, "does not equal Security-v2 rebuild"):
            reseal.reseal(
                self.run_root,
                expected_harness_revision=HARNESS,
                expected_old_index_sha256=sha(self.index),
                fixture_root=self.fixture,
                index_path=self.index,
            )

    def test_reseal_rejects_harness_classification_disagreement(self):
        self.write_run()
        path = self.run_root / "pool-run-receipt.json"
        value = json.loads(path.read_text())
        value["classification"]["standing"] = "NO_OBSERVED_DRIFT"
        write_json(path, value)
        with self.assertRaisesRegex(reseal.ResealError, "classification disagrees"):
            reseal.reseal(
                self.run_root,
                expected_harness_revision=HARNESS,
                expected_old_index_sha256=sha(self.index),
                fixture_root=self.fixture,
                index_path=self.index,
            )

    def test_reseal_rejects_stale_old_index_digest(self):
        self.write_run()
        with self.assertRaisesRegex(reseal.ResealError, "differs from expected old index"):
            reseal.reseal(
                self.run_root,
                expected_harness_revision=HARNESS,
                expected_old_index_sha256="sha256:" + "f" * 64,
                fixture_root=self.fixture,
                index_path=self.index,
            )


if __name__ == "__main__":
    unittest.main()
