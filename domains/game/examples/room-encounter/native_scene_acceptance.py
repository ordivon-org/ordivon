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


def verify_receipt(exit_code: int, stdout: str, stderr: str, receipt: str) -> str:
    combined = stdout + "\n" + stderr
    if exit_code != 0 or any(term in combined for term in SCRIPT_FAILURES):
        raise AssertionError(
            f"native Godot failed or silently emitted script error: exit={exit_code} "
            f"stdout={stdout[-3000:]} stderr={stderr[-3000:]}")
    # Godot can exit 0 after an engine error. A success token must begin exactly
    # one complete stdout line, never be embedded in unrelated/fake output.
    matching = [
        line for line in stdout.splitlines()
        if line == receipt or line.startswith(receipt + " ")
    ]
    if len(matching) != 1:
        raise AssertionError(
            f"expected one anchored native success receipt {receipt}, got {len(matching)}: "
            f"{combined[-3500:]}")
    return matching[0]


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
        receipt = "GAME_ROOM_ENCOUNTER_PASS"
        positive = [
            receipt,
            receipt + " assertions=23",
            "engine prelude\n" + receipt + " assertions=23",
        ]
        for out in positive:
            assert verify_receipt(0, out, "", receipt).startswith(receipt)
        negative = [
            (0, receipt, "SCRIPT ERROR: missing typed node"),
            (0, receipt, "Parse Error: invalid script"),
            (0, "unrelated success", ""),
            (1, receipt, ""),
            (0, "NOT_" + receipt + "_FAKE", ""),
            (0, receipt + "_FABRICATED", ""),
            (0, "engine prelude " + receipt, ""),
            (0, receipt + "\n" + receipt, ""),
        ]
        for rc, out, err in negative:
            try:
                verify_receipt(rc, out, err, receipt)
            except AssertionError:
                continue
            raise AssertionError("native error-injection control failed")
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
