"""Native Agent action/observation boundary acceptance for Room Encounter.

No simulation reimplementation: every transition executes the installed Godot
scene and its real EncounterRules. Player observations are native HUD/dialogue only; privileged state is
explicit debug opt-in, never pixel or Human-play evidence.
"""
import json
import subprocess
from pathlib import Path

GAME = Path(__file__).resolve().parent
PREFIX = "GAME_AGENT_EPISODE_JSON="


def episode(actions, observation="debug"):
    command = [
        "godot", "--headless", "--path", str(GAME),
        "--script", "res://agent_episode.gd", "--", "--actions", actions,
        *(["--observation", observation] if observation is not None else [])
    ]
    run = subprocess.run(command, text=True, capture_output=True, timeout=60)
    lines = [line[len(PREFIX):] for line in run.stdout.splitlines()
             if line.startswith(PREFIX)]
    assert len(lines) == 1, f"missing or duplicate episode receipt: {run.stdout}\n{run.stderr}"
    return run.returncode, json.loads(lines[0]), run.stderr


def main():
    status, first, stderr = episode("attack,attack,advance,guard")
    assert status == 0, (status, stderr)
    assert first["schema_version"] == 2
    assert first["observation_mode"] == "authoritative_debug_state_not_pixels"
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

    # Player-visible observations are projected from the rendered native UI.
    status, visible, _ = episode("attack,advance,guard", "player")
    assert status == 0 and visible["schema_version"] == 2
    assert visible["observation_mode"] == "player_visible_ui"
    assert visible["initial"]["status"].startswith("ROOM 1/3")
    assert "ENCOUNTER:" in visible["initial"]["encounter"]
    assert visible["initial"]["actions"]["attack"]
    assert "player_health" not in visible["initial"] and "phase" not in visible["initial"]
    assert visible["steps"][0]["after"]["dialogue"]["responses"]
    assert visible["steps"][0]["after"]["actions"]["advance"]
    assert all(set(step) == {"action", "before", "after"} for step in visible["steps"])
    assert visible["steps"][1]["before"] != visible["steps"][1]["after"]
    assert visible["steps"][1]["after"]["status"].startswith("ROOM 2/3")
    assert "dialogue" not in visible["steps"][1]["after"]
    assert visible["steps"][2]["before"] != visible["steps"][2]["after"]
    # Every observation, including those after terminal/failed transitions,
    # has a small UI-only key set rather than an accidentally leaked state.
    observed = [visible["initial"], visible["final"]]
    for step in visible["steps"]:
        observed.extend([step["before"], step["after"]])
    for value in observed:
        assert set(value).issubset({"title", "status", "encounter", "actions", "dialogue"})
        assert isinstance(value["status"], str) and isinstance(value["encounter"], str)
    status_repeat, visible_repeat, _ = episode("attack,advance,guard", "player")
    assert status_repeat == 0 and visible_repeat == visible
    status_default, default_obs, _ = episode("attack", None)
    assert status_default == 0 and default_obs["observation_mode"] == "player_visible_ui"
    assert "player_health" not in default_obs["initial"]
    status_invalid, invalid_obs, _ = episode("attack", "anything")
    assert status_invalid == 2 and invalid_obs["error"].startswith("expected:")
    # Human Trial button and Agent symbolic trial both invoke the same
    # native resource-backed Game action, never independent combat logic.
    status, tactic, _ = episode("trial,attack,guard", "debug")
    assert status == 0 and tactic["steps"][0]["accepted"]
    assert tactic["steps"][0]["control_path"] == "native.trial_resource"
    assert tactic["steps"][0]["after"]["foes"] == 2
    assert tactic["steps"][0]["after"]["enemy_health"] == 5
    assert tactic["steps"][1]["after"]["enemy_health"] == 2
    assert tactic["steps"][2]["after"]["turn"] == 2
    status, visible_tactic, _ = episode("trial,attack", "player")
    assert status == 0 and "NEXT FOE HIT" in visible_tactic["final"]["encounter"]
    assert all(set(step) == {"action", "before", "after"} for step in visible_tactic["steps"])
    assert visible_tactic["initial"]["actions"]["trial"]
    assert visible_tactic["steps"][0]["after"]["status"].startswith("ROOM 1/3")
    status, classic_return, _ = episode("trial,classic", "debug")
    assert status == 0 and classic_return["steps"][1]["accepted"]
    assert classic_return["steps"][1]["control_path"] == "native.classic_resource"
    assert classic_return["final"]["foes"] == 1
    assert classic_return["final"]["enemy_health"] == 3
    status, player_return, _ = episode("trial,classic", "player")
    assert status == 0 and player_return["final"]["title"].startswith("ORIGINAL GRAYBOX")
    assert player_return["steps"][0]["after"]["title"].startswith("TACTICAL TRIAL")
    assert all(set(step) == {"action", "before", "after"} for step in player_return["steps"])
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
    print("GAME_AGENT_EPISODE_PASS native_episodes=15 player_ui_default=yes debug_opt_in=yes deterministic=yes terminal_win=yes narrative_gate=yes")


if __name__ == "__main__":
    main()
