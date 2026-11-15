"""Fail-closed native Godot acceptance for the actual Room Encounter.

Godot sometimes returns exit code 0 after an uncaught GDScript error.
Verify a positive receipt AND absence of script exceptions, not just rc=0.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

GAME = Path(__file__).resolve().parent
SCRIPT_FAILURES = ("SCRIPT ERROR:", "Parse Error:", "ERROR: Failed to load")


def verify_receipt(exit_code: int, stdout: str, stderr: str, receipt: str) -> None:
    combined = stdout + "\n" + stderr
    if exit_code != 0 or any(term in combined for term in SCRIPT_FAILURES):
        raise AssertionError(
            f"native Godot failed or silently emitted script error: exit={exit_code} "
            f"stdout={stdout[-3000:]} stderr={stderr[-3000:]}")
    if receipt not in stdout:
        raise AssertionError(f"missing native success receipt {receipt}: {combined[-3500:]}")


def engine(script: str, receipt: str, extra=()):
    process = subprocess.run(
        ["godot", "--headless", "--path", str(GAME),
         "--script", "res://" + script, *extra],
        capture_output=True, text=True, timeout=65)
    verify_receipt(process.returncode, process.stdout, process.stderr, receipt)
    print(next(line for line in process.stdout.splitlines() if receipt in line))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("encounter", "dialogue", "selftest"),
                        required=True)
    suite = parser.parse_args().suite
    if suite == "selftest":
        verify_receipt(0, "GAME_ROOM_ENCOUNTER_PASS", "", "GAME_ROOM_ENCOUNTER_PASS")
        for rc, out, err in [
            (0, "GAME_ROOM_ENCOUNTER_PASS", "SCRIPT ERROR: missing typed node"),
            (0, "GAME_ROOM_ENCOUNTER_PASS", "Parse Error: invalid script"),
            (0, "unrelated success", "",),
            (1, "GAME_ROOM_ENCOUNTER_PASS", "")
        ]:
            try:
                verify_receipt(rc, out, err, "GAME_ROOM_ENCOUNTER_PASS")
            except AssertionError:
                continue
            raise AssertionError("native error-injection control failed")
        print("GAME_NATIVE_RECEIPT_FAIL_CLOSED_PASS cases=5")
        return
    imported = subprocess.run(
        ["godot", "--headless", "--editor", "--import", "--path", str(GAME)],
        capture_output=True, text=True, timeout=90)
    if imported.returncode or any(term in imported.stderr + imported.stdout for term in SCRIPT_FAILURES):
        raise AssertionError(f"Godot import failed: {imported.stderr[-3000:]}")
    if suite == "encounter":
        engine("assert.gd", "GAME_ROOM_ENCOUNTER_PASS")
        with tempfile.TemporaryDirectory(prefix="ordivon-game-checkpoint-") as tmp:
            slot = str(Path(tmp) / "run.cfg")
            for phase, number in (("save", 8), ("load", 9)):
                engine("assert_process_restart.gd",
                       f"GAME_ROOM_PROCESS_RESTART_PASS checks={number} phase={phase}",
                       ("--", "--phase", phase, "--slot", slot))
    else:
        engine("narrative/acceptance.gd", "GAME_INTEGRATED_ROOM_DIALOGUE_PASS")
        quiet = subprocess.run(
            ["godot", "--headless", "--path", str(GAME), "--quit-after", "2"],
            capture_output=True, text=True, timeout=35)
        if quiet.returncode or any(term in quiet.stderr + quiet.stdout for term in SCRIPT_FAILURES):
            raise AssertionError(f"native launch failed: {quiet.stderr[-3000:]}")


if __name__ == "__main__":
    main()
