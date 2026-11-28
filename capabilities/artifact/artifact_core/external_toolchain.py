"""Canonical external Artifact toolchain root selection."""

from __future__ import annotations

import os
from pathlib import Path

ARTIFACT_TOOLCHAIN_ROOT_ENV = "ARTIFACT_TOOLCHAIN_ROOT"
DEFAULT_ARTIFACT_TOOLCHAIN_ROOT = Path("/opt/ordivon/external/artifact-toolchain")


def artifact_toolchain_root() -> Path:
    """Return the configured external toolchain root or its canonical default."""
    configured = os.environ.get(ARTIFACT_TOOLCHAIN_ROOT_ENV)
    return Path(configured) if configured else DEFAULT_ARTIFACT_TOOLCHAIN_ROOT
