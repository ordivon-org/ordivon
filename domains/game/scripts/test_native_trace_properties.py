"""Shrinking native Rules programs, observed independently of implementation."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

import hypothesis
from hypothesis import given, example, settings, strategies as st

from native_process import verify_process

GAME = Path(__file__).resolve().parents[1] / "examples" / "room-encounter"
PROBE = Path(__file__).resolve().parent / "fixtures" / "room_trace_probe.gd"
ACTIONS = ("attack", "guard", "advance", "restart", "checkpoint", "restore", "invalid_restore")


def stage(root, source=GAME):
    for name in ("encounter_rules.gd", "encounter_tuning.gd", "configs/default.tres",
                 "configs/tactical_trial.tres"):
        out = root / name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, out)
    shutil.copyfile(PROBE, root / "room_trace_probe.gd")
    (root / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Native trace test"\n')


def observe(root, actions):
    p = subprocess.run(["godot", "--headless", "--path", str(root), "--script",
                        "res://room_trace_probe.gd", "--", json.dumps(actions, separators=(",", ":"))],
                       capture_output=True, text=True, timeout=20)
    verify_process(p.returncode, p.stdout, p.stderr)
    prefix = "GAME_NATIVE_TRACE_OBSERVATION="
    lines = [line.removeprefix(prefix) for line in p.stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise AssertionError("expected exactly one native observation")
    return json.loads(lines[0])


def verify_trace(observations, actions):
    assert [row["mode"] for row in observations] == ["classic", "trial"], "mode inventory"
    for row in observations:
        initial = row["initial"]
        assert initial["phase"] == "fighting" and initial["turn"] == 0
        assert row["initial_events"] == [["state", initial]], "initial observer"
        assert [step["action"] for step in row["steps"]] == actions, "step inventory"
        current = saved = initial
        for step in row["steps"]:
            action, before, after = step["action"], step["before"], step["after"]
            assert before == current, f"{action}: discontinuous observation"
            allowed = {
                "attack": before["phase"] == "fighting" and before["stamina"] >= before["attack_cost"],
                "guard": before["phase"] == "fighting",
                "advance": before["phase"] == "cleared",
                "restart": True, "checkpoint": True, "restore": True, "invalid_restore": False,
            }[action]
            assert step["accepted"] is allowed, f"{action}: admission"
            if not allowed or action == "checkpoint":
                assert after == before, f"{action}: rejected/observational state effect"
                expected_events = []
            else:
                expected_events = [["state", after]]
                if action in ("attack", "guard"):
                    expected_events.append(["action", action])
                    assert after["turn"] == before["turn"] + 1, f"{action}: turn progression"
                    if "forecast" in before:
                        assert before["player_health"] - after["player_health"] == before["forecast"][action + "_health_loss"], f"{action}: forecast"
                elif action == "restart":
                    assert after == initial, "restart: initial state"
                elif action == "restore":
                    assert after == saved, "restore: checkpoint equality"
                elif action == "advance":
                    assert after["turn"] == before["turn"], "advance: changed combat turn"
            assert step["events"] == expected_events, f"{action}: observer trace differs"
            if action == "checkpoint":
                saved = before
            assert 1 <= after["room"] <= after["total_rooms"]
            assert all(after[k] >= 0 for k in ("foes", "player_health", "enemy_health", "stamina", "turn"))
            current = after


class NativeTraceProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="game-native-trace-")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        stage(cls.root)

    @settings(max_examples=24, deadline=None, derandomize=True, database=None)
    @example(actions=["advance"])
    @example(actions=["attack", "checkpoint", "guard", "restart", "restore", "invalid_restore", "advance"])
    @example(actions=["guard"] * 15 + ["attack", "restart", "restore"])
    @given(actions=st.lists(st.sampled_from(ACTIONS), min_size=1, max_size=40))
    def test_generated_native_trace(self, actions):
        verify_trace(observe(self.root, actions), actions)


if __name__ == "__main__":
    print(f"GAME_HYPOTHESIS_VERSION={hypothesis.__version__}", flush=True)
    unittest.main(verbosity=2)
