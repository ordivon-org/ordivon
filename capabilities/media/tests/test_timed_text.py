from __future__ import annotations

import unittest

from ordivon_studio.timed_text import export_srt, export_webvtt, validate_timed_text_delivery


DOCUMENT = {
    "language": "en",
    "timeBase": {"ticksPerSecond": 1000},
    "cues": [
        {
            "id": "cue-1",
            "startTick": 0,
            "endTick": 1250,
            "text": "First",
            "status": "locked",
            "kind": "dialogue",
        },
        {
            "id": "cue-2",
            "startTick": 1500,
            "endTick": 3000,
            "text": "Second",
            "status": "locked",
            "kind": "caption",
        },
    ],
}


class TimedTextTests(unittest.TestCase):
    def test_exports_webvtt(self) -> None:
        result = export_webvtt(DOCUMENT)
        self.assertIn("WEBVTT", result)
        self.assertIn("00:00:00.000 --> 00:00:01.250", result)
        self.assertIn("cue-2", result)

    def test_exports_srt(self) -> None:
        result = export_srt(DOCUMENT)
        self.assertIn("00:00:01,500 --> 00:00:03,000", result)
        self.assertIn("2\n", result)

    def test_rejects_duplicate_ids(self) -> None:
        document = {"timeBase": {"ticksPerSecond": 1000}, "cues": [DOCUMENT["cues"][0], DOCUMENT["cues"][0]]}
        with self.assertRaises(ValueError):
            export_webvtt(document)

    def test_delivery_validation_binds_locked_cues_to_media_duration(self) -> None:
        result = validate_timed_text_delivery(DOCUMENT, media_duration_seconds="3.000")
        self.assertTrue(result["ok"])
        self.assertEqual(result["lastCueEndTick"], 3000)
        self.assertEqual(result["mediaDurationTicks"], "3000")
        self.assertEqual(result["semanticCaptionCoverage"], "not-evaluated")

    def test_delivery_validation_rejects_overrun_and_provisional_cue(self) -> None:
        document = {
            **DOCUMENT,
            "cues": [
                DOCUMENT["cues"][0],
                {**DOCUMENT["cues"][1], "endTick": 3200, "status": "provisional"},
            ],
        }
        result = validate_timed_text_delivery(document, media_duration_seconds="3.000")
        self.assertFalse(result["ok"])
        self.assertTrue(any("after media duration" in error for error in result["errors"]))
        self.assertTrue(any("not locked" in error for error in result["errors"]))

    def test_delivery_validation_rejects_non_delivery_kind(self) -> None:
        document = {**DOCUMENT, "cues": [{**DOCUMENT["cues"][0], "kind": "chapter"}]}
        result = validate_timed_text_delivery(document, media_duration_seconds="3")
        self.assertFalse(result["ok"])
        self.assertTrue(any("allowed delivery kinds" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
