import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.browser_security_witness_source import (
    _collect_host_facts,
    assemble_manifest,
    browserless_container_name,
    normalize_effective_launch_argv,
    normalize_execution_contexts,
    profile_cookie_metadata,
)


D_BROWSER = "sha256:" + "a" * 64
D_NETWORK = "sha256:" + "b" * 64


class BrowserSecurityWitnessSourceTests(unittest.TestCase):
    def test_browserless_container_name_uses_endpoint_suffix(self) -> None:
        self.assertEqual(browserless_container_name("chatgpt-carrier-11"), "ordivon-browserless-11")
        with self.assertRaisesRegex(ValueError, "numeric suffix"):
            browserless_container_name("chatgpt-carrier-primary")

    @patch("scripts.browser_security_witness_source.profile_cookie_metadata", return_value={"cookieRows": 3, "cookieHosts": 2})
    @patch("scripts.browser_security_witness_source._font_resolution", return_value="Font Family")
    @patch("scripts.browser_security_witness_source._browser_binary_digest", return_value=D_BROWSER)
    @patch("scripts.browser_security_witness_source._container_image_identity", return_value="sha256:image")
    def test_collect_host_facts_keeps_host_control_plane_outside_browser_netns(
        self, image, browser_digest, font_resolution, profile_metadata
    ) -> None:
        facts = _collect_host_facts("chatgpt-carrier-11")
        self.assertEqual(facts["containerImageIdentity"], "sha256:image")
        self.assertEqual(facts["browserBinaryDigest"], D_BROWSER)
        self.assertEqual(facts["profileMetadata"], {"cookieRows": 3, "cookieHosts": 2})
        self.assertEqual(facts["fontResolution"]["Arial"], "Font Family")

    def test_profile_cookie_metadata_reads_counts_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Cookies"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE cookies(host_key TEXT, name TEXT, value TEXT)")
                db.executemany(
                    "INSERT INTO cookies(host_key,name,value) VALUES(?,?,?)",
                    [
                        ("a.example", "session", "secret-one"),
                        ("a.example", "prefs", "secret-two"),
                        ("b.example", "session", "secret-three"),
                    ],
                )
            value = profile_cookie_metadata(path)
            self.assertEqual(value, {"cookieRows": 3, "cookieHosts": 2})
            self.assertNotIn("secret", json.dumps(value).lower())

    def test_effective_launch_argv_normalizes_only_transient_debug_port(self) -> None:
        argv = [
            "/path/to/chrome",
            "--enable-automation",
            "--remote-debugging-port=34071",
            "--user-data-dir=/data",
            "--disable-features=Translate,MediaRouter",
            "about:blank",
        ]
        self.assertEqual(
            normalize_effective_launch_argv(argv),
            [
                "--enable-automation",
                "--remote-debugging-port=<ephemeral>",
                "--user-data-dir=/data",
                "--disable-features=Translate,MediaRouter",
                "about:blank",
            ],
        )

    def test_execution_context_normalization_erases_invocation_suffix(self) -> None:
        contexts = [
            {"name": "", "auxData": {"isDefault": True, "frameId": "main"}},
            {
                "name": "__playwright_utility_world_page@a1b2c3",
                "auxData": {"isDefault": False, "frameId": "main"},
            },
            {"name": "", "auxData": {"isDefault": True, "frameId": "child"}},
            {
                "name": "__playwright_utility_world_page@different",
                "auxData": {"isDefault": False, "frameId": "child"},
            },
        ]
        self.assertEqual(
            normalize_execution_contexts(contexts),
            ["default", "playwright-utility", "default", "playwright-utility"],
        )

    def test_manifest_is_security_collector_shape_and_has_no_challenge_oracle(self) -> None:
        manifest = assemble_manifest(
            witness_id="w-1",
            browser_binary_digest=D_BROWSER,
            control_layer={"routeFamily": "browserless/chromium"},
            network_authority={"generationDigest": D_NETWORK, "kind": "network-v2"},
            readings=[
                {
                    "detectorId": "cf04-browser-js-presentation",
                    "family": "CF04",
                    "detectorVersion": "harness-r1",
                    "coverage": "page-visible browser presentation",
                    "publicObservation": {"navigatorWebdriver": True},
                }
            ],
        )
        self.assertEqual(
            set(manifest),
            {
                "schemaVersion",
                "witnessId",
                "browserBinaryDigest",
                "controlLayer",
                "networkAuthority",
                "readings",
                "challengeStanding",
            },
        )
        self.assertIsNone(manifest["challengeStanding"])
        encoded = json.dumps(manifest, sort_keys=True)
        self.assertNotIn("sendAttempted", encoded)
        self.assertNotIn("providerEffectAttempted", encoded)


if __name__ == "__main__":
    unittest.main()
