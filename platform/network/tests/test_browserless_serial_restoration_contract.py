"""Network N04: optimized Python cannot bypass restoration namespace identity.

The acceptance gate's live systemd/curl effects are deliberately NOT invoked:
only its exact embedded source-bound Python proof is replayed against isolated
JSON provider fixtures. This is not production namespace verification.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "consumers/browserless/acceptance/serial-browserless.sh"
)
START = "  python3 - <<'PY'\n"
END = "\nPY\n"


def _restoration_proof(current_namespace: object, expected_namespace: object) -> subprocess.CompletedProcess[str]:
    source = SCRIPT.read_text()
    assert source.count(START) == 1
    body = source.split(START, 1)[1].split(END, 1)[0]
    runtime = {"namespace": current_namespace, "endpointIp": "10.1.0.1", "recoveryState": "active"}
    endpoint = {} if expected_namespace is None else {"networkNamespace": expected_namespace}
    config = {"browserSubstrate": {"endpoints": [endpoint]}}
    # Builtins interception isolates the original source from live /etc and /root.
    # No implementation or verifier rule is reimplemented in this test.
    prefix = (
        "import builtins, io\n"
        f"_files={{'/root/.local/state/ordivon-workstation/exterior-anchors/chatgpt-browserless-r1/runtime-state.json':{json.dumps(json.dumps(runtime))},"
        f"'/etc/ordivon/agent-automation-browserless.json':{json.dumps(json.dumps(config))}}}\n"
        "_real_open=builtins.open\n"
        "def _fixture_open(path,*args,**kwargs):\n"
        "    if path not in _files: raise ValueError('unexpected file: '+str(path))\n"
        "    return io.StringIO(_files[path])\n"
        "builtins.open=_fixture_open\n"
    )
    return subprocess.run(
        [sys.executable, "-O", "-c", prefix + body],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_restoration_identity_accepts_matching_producer_and_config_under_optimization() -> None:
    outcome = _restoration_proof("nv2-browserless-prod", "nv2-browserless-prod")
    assert outcome.returncode == 0, outcome.stderr
    assert "restored_namespace=nv2-browserless-prod" in outcome.stdout


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        ("nv2-browserless-prod", "attacker-namespace"),
        ("untrusted-namespace", "nv2-browserless-prod"),
        ("nv2-browserless-prod", None),
    ],
)
def test_restoration_identity_mismatch_fails_closed_even_under_optimization(
    current: str, expected: str | None
) -> None:
    outcome = _restoration_proof(current, expected)
    assert outcome.returncode != 0, outcome.stdout
    assert "restored_namespace=" not in outcome.stdout


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        ("", ""),
        ("   ", "   "),
        (None, None),
        (37, 37),
    ],
)
def test_restoration_identity_requires_a_nonempty_string_type_under_optimization(
    current: object, expected: object
) -> None:
    outcome = _restoration_proof(current, expected)
    assert outcome.returncode != 0, outcome.stdout
    assert "restored_namespace=" not in outcome.stdout
