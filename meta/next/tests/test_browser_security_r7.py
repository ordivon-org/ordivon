import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/browser-security-r7/launcher_default_ablation.py"
)
SPEC = importlib.util.spec_from_file_location("launcher_default_ablation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
r7 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r7)


class BrowserSecurityR7Tests(unittest.TestCase):
    def test_managed_flags_strip_dynamic_and_auto_arguments(self) -> None:
        args = [
            "/x/chrome",
            "--alpha",
            "--remote-debugging-port=1234",
            "--user-data-dir=/tmp/profile",
            "--ozone-platform=x11",
            "--flag-switches-begin",
            "--flag-switches-end",
            "about:blank",
            "--beta",
        ]
        self.assertEqual(
            r7.managed_flags_from_command_line(args), ["--alpha", "--beta"]
        )

    def test_frozen_browserless_flags_are_neutral_launch_configuration(self) -> None:
        self.assertIn("--enable-automation", r7.BROWSERLESS_MANAGED_FLAGS)
        self.assertIn("--disable-background-networking", r7.BROWSERLESS_MANAGED_FLAGS)
        self.assertNotIn("--window-size=1440,1000", r7.BROWSERLESS_MANAGED_FLAGS)
        text = " ".join(r7.BROWSERLESS_MANAGED_FLAGS).lower()
        self.assertNotIn("chatgpt", text)
        self.assertNotIn("cloudflare", text)
        self.assertNotIn("token", text)
        self.assertNotIn("cookie", text)

    def test_container_shell_uses_neutral_about_blank(self) -> None:
        value = r7.container_shell_command(
            debug_port=9999,
            display=":99",
            flags=("--enable-automation", "--no-sandbox"),
        )
        self.assertIn("about:blank", value)
        self.assertIn("--remote-debugging-port=9999", value)
        self.assertIn("--enable-automation", value)
        self.assertNotIn("chatgpt.com", value.lower())
        self.assertNotIn("cloudflare.com", value.lower())

    def test_reserved_resources_do_not_overlap_r5_or_production_ports(self) -> None:
        self.assertNotEqual(r7.BASELINE_PORT, r7.LAUNCHER_PORT)
        self.assertNotIn(r7.BASELINE_PORT, {3011, 3012, 3013, 9231, 9232})
        self.assertNotIn(r7.LAUNCHER_PORT, {3011, 3012, 3013, 9231, 9232})
        self.assertNotEqual(r7.BASELINE_CONTAINER, r7.LAUNCHER_CONTAINER)

    def test_pair_summary_exposes_target_and_geometry_residuals(self) -> None:
        left = {
            "page": {"windowInner": [100, 100], "windowOuter": [120, 120]},
            "browser": {
                "commandLineArguments": ["/x/chrome", "--enable-automation"],
                "systemInfo": {"commandLine": ["/x/chrome", "--enable-automation"]},
                "targetTypeCounts": {"page": 1},
            },
        }
        right = {
            "page": {"windowInner": [90, 90], "windowOuter": [110, 110]},
            "browser": {
                "commandLineArguments": ["/y/chrome", "--enable-automation"],
                "systemInfo": {"commandLine": ["/y/chrome", "--enable-automation"]},
                "targetTypeCounts": {"page": 2},
            },
        }
        value = r7.pair_summary(left, right)
        self.assertTrue(value["managedLauncherFlagsEqual"])
        self.assertIn("$.targetTypeCounts.page", value["browserChangedPaths"])
        self.assertIn("$.windowInner[0]", value["pageChangedPaths"])


if __name__ == "__main__":
    unittest.main()
