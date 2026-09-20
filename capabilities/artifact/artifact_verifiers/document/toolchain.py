from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(
    os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain")
)
GLOBAL_PANDOC = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "pandoc/3.10.2/bin/pandoc"
GLOBAL_PANDOC_ARCHIVE = (
    GLOBAL_ARTIFACT_TOOLCHAIN_ROOT
    / "pandoc/3.10.2/pandoc-3.10.2-linux-amd64.tar.gz"
)
DEFAULT_TOOLCHAIN_LOCK = ROOT / "artifact-delivery/toolchain-v1.lock.json"


def selected_external_file(env_name: str, global_candidate: Path) -> Path:
    configured = os.environ.get(env_name)
    return Path(configured) if configured else global_candidate
