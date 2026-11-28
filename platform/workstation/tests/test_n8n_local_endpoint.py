"""Operator CLI admission and native psql argument binding, without live effects."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CALLERS = (
    "accept-n8n-distribution-adapter-smoke.sh",
    "converge-n8n-distribution-adapter-smoke.sh",
    "converge-n8n-integration-smoke.sh",
    "verify-n8n-rootless.sh",
)


def fixture_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    shim = tmp_path / "bin"
    shim.mkdir()
    marker = tmp_path / "called"
    for cmd in ("runuser", "curl", "install", "mktemp"):
        p = shim / cmd
        p.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$EFFECT_MARKER"\nexit 73\n')
        p.chmod(0o755)
    env = {**os.environ, "PATH": f"{shim}:/usr/bin:/bin",
           "EFFECT_MARKER": str(marker)}
    for k in ("PGHOST", "PGPORT", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        env.pop(k, None)
    return env, marker


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("values", [
    {},
    {"PGHOST": "/tmp/socket"},
    {"PGPORT": "14550"},
    {"PGHOST": "remote.example.invalid", "PGPORT": "14550"},
    {"PGHOST": "/tmp/socket,remote.example.invalid", "PGPORT": "14550"},
    {"PGHOST": "/tmp/socket", "PGPORT": "65536"},
    {"PGHOST": "/tmp/socket", "PGPORT": "14550 -c bad"},
])
def test_invalid_or_absent_endpoint_cannot_enter_effects(
    tmp_path: Path, caller: str, values: dict[str, str],
) -> None:
    env, marker = fixture_env(tmp_path)
    result = subprocess.run(
        ["/bin/bash", str(SCRIPTS / caller)], env={**env, **values},
        capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode != 0
    assert "PGHOST" in result.stderr or "PGPORT" in result.stderr or (
        "invalid local PostgreSQL endpoint" in result.stderr
    )
    assert not marker.exists()


def test_actual_acceptance_first_psql_uses_explicit_endpoint(tmp_path: Path) -> None:
    env, marker = fixture_env(tmp_path)
    # The real script checks loopback readiness before the first SQL read.
    # Simulate only that observation; the next stub stops all further effects.
    (tmp_path / "bin/curl").write_text("#!/bin/sh\nexit 0\n")
    (tmp_path / "bin/runuser").write_text(
        '#!/bin/sh\n'
        'if [ "${PGHOSTADDR+x}${PGSERVICE+x}${PGSERVICEFILE+x}" ]; then exit 74; fi\n'
        'printf "%s\\n" "$@" > "$EFFECT_MARKER"\nexit 73\n'
    )
    result = subprocess.run(
        ["/bin/bash", str(SCRIPTS / CALLERS[0])],
        env={
            **env, "PGHOST": "/tmp/qualification-socket", "PGPORT": "15999",
            "PGHOSTADDR": "127.0.0.1", "PGSERVICE": "foreign",
            "PGSERVICEFILE": "/tmp/nonexistent-foreign-service",
        },
        capture_output=True, text=True, timeout=5, check=False,
    )
    if os.geteuid() != 0:
        assert result.returncode == 2
        assert "must run as root" in result.stderr
        assert not marker.exists()
        return
    assert result.returncode == 73
    args = marker.read_text().splitlines()
    assert args[:10] == [
        "-u", "postgres", "--", "psql", "-h", "/tmp/qualification-socket",
        "-p", "15999", "-d", "n8n",
    ]
