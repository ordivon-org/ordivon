from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "consumers" / "x-reality"

def test_authority_is_transport_only_and_exact():
    a = json.loads((X / "config" / "authority.json").read_text())
    assert a["listen"] == {"host":"127.0.0.1","port":19681,"protocol":"http"}
    assert a["allowedHttpsDomains"] == ["api.x.com"]
    assert a["directFallback"] is False
    assert a["authenticationAuthority"] == {"separate": True, "transportConsumerOwnsCredential": False, "userContextProven": False}

def test_egress_uses_shared_carrier_and_rejects_unknown():
    e = json.loads((X / "config" / "egress.json").read_text())
    assert e["outbounds"] == [{"type":"http","tag":"provider-carrier","server":"10.252.246.2","server_port":19680}]
    route = e["route"]["rules"][0]
    assert route["domain"] == ["api.x.com"]
    assert route["port"] == 443
    assert e["route"]["rules"][-1]["action"] == "reject"

def test_semantic_service_soft_depends_on_carrier():
    u = (X / "systemd" / "network-v2-x-reality-egress.service").read_text()
    assert "Wants=network-v2-browserless-provider-carrier.service" in u
    assert "Requires=network-v2-browserless-provider-carrier.service" not in u
    assert "After=network-v2-browserless-provider-carrier.service" in u

def test_readiness_has_no_credential_surface():
    r = (X / "ready.sh").read_text()
    assert "api.x.com/2/users/me" in r
    assert 'http_connect' in r
    assert '"$connect" == 200' in r
    assert "--noproxy ''" in r
    assert 'authenticationAttempted":false' in r
    assert 'credentialMaterialized":false' in r
    assert 'userContextProven":false' in r
    lowered = (X / "README.md").read_text().lower()
    assert "does not read" in lowered



import os
import subprocess
import pytest


@pytest.mark.parametrize(
    ("connect_status", "expected_ready"),
    [
        ("407", False),  # Proxy explicitly denied the HTTPS tunnel.
        ("000", False),  # No HTTP CONNECT evidence exists.
        ("200", True),   # Upstream 401 came through the expected tunnel.
    ],
)
def test_readiness_requires_https_tunnel_and_no_direct_bypass(
    tmp_path: Path, connect_status: str, expected_ready: bool
) -> None:
    """Run the physical readiness Bash entrypoint with isolated external commands."""
    tools = tmp_path / "bin"
    tools.mkdir()
    scripts = {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ss": "#!/bin/sh\necho 'LISTEN 0 32 127.0.0.1:19681'\n",
        "sleep": "#!/bin/sh\nexit 0\n",
        "curl": (
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "args = sys.argv[1:]\n"
            "with open(os.environ['X_READY_CURL_LOG'], 'a') as f:\n"
            "    f.write(json.dumps(args)+'\\n')\n"
            "if any('api.x.com' in x for x in args):\n"
            "    receipt = '401 ' + os.environ['X_CONNECT_STATUS']\n"
            "    print(receipt if any('%{http_connect}' in arg for arg in args) else '401', end='')\n"
            "    sys.exit(0)\n"
            "sys.exit(7)\n"
        ),
    }
    for name, content in scripts.items():
        entry = tools / name
        entry.write_text(content)
        entry.chmod(0o755)
    logfile = tmp_path / "curl.jsonl"
    env = {
        **os.environ,
        "PATH": f"{tools}:{os.environ.get('PATH','')}",
        "X_READY_CURL_LOG": str(logfile),
        "X_CONNECT_STATUS": connect_status,
        "NO_PROXY": "api.x.com,example.com",
        "no_proxy": "api.x.com,example.com",
    }
    result = subprocess.run(
        ["/usr/bin/bash", str(X / "ready.sh")],
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert (result.returncode == 0) is expected_ready, (
        result.stdout, result.stderr
    )
    calls = [json.loads(line) for line in logfile.read_text().splitlines()]
    assert len(calls) >= 2
    for call in calls:
        assert "-q" in call and "--noproxy" in call
        assert call[call.index("--noproxy") + 1] == ""
    assert any("%{http_connect}" in arg for arg in calls[0])
    if expected_ready:
        payload = json.loads(result.stdout)
        assert payload["standing"] == "READY"
        assert payload["xHttpStatus"] == 401
        assert payload["unknownDestination"] == "REJECTED"
        assert payload["directFallback"] is False
