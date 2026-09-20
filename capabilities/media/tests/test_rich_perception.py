from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.rich_perception import (
    ARTICLE_RICH_FEATURES,
    article_structure_features,
    audio_structure_features,
    canonical_digest,
    crossmodal_circular_shift_null,
    crossmodal_profile_coupling,
    cue_boundary_silence_score,
    media_intervention_report,
    paired_discrimination,
    profile_signature,
    structural_distance,
    video_structure_features,
)


class RichPerceptionTest(unittest.TestCase):
    def test_article_features_preserve_structure_without_raw_body(self) -> None:
        body = (
            "A precise opening explains the mechanism. "
            "Why does it matter? The second sentence adds 3 concrete facts. "
            "A final paragraph returns to the opening mechanism."
        )
        html = "<p>A precise opening explains the mechanism.</p><h2>Evidence</h2><p>Why does it matter? The second sentence adds <a href='x'>3 concrete facts</a>.</p><p>A final paragraph returns to the opening mechanism.</p>"
        result = article_structure_features(body_text=body, body_html=html, trail_text="A short lead")
        self.assertEqual(set(result["features"]), set(ARTICLE_RICH_FEATURES))
        self.assertEqual(result["structure"]["paragraphs"], 3)
        self.assertEqual(result["structure"]["subheadings"], 1)
        self.assertEqual(result["structure"]["links"], 1)
        self.assertEqual(len(result["positionProfile"]), 12)
        self.assertTrue(result["contentDigest"].startswith("sha256:"))
        self.assertNotIn("bodyText", result)

    def test_profile_signature_is_position_sensitive(self) -> None:
        left = profile_signature([1, 2, 3, 8, 3, 2, 1])
        right = profile_signature([8, 3, 2, 1, 1, 2, 3])
        self.assertNotEqual(left["peakPosition"], right["peakPosition"])
        self.assertNotEqual(left["earlyLateDeltaZ"], right["earlyLateDeltaZ"])

    def test_paired_discrimination_recovers_known_direction(self) -> None:
        records = []
        for index in range(12):
            records.append(
                {
                    "section": "a" if index < 6 else "b",
                    "candidate": {"x": 3.0 + index * 0.1, "noise": float(index % 2)},
                    "control": {"x": 1.0 + index * 0.1, "noise": float(index % 2)},
                }
            )
        report = paired_discrimination(records, feature_names=("x", "noise"), candidate_key="candidate", control_key="control", permutations=100)
        self.assertEqual(report["accuracy"], 1.0)
        self.assertLess(report["permutationP"], 0.1)
        self.assertEqual(report["byLabel"]["a"]["pairs"], 6)

    def test_media_intervention_report_separates_control_from_known_change(self) -> None:
        baseline = {"technical": {"durationSeconds": 2.0}, "structuralVector": [0.0, 0.0, 0.0]}
        control = {"technical": {"durationSeconds": 2.0}, "structuralVector": [0.01, 0.0, -0.01]}
        perturbation = {"technical": {"durationSeconds": 2.0}, "structuralVector": [1.0, -1.0, 1.0]}
        report = media_intervention_report(baseline=baseline, controls=[("reencode", control)], perturbations=[("reorder", perturbation)])
        self.assertEqual(report["equipmentDecision"], "earned-controlled-sensitivity")
        self.assertFalse(report["exactControlMatch"])
        self.assertTrue(report["strictSeparation"])
        self.assertGreater(report["separationRatio"], 10)

    def test_cue_and_crossmodal_metrics_are_explicitly_structural(self) -> None:
        audio = {
            "technical": {"durationSeconds": 4.0},
            "profiles": {
                "rmsAmplitude": [1.0, 0.1, 1.0, 0.1],
                "spectralFlux": [0.0, 1.0, 0.0, 1.0],
            },
        }
        video = {"profiles": {"change": [0.0, 1.0, 0.0, 1.0]}}
        timed = {"timeBase": {"ticksPerSecond": 1000}, "cues": [{"startTick": 0}, {"startTick": 1000}, {"startTick": 2000}, {"startTick": 3000}]}
        score = cue_boundary_silence_score(audio, timed, window_seconds=0.6)
        coupling = crossmodal_profile_coupling(video, audio)
        null = crossmodal_circular_shift_null(video, audio)
        self.assertIn("boundarySilenceContrastZ", score)
        self.assertGreater(coupling["videoChangeAudioFluxCorrelation"], 0.9)
        self.assertEqual(null["tests"]["videoChangeVsAudioFlux"]["rankHigh"], 1)
        self.assertGreaterEqual(null["tests"]["videoChangeVsAudioFlux"]["percentile"], 0.75)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_real_ffmpeg_audio_and_video_equipment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "tone.wav"
            video = root / "test.mp4"
            subprocess.run(
                ["/usr/bin/ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2:sample_rate=48000", "-c:a", "pcm_s24le", str(audio)],
                check=True,
            )
            subprocess.run(
                ["/usr/bin/ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10:duration=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)],
                check=True,
            )
            audio_features = audio_structure_features(audio, bins=8)
            video_features = video_structure_features(video, bins=8, sample_step_frames=2)
            self.assertEqual(len(audio_features["profiles"]["spectralFlux"]), 8)
            self.assertEqual(len(video_features["profiles"]["change"]), 8)
            self.assertGreater(len(audio_features["structuralVector"]), 8)
            self.assertGreater(len(video_features["structuralVector"]), 8)
            self.assertEqual(structural_distance(audio_features, audio_features), 0.0)
            self.assertTrue(canonical_digest({"a": 1}).startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
