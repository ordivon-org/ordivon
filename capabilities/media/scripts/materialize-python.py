from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV = Path("/usr/bin/uv")
RECEIPT = ROOT / ".venv" / ".ordivon-materialization.json"
INPUTS = ("pyproject.toml", "uv.lock", ".python-version")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True, timeout=15)
    return (result.stdout or result.stderr).strip().splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Explicitly materialize Studio's Python dependency capability and emit an exact local receipt.")
    parser.add_argument("--extra", action="append", default=[], choices=["resolve"])
    args = parser.parse_args()
    if not UV.is_file():
        raise SystemExit("/usr/bin/uv is unavailable; Workstation Python supply must be repaired before Studio acquisition")
    command = [str(UV), "sync", "--frozen"]
    for extra in sorted(set(args.extra)):
        command.extend(["--extra", extra])
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        return completed.returncode
    python = ROOT / ".venv" / "bin" / "python"
    if not python.is_file():
        raise SystemExit("uv sync returned success without .venv/bin/python")
    extras = sorted(set(args.extra))
    probe = ["import importlib.metadata as m; assert m.version('jsonschema') == '4.25.1'"]
    if "resolve" in extras:
        probe.append("assert m.version('opentimelineio') == '0.18.1'")
    subprocess.run([str(python), "-c", "; ".join(probe)], cwd=ROOT, check=True, timeout=15)
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-python-materialization-receipt",
        "inputs": {name: digest(ROOT / name) for name in INPUTS},
        "extras": extras,
        "uv": command_output([str(UV), "--version"]),
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
