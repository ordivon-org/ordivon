from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(
    os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain")
)
GLOBAL_VERAPDF = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "verapdf/1.30.2/verapdf"


def qpdf_executable() -> Path | None:
    selected = shutil.which("qpdf")
    return Path(selected) if selected else None


def verapdf_executable() -> Path | None:
    configured = os.environ.get("ARTIFACT_VERAPDF")
    path = Path(configured) if configured else GLOBAL_VERAPDF
    return path if path.is_file() else None
