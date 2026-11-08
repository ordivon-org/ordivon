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

    def test_tick_boolean_aliases_are_rejected_by_all_public_consumers(self) -> None:
        # JSON Schema rejects booleans as integers, but direct Python callers
        # bypass the schema and must not silently reinterpret True as tick 1.
        for field in ("base", "start", "end"):
            document = {
                **DOCUMENT,
                "timeBase": dict(DOCUMENT["timeBase"]),
                "cues": [dict(cue) for cue in DOCUMENT["cues"]],
            }
            if field == "base":
                document["timeBase"]["ticksPerSecond"] = True
            elif field == "start":
                document["cues"][0]["startTick"] = False
            else:
                document["cues"][0]["endTick"] = True
            with self.subTest(field=field):
                for consumer in (
                    export_webvtt,
                    export_srt,
                ):
                    with self.assertRaises(ValueError):
                        consumer(document)
                with self.assertRaises(ValueError):
                    validate_timed_text_delivery(document, media_duration_seconds="3.000")

    def test_submillisecond_cue_is_not_silently_exported_as_zero_duration(self) -> None:
        # Former real counterexample: valid 0.1 ms source becomes 0 --> 0 ms
        # in both delivery formats, which is not a valid WebVTT cue interval.
        document = {
            "language": "en",
            "timeBase": {"ticksPerSecond": 10_000},
            "cues": [
                {
                    "id": "short",
                    "startTick": 1,
                    "endTick": 2,
                    "text": "A",
                    "status": "locked",
                    "kind": "caption",
                }
            ],
        }
        result = validate_timed_text_delivery(document, media_duration_seconds="1")
        self.assertFalse(result["ok"])
        self.assertTrue(any("collapses at millisecond" in err for err in result["errors"]))
        for encoder in (export_srt, export_webvtt):
            with self.subTest(format=encoder.__name__):
                with self.assertRaisesRegex(ValueError, "short interval collapses"):
                    encoder(document)

    def test_millisecond_rounding_matches_independent_integer_oracle(self) -> None:
        # Bounded implementation-refinement witness for exactly the modeled
        # quotient/remainder and ties-even decision, not a universal Python proof.
        from ordivon_studio.timed_text import _milliseconds

        rates = (1, 24, 25, 30, 1000, 2000, 1001, 10_000, 48_000)
        ticks = tuple(range(0, 90)) + (1_000_001, 10**16 + 3)
        for rate in rates:
            for tick in ticks:
                quotient, remainder = divmod(tick * 1000, rate)
                if 2 * remainder < rate:
                    expected = quotient
                elif 2 * remainder > rate:
                    expected = quotient + 1
                else:
                    expected = quotient + (quotient % 2)
                self.assertEqual(_milliseconds(tick, rate), expected, (tick, rate))

    def test_exact_rational_millisecond_conversion_preserves_representable_cues(self) -> None:
        document = {
            "language": "en",
            "timeBase": {"ticksPerSecond": 10_000},
            "cues": [
                {
                    "id": "representable",
                    "startTick": 10,
                    "endTick": 20,
                    "text": "Exactly one millisecond",
                    "status": "locked",
                    "kind": "dialogue",
                },
            ],
        }
        self.assertTrue(validate_timed_text_delivery(document, media_duration_seconds="1")["ok"])
        self.assertIn("00:00:00.001 --> 00:00:00.002", export_webvtt(document))
        self.assertIn("00:00:00,001 --> 00:00:00,002", export_srt(document))

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
