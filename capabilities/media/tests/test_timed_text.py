from __future__ import annotations

import unittest

from ordivon_studio.timed_text import export_srt, export_webvtt


DOCUMENT = {
    "timeBase": {"ticksPerSecond": 1000},
    "cues": [
        {"id": "cue-1", "startTick": 0, "endTick": 1250, "text": "First"},
        {"id": "cue-2", "startTick": 1500, "endTick": 3000, "text": "Second"},
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


if __name__ == "__main__":
    unittest.main()
