"""Independent PCM relation tests; actual Godot output is separately consumed."""
import struct
import unittest
from mixed_audio_acceptance import PCM_BYTES, summarize_pcm, verify_audio_relations


class AudioContract(unittest.TestCase):
    def setUp(self):
        self.quiet = summarize_pcm(bytes(PCM_BYTES))
        self.active = summarize_pcm(struct.pack("<h", -32768) * 120 + bytes(PCM_BYTES - 240))

    def test_positive(self):
        self.assertEqual(self.active["peak_s16"], 32768)
        verify_audio_relations(self.quiet, self.active, self.quiet)

    def test_silent_attack(self):
        with self.assertRaisesRegex(ValueError, "silent"):
            verify_audio_relations(self.quiet, self.quiet, self.quiet)

    def test_audible_control(self):
        with self.assertRaisesRegex(ValueError, "irrelevant"):
            verify_audio_relations(self.active, self.active, self.quiet)

    def test_audible_reset(self):
        with self.assertRaisesRegex(ValueError, "reset"):
            verify_audio_relations(self.quiet, self.active, self.active)

    def test_truncated_pcm(self):
        with self.assertRaisesRegex(ValueError, "byte count"):
            summarize_pcm(bytes(PCM_BYTES - 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
