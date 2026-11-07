"""Native Agent action/observation boundary acceptance for Room Encounter.

No simulation reimplementation: every transition executes the installed Godot
scene and its real EncounterRules. The output is privileged symbolic state,
not pixels or Human-play evidence.
"""
import json
import subprocess
from pathlib import Path

GAME = Path(__file__).resolve().parent
PREFIX = "GAME_AGENT_EPISODE_JSON="


def episode(actions):
    command = [
        "godot", "--headless", "--path", str(GAME),
        "--script", "res://agent_episode.gd", "--", "--actions", actions
    ]
    run = subprocess.run(command, text=True, capture_output=True, timeout=60)
    lines = [line[len(PREFIX):] for line in run.stdout.splitlines()
             if line.startswith(PREFIX)]
    assert len(lines) == 1, f"missing or duplicate episode receipt: {run.stdout}\n{run.stderr}"
    return run.returncode, json.loads(lines[0]), run.stderr


def main():
    status, first, stderr = episode("attack,attack,advance,guard")
    assert status == 0, (status, stderr)
    assert first["schema_version"] == 1
    assert first["observation_mode"] == "authoritative_state_not_pixels"
    assert first["initial"]["room"] == 1
    assert first["initial"]["phase"] == "fighting"
    assert len(first["steps"]) == 4
    assert first["steps"][0]["accepted"]
    assert first["steps"][0]["after"]["phase"] == "cleared"
    assert not first["steps"][1]["accepted"]
    assert first["steps"][1]["after"] == first["steps"][1]["before"]
    assert first["steps"][2]["accepted"]
    assert first["steps"][2]["control_path"] == "dialogue.unlock_choice"
    assert first["steps"][2]["after"]["room"] == 2
    assert first["steps"][3]["accepted"]
    assert first["final"]["phase"] == "fighting"
    assert not first["terminal"]
    status_repeat, repeat, _ = episode("attack,attack,advance,guard")
    assert status_repeat == 0 and repeat == first, "same real native run must replay deterministically"

    status, bad, _ = episode("warp")
    assert status == 0 and not bad["steps"][0]["recognized"]
    assert not bad["steps"][0]["accepted"]
    assert bad["steps"][0]["before"] == bad["steps"][0]["after"] == bad["initial"]
    status, premature, _ = episode("advance")
    assert status == 0 and premature["steps"][0]["recognized"]
    assert not premature["steps"][0]["accepted"]
    assert premature["steps"][0]["control_path"] == "dialogue.unavailable"
    assert premature["steps"][0]["before"] == premature["steps"][0]["after"]
    status, empty, _ = episode("")
    assert status == 0 and not empty["steps"] and empty["initial"] == empty["final"]
    status, long, _ = episode(",".join(["guard"] * 65))
    assert status == 2 and long["error"] == "action limit exceeded"
    win_path = "attack,advance,attack,attack,advance,guard,attack,guard,attack,advance"
    status, finished, _ = episode(win_path)
    assert status == 0 and finished["terminal"] and finished["final"]["phase"] == "won"
    assert finished["final"]["room"] == 3
    assert all(step["accepted"] for step in finished["steps"])
    assert all(step["control_path"] == "dialogue.unlock_choice"
               for step in finished["steps"] if step["action"] == "advance")
    print("GAME_AGENT_EPISODE_PASS native_episodes=7 deterministic=yes terminal_win=yes narrative_gate=yes")


if __name__ == "__main__":
    main()
