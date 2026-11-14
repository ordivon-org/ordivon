"""Owner-scoped Gateway formal task entry without redundant model replays."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_root_task_delegates_to_natural_gateway_owner() -> None:
    root = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
    task = root["tasks"]["gateway:formal:verify"]
    assert task["run"] == "bash services/gateway/formal/verify.sh"
    runner = ROOT / "services/gateway/formal/verify.sh"
    assert runner.is_file() and not runner.is_symlink()
    assert runner.read_text(encoding="utf-8").splitlines()[:2] == [
        "#!/usr/bin/env bash", "set -euo pipefail",
    ]
    subprocess.run(["bash", "-n", str(runner)], check=True)


def test_owner_script_preserves_existing_formal_toolchain_and_models() -> None:
    source = (ROOT / "services/gateway/formal/verify.sh").read_text(encoding="utf-8")
    assert "services/runtime/formal/toolchain.lock.json" in source
    assert "sha256" in source
    assert "Unqualified TLA+ JAR digest" in source
    assert "Model checking completed. No error has been found." in source
    for name in (
        "GatewayRoutingR1",
        "GatewayOwnerObservationR1",
        "GatewayCapabilityAuthzR1",
        "GatewayAgentWorkspaceBindingR1",
    ):
        assert f"{name}.tla" in source
        assert f"{name}.cfg" in source
        assert f"{name}.reachability.cfg" in source
        assert f"{name}.unsafe.cfg" in source
