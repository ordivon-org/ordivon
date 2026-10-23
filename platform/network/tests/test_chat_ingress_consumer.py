from __future__ import annotations

import json
from pathlib import Path

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
