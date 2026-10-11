"""Preflight must reject occupied host-veth port even when bound to wildcard IP."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "capabilities/gluetun/acceptance/compatibility-hop.sh"


def executable(path: Path, contents: str) -> None:
    path.write_text("#!/bin/sh\n" + contents, encoding="utf-8")
    path.chmod(0o755)


def run_preflight(tmp_path: Path, ss_output: str) -> subprocess.CompletedProcess[str]:
    # Shadow all external binaries; only the pre-existing netns file gate is
    # replaced with a fixture marker in this disposable script copy.
    marker = tmp_path / "mock-netns"
    marker.touch()
    script = PREFLIGHT.read_text(encoding="utf-8")
    original = 'test -e "/run/netns/$NS"'
    assert script.count(original) == 1
    script = script.replace(original, f'test -e "{marker}"')
    script_path = tmp_path / "preflight.sh"
    script_path.write_text(script, encoding="utf-8")

    bins = tmp_path / "bin"
    bins.mkdir()
    executable(
        bins / "ip",
        """case "$*" in
"-4 addr show nv2blph") echo "inet 10.252.246.1/30 dev nv2blph";;
"netns exec nv2-browserless-prod ip -4 route get 10.252.246.1")
  echo "10.252.246.1 dev nv2blpn src 10.252.246.2";;
*) exit 45;;
esac
""",
    )
    executable(bins / "ss", f"printf '%s\\n' '{ss_output}'\n")
    executable(bins / "sing-box", "exit 0\n")
    env = dict(os.environ, PATH=f"{bins}:{os.environ['PATH']}")
    return subprocess.run(
        ["/bin/bash", str(script_path)],
        text=True, capture_output=True, env=env, cwd=ROOT, check=False,
    )


@pytest.mark.parametrize("bind", ["0.0.0.0:19682", "[::]:19682", "10.252.246.1:19682"])
def test_preflight_rejects_port_occupied_by_any_binding(tmp_path: Path, bind: str):
    result = run_preflight(tmp_path, f"LISTEN 0 4096 {bind} 0.0.0.0:*")
    assert result.returncode == 32, (bind, result.returncode, result.stdout, result.stderr)


def test_preflight_succeeds_when_candidate_port_is_vacant(tmp_path: Path):
    result = run_preflight(tmp_path, "")
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert '"twoHopExecutionProven":false' in result.stdout
