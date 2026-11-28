from __future__ import annotations

import ast
from pathlib import Path

from artifact_core.external_toolchain import (
    ARTIFACT_TOOLCHAIN_ROOT_ENV,
    DEFAULT_ARTIFACT_TOOLCHAIN_ROOT,
    artifact_toolchain_root,
)

ROOT = Path(__file__).resolve().parents[1]
CONSUMERS = (
    ROOT / "artifact_trust/cosign_toolchain.py",
    ROOT / "artifact_verifiers/document/toolchain.py",
    ROOT / "artifact_verifiers/pdf/toolchain.py",
    ROOT / "artifact_verifiers/web/toolchain.py",
    ROOT / "scripts/artifact_delivery_toolchain_doctor.py",
)


def _reads_toolchain_root_directly(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = node.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "get"
            and isinstance(function.value, ast.Attribute)
            and function.value.attr == "environ"
            and isinstance(function.value.value, ast.Name)
            and function.value.value.id == "os"
        ):
            continue
        key = node.args[0]
        if isinstance(key, ast.Constant) and key.value == "ARTIFACT_TOOLCHAIN_ROOT":
            return True
    return False


def test_external_toolchain_root_has_one_config_authority(monkeypatch) -> None:
    monkeypatch.delenv(ARTIFACT_TOOLCHAIN_ROOT_ENV, raising=False)
    assert artifact_toolchain_root() == DEFAULT_ARTIFACT_TOOLCHAIN_ROOT

    configured = Path("/tmp/ordivon-artifact-toolchain-fixture")
    monkeypatch.setenv(ARTIFACT_TOOLCHAIN_ROOT_ENV, str(configured))
    assert artifact_toolchain_root() == configured


def test_toolchain_consumers_do_not_reimplement_root_env_selection() -> None:
    offenders = [str(path.relative_to(ROOT)) for path in CONSUMERS if _reads_toolchain_root_directly(path)]
    assert offenders == []
