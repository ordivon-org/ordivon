"""Verify the natural Gateway TLC entry without invoking an unqualified tool."""

from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_root_alias_preserves_gateway_model_inventory() -> None:
    task = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]["gateway:formal:verify"]
    assert task["run"] == "bash services/gateway/formal/verify.sh"
    formal = ROOT / "services/gateway/formal"
    script = formal / "verify.sh"
    source = script.read_text()
    subprocess.run(["bash", "-n", str(script)], check=True)
    for model in formal.glob("*.tla"):
        assert model.name in source
    for config in formal.glob("*.cfg"):
        assert config.name in source
    assert source.count("tla2sany.SANY") == 5


def test_gateway_checker_rejects_unqualified_jar(tmp_path: Path) -> None:
    fake = tmp_path / "fake.jar"
    fake.write_bytes(b"not the pinned checker")
    run = subprocess.run(
        ["bash", "services/gateway/formal/verify.sh"],
        cwd=ROOT,
        env={**os.environ, "ORDIVON_TLA_TOOLS_JAR": str(fake)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 2
    assert "Unqualified TLA+ JAR digest" in run.stderr
