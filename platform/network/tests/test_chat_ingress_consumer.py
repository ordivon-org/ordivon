from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / 'consumers' / 'chat-ingress'


def test_chat_ingress_consumer_is_scoped_to_existing_browserless_network_authority():
    cfg = json.loads((CONSUMER / 'config' / 'egress.json').read_text())
    assert cfg['schemaVersion'] == 1
    assert cfg['kind'] == 'ordivon.network-v2.chat-ingress-egress'
    assert cfg['listen'] == {'host': '127.0.0.1', 'port': 19081, 'protocol': 'mixed'}
    assert cfg['networkAuthority'] == {
        'kind': 'network-v2',
        'name': 'browserless-prod',
        'namespace': 'nv2-browserless-prod',
        'serviceUnit': 'network-v2-browserless.target',
    }
    assert cfg['directFallback'] is False
    assert cfg['allowedOrigins'] == ['https://chatgpt.com']


def test_chat_ingress_units_relay_only_to_namespace_local_proxy_and_do_not_change_host_routes():
    proxy = (CONSUMER / 'systemd' / 'network-v2-chat-ingress-proxy.service').read_text()
    relay = (CONSUMER / 'systemd' / 'network-v2-chat-ingress-relay.service').read_text()
    target = (CONSUMER / 'systemd' / 'network-v2-chat-ingress.target').read_text()

    assert 'NetworkNamespacePath=/run/netns/nv2-browserless-prod' in proxy
    assert '127.0.0.1:19080' in proxy
    assert '127.0.0.1:19081' in relay
    assert 'systemd-socket-proxyd 127.0.0.1:19080' in relay
    assert 'BindsTo=network-v2-browserless.target' in proxy
    assert 'BindsTo=network-v2-browserless.target' in relay
    combined = '\n'.join((proxy, relay, target)).lower()
    for forbidden in ('ip route replace', 'route add', 'netsh', 'proxyenable', 'wg-quick up'):
        assert forbidden not in combined


def test_chat_ingress_has_standard_network_v2_lifecycle_tasks_and_readiness():
    taskfile = (ROOT / 'Taskfile.yml').read_text()
    for task in (
        'consumer:chat-ingress:validate:',
        'consumer:chat-ingress:materialize:',
        'consumer:chat-ingress:start:',
        'consumer:chat-ingress:ready:',
        'consumer:chat-ingress:stop:',
    ):
        assert task in taskfile
    ready = (CONSUMER / 'ready.sh').read_text()
    assert 'network-v2-chat-ingress.target' in ready
    assert '127.0.0.1:19081' in ready
    assert 'https://chatgpt.com/' in ready
    assert '-I' in ready
    assert 'POST' not in ready


def test_relay_waits_for_namespace_proxy_and_target_is_enableable():
    relay = (CONSUMER / 'systemd' / 'network-v2-chat-ingress-relay.service').read_text()
    target = (CONSUMER / 'systemd' / 'network-v2-chat-ingress.target').read_text()
    assert 'ExecStartPre=' in relay
    assert '19080' in relay.split('ExecStartPre=', 1)[1]
    assert '[Install]' in target
    assert 'WantedBy=multi-user.target' in target


@pytest.mark.parametrize(
    ("receipt", "exit_code", "ready"),
    [
        ("403 200", 0, True),  # auth challenge is transport, not identity proof
        ("000 407", 0, False),  # forbidden CONNECT is not a healthy tunnel
        ("502 200", 0, False),  # bad upstream is not application readiness
        ("200 000", 0, False),  # origin-looking HTTP alone is insufficient
        ("200 200 extra", 0, False),  # malformed status projection fails closed
        ("200 200", 7, False),  # curl failure cannot be hidden by output text
    ],
)
def test_chat_ingress_ready_requires_valid_connect_and_origin_pair(
    tmp_path: Path, receipt: str, exit_code: int, ready: bool
) -> None:
    # Actual Bash consumer invocation; fake only external network and systemd.
    bin_path = tmp_path / "bin"
    bin_path.mkdir()
    scripts = {
        "systemctl": "#!/bin/sh\nexit 0\n",
        "ss": "#!/bin/sh\necho '127.0.0.1:19081'\n",
        "curl": (
            "#!/bin/sh\n"
            "printf '%s\n' \"$*\" >> \"$CHAT_CURL_CALLS\"\n"
            "printf '%s' \"$CHAT_RECEIPT\"\n"
            "exit \"$CHAT_EXIT\"\n"
        ),
    }
    for name, source in scripts.items():
        path = bin_path / name
        path.write_text(source, encoding="utf-8")
        path.chmod(0o755)
    calls = tmp_path / "curl-args.txt"
    proc = subprocess.run(
        ["/usr/bin/bash", str(CONSUMER / "ready.sh")],
        env={
            **os.environ,
            "PATH": str(bin_path) + os.pathsep + os.environ.get("PATH", ""),
            "CHAT_CURL_CALLS": str(calls),
            "CHAT_RECEIPT": receipt,
            "CHAT_EXIT": str(exit_code),
        },
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    assert (proc.returncode == 0) is ready, (receipt, proc.stdout, proc.stderr)
    if ready:
        payload = json.loads(proc.stdout)
        assert payload["standing"] == "READY"
        assert payload["httpStatus"] == 403
        assert payload["connectStatus"] == 200
    else:
        assert '"standing":"READY"' not in proc.stdout
    recorded = calls.read_text(encoding="utf-8")
    assert "--noproxy" in recorded and "--proxy" in recorded
    assert "%{http_connect}" in recorded
    assert "-q" in recorded
