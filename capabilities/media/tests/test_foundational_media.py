from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.foundational_media import (
    ProfileArm,
    RegisteredCase,
    haptic_challenger_report,
    live_realtime_experiment,
    profile_distinction_report,
    spatial_reference_experiment,
    still_intervention_report,
    still_visual_features,
)


class FoundationalMediaTest(unittest.TestCase):
    def test_profile_distinction_exposes_target_specific_information(self) -> None:
        cases = [
            RegisteredCase("a", "crop-removes-qualifier", "still"),
            RegisteredCase("b", "viewing-distance-legibility", "still"),
            RegisteredCase("c", "color-implies-outcome", "still"),
        ]
        report = profile_distinction_report(
            cases,
            [
                ProfileArm("core", frozenset({"color-implies-outcome"}), 120),
                ProfileArm("still", frozenset({case.failure_class for case in cases}), 180),
                ProfileArm("wrong-motion", frozenset({"temporal-causality", "motion-implies-state"}), 180),
                ProfileArm("sham", frozenset(), 180),
            ],
        )
        by_arm = {item["arm"]: item for item in report["arms"]}
        self.assertEqual(by_arm["still"]["recall"], 1.0)
        self.assertGreater(by_arm["core"]["recall"], by_arm["wrong-motion"]["recall"])
        self.assertEqual(by_arm["sham"]["recall"], 0.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and shutil.which("rsvg-convert"), "ffmpeg/ffprobe/rsvg-convert required")
    def test_real_still_render_equipment_separates_registered_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_svg = root / "baseline.svg"
            changed_svg = root / "changed.svg"
            baseline_png = root / "baseline.png"
            control_png = root / "control.png"
            changed_png = root / "changed.png"
            baseline_svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><rect width="320" height="180" fill="#111"/><rect x="40" y="50" width="240" height="80" fill="#eee"/><text x="70" y="98" font-size="20" fill="#111">OUTCOME UNKNOWN</text></svg>',
                encoding="utf-8",
            )
            changed_svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><rect width="320" height="180" fill="#111"/><rect x="20" y="20" width="280" height="140" fill="#b00020"/><text x="70" y="98" font-size="20" fill="#fff">OUTCOME UNKNOWN</text></svg>',
                encoding="utf-8",
            )
            subprocess.run(["/usr/bin/rsvg-convert", "-o", str(baseline_png), str(baseline_svg)], check=True)
            subprocess.run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline_png), "-frames:v", "1", str(control_png)], check=True)
            subprocess.run(["/usr/bin/rsvg-convert", "-o", str(changed_png), str(changed_svg)], check=True)
            baseline = still_visual_features(baseline_png)
            control = still_visual_features(control_png)
            changed = still_visual_features(changed_png)
            report = still_intervention_report(baseline, controls=[("reencode", control)], perturbations=[("outcome-color", changed)])
            self.assertTrue(report["strictSeparation"])
            self.assertGreater(report["minPerturbationDistance"], report["maxControlDistance"])

    def test_spatial_reference_and_viewpoint_are_not_fixed_image_facts(self) -> None:
        report = spatial_reference_experiment()
        self.assertTrue(report["fixedViewAblationLosesViewpointEffect"])
        self.assertTrue(report["undeclaredReferenceSpaceCreatesMaterialError"])
        self.assertGreater(report["referenceFrameError"], 0.05)

    def test_live_trace_exposes_stale_window_that_replay_can_hide(self) -> None:
        report = live_realtime_experiment(seed=20260813)
        self.assertTrue(report["guardedFlagsStale"])
        self.assertTrue(report["naiveMarksStaleCurrent"])
        self.assertGreater(report["naiveMisleadingExposureMs"], 0.0)
        self.assertTrue(report["editedReplayCanRemoveCorrectionWindow"])

    def test_haptic_stays_challenger_without_physical_encounter(self) -> None:
        report = haptic_challenger_report()
        self.assertFalse(report["localPhysicalOutputAvailable"])
        self.assertEqual(report["disposition"], "retain-challenger-no-profile")


if __name__ == "__main__":
    unittest.main()
