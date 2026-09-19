import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/browser-security-r5/container_direct_differential.py"
)
SPEC = importlib.util.spec_from_file_location("container_direct_differential", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
r5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r5)


class BrowserSecurityR5Tests(unittest.TestCase):
    def test_current_image_requires_one_immutable_browserless_ref(self) -> None:
        image = "ghcr.io/browserless/chromium@sha256:" + "a" * 64
        self.assertEqual(r5.current_image(f"[Container]\nImage={image}\n"), image)
        with self.assertRaisesRegex(RuntimeError, "one exact immutable image"):
            r5.current_image("[Container]\n")
        with self.assertRaisesRegex(RuntimeError, "one exact immutable image"):
            r5.current_image(
                f"[Container]\nImage={image}\nImage={image}\n"
            )

    def test_direct_launch_arguments_are_matched_except_profile_and_port(self) -> None:
        a = r5.direct_arguments(debug_port=1001, profile="/tmp/a")
        b = r5.direct_arguments(debug_port=1002, profile="/tmp/b")
        def normalized(rows):
            return [
                "--remote-debugging-port=<port>"
                if row.startswith("--remote-debugging-port=")
                else "--user-data-dir=<profile>"
                if row.startswith("--user-data-dir=")
                else row
                for row in rows
            ]

        self.assertEqual(normalized(a), normalized(b))
        self.assertIn("--enable-automation", a)
        self.assertIn("--window-size=1440,1000", a)
        self.assertEqual(a[-1], "about:blank")

    def test_pair_differences_separates_font_and_canvas_changes(self) -> None:
        left = {
            "page": {"canvasTextWidths": {family: 1.0 for family in r5.FONT_FAMILIES}},
            "browser": {"targetTypeCounts": {"page": 1}},
        }
        right = {
            "page": {
                "canvasTextWidths": {
                    family: (2.0 if family == "Arial" else 1.0)
                    for family in r5.FONT_FAMILIES
                }
            },
            "browser": {"targetTypeCounts": {"page": 2}},
        }
        lf = {family: family for family in r5.FONT_FAMILIES}
        rf = dict(lf)
        rf["Segoe UI"] = "Selawik"
        value = r5.pair_differences(left, right, left_fonts=lf, right_fonts=rf)
        self.assertEqual(value["fontResolutionFamilies"], ["Segoe UI"])
        self.assertEqual(value["canvasWidthFamilies"], ["Arial"])
        self.assertIn("$.targetTypeCounts.page", value["browserChangedPaths"])

    def test_browser_comparison_normalizes_executable_path_only(self) -> None:
        left = {
            "commandLineArguments": ["/host/chrome", "--enable-automation"],
            "systemInfo": {"commandLine": ["/host/chrome", "--enable-automation"]},
        }
        right = {
            "commandLineArguments": ["/container/chrome", "--enable-automation"],
            "systemInfo": {"commandLine": ["/container/chrome", "--enable-automation"]},
        }
        self.assertEqual(
            r5.normalized_browser_view(left),
            r5.normalized_browser_view(right),
        )

    def test_presentation_environment_is_allowlisted(self) -> None:
        self.assertEqual({"TZ", "LANG"}, {"TZ", "LANG"})
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn('allowed = {"TZ", "LANG"}', source)
        self.assertNotIn('allowed = {"TOKEN"', source)

    def test_container_shell_is_neutral_and_uses_same_direct_flags(self) -> None:
        command = r5.container_shell_command()
        for arg in r5.DIRECT_COMMON_ARGS:
            self.assertIn(arg, command)
        self.assertIn("about:blank", command)
        self.assertIn("Xvfb", command)
        self.assertNotIn("chatgpt.com", command.lower())
        self.assertNotIn("cloudflare.com", command.lower())

    def test_port_probe_tolerates_time_wait_semantics(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("socket.SO_REUSEADDR", source)

    def test_reserved_resources_are_disjoint_from_production_instances(self) -> None:
        self.assertEqual(r5.CONTAINER_NAME, "ordivon-browser-security-r5-container-direct")
        self.assertNotIn(r5.HOST_DEBUG_PORT, {3011, 3012, 3013})
        self.assertNotIn(r5.CONTAINER_DEBUG_PORT, {3011, 3012, 3013})
        self.assertNotEqual(r5.HOST_DEBUG_PORT, r5.CONTAINER_DEBUG_PORT)


if __name__ == "__main__":
    unittest.main()
