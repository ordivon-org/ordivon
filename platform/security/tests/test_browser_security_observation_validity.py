import unittest

from ordivon_security_v2 import (
    build_browser_security_witness_bundle,
    classify_browser_security_observation_validity,
    compare_browser_security_bundles,
    compare_browser_security_pool,
)


D_BROWSER = "sha256:" + "a" * 64


def bundle(
    witness_id: str,
    *,
    cf02=None,
    cf06=None,
):
    if cf02 is None:
        cf02 = {
            "standing": "OBSERVED",
            "httpVersion": "h2",
            "ja4": "stable-ja4",
            "peetprintHash": "stable-peet",
            "http2AkamaiFingerprintHash": "stable-h2",
            "tlsVersionNegotiated": "772",
        }
    if cf06 is None:
        cf06 = {
            "network": {
                "loc": "KR",
                "colo": "ICN",
                "http": "http/2",
                "tls": "TLSv1.3",
                "warp": "off",
                "observer": "python-urllib",
            },
            "browser": {"timezone": "Asia/Shanghai"},
            "fontResolution": {"Arial": "Liberation Sans"},
        }
    return build_browser_security_witness_bundle(
        witness_id=witness_id,
        browser_binary_digest=D_BROWSER,
        control_layer={"routeFamily": "browserless/chromium"},
        network_authority={
            "kind": "network-v2",
            "generationDigest": "sha256:" + "b" * 64,
        },
        readings=[
            {
                "detectorId": "cf02-transport-normalized",
                "family": "CF02",
                "detectorVersion": "harness-browser-security-r2",
                "coverage": "browser TLS/HTTP2 normalized fields",
                "publicObservation": cf02,
            },
            {
                "detectorId": "cf06-cross-layer-consistency",
                "family": "CF06",
                "detectorVersion": "harness-browser-security-r2",
                "coverage": "network/browser/font cross-layer consistency",
                "publicObservation": cf06,
            },
        ],
    )


class BrowserSecurityObservationValidityTests(unittest.TestCase):
    def test_valid_observation_has_no_validity_issues(self) -> None:
        value = classify_browser_security_observation_validity(
            {"standing": "OBSERVED", "value": 1}
        )
        self.assertEqual(value, {"standing": "VALID", "issues": []})

    def test_unavailable_external_observer_is_not_subject_evidence(self) -> None:
        value = classify_browser_security_observation_validity(
            {"standing": "UNAVAILABLE", "detail": "URLError"}
        )
        self.assertEqual(value["standing"], "OBSERVER_UNAVAILABLE")
        self.assertEqual(value["issues"][0]["path"], "$")
        self.assertEqual(value["issues"][0]["detail"], "URLError")

    def test_nested_network_observer_unavailable_suppresses_cf06_subject_drift(self) -> None:
        baseline = bundle("baseline")
        candidate = bundle(
            "candidate",
            cf06={
                "network": {"standing": "UNAVAILABLE", "detail": "URLError"},
                "browser": {"timezone": "Asia/Shanghai"},
                "fontResolution": {"Arial": "Liberation Sans"},
            },
        )
        result = compare_browser_security_bundles(baseline, candidate)
        self.assertEqual(result["changedFamilies"], [])
        self.assertEqual(
            result["invalidObservationDetectors"],
            ["cf06-cross-layer-consistency"],
        )
        self.assertTrue(result["observationClassificationSuppressed"])
        row = next(
            row
            for row in result["detectors"]
            if row["detectorId"] == "cf06-cross-layer-consistency"
        )
        self.assertEqual(row["status"], "OBSERVATION_INVALID")
        self.assertEqual(result["publicObservationChanges"], [])

    def test_cf02_unavailable_is_not_reported_as_transport_subject_drift(self) -> None:
        baseline = bundle("baseline")
        candidate = bundle(
            "candidate",
            cf02={"standing": "UNAVAILABLE", "detail": "Error"},
        )
        result = compare_browser_security_bundles(baseline, candidate)
        self.assertEqual(result["changedFamilies"], [])
        self.assertEqual(
            result["invalidObservationDetectors"],
            ["cf02-transport-normalized"],
        )
        self.assertEqual(result["repairRoutes"], [])

    def test_pool_suppresses_subject_classification_when_observer_is_unavailable(self) -> None:
        pairs = {}
        for carrier in ("chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13"):
            pairs[carrier] = (
                bundle(f"{carrier}-baseline"),
                bundle(
                    f"{carrier}-candidate",
                    cf02={"standing": "UNAVAILABLE", "detail": "Error"},
                    cf06={
                        "network": {
                            "standing": "UNAVAILABLE",
                            "detail": "URLError",
                        },
                        "browser": {"timezone": "Asia/Shanghai"},
                        "fontResolution": {"Arial": "Liberation Sans"},
                    },
                ),
            )
        result = compare_browser_security_pool(pairs)
        self.assertEqual(result["standing"], "OBSERVATION_INVALID")
        self.assertTrue(result["subjectClassificationSuppressed"])
        self.assertEqual(result["sharedChangedFamilies"], [])
        self.assertEqual(result["sharedInfrastructureChanges"], [])
        self.assertEqual(result["repairRoutes"], ["observation-validity"])
        self.assertEqual(set(result["observationInvalidCarriers"]), set(pairs))
        self.assertFalse(result["rootCauseEstablished"])

    def test_one_invalid_carrier_suppresses_pool_classification(self) -> None:
        pairs = {
            "chatgpt-carrier-11": (bundle("11-b"), bundle("11-c")),
            "chatgpt-carrier-12": (
                bundle("12-b"),
                bundle(
                    "12-c",
                    cf06={
                        "network": {
                            "standing": "UNAVAILABLE",
                            "detail": "TimeoutError",
                        },
                        "browser": {"timezone": "Asia/Shanghai"},
                        "fontResolution": {"Arial": "Liberation Sans"},
                    },
                ),
            ),
            "chatgpt-carrier-13": (bundle("13-b"), bundle("13-c")),
        }
        result = compare_browser_security_pool(pairs)
        self.assertEqual(result["standing"], "OBSERVATION_INVALID")
        self.assertEqual(
            result["observationInvalidCarriers"],
            {"chatgpt-carrier-12": ["cf06-cross-layer-consistency"]},
        )

    def test_valid_subject_change_keeps_existing_drift_semantics(self) -> None:
        baseline = bundle("baseline")
        candidate = bundle(
            "candidate",
            cf06={
                "network": {
                    "loc": "US",
                    "colo": "SJC",
                    "http": "http/2",
                    "tls": "TLSv1.3",
                    "warp": "off",
                    "observer": "python-urllib",
                },
                "browser": {"timezone": "Asia/Shanghai"},
                "fontResolution": {"Arial": "Liberation Sans"},
            },
        )
        result = compare_browser_security_bundles(baseline, candidate)
        self.assertEqual(result["changedFamilies"], ["CF06"])
        self.assertEqual(result["invalidObservationDetectors"], [])
        self.assertFalse(result["observationClassificationSuppressed"])


if __name__ == "__main__":
    unittest.main()
