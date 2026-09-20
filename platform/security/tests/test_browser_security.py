import unittest

from ordivon_security_v2 import BrowserSecurityWitness, compare_browser_security_witnesses

D0 = "sha256:" + "0" * 64
D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64


def witness(*, obs_digest: str = D0, version: str = "r1", family: str = "CF06", oracle=False):
    return {
        "schemaVersion": 1,
        "witnessId": "w-1",
        "browserBinaryDigest": D1,
        "controlLayerDigest": D2,
        "networkAuthorityDigest": D3,
        "observations": [
            {
                "detectorId": "consistency",
                "family": family,
                "detectorVersion": version,
                "observationDigest": obs_digest,
                "coverage": "timezone/network/font/window consistency",
            }
        ],
        "challengeStanding": "CHALLENGE_GATED",
        "protectedChallengeUsedAsDetectorOracle": oracle,
    }


class BrowserSecurityWitnessTests(unittest.TestCase):
    def test_changed_family_routes_to_owner(self) -> None:
        baseline = BrowserSecurityWitness.from_dict(witness(obs_digest=D0))
        candidate = BrowserSecurityWitness.from_dict({**witness(obs_digest=D1), "witnessId": "w-2"})
        result = compare_browser_security_witnesses(baseline, candidate)
        self.assertEqual(result["changedFamilies"], ["CF06"])
        self.assertEqual(result["repairRoutes"], ["cross-layer-consistency"])
        self.assertFalse(result["rootCauseEstablished"])

    def test_detector_version_drift_is_not_subject_drift(self) -> None:
        baseline = BrowserSecurityWitness.from_dict(witness(version="r1", obs_digest=D0))
        candidate = BrowserSecurityWitness.from_dict(
            {**witness(version="r2", obs_digest=D1), "witnessId": "w-2"}
        )
        result = compare_browser_security_witnesses(baseline, candidate)
        self.assertEqual(result["changedFamilies"], [])
        self.assertEqual(result["detectorDrift"], ["consistency"])
        self.assertEqual(result["detectors"][0]["status"], "DETECTOR_DRIFT")

    def test_protected_challenge_cannot_be_detector_oracle(self) -> None:
        with self.assertRaisesRegex(ValueError, "detector oracle"):
            BrowserSecurityWitness.from_dict(witness(oracle=True))

    def test_unknown_family_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            BrowserSecurityWitness.from_dict(witness(family="CF99"))

    def test_extra_detector_fields_rejected(self) -> None:
        value = witness()
        value["observations"][0]["cookieValue"] = "must-not-enter-witness"
        with self.assertRaisesRegex(ValueError, "canonical fields"):
            BrowserSecurityWitness.from_dict(value)


if __name__ == "__main__":
    unittest.main()
