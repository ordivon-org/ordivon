"""Capture supported native Godot export input identity, not an export engine."""
from __future__ import annotations

import configparser
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from native_process import verify_process

PRESETS = {
    "Linux x86_64": ("Linux/X11", "LINUX", "linux_release.x86_64"),
    "Windows x86_64": ("Windows Desktop", "WINDOWS", "windows_release_x86_64.exe"),
}


def digest(path: Path) -> str:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty native export input: {path}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def capture(project: Path) -> str:
    if os.environ.get("GAME_GODOT_TEMPLATE_DIR"):
        raise ValueError("GAME_GODOT_TEMPLATE_DIR is unsupported; use Godot's XDG_DATA_HOME")
    editor = Path(shutil.which("godot") or "godot").resolve(strict=True)
    if any((editor.parent / flag).exists() for flag in ("_sc_", "._sc_")):
        raise ValueError("self-contained editor unsupported by this native factory")
    proc = subprocess.run([str(editor), "--version"], capture_output=True, text=True, timeout=20)
    verify_process(proc.returncode, proc.stdout, proc.stderr, strict=True)
    version = proc.stdout.strip()
    match = re.fullmatch(r"([0-9]+\.[0-9]+(?:\.[0-9]+)?\.stable)\.official\.[0-9a-f]+", version)
    if match is None:
        raise ValueError(f"unsupported engine version: {version!r}")
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    if not data.is_absolute():
        raise ValueError("XDG_DATA_HOME must be absolute")
    templates = data / "godot" / "export_templates" / match[1]
    config = configparser.ConfigParser(interpolation=None)
    with (project / "export_presets.cfg").open() as stream:
        config.read_file(stream)
    seen = set()
    result = [f"ENGINE={version}", f"ENGINE_SHA256={digest(editor)}"]
    for section in config.sections():
        if not re.fullmatch(r"preset\.[0-9]+", section):
            continue
        name = config[section]["name"].strip('"')
        if name not in PRESETS:
            continue
        platform, label, filename = PRESETS[name]
        options = config[section + ".options"]
        if (name in seen or config[section]["platform"] != f'"{platform}"'
                or options.get("binary_format/architecture") != '"x86_64"'
                or options.get("custom_template/release") != '""'):
            raise ValueError(f"unsupported or ambiguous native export preset: {name}")
        seen.add(name)
        result.append(f"TEMPLATE_{label}_SHA256={digest(templates / filename)}")
    if seen != PRESETS.keys():
        raise ValueError("missing supported native export presets")
    return "\n".join(result)


if __name__ == "__main__":
    print(capture(Path(sys.argv[1])))
