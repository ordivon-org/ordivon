"""Shared immutable Equipment proposal and narrow host-path compatibility helpers.

The public Studio equipment API reexports these exact types. This module
contains no provider discovery, operation selection or physical effects.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EquipmentPlan:
    equipment_id: str
    capability: str
    transport: str
    executable: str | None
    args: tuple[str, ...]
    notes: tuple[str, ...] = ()
    environment: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "equipmentId": self.equipment_id,
            "capability": self.capability,
            "transport": self.transport,
            "executable": self.executable,
            "args": list(self.args),
            "notes": list(self.notes),
            "environment": dict(self.environment),
        }


def _require_existing(path: str) -> str:
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    return path


def _windows_native_argument(path: str) -> str:
    """Translate a WSL-mounted Windows absolute path for a Windows-native process.

    Relative paths intentionally remain relative: WSL interop can project the Runtime
    Workspace as the Windows process working directory, as proven by Blender dogfood.
    """
    if len(path) >= 7 and path.startswith("/mnt/") and path[5].isalpha() and path[6] == "/":
        drive = path[5].upper()
        rest = path[7:].replace("/", "\\")
        return f"{drive}:\\{rest}"
    return path


def _first_existing(*patterns: str) -> str:
    for pattern in patterns:
        for raw in sorted(glob.glob(pattern)):
            if Path(raw).is_file():
                return raw
    raise FileNotFoundError(patterns[0] if patterns else "no equipment path supplied")
