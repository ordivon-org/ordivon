import json
import os
import subprocess
import sys
import tempfile
import unittest

from ordivon_security_v2 import build_browser_security_witness_bundle, compare_browser_security_pool

D_BROWSER = "sha256:" + "a" * 64
D_BROWSER_2 = "sha256:" + "b" * 64


def bundle(carrier: str, *, cf06=0, cf07=0, version="r1", browser_digest=D_BROWSER):
    return build_browser_security_witness_bundle(
        witness_id=f"{carrier}-{cf06}-{cf07}-{version}",
        browser_binary_digest=browser_digest,
        control_layer={"endpointId": carrier, "route": "browserless"},
        network_authority={"name": "browserless-prod", "generation": "g1"},
        readings=[
            {
                "detectorId": "cf06-cross-layer-consistency",
                "family": "CF06",
                "detectorVersion": version,
                "coverage": "cf06 test coverage",
                "publicObservation": {"geometryRevision": cf06},
            },
            {
                "detectorId": "cf07-profile-metadata",
                "family": "CF07",
                "detectorVersion": version,
                "coverage": "cf07 test coverage",
                "publicObservation": {"profileRevision": cf07},
            },
        ],
    )


def pool_pairs(changes=None):
    changes = changes or {}
    pairs = {}
    for carrier in ("chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13"):
        baseline = bundle(carrier)
        kwargs = changes.get(carrier, {})
        pairs[carrier] = (baseline, bundle(carrier, **kwargs))
    return pairs


class BrowserSecurityPoolDriftTests(unittest.TestCase):
    def test_no_observed_drift(self) -> None:
        result = compare_browser_security_pool(pool_pairs())
        self.assertEqual(result["standing"], "NO_OBSERVED_DRIFT")
        self.assertEqual(result["sharedChangedFamilies"], [])
        self.assertEqual(result["carrierLocalChangedFamilies"], {})
        self.assertFalse(result["subjectClassificationSuppressed"])

    def test_same_family_on_all_carriers_is_global_drift(self) -> None:
        result = compare_browser_security_pool(
            pool_pairs({carrier: {"cf06": 1} for carrier in ("chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13")})
        )
        self.assertEqual(result["standing"], "GLOBAL_DRIFT")
        self.assertEqual(result["sharedChangedFamilies"], ["CF06"])
        self.assertEqual(result["carrierLocalChangedFamilies"], {})
        self.assertEqual(result["sharedInfrastructureChanges"], [])

    def test_one_carrier_family_change_is_local_drift(self) -> None:
        result = compare_browser_security_pool(
            pool_pairs({"chatgpt-carrier-12": {"cf07": 1}})
        )
        self.assertEqual(result["standing"], "CARRIER_LOCAL_DRIFT")
        self.assertEqual(result["sharedChangedFamilies"], [])
        self.assertEqual(
            result["carrierLocalChangedFamilies"], {"chatgpt-carrier-12": ["CF07"]}
        )

    def test_shared_plus_local_is_mixed_drift(self) -> None:
        changes = {
            "chatgpt-carrier-11": {"cf06": 1},
            "chatgpt-carrier-12": {"cf06": 1, "cf07": 1},
            "chatgpt-carrier-13": {"cf06": 1},
        }
        result = compare_browser_security_pool(pool_pairs(changes))
        self.assertEqual(result["standing"], "MIXED_DRIFT")
        self.assertEqual(result["sharedChangedFamilies"], ["CF06"])
        self.assertEqual(
            result["carrierLocalChangedFamilies"], {"chatgpt-carrier-12": ["CF07"]}
        )

    def test_detector_drift_fails_closed_before_subject_classification(self) -> None:
        result = compare_browser_security_pool(
            pool_pairs({"chatgpt-carrier-12": {"cf07": 1, "version": "r2"}})
        )
        self.assertEqual(result["standing"], "DETECTOR_DRIFT")
        self.assertTrue(result["subjectClassificationSuppressed"])
        self.assertEqual(result["sharedChangedFamilies"], [])
        self.assertEqual(result["carrierLocalChangedFamilies"], {})
        self.assertEqual(result["detectorDriftCarriers"], ["chatgpt-carrier-12"])

    def test_shared_infrastructure_change_is_global_drift(self) -> None:
        result = compare_browser_security_pool(
            pool_pairs({carrier: {"browser_digest": D_BROWSER_2} for carrier in ("chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13")})
        )
        self.assertEqual(result["standing"], "GLOBAL_DRIFT")
        self.assertEqual(result["sharedInfrastructureChanges"], ["browserBinary"])
        self.assertEqual(result["carrierLocalInfrastructureChanges"], {})

    def test_cli_comparison_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.abspath(tmp)
            rows = []
            for carrier in ("chatgpt-carrier-11", "chatgpt-carrier-12"):
                baseline_path = os.path.join(root, f"{carrier}-baseline.json")
                candidate_path = os.path.join(root, f"{carrier}-candidate.json")
                with open(baseline_path, "w", encoding="utf-8") as handle:
                    json.dump(bundle(carrier).to_dict(), handle)
                with open(candidate_path, "w", encoding="utf-8") as handle:
                    json.dump(bundle(carrier).to_dict(), handle)
                rows.append(
                    {
                        "carrierId": carrier,
                        "baselineBundle": os.path.basename(baseline_path),
                        "candidateBundle": os.path.basename(candidate_path),
                    }
                )
            manifest = os.path.join(root, "pool-comparison.json")
            with open(manifest, "w", encoding="utf-8") as handle:
                json.dump({"schemaVersion": 1, "carriers": rows}, handle)
            env = {**os.environ, "PYTHONPATH": "src"}
            proc = subprocess.run(
                [sys.executable, "scripts/compare_browser_security_pool.py", manifest],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["standing"], "NO_OBSERVED_DRIFT")
            self.assertEqual(result["carrierIds"], ["chatgpt-carrier-11", "chatgpt-carrier-12"])


if __name__ == "__main__":
    unittest.main()
