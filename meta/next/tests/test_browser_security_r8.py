import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/browser-security-r8/fresh_service_attribution.py"
)
SPEC = importlib.util.spec_from_file_location("fresh_service_attribution", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
r8 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r8)


class BrowserSecurityR8Tests(unittest.TestCase):
    def test_r7_reference_is_repeatability_bound(self) -> None:
        evidence, digest = r8.load_r7_reference()
        receipt = json.loads(r8.R7_REPEATABILITY.read_text())
        self.assertEqual(digest, receipt["run1"]["sha256"])
        self.assertEqual(receipt["standing"], "BYTE_IDENTICAL_CONTROLLED_REPEATABILITY")
        self.assertFalse(evidence["safetyBoundary"]["protectedProviderVisited"])

    def test_script_does_not_name_protected_provider_urls(self) -> None:
        text = MODULE_PATH.read_text().lower()
        self.assertNotIn("chatgpt.com", text)
        self.assertNotIn("cloudflare.com", text)
        self.assertIn("'productionbrowserconnected':false", text.replace(" ", ""))

    def test_reference_comparison_can_localize_fresh_service(self) -> None:
        reference, _ = r8.load_r7_reference()
        launcher = reference["arms"]["containerDirectLauncherMatched"]
        production = reference["arms"]["browserlessCurrent"]
        self.assertNotEqual(
            launcher["browser"]["targetTypeCounts"],
            production["browser"]["targetTypeCounts"],
        )
        value = r8.r7.pair_summary(launcher, production)
        self.assertIn("$.targetTypeCounts.page", value["browserChangedPaths"])
        self.assertTrue(value["pageChangedPaths"])

    def test_network_namespace_guard_compares_exact_namespace_identity(self) -> None:
        current = type("Stat", (), {"st_dev": 1, "st_ino": 2})()
        target = type("Stat", (), {"st_dev": 1, "st_ino": 2})()
        with mock.patch.object(r8.os, "stat", side_effect=[current, target]):
            r8.require_network_namespace()
        wrong = type("Stat", (), {"st_dev": 1, "st_ino": 3})()
        with mock.patch.object(r8.os, "stat", side_effect=[current, wrong]):
            with self.assertRaisesRegex(RuntimeError, "Network-v2 namespace"):
                r8.require_network_namespace()

    def test_cleanup_state_shape_is_boolean_only(self) -> None:
        # This is a *shape/negation* test, not an installed Podman cleanup
        # acceptance. Never query host Podman, X sockets or user profiles from
        # a portable unit test; actual cleanup is checked by the live canary.
        with (
            mock.patch.object(
                r8.r7.r5, "podman_container_exists", return_value=True
            ) as podman_exists,
            mock.patch.object(
                r8.pathlib.Path, "exists", side_effect=(True, False, True)
            ) as path_exists,
        ):
            value = r8._fresh_cleanup_state()
        podman_exists.assert_called_once_with(r8.canary.CANARY_CONTAINER)
        self.assertEqual(path_exists.call_count, 3)
        self.assertEqual(
            value,
            {
                "containerAbsent": False,
                "profileAbsent": False,
                "xSocketAbsent": True,
                "xauthAbsent": False,
            },
        )
        self.assertTrue(all(isinstance(v, bool) for v in value.values()))

        with (
            mock.patch.object(r8.r7.r5, "podman_container_exists", return_value=False),
            mock.patch.object(r8.pathlib.Path, "exists", return_value=False),
        ):
            absent = r8._fresh_cleanup_state()
        self.assertTrue(all(absent.values()))


if __name__ == "__main__":
    unittest.main()
