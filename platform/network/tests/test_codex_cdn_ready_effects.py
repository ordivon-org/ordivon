"""Consumer readiness is a protocol witness, not an origin string-presence test."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "consumers/codex/ready.sh"


@pytest.fixture
def fake_commands(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command, content in {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ss": "#!/bin/sh\necho 'LISTEN 127.0.0.1:19982'\n",
        "curl": """#!/usr/bin/env python3
import os, sys
url=next((a for a in sys.argv if a.startswith('https://')), '')
case=os.environ.get('CODEX_PROBE_CASE', 'ready')
if 'chatgpt.com/' in url:
    sys.stdout.write('403 200 0.5' if case=='chatgpt_denied' else '200 200 0.5')
elif 'persistent.oaistatic.com/' in url:
    if case=='cdn_tls_failure':
        sys.stdout.write('000 200 0.000000')
        sys.exit(35)
    sys.stdout.write('404 200 0.4')
elif 'example.com/' in url:
    if case=='unknown_admitted':
        sys.stdout.write('200 200 0.4')
    else:
        sys.stdout.write('000 200 0.000000')
        sys.exit(35)
else:
    sys.exit(77)
""",
    }.items():
        p = bin_dir / command
        p.write_text(content)
        p.chmod(0o755)
    return bin_dir


def invoke(bin_dir: Path, case: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "CODEX_PROBE_CASE": case,
    }
    return subprocess.run(
        ["/usr/bin/bash", str(READY)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=9,
        check=False,
    )


def test_real_protocol_contract_accepts_tls_and_explicit_denial(fake_commands: Path):
    result = invoke(fake_commands, "ready")
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["standing"] == "READY"
    assert receipt["chatgptHttp"] == 200
    assert receipt["cdnHttp"] == 404
    assert receipt["unknownDestination"] == "REJECTED"
    assert receipt["applicationProcessEgress"] == "UNKNOWN"


@pytest.mark.parametrize("case", ["cdn_tls_failure", "chatgpt_denied", "unknown_admitted"])
def test_live_witness_rejects_failed_cdn_origin_or_policy(case: str, fake_commands: Path):
    result = invoke(fake_commands, case)
    assert result.returncode != 0
    assert '"standing":"READY"' not in result.stdout
