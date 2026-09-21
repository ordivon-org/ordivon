#!/usr/bin/env python3
"""Materialize consumer-owned Jev credentials into Windows DPAPI CurrentUser blobs."""

from __future__ import annotations

import argparse
import json
import stat
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_TYPESAFE = Path.home() / ".config/ordivon/secrets/jev-typesafe-api-key"
DEFAULT_TEXT_MODEL = Path.home() / ".config/ordivon/secrets/openrouter.json"
POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
SCRIPT = Path(__file__).with_name("materialize-jev-consumer-secrets.ps1")


def _private_file(path: Path, label: str) -> Path:
    meta = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(meta.st_mode):
        raise RuntimeError(f"{label} must be a regular non-symlink file")
    if stat.S_IMODE(meta.st_mode) & 0o077:
        raise RuntimeError(f"{label} must not be group/world accessible")
    if meta.st_size > 16_384:
        raise RuntimeError(f"{label} exceeds size bound")
    return path


def _one_token(path: Path, label: str) -> str:
    value = _private_file(path, label).read_text(encoding="utf-8").strip()
    if not value or any(ch.isspace() for ch in value):
        raise RuntimeError(f"{label} must contain one non-whitespace value")
    return value


def _text_model_key(path: Path) -> str:
    raw = json.loads(_private_file(path, "text-model credential").read_text(encoding="utf-8"))
    value = raw.get("apiKey") if isinstance(raw, dict) else None
    if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
        raise RuntimeError("text-model credential apiKey is missing or malformed")
    return value


def _windows_path(path: Path) -> str:
    proc = subprocess.run(
        ["/usr/bin/wslpath", "-w", str(path.resolve())],
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("cannot project materializer path into Windows namespace")
    return proc.stdout.strip()


def materialize(typesafe_path: Path, text_model_path: Path) -> dict[str, Any]:
    if not POWERSHELL.is_file():
        raise RuntimeError("Windows PowerShell is unavailable")
    payload = {
        "TYPESAFE_API_KEY": _one_token(typesafe_path, "TypeSafe credential"),
        "TEXT_MODEL_API_KEY": _text_model_key(text_model_path),
    }
    try:
        proc = subprocess.run(
            [
                str(POWERSHELL), "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-File", _windows_path(SCRIPT),
            ],
            input=json.dumps(payload, separators=(",", ":")),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    finally:
        payload.clear()
    if proc.returncode != 0:
        raise RuntimeError("Windows Jev secret materialization failed: " + proc.stderr[-1200:])
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Windows Jev secret materializer returned invalid JSON") from exc
    if not isinstance(value, dict) or value.get("materialized") is not True:
        raise RuntimeError("Windows Jev secret materializer did not report success")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--typesafe", type=Path, default=DEFAULT_TYPESAFE)
    parser.add_argument("--text-model", type=Path, default=DEFAULT_TEXT_MODEL)
    args = parser.parse_args()
    try:
        print(json.dumps(materialize(args.typesafe, args.text_model), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"schemaVersion": 1, "standing": "FAILED", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
