"""Cheap source-cut/treatment isolation contracts; actual exports are separate."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_pair as pair


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


class PairSource(unittest.TestCase):
    def test_exact_staged_difference_and_production_unchanged(self):
        original = (pair.SOURCE / "configs/tactical_trial.tres").read_bytes()
        head = pair.git("rev-parse", "HEAD")
        with tempfile.TemporaryDirectory(prefix="game-pair-contract-") as tmp:
            root = Path(tmp)
            a = pair.stage_project(root / "a", head, "A")
            b = pair.stage_project(root / "b", head, "B")
            af, bf = files(a), files(b)
            self.assertEqual(set(af), set(bf))
            self.assertEqual({k for k in af if af[k] != bf[k]},
                             {"project.godot", "configs/tactical_trial.tres"})
            self.assertEqual(af["configs/tactical_trial.tres"], original)
            self.assertEqual(bf["configs/tactical_trial.tres"], pair.TREATMENT.read_bytes())
            self.assertEqual(bf["configs/tactical_trial.tres"],
                             original.replace(b"player_health = 48", b"player_health = 53")
                                     .replace(b"guard_block = 3", b"guard_block = 2"))
            self.assertEqual(af["project.godot"].replace(b"OrdivonRoomStudy/A", b"OrdivonRoomStudy/B"),
                             bf["project.godot"])
            self.assertNotEqual(af["project.godot"], bf["project.godot"])
        self.assertEqual((pair.SOURCE / "configs/tactical_trial.tres").read_bytes(), original)

    def test_third_parameter_intervention_rejected(self):
        head = pair.git("rev-parse", "HEAD")
        with tempfile.TemporaryDirectory(prefix="game-pair-contract-") as tmp:
            root = Path(tmp)
            bad = root / "bad.tres"
            original = pair.TREATMENT.read_text()
            changed = original.replace("enemy_damage = 3", "enemy_damage = 4")
            self.assertNotEqual(original, changed)
            bad.write_text(changed)
            with patch.object(pair, "TREATMENT", bad):
                with self.assertRaisesRegex(ValueError, "exact two-parameter intervention"):
                    pair.stage_project(root / "stage", head, "B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
