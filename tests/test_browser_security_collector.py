import json
import os
import subprocess
import sys
import tempfile
import unittest

from ordivon_security_v2 import (
    BrowserSecurityWitnessBundle,
    build_browser_security_witness_bundle,
    compare_browser_security_bundles,
)

D_BROWSER = "sha256:" + "a" * 64


def reading(detector_id="browser-js", family="CF04", version="r1", observation=None):
    return {
        "detectorId": detector_id,
        "family": family,
        "detectorVersion": version,
        "coverage": "declared test coverage",
        "publicObservation": observation if observation is not None else {"webdriver": True},
    }


class BrowserSecurityWitnessCollectorTests(unittest.TestCase):
    def test_builder_canonicalizes_observation_and_infrastructure_digests(self) -> None:
        left = build_browser_security_witness_bundle(
            witness_id="w-1",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "browserless", "flags": ["--enable-automation"]},
            network_authority={"name": "browserless-prod", "generation": "g1"},
            readings=[reading(observation={"b": 2, "a": 1})],
            challenge_standing="CHALLENGE_GATED",
        )
        right = build_browser_security_witness_bundle(
            witness_id="w-2",
            browser_binary_digest=D_BROWSER,
            control_layer={"flags": ["--enable-automation"], "route": "browserless"},
            network_authority={"generation": "g1", "name": "browserless-prod"},
            readings=[reading(observation={"a": 1, "b": 2})],
            challenge_standing="CHALLENGE_GATED",
        )
        self.assertEqual(left.witness.control_layer_digest, right.witness.control_layer_digest)
        self.assertEqual(left.witness.network_authority_digest, right.witness.network_authority_digest)
        self.assertEqual(
            left.witness.observations[0].observation_digest,
            right.witness.observations[0].observation_digest,
        )

    def test_bundle_roundtrip_revalidates_public_observation_digest(self) -> None:
        bundle = build_browser_security_witness_bundle(
            witness_id="w-1",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "direct"},
            network_authority={"name": "browserless-prod"},
            readings=[reading(observation={"webdriver": False, "screen": [1440, 1000]})],
        )
        value = bundle.to_dict()
        parsed = BrowserSecurityWitnessBundle.from_dict(value)
        self.assertEqual(parsed.to_dict(), value)
        value["publicObservations"][0]["observation"]["webdriver"] = True
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            BrowserSecurityWitnessBundle.from_dict(value)

    def test_secret_shaped_fields_are_rejected_recursively(self) -> None:
        with self.assertRaisesRegex(ValueError, "sensitive field"):
            build_browser_security_witness_bundle(
                witness_id="w-1",
                browser_binary_digest=D_BROWSER,
                control_layer={"route": "browserless"},
                network_authority={"name": "browserless-prod"},
                readings=[reading(observation={"profile": {"cookieValue": "secret"}})],
            )

    def test_bundle_diff_reports_changed_public_paths_without_claiming_root_cause(self) -> None:
        baseline = build_browser_security_witness_bundle(
            witness_id="baseline",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "browserless"},
            network_authority={"name": "browserless-prod"},
            readings=[reading(observation={"webdriver": True, "window": {"innerWidth": 1288}})],
            challenge_standing="CHALLENGE_GATED",
        )
        candidate = build_browser_security_witness_bundle(
            witness_id="candidate",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "browserless"},
            network_authority={"name": "browserless-prod"},
            readings=[reading(observation={"webdriver": False, "window": {"innerWidth": 1050}})],
            challenge_standing="READY",
        )
        result = compare_browser_security_bundles(baseline, candidate)
        self.assertEqual(result["changedFamilies"], ["CF04"])
        self.assertEqual(
            result["publicObservationChanges"],
            [
                {
                    "detectorId": "browser-js",
                    "changedPaths": ["$.webdriver", "$.window.innerWidth"],
                }
            ],
        )
        self.assertTrue(result["challengeStandingChanged"])
        self.assertFalse(result["rootCauseEstablished"])

    def test_build_and_compare_cli_roundtrip(self) -> None:
        manifest = {
            "schemaVersion": 1,
            "witnessId": "cli-witness",
            "browserBinaryDigest": D_BROWSER,
            "controlLayer": {"route": "browserless"},
            "networkAuthority": {"name": "browserless-prod"},
            "readings": [reading(observation={"webdriver": True})],
            "challengeStanding": "CHALLENGE_GATED",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.abspath(tmp)
            source = os.path.join(root, "manifest.json")
            built = os.path.join(root, "bundle.json")
            with open(source, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle)
            env = {**os.environ, "PYTHONPATH": "src"}
            subprocess.run(
                [sys.executable, "scripts/build_browser_security_witness.py", source, "--output", built],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            with open(built, encoding="utf-8") as handle:
                value = json.load(handle)
            self.assertEqual(value["witness"]["witnessId"], "cli-witness")
            proc = subprocess.run(
                [sys.executable, "scripts/compare_browser_security_bundles.py", built, built],
                check=True,
                env=env,
                capture_output=True,
                text=True,
            )
            comparison = json.loads(proc.stdout)
            self.assertEqual(comparison["changedFamilies"], [])
            self.assertEqual(comparison["publicObservationChanges"], [])
            self.assertFalse(comparison["rootCauseEstablished"])

    def test_coverage_change_is_detector_drift_not_subject_drift(self) -> None:
        baseline = build_browser_security_witness_bundle(
            witness_id="baseline",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "browserless"},
            network_authority={"name": "browserless-prod"},
            readings=[reading(observation={"webdriver": True})],
        )
        changed = reading(observation={"webdriver": False})
        changed["coverage"] = "expanded coverage"
        candidate = build_browser_security_witness_bundle(
            witness_id="candidate",
            browser_binary_digest=D_BROWSER,
            control_layer={"route": "browserless"},
            network_authority={"name": "browserless-prod"},
            readings=[changed],
        )
        result = compare_browser_security_bundles(baseline, candidate)
        self.assertEqual(result["changedFamilies"], [])
        self.assertEqual(result["detectorDrift"], ["browser-js"])
        self.assertEqual(result["publicObservationChanges"], [])


if __name__ == "__main__":
    unittest.main()
