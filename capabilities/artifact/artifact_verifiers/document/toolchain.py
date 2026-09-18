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
LEGACY_PANDOC = ROOT / ".cache/artifact-toolchain/pandoc/current/bin/pandoc"
LEGACY_PANDOC_ARCHIVE = (
    ROOT / ".cache/artifact-toolchain/pandoc/pandoc-3.10.2-linux-amd64.tar.gz"
)
DEFAULT_TOOLCHAIN_LOCK = ROOT / "artifact-delivery/toolchain-v1.lock.json"
DEFAULT_OPENXML_VALIDATOR = Path(
    os.environ.get(
        "ARTIFACT_OPENXML_VALIDATOR",
        "/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml",
    )
)


def selected_external_file(
    env_name: str,
    global_candidate: Path,
    legacy_candidate: Path,
) -> Path:
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured)
    if global_candidate.is_file():
        return global_candidate
    if legacy_candidate.is_file():
        return legacy_candidate
    return global_candidate
