from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNNER_FILENAME = "Ordivon Studio Runner.py"
CONFIG_FILENAME = "ordivon-runner.config.json"
OPERATION_FILENAME = "resolve-operation.json"
RESULT_FILENAME = "resolve-result.json"
_OPERATION_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class ResolvePaths:
    scripts_directory: Path
    control_directory: Path
    windows_control_directory: str


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _powershell_environment() -> dict[str, str]:
    powershell = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
    if not powershell.is_file():
        raise RuntimeError("Windows PowerShell is unavailable; pass explicit Resolve paths")
    command = (
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new(); "
        "$value=[ordered]@{AppData=$env:APPDATA;LocalAppData=$env:LOCALAPPDATA}; "
        "$value | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell environment discovery failed")
    value = json.loads(result.stdout.strip())
    if not isinstance(value, dict) or not all(isinstance(value.get(key), str) for key in ("AppData", "LocalAppData")):
        raise RuntimeError("PowerShell returned incomplete Windows profile paths")
    return {"AppData": value["AppData"], "LocalAppData": value["LocalAppData"]}


def _wslpath(value: str, mode: str) -> str:
    executable = Path("/usr/bin/wslpath")
    if not executable.is_file():
        raise RuntimeError("wslpath is unavailable; pass explicit path forms")
    result = subprocess.run(
        [str(executable), mode, value],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"wslpath {mode} failed")
    return result.stdout.strip()


def discover_resolve_paths() -> ResolvePaths:
    environment = _powershell_environment()
    windows_scripts = (
        environment["AppData"]
        + r"\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\Ordivon"
    )
    windows_control = environment["LocalAppData"] + r"\OrdivonStudio\control"
    return ResolvePaths(
        scripts_directory=Path(_wslpath(windows_scripts, "-u")),
        control_directory=Path(_wslpath(windows_control, "-u")),
        windows_control_directory=windows_control,
    )


def _resolved_paths(
    *,
    scripts_directory: Path | None = None,
    control_directory: Path | None = None,
    windows_control_directory: str | None = None,
) -> ResolvePaths:
    if scripts_directory is None and control_directory is None and windows_control_directory is None:
        return discover_resolve_paths()

    discovered: ResolvePaths | None = None
    if scripts_directory is None or control_directory is None:
        discovered = discover_resolve_paths()
    scripts = scripts_directory or discovered.scripts_directory  # type: ignore[union-attr]
    control = control_directory or discovered.control_directory  # type: ignore[union-attr]
    windows_control = windows_control_directory
    if windows_control is None:
        try:
            windows_control = _wslpath(str(control), "-w")
        except RuntimeError:
            if discovered and control == discovered.control_directory:
                windows_control = discovered.windows_control_directory
            else:
                raise
    return ResolvePaths(Path(scripts), Path(control), windows_control)


def install_runner(
    *,
    scripts_directory: Path | None = None,
    control_directory: Path | None = None,
    windows_control_directory: str | None = None,
) -> dict[str, Any]:
    paths = _resolved_paths(
        scripts_directory=scripts_directory,
        control_directory=control_directory,
        windows_control_directory=windows_control_directory,
    )
    source = Path(__file__).resolve().with_name("resolve_runner_menu.py")
    if not source.is_file():
        raise FileNotFoundError(source)

    paths.scripts_directory.mkdir(parents=True, exist_ok=True)
    paths.control_directory.mkdir(parents=True, exist_ok=True)
    destination = paths.scripts_directory / RUNNER_FILENAME
    shutil.copyfile(source, destination)
    config = {
        "schemaVersion": 1,
        "controlDirectory": paths.windows_control_directory,
    }
    _atomic_write_json(paths.scripts_directory / CONFIG_FILENAME, config)
    return {
        "installed": True,
        "runner": str(destination),
        "config": str(paths.scripts_directory / CONFIG_FILENAME),
        "controlDirectory": str(paths.control_directory),
        "menu": "Workspace > Scripts > Utility > Ordivon > Ordivon Studio Runner",
    }


def _new_operation_id() -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dt%H%M%Sz").lower()
    return f"resolve-probe-{timestamp}-{secrets.token_hex(4)}"


def build_probe_operation(operation_id: str | None = None) -> dict[str, Any]:
    operation_id = operation_id or _new_operation_id()
    if not _OPERATION_ID.fullmatch(operation_id):
        raise ValueError("operationId has an invalid format")
    return {
        "schemaVersion": 1,
        "operationId": operation_id,
        "action": "probe",
        "requestedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def prepare_probe(*, control_directory: Path | None = None, operation_id: str | None = None) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    operation = build_probe_operation(operation_id)
    path = control / OPERATION_FILENAME
    _atomic_write_json(path, operation)
    stale_result = control / RESULT_FILENAME
    if stale_result.exists():
        stale_result.unlink()
    return {
        "prepared": True,
        "operation": operation,
        "operationDigest": _canonical_digest(operation),
        "operationPath": str(path),
    }


def validate_probe_result(result: dict[str, Any], *, expected_operation_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if result.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if result.get("adapter") != "resolve":
        errors.append("adapter must be resolve")
    if result.get("action") != "probe":
        errors.append("action must be probe")
    if result.get("status") not in {"succeeded", "failed"}:
        errors.append("status must be succeeded or failed")
    operation_id = result.get("operationId")
    if operation_id is not None and (not isinstance(operation_id, str) or not _OPERATION_ID.fullmatch(operation_id)):
        errors.append("operationId has an invalid format")
    if expected_operation_id is not None and operation_id != expected_operation_id:
        errors.append(f"operationId does not match expected {expected_operation_id}")
    digest = result.get("operationDigest")
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest)):
        errors.append("operationDigest is invalid")
    if result.get("status") == "succeeded":
        probe = result.get("probe")
        if not isinstance(probe, dict):
            errors.append("successful result must contain probe")
        elif not isinstance(probe.get("capabilities"), dict):
            errors.append("probe must contain capabilities")
    if result.get("status") == "failed" and not isinstance(result.get("error"), dict):
        errors.append("failed result must contain error")
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ("Authorization", "Bearer ", "ORDIVON_BEARER_TOKEN", "\\Users\\", "/root/"):
        if forbidden in encoded:
            errors.append(f"result contains forbidden private material: {forbidden!r}")
    return errors


def read_result(
    *, control_directory: Path | None = None, expected_operation_id: str | None = None
) -> dict[str, Any]:
    control = control_directory or discover_resolve_paths().control_directory
    path = control / RESULT_FILENAME
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("Resolve result root must be an object")
    errors = validate_probe_result(value, expected_operation_id=expected_operation_id)
    if errors:
        raise ValueError("; ".join(errors))
    return value
