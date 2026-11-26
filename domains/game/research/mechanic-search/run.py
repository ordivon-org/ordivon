"""Run native bounded mechanic search in a private project and emit source-bound evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

GAME = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GAME / "scripts"))
from native_process import verify_process

FILES = ("encounter_rules.gd", "encounter_tuning.gd", "configs/default.tres",
         "configs/tactical_trial.tres")
PROBE = Path(__file__).with_name("room_search.gd")
TREATMENT = PROBE.parent / "conditions/trial_block2_hp53.tres"


def require(test, message):
    if not test:
        raise ValueError(message)


def validate(rows):
    require([r["case"] for r in rows] == ["classic", "trial", "trial_block2", "trial_block2_hp53"], "case inventory")
    expected = {"classic": (14, 1, 2), "trial": (48, 3, 3),
                "trial_block2": (48, 2, 3), "trial_block2_hp53": (53, 2, 3)}
    for r in rows:
        require((r["initial_health"], r["guard_block"], r["enemy_damage"]) == expected[r["case"]],
                "treatment identity")
        cycle = r["guard_cycle"]
        before, after = cycle["before"], cycle["after"]
        require(cycle["path"] == ["guard"] * 3 and before["turn"] == 0 and after["turn"] == 3,
                "guard cycle turn witness")
        key = ("room", "foes", "enemy_health", "player_health", "stamina", "phase")
        same = all(before[k] == after[k] for k in key) and before["turn"] % 3 == after["turn"] % 3
        require(cycle["same_quotient"] is same, "guard cycle quotient differs")
        require(before["player_health"] == r["initial_health"] and after["player_health"] <= before["player_health"],
                "guard cycle health")
        for kind in ("reduced", "exact"):
            result = r[kind]
            require(result["horizon"] == 48 and result["exact"] is (kind == "exact"), "search scope")
            require(0 < result["states"] <= 100000 and result["transitions"] >= result["states"] - 1,
                    "search census")
            require(bool(result["frontier"]), "no winning witness")
            previous_health, previous_actions = r["initial_health"] + 1, 49
            for point in result["frontier"]:
                require(0 < point["health"] < previous_health and
                        0 < point["actions"] < previous_actions, "frontier order")
                require(len(point["path"]) == point["actions"] <= 48 and
                        set(point["path"]) <= {"attack", "guard", "advance"}, "witness inventory")
                require(point["path"].count("attack") + point["path"].count("guard") == point["turns"],
                        "turn identity")
                previous_health, previous_actions = point["health"], point["actions"]
        require([(p["health"], p["actions"]) for p in r["reduced"]["frontier"]] ==
                [(p["health"], p["actions"]) for p in r["exact"]["frontier"]], "quotient mismatch")
        require(r["reduced"]["states"] <= r["exact"]["states"], "quotient state count")
        for kind in ("attack_first", "forecast_aware"):
            p = r[kind]
            require(p["phase"] in {"won", "lost"} or p["actions"] == 48, "policy not terminal/bounded")
            require(len(p["path"]) == p["actions"] <= 48, "policy path")
            if p["phase"] == "won":
                require(any(q["health"] >= p["health"] and q["actions"] <= p["actions"]
                            for q in r["exact"]["frontier"]), "policy missing from frontier")


def main():
    source = GAME / "examples/room-encounter"
    hashes = {f: hashlib.sha256((source / f).read_bytes()).hexdigest() for f in FILES}
    version = subprocess.check_output(["godot", "--version"], text=True, timeout=10).strip()
    with tempfile.TemporaryDirectory(prefix="game-mechanic-search-") as tmp:
        root = Path(tmp)
        for f in FILES:
            p = root / f
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / f, p)
        shutil.copyfile(PROBE, root / "room_search.gd")
        shutil.copyfile(TREATMENT, root / "configs/trial_block2_hp53.tres")
        (root / "project.godot").write_text('config_version=5\n[application]\nconfig/name="Native mechanic search"\n')
        start = time.monotonic()
        p = subprocess.run(["godot", "--headless", "--path", str(root), "--script",
                            "res://room_search.gd"], capture_output=True, text=True, timeout=120)
        elapsed = time.monotonic() - start
        verify_process(p.returncode, p.stdout, p.stderr)
        rows = [line.removeprefix("GAME_MECHANIC_SEARCH=") for line in p.stdout.splitlines()
                if line.startswith("GAME_MECHANIC_SEARCH=")]
        require(len(rows) == 1, "expected one native search observation")
        rows = json.loads(rows[0])
        validate(rows)
    require(hashes == {f: hashlib.sha256((source / f).read_bytes()).hexdigest() for f in FILES},
            "source changed")
    print(json.dumps(dict(scope="bounded_native_mechanic_search", godot=version,
                          source_sha256=hashes, treatment_sha256=hashlib.sha256(TREATMENT.read_bytes()).hexdigest(), probe_sha256=hashlib.sha256(PROBE.read_bytes()).hexdigest(),
                          elapsed_seconds=elapsed, cases=rows), sort_keys=True))


if __name__ == "__main__":
    main()
