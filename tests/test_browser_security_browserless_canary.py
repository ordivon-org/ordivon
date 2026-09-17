import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.browser_security_browserless_canary as canary

from scripts.browser_security_browserless_canary import (
    CANARY_CONTAINER,
    CANARY_DISPLAY,
    CANARY_PORT,
    build_canary_podman_command,
    classify_canary_comparison,
    production_control_from_quadlet,
    validate_image_ref,
)


IMAGE_A = "ghcr.io/browserless/chromium@sha256:" + "a" * 64
IMAGE_B = "ghcr.io/browserless/chromium@sha256:" + "b" * 64


def installed_quadlet(image: str = IMAGE_A, *, tz: str = "Asia/Shanghai") -> str:
    return "\n".join(
        [
            "[Container]",
            f"Image={image}",
            "Network=ns:/run/netns/nv2-browserless-prod",
            "Environment=CONCURRENT=1",
            "Environment=QUEUED=8",
            "Environment=TIMEOUT=180000",
            "Environment=HEALTH=true",
            "Environment=MAX_CPU_PERCENT=90",
            "Environment=MAX_MEMORY_PERCENT=90",
            "Environment=DEBUG=-*",
            f"Environment=TZ={tz}",
            "Environment=XAUTHORITY=/run/ordivon-xauth",
            "Environment=DISPLAY=:1%i",
            "Environment=PORT=30%i",
            "",
        ]
    )


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

    def test_production_control_allows_sleeping_on_demand_carriers(self) -> None:
        value = production_control_from_quadlet(installed_quadlet(), {11: row(11)})
        self.assertEqual(value["image"], IMAGE_A)
        self.assertEqual(value["networkNamespace"], "nv2-browserless-prod")
        self.assertEqual(value["environment"]["TZ"], "Asia/Shanghai")
        self.assertEqual(value["activeInstances"], [11])
        self.assertEqual(value["inactiveInstances"], [12, 13])
        self.assertEqual(value["controlAuthority"], "installed-rendered-quadlet")

    def test_active_carrier_must_agree_with_installed_control(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "image disagrees"):
            production_control_from_quadlet(installed_quadlet(), {11: row(11, image=IMAGE_B)})
        with self.assertRaisesRegex(RuntimeError, "env TZ disagrees"):
            production_control_from_quadlet(installed_quadlet(), {11: row(11, tz="UTC")})

    def test_installed_control_requires_exact_image_network_and_environment(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "exactly one Image"):
            production_control_from_quadlet(installed_quadlet().replace(f"Image={IMAGE_A}\n", ""))
        with self.assertRaisesRegex(RuntimeError, "Network-v2 namespace"):
            production_control_from_quadlet(
                installed_quadlet().replace("Network=ns:/run/netns/nv2-browserless-prod\n", "")
            )
        with self.assertRaisesRegex(RuntimeError, "lacks env TZ"):
            production_control_from_quadlet(
                installed_quadlet().replace("Environment=TZ=Asia/Shanghai\n", "")
            )

    def test_canary_config_drops_production_warm_endpoint_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "automation.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "browserNetworkAuthority": {"kind": "network-v2"},
                        "browserlessWarmEndpointIds": ["chatgpt-carrier-11"],
                        "browserSubstrate": {
                            "kind": "browserless",
                            "endpoints": [
                                {
                                    "id": "chatgpt-carrier-11",
                                    "networkNamespace": "nv2-browserless-prod",
                                }
                            ],
                        },
                    }
                )
                + "\n"
            )
            with mock.patch.object(canary, "PRODUCTION_CONFIG", path):
                value = canary._load_production_config("nv2-browserless-prod")
        self.assertEqual(value["browserlessWarmEndpointIds"], [])
        self.assertEqual(
            [row["id"] for row in value["browserSubstrate"]["endpoints"]],
            [canary.CANARY_ENDPOINT_ID],
        )

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
