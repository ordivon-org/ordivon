from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(
    os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain")
)
GLOBAL_VNU = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "vnu/26.9.7/vnu.jar"
GLOBAL_NODE_PACKAGE_ROOT = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "node/1.63.0"
WEB_VERIFIER_RUNNER = Path(__file__).resolve().parent / "node/verify_html.mjs"


def vnu_jar() -> Path | None:
    configured = os.environ.get("ARTIFACT_VNU")
    path = Path(configured) if configured else GLOBAL_VNU
    return path if path.is_file() else None


def java_executable() -> Path | None:
    selected = shutil.which("java")
    return Path(selected) if selected else None


def node_executable() -> Path | None:
    selected = shutil.which("node")
    return Path(selected) if selected else None


def node_package_root() -> Path | None:
    configured = os.environ.get("ARTIFACT_NODE_PACKAGE_ROOT")
    path = Path(configured) if configured else GLOBAL_NODE_PACKAGE_ROOT
    return path if (path / "package.json").is_file() else None


def web_verifier_runner() -> Path:
    return WEB_VERIFIER_RUNNER
