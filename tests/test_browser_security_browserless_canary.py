import unittest

from scripts.browser_security_browserless_canary import (
    CANARY_CONTAINER,
    CANARY_DISPLAY,
    CANARY_PORT,
    build_canary_podman_command,
    classify_canary_comparison,
    production_control_from_rows,
    validate_image_ref,
)


IMAGE_A = "ghcr.io/browserless/chromium@sha256:" + "a" * 64
IMAGE_B = "ghcr.io/browserless/chromium@sha256:" + "b" * 64


def row(instance: int, *, image: str = IMAGE_A, namespace: str = "nv2-browserless-prod", tz: str = "Asia/Shanghai"):
    return {
        "State": {"Running": True},
        "ImageName": image,
        "HostConfig": {"NetworkMode": f"ns:/run/netns/{namespace}"},
        "Config": {
            "Env": [
                "CONCURRENT=1",
                "QUEUED=8",
                "TIMEOUT=180000",
                "HEALTH=true",
                "MAX_CPU_PERCENT=90",
                "MAX_MEMORY_PERCENT=90",
                "DEBUG=-*",
                f"TZ={tz}",
                "XAUTHORITY=/run/ordivon-xauth",
                f"PORT=30{instance}",
                f"DISPLAY=:1{instance}",
                "TOKEN=redacted",
            ]
        },
    }


def comparison(*, families=None, detector_drift=None, network=False, browser=False, control=False, public=None):
    return {
        "rootCauseEstablished": False,
        "detectors": [
            {"detectorId": "cf04", "family": "CF04", "status": "UNCHANGED"}
        ],
        "detectorDrift": detector_drift or [],
        "changedFamilies": families or [],
        "publicObservationChanges": public or [],
        "challengeStandingChanged": False,
        "infrastructureChanges": {
            "browserBinary": browser,
            "controlLayer": control,
            "networkAuthority": network,
        },
    }


class BrowserSecurityBrowserlessCanaryTests(unittest.TestCase):
    def test_image_ref_requires_exact_digest(self) -> None:
        self.assertEqual(validate_image_ref(IMAGE_A), IMAGE_A)
        for value in ("browserless/chromium:latest", "ghcr.io/browserless/chromium:latest", "sha256:" + "a" * 64):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "exact"):
                validate_image_ref(value)

    def test_production_control_requires_three_running_consistent_carriers(self) -> None:
        value = production_control_from_rows({n: row(n) for n in (11, 12, 13)})
        self.assertEqual(value["image"], IMAGE_A)
        self.assertEqual(value["networkNamespace"], "nv2-browserless-prod")
        self.assertEqual(value["environment"]["TZ"], "Asia/Shanghai")
        with self.assertRaisesRegex(RuntimeError, "one immutable image"):
            production_control_from_rows({11: row(11), 12: row(12, image=IMAGE_B), 13: row(13)})
        with self.assertRaisesRegex(RuntimeError, "one Ordivon environment"):
            production_control_from_rows({11: row(11), 12: row(12, tz="UTC"), 13: row(13)})

    def test_same_image_control_requires_complete_reproducibility(self) -> None:
        stable = classify_canary_comparison(
            control_image=IMAGE_A, candidate_image=IMAGE_A, comparison=comparison()
        )
        self.assertEqual(stable["standing"], "PASS_CONTROL_REPRODUCIBLE")
        unstable = classify_canary_comparison(
            control_image=IMAGE_A,
            candidate_image=IMAGE_A,
            comparison=comparison(control=True),
        )
        self.assertEqual(unstable["standing"], "HOLD_CONTROL_NONREPRODUCIBLE")

    def test_changed_image_allows_identity_change_but_not_presentation_change(self) -> None:
        expected = classify_canary_comparison(
            control_image=IMAGE_A,
            candidate_image=IMAGE_B,
            comparison=comparison(browser=True, control=True),
        )
        self.assertEqual(expected["standing"], "PASS_EXPECTED_INFRASTRUCTURE_CHANGE")
        drift = classify_canary_comparison(
            control_image=IMAGE_A,
            candidate_image=IMAGE_B,
            comparison=comparison(families=["CF06"], browser=True, control=True),
        )
        self.assertEqual(drift["standing"], "HOLD_PRESENTATION_DRIFT")

    def test_detector_and_network_drift_fail_closed(self) -> None:
        detector = comparison(detector_drift=["cf04"])
        detector["detectors"][0]["status"] = "DETECTOR_DRIFT"
        self.assertEqual(
            classify_canary_comparison(
                control_image=IMAGE_A, candidate_image=IMAGE_B, comparison=detector
            )["standing"],
            "HOLD_DETECTOR_DRIFT",
        )
        self.assertEqual(
            classify_canary_comparison(
                control_image=IMAGE_A,
                candidate_image=IMAGE_B,
                comparison=comparison(network=True),
            )["standing"],
            "HOLD_NETWORK_AUTHORITY_DRIFT",
        )

    def test_canary_podman_command_is_isolated_and_never_pulls(self) -> None:
        env = {
            "CONCURRENT": "1",
            "QUEUED": "8",
            "TIMEOUT": "180000",
            "HEALTH": "true",
            "MAX_CPU_PERCENT": "90",
            "MAX_MEMORY_PERCENT": "90",
            "DEBUG": "-*",
            "TZ": "Asia/Shanghai",
            "XAUTHORITY": "/run/ordivon-xauth",
        }
        cmd = build_canary_podman_command(
            image=IMAGE_A, namespace="nv2-browserless-prod", environment=env
        )
        self.assertIn(CANARY_CONTAINER, cmd)
        self.assertIn(f"DISPLAY={CANARY_DISPLAY}", cmd)
        self.assertIn(f"PORT={CANARY_PORT}", cmd)
        self.assertIn("never", cmd)
        self.assertIn("ns:/run/netns/nv2-browserless-prod", cmd)
        self.assertIn("/run/ordivon/browserless-xauth/91:/run/ordivon-xauth:ro", cmd)
        self.assertNotIn("TOKEN=", " ".join(cmd))
        self.assertEqual(cmd[-1], IMAGE_A)


if __name__ == "__main__":
    unittest.main()
