import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments/browser-security-r9/window_placement_attribution.py"
)
SPEC = importlib.util.spec_from_file_location("window_placement_attribution", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
r9 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r9)


class BrowserSecurityR9Tests(unittest.TestCase):
    def test_window_projection_returns_only_allowlisted_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Preferences"
            path.write_text(
                json.dumps(
                    {
                        "browser": {
                            "window_placement": {
                                "left": 0,
                                "top": 0,
                                "right": 1288,
                                "bottom": 851,
                                "maximized": False,
                                "work_area_left": 0,
                                "work_area_top": 0,
                                "work_area_right": 1440,
                                "work_area_bottom": 1000,
                                "unrelated": "must-not-project",
                            }
                        },
                        "sensitiveDistractor": "must-not-project",
                    }
                )
            )
            value = r9.project_window_placement(path)
        self.assertEqual(set(value), set(r9.WINDOW_KEYS))
        self.assertNotIn("unrelated", value)
        self.assertNotIn("sensitiveDistractor", value)

    def test_outer_dimensions_derive_from_coordinates(self) -> None:
        placement = {
            "left": 0,
            "top": 0,
            "right": 1288,
            "bottom": 851,
            "maximized": False,
            "work_area_left": 0,
            "work_area_top": 0,
            "work_area_right": 1440,
            "work_area_bottom": 1000,
        }
        self.assertEqual(r9.outer_from_placement(placement), [1288, 851])

    def test_synthetic_preferences_contains_only_browser_window_placement(self) -> None:
        placement = {
            "left": 1,
            "top": 2,
            "right": 3,
            "bottom": 4,
            "maximized": False,
            "work_area_left": 0,
            "work_area_top": 0,
            "work_area_right": 10,
            "work_area_bottom": 10,
        }
        with tempfile.TemporaryDirectory() as tmp:
            target = r9.write_synthetic_preferences(Path(tmp), placement)
            value = json.loads(target.read_text())
        self.assertEqual(value, {"browser": {"window_placement": placement}})

    def test_r8_reference_is_repeatability_bound(self) -> None:
        evidence, digest = r9.load_r8_reference()
        receipt = json.loads(r9.R8_REPEATABILITY.read_text())
        self.assertEqual(digest, receipt["run1"]["sha256"])
        self.assertEqual(receipt["standing"], "BYTE_IDENTICAL_FRESH_SERVICE_REPEATABILITY")
        self.assertFalse(evidence["safetyBoundary"]["protectedProviderVisited"])

    def test_network_namespace_guard_compares_exact_namespace_identity(self) -> None:
        current = type("Stat", (), {"st_dev": 1, "st_ino": 2})()
        target = type("Stat", (), {"st_dev": 1, "st_ino": 2})()
        with mock.patch.object(r9.os, "stat", side_effect=[current, target]):
            r9.require_network_namespace()
        wrong = type("Stat", (), {"st_dev": 1, "st_ino": 3})()
        with mock.patch.object(r9.os, "stat", side_effect=[current, wrong]):
            with self.assertRaisesRegex(RuntimeError, "Network-v2 namespace"):
                r9.require_network_namespace()


if __name__ == "__main__":
    unittest.main()
