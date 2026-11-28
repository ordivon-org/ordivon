from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys

from python_dependency_contract import EXPECTED_PYTHON, INPUTS, ROOT, digest, environment_probe

RECEIPT = ROOT / ".venv" / ".ordivon-materialization.json"


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True, timeout=15)
    return (result.stdout or result.stderr).strip().splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicitly materialize Studio's Python dependency capability and emit an exact local receipt.")
    parser.parse_args()
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("uv is unavailable on PATH; run this command through the repository mise toolchain")
    if platform.python_version() != EXPECTED_PYTHON:
        raise SystemExit(f"Studio expects Python {EXPECTED_PYTHON}, got {platform.python_version()}; run through mise")
    command = [uv, "sync", "--python", sys.executable, "--frozen"]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        return completed.returncode
    python = ROOT / ".venv" / "bin" / "python"
    if not python.is_file():
        raise SystemExit("uv sync returned success without .venv/bin/python")
    probe = environment_probe()
    subprocess.run([str(python), "-c", probe], cwd=ROOT, check=True, timeout=30)
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-python-materialization-receipt",
        "inputs": {name: digest(ROOT / name) for name in INPUTS},
        "uv": command_output([uv, "--version"]),
        "python": command_output([str(python), "--version"]),
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(RECEIPT)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
