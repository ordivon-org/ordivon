"""Discover the installed Resolve and Windows/WSL path environment.

These operations observe native PowerShell/WSL and FFprobe results. They do
not install the Resolve menu Runner, own media bytes, run editing operations
or judge editorial correctness.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .resolve_contracts import _OPERATION_ID

SMOKE_FIXTURE_FILENAME = "resolve-smoke-1080p30.mp4"


@dataclass(frozen=True, slots=True)
class ResolvePaths:
    scripts_directory: Path
    control_directory: Path
    windows_control_directory: str


@dataclass(frozen=True, slots=True)
class MediaCachePaths:
    directory: Path
    windows_directory: str


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


def discover_smoke_fixture() -> tuple[Path, str]:
    environment = _powershell_environment()
    windows_path = environment["LocalAppData"] + rf"\OrdivonStudio\fixtures\{SMOKE_FIXTURE_FILENAME}"
    return Path(_wslpath(windows_path, "-u")), windows_path


def _media_frame_count(path: Path, *, ffprobe: str = "/usr/bin/ffprobe") -> int:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames,avg_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed for compatibility fixture")
    value = json.loads(result.stdout)
    streams = value.get("streams")
    if not isinstance(streams, list) or len(streams) != 1 or not isinstance(streams[0], dict):
        raise ValueError("compatibility fixture must contain exactly one video stream")
    stream = streams[0]
    nb_frames = stream.get("nb_frames")
    if isinstance(nb_frames, str) and nb_frames.isdigit():
        frames = int(nb_frames)
    else:
        rate_text = stream.get("avg_frame_rate")
        duration_text = value.get("format", {}).get("duration") if isinstance(value.get("format"), dict) else None
        if not isinstance(rate_text, str) or "/" not in rate_text or not isinstance(duration_text, str):
            raise ValueError("compatibility fixture has no reliable frame count")
        numerator, denominator = (int(part) for part in rate_text.split("/", 1))
        if denominator == 0:
            raise ValueError("compatibility fixture frame rate denominator is zero")
        frames = round(float(duration_text) * numerator / denominator)
    if frames < 60:
        raise ValueError("compatibility fixture must contain at least 60 frames")
    return frames


def discover_production_media(production_id: str) -> MediaCachePaths:
    if not _OPERATION_ID.fullmatch(production_id):
        raise ValueError("productionId has an invalid format")
    environment = _powershell_environment()
    windows_directory = environment["LocalAppData"] + rf"\OrdivonStudio\productions\{production_id}\media"
    return MediaCachePaths(
        directory=Path(_wslpath(windows_directory, "-u")),
        windows_directory=windows_directory,
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
