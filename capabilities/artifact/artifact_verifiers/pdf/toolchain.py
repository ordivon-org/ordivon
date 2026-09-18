from __future__ import annotations

import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(
    os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain")
)
GLOBAL_VERAPDF = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "verapdf/1.30.2/verapdf"
LEGACY_VERAPDF = ROOT / ".cache/artifact-toolchain/verapdf/current/verapdf"


def qpdf_executable() -> Path | None:
    selected = shutil.which("qpdf")
    return Path(selected) if selected else None


def verapdf_executable() -> Path | None:
    configured = os.environ.get("ARTIFACT_VERAPDF")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    if GLOBAL_VERAPDF.is_file():
        return GLOBAL_VERAPDF
    if LEGACY_VERAPDF.is_file():
        return LEGACY_VERAPDF
    system = shutil.which("verapdf")
    return Path(system) if system else None
