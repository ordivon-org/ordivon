"""Fail-closed native Godot acceptance for the actual Room Encounter.

Godot sometimes returns exit code 0 after an uncaught GDScript error.
Verify a positive receipt AND absence of script exceptions, not just rc=0.
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

GAME = Path(__file__).resolve().parent
SCRIPT_FAILURES = ("SCRIPT ERROR:", "Parse Error:", "ERROR: Failed to load")


def verify_receipt(exit_code: int, stdout: str, stderr: str, receipt: str) -> str:
    combined = stdout + "\n" + stderr
    if exit_code != 0 or any(term in combined for term in SCRIPT_FAILURES):
        raise AssertionError(
            f"native Godot failed or silently emitted script error: exit={exit_code} "
            f"stdout={stdout[-3000:]} stderr={stderr[-3000:]}")
    # Admit only the exact native Godot producer format, not an arbitrary suffix.
    # The process-restart receipt already contains its exact checks/phase values.
    if receipt == "GAME_ROOM_ENCOUNTER_PASS":
        pattern = re.escape(receipt) + r" assertions=[1-9][0-9]* traces=[1-9][0-9]*"
    elif receipt == "GAME_INTEGRATED_ROOM_DIALOGUE_PASS":
        pattern = re.escape(receipt) + r" checks=[1-9][0-9]*"
    else:
        pattern = re.escape(receipt)
    claimed = [line for line in stdout.splitlines() if line.startswith(receipt)]
    if len(claimed) != 1 or re.fullmatch(pattern, claimed[0]) is None:
        raise AssertionError(
            f"expected one format-qualified native success receipt {receipt}: "
            f"{combined[-3500:]}")
    return claimed[0]


def engine(script: str, receipt: str, extra=()):
    process = subprocess.run(
        ["godot", "--headless", "--path", str(GAME),
         "--script", "res://" + script, *extra],
        capture_output=True, text=True, timeout=65)
    native_receipt = verify_receipt(process.returncode, process.stdout, process.stderr, receipt)
    print(native_receipt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("encounter", "dialogue", "selftest"),
                        required=True)
    suite = parser.parse_args().suite
    if suite == "selftest":
        room = "GAME_ROOM_ENCOUNTER_PASS"
        dialogue = "GAME_INTEGRATED_ROOM_DIALOGUE_PASS"
        save = "GAME_ROOM_PROCESS_RESTART_PASS checks=8 phase=save"
        load = "GAME_ROOM_PROCESS_RESTART_PASS checks=9 phase=load"
        positive = [
            (room, room + " assertions=23 traces=486"),
            (room, "engine prelude\n" + room + " assertions=23 traces=486"),
            (dialogue, dialogue + " checks=20"),
            (save, save),
            (load, load),
        ]
        for expected, out in positive:
            assert verify_receipt(0, out, "", expected) == out.splitlines()[-1]
        negative = [
            (room, 0, room + " assertions=23 traces=486", "SCRIPT ERROR: missing typed node"),
            (room, 0, room + " assertions=23 traces=486", "Parse Error: invalid script"),
            (room, 0, "unrelated success", ""),
            (room, 1, room + " assertions=23 traces=486", ""),
            (room, 0, "NOT_" + room + "_FAKE", ""),
            (room, 0, room + "_FABRICATED", ""),
            (room, 0, "engine prelude " + room + " assertions=23 traces=486", ""),
            (room, 0, room + " assertions=23 traces=486\n" + room + " assertions=24 traces=486", ""),
            (room, 0, room + " GARBAGE", ""),
            (room, 0, room + " assertions=bogus traces=486", ""),
            (room, 0, room + " assertions=0 traces=486", ""),
            (room, 0, room + " assertions=23 traces=0", ""),
            (dialogue, 0, dialogue + " checks=bogus", ""),
            (save, 0, save + " trailer", ""),
        ]
        for expected, rc, out, err in negative:
            try:
                verify_receipt(rc, out, err, expected)
            except AssertionError:
                continue
            raise AssertionError(f"native error-injection control failed: {out!r}")
        print(f"GAME_NATIVE_RECEIPT_FAIL_CLOSED_PASS cases={len(positive) + len(negative)}")
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
