from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / ".venv" / ".ordivon-materialization.json"
PYTHON = ROOT / ".venv" / "bin" / "python"
INPUTS = ("pyproject.toml", "uv.lock", ".python-version")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str, *, resolve: bool) -> int:
    target = "pnpm bootstrap:resolve" if resolve else "pnpm bootstrap:python"
    print("Studio Python dependencies are not currently materialized for this Workspace.")
    print(f"- {message}")
    print(f"Run `{target}` once, then replay the intended command.")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail closed unless Studio's existing Python environment matches its exact materialization receipt.")
    parser.add_argument("--extra", action="append", default=[], choices=["resolve"])
    args = parser.parse_args()
    required_extras = set(args.extra)
    if not PYTHON.is_file():
        return fail("missing .venv/bin/python", resolve="resolve" in required_extras)
    if not RECEIPT.is_file():
        return fail("missing .venv/.ordivon-materialization.json", resolve="resolve" in required_extras)
    try:
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fail("materialization receipt is unreadable", resolve="resolve" in required_extras)
    if receipt.get("schemaVersion") != 1 or receipt.get("kind") != "ordivon.studio-python-materialization-receipt":
        return fail("materialization receipt schema is unsupported", resolve="resolve" in required_extras)
    recorded = receipt.get("inputs")
    if not isinstance(recorded, dict):
        return fail("materialization receipt has no exact input bindings", resolve="resolve" in required_extras)
    for name in INPUTS:
        current = digest(ROOT / name)
        if recorded.get(name) != current:
            return fail(f"{name} differs from the materialized receipt", resolve="resolve" in required_extras)
    actual_extras = set(receipt.get("extras", []))
    if not required_extras.issubset(actual_extras):
        return fail(f"missing required Python extras: {sorted(required_extras - actual_extras)}", resolve="resolve" in required_extras)
    probe = ["import importlib.metadata as m; assert m.version('jsonschema') == '4.25.1'"]
    if "resolve" in required_extras:
        probe.append("assert m.version('opentimelineio') == '0.18.1'")
    result = subprocess.run([str(PYTHON), "-c", "; ".join(probe)], cwd=ROOT, capture_output=True, text=True, timeout=15, check=False)
    if result.returncode != 0:
        return fail("installed Python package state does not satisfy the expected versions", resolve="resolve" in required_extras)
    print("studio_python_dependencies=ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
