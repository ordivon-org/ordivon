"""Claude client consumer contract: explicit CONNECT/TLS + no direct fallback.

Runs existing Bash readiness with mocked *physical* providers, not a new runner.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "consumers/claude/ready.sh"


def _shim(root: Path, name: str, body: str) -> None:
    file = root / name
    file.write_text("#!/usr/bin/env bash\n" + body)
    file.chmod(0o755)


def _readiness(tmp_path: Path, scenario: str) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    mock = tmp_path / "bin"
    mock.mkdir()
    _shim(mock, "systemctl", "exit 0\n")
    _shim(mock, "ss", """printf 'LISTEN 0 64 127.0.0.1:19481 0.0.0.0:*\\nLISTEN 0 64 10.252.247.1:19482 0.0.0.0:*\\n'\n""")
    _shim(mock, "sleep", "exit 0\n")
    _shim(mock, "ip", """
if [[ "$1" == "netns" && "$2" == "exec" ]];then
  shift 3
  exec "$@"
fi
if [[ "$1" == "-4" || "$1" == "-6" ]];then
  exit 0
fi
exit 75
""")
    _shim(mock, "curl", r"""
printf '%s\n' "$*" >> "$CLAUDE_CURL_RECORD"
joined=" $* "
if [[ "$joined" == *"https://example.com/"* ]];then
  case "$MOCK_CLAUDE_SCENARIO" in
    valid|unknown_connect_denied)
      # The proxy explicitly refused HTTPS CONNECT. Curl may exit 56
      # but still emits its documented per-attempt CONNECT receipt.
      printf '000|403'
      exit 56;;
    unknown_transport_failure)
      printf '000|000'
      exit 56;;
    unknown_proxy_auth_failure)
      printf '000|407'
      exit 56;;
    unknown_trailing_delimiter)
      printf '000|403|'
      exit 56;;
    unknown_multiline_receipt)
      printf '000|403\n000|000'
      exit 56;;
    unknown_tls_handshake_failure)
      # Independently observed live probe: CONNECT=200, TLS handshake failed
      # (curl exit35). Transport failure does not authenticate policy reject.
      printf '000|200'
      exit 35;;
    unknown_origin_forbidden|unknown_http_forbidden)
      # The origin replied 403 through an ACCEPTED CONNECT tunnel.
      printf '403|200'
      exit 0;;
    unknown_malformed)
      printf 'malformed'
      exit 56;;
    unknown_bad_http)
      printf '500|403'
      exit 56;;
    unknown_extra_receipt)
      printf '000|403|extra'
      exit 56;;
    *) exit 22;;
  esac
fi
if [[ "$joined" == *"https://api.anthropic.com/"* ]];then
  if [[ "$joined" != *" -x "* && "$joined" != *" --proxy "* ]];then
    if [[ "$MOCK_CLAUDE_SCENARIO" == direct_http_forbidden ]];then
      # Direct TLS succeeded: HTTP status is 403, not network isolation.
      [[ "$joined" == *" -f"* ]] && exit 22
      exit 0
    fi
    exit 28
  fi
  case "$MOCK_CLAUDE_SCENARIO" in
    connect_denied) printf '404|403|0';;
    tls_missing) printf '404|200|0';;
    gateway_failure) printf '502|200|0.5';;
    timeout) exit 28;;
    malformed) printf 'garbage';;
    *) printf '404|200|0.5';;
  esac
  exit 0
fi
if [[ "$joined" == *"https://claude.ai/install.sh"* ]];then
  case "$MOCK_CLAUDE_SCENARIO" in
    installer_bad_redirect) loc='https://evil.example.com/';;
    *) loc='https://downloads.claude.ai/releases/latest';;
  esac
  case "$MOCK_CLAUDE_SCENARIO" in
    installer_tls_missing) metrics='302|200|0';;
    installer_connect_denied) metrics='302|403|0';;
    installer_bad_status) metrics='200|200|0.7';;
    *) metrics='302|200|0.7';;
  esac
  i=1
  prev=''
  for x in "$@";do
    if [[ "$prev" == "-D" || "$prev" == "--dump-header" ]];then
      printf 'HTTP/2 302\r\nlocation: %s\r\n\r\n' "$loc" > "$x"
    fi
    prev="$x"
  done
  if [[ "$joined" != *" -D "* && "$joined" != *" --dump-header "* ]];then
    printf 'HTTP/2 302\r\nlocation: %s\r\n\r\n' "$loc"
  fi
  printf '%s' "$metrics"
  exit 0
fi
exit 88
""")
    log = tmp_path / "curl.log"
    proc = subprocess.run(
        ["/usr/bin/bash", str(SCRIPT)],
        env={
            **os.environ,
            "PATH": f"{mock}:/usr/bin:/bin",
            "MOCK_CLAUDE_SCENARIO": scenario,
            "CLAUDE_CURL_RECORD": str(log),
            "NO_PROXY": "*",
            "no_proxy": "*",
        },
        text=True,
        capture_output=True,
        timeout=16,
        check=False,
    )
    return proc, log.read_text().splitlines() if log.exists() else []


def test_live_transport_shape_and_isolated_proxy_contract(tmp_path):
    outcome, calls = _readiness(tmp_path, "valid")
    assert outcome.returncode == 0, (outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' in outcome.stdout
    assert '"directFallback":false' in outcome.stdout
    assert '"apiHttpStatus":404' in outcome.stdout
    api = [s for s in calls if "https://api.anthropic.com/" in s and " -x " in " "+s]
    installer = [s for s in calls if "https://claude.ai/install.sh" in s]
    assert api and installer
    for call in api + installer:
        assert "-x http://10.252.247.1:19482" in call
        assert "--noproxy" in call
        assert "%{http_connect}" in call
        assert "%{time_appconnect}" in call
        assert "--insecure" not in call
    assert all("https://example.com/" not in a or "-x http://10.252.247.1:19482" in a for a in calls)
    direct = [s for s in calls if "https://api.anthropic.com/" in s and " -x " not in " "+s]
    unknown = [s for s in calls if "https://example.com/" in s]
    assert len(direct) == 1 and "--noproxy *" in direct[0]
    assert len(unknown) == 1 and "--noproxy" in unknown[0]
    assert "%{http_connect}" in unknown[0]
    assert "%{http_code}" in unknown[0]
    assert not any("-fsS" in call for call in direct + unknown)
    assert all(" -q " in " "+line for line in calls)


@pytest.mark.parametrize("fault", [
    "connect_denied",
    "tls_missing",
    "gateway_failure",
    "timeout",
    "malformed",
    "installer_tls_missing",
    "installer_connect_denied",
    "installer_bad_status",
    "installer_bad_redirect",
])
def test_real_consumer_readiness_fails_closed_for_upstream_faults(tmp_path, fault):
    outcome, calls = _readiness(tmp_path, fault)
    assert outcome.returncode != 0, (fault, outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' not in outcome.stdout
    assert calls
    assert not any("--insecure" in line for line in calls)


@pytest.mark.parametrize(
    "scenario",
    (
        "unknown_transport_failure",
        "unknown_proxy_auth_failure",
        "unknown_trailing_delimiter",
        "unknown_multiline_receipt",
        "unknown_tls_handshake_failure",
        "unknown_origin_forbidden",
        "unknown_http_forbidden",
        "unknown_malformed",
        "unknown_bad_http",
        "unknown_extra_receipt",
    ),
)
def test_unknown_destination_requires_explicit_connect_policy_rejection(
    tmp_path: Path, scenario: str
) -> None:
    """A curl failure is not policy proof; status 403 from origin is not denial."""
    outcome, calls = _readiness(tmp_path, scenario)
    assert outcome.returncode != 0, (scenario, outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' not in outcome.stdout
    attempts = [s for s in calls if "https://example.com/" in s]
    assert len(attempts) == 1
    assert "-x http://10.252.247.1:19482" in attempts[0]
    assert "--noproxy" in attempts[0]
    assert "--insecure" not in attempts[0]


@pytest.mark.parametrize("scenario", ["direct_http_forbidden", "unknown_http_forbidden"])
def test_http_denial_is_not_an_isolation_or_allowlist_witness(tmp_path, scenario):
    # A completed TLS exchange with HTTP 403 is a reachable endpoint,
    # even when curl -f turns the 403 into an exit-22 status.
    outcome, calls = _readiness(tmp_path, scenario)
    assert outcome.returncode != 0, (scenario, outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' not in outcome.stdout
    assert calls


def test_existing_production_components_and_authority_remain_unchanged():
    script = SCRIPT.read_text()
    assert "grep -q" not in script
    assert "grep -F '127.0.0.1:19481' >/dev/null" in script
    assert "grep -F '10.252.247.1:19482' >/dev/null" in script
    assert "%{http_connect}" in script
    assert "%{time_appconnect}" in script
    assert "--noproxy" in script
    assert "nv2-claude-client" in script
    assert "https://downloads" in script
    for forbidden in (
        "wg-quick up",
        "ip route replace",
        "systemctl restart",
        "Authorization:",
        "--insecure",
    ):
        assert forbidden not in script


def test_n08_source_consumer_contract_matches_install_and_proxy_policy() -> None:
    """The registered consumer route is checked, not merely narrated."""
    import json

    plan = json.loads((ROOT / "planning/lego-plan-r1.json").read_text())
    n08 = next(row for row in plan["nodes"] if row["id"] == "N08")
    consumers = "/".join(n08["consumers"])
    taskfile = (ROOT / "Taskfile.yml").read_text()
    readiness = SCRIPT.read_text()
    assert "consumer:claude:materialize" in taskfile
    assert (
        "install -m 0755 consumers/claude/ready.sh "
        "/usr/local/libexec/network-v2/claude-ready"
    ) in taskfile
    assert "consumer:claude:materialize" in consumers
    assert "test_claude_egress_readiness_consumer.py" in consumers
    assert "CONNECT=403" in n08["behavioralContract"][0]
    assert "CONNECT=407" in n08["behavioralContract"][0]
    assert "CONNECT=200" in n08["behavioralContract"][0]
    assert "%{http_code}|%{http_connect}" in readiness
    assert '[[ ! "$deny_receipt" =~ ^(000|403)\\|403$ ]]' in readiness
    assert all("live" not in x.lower() for x in n08["consumers"])
