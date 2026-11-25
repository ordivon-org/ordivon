"""Metamorphic relation tests; actual X11 product witness is separate."""
import unittest
from x11_interaction_acceptance import FRAME_BYTES, WIDTH, STATUS_ROWS, verify_relations, room_window_identity


class Relations(unittest.TestCase):
    def setUp(self):
        base = bytes(FRAME_BYTES)
        pos = STATUS_ROWS[0] * WIDTH * 3
        attack = base[:pos] + b"\xff" + base[pos + 1:]
        reset = base[:-1] + b"\xff"  # local non-status presentation difference
        self.frames = dict(baseline=base, baseline_repeat=base, irrelevant=base,
                           attack=attack, restart=reset, attack_repeat=attack,
                           restart_repeat=reset)

    def test_accept_focus_difference(self):
        self.assertEqual(len(verify_relations(self.frames)), 7)

    def test_no_effect(self):
        self.frames["attack"] = self.frames["baseline"]
        with self.assertRaisesRegex(ValueError, "attack did not"):
            verify_relations(self.frames)

    def test_irrelevant_effect(self):
        self.frames["irrelevant"] = self.frames["attack"]
        with self.assertRaisesRegex(ValueError, "irrelevant"):
            verify_relations(self.frames)

    def test_wrong_reset(self):
        self.frames["restart"] = self.frames["attack"]
        with self.assertRaisesRegex(ValueError, "restore status"):
            verify_relations(self.frames)

    def test_repeat_drift(self):
        self.frames["attack_repeat"] = self.frames["baseline"]
        with self.assertRaisesRegex(ValueError, "replay differs"):
            verify_relations(self.frames)

    def test_incomplete_inventory(self):
        del self.frames["restart_repeat"]
        with self.assertRaisesRegex(ValueError, "inventory"):
            verify_relations(self.frames)


class WindowIdentity(unittest.TestCase):
    def test_native_movie_title_is_mode_specific(self):
        def props(title, pid=42):
            return f'_NET_WM_PID(CARDINAL) = {pid}\nWM_NAME(STRING) = "{title}"\n'
        movie = "MovieWriter: Frame 41 (time: 00:00:01:11) - Room Encounter"
        self.assertTrue(room_window_identity(props(movie), 42, movie=True))
        self.assertFalse(room_window_identity(props(movie), 42))
        self.assertTrue(room_window_identity(props("Room Encounter"), 42))
        self.assertFalse(room_window_identity(props("Room Encounter"), 42, movie=True))
        self.assertFalse(room_window_identity(props(movie, 43), 42, movie=True))
        self.assertFalse(room_window_identity(props(movie + " impostor"), 42, movie=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
