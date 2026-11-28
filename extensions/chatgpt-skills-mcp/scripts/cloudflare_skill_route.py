#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CREDENTIAL = Path('/root/.config/ordivon/secrets/cloudflare-account-api-token.json')


def load_credential(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    required = {'version', 'token_type', 'api_base', 'account_id', 'zone_id', 'zone_name', 'api_token'}
    missing = sorted(required - set(value))
    if missing:
        raise RuntimeError('credential missing fields: ' + ','.join(missing))
    if value['token_type'] != 'account':
        raise RuntimeError('credential is not account API token authority')
    if value['api_base'] != 'https://api.cloudflare.com/client/v4':
        raise RuntimeError('unexpected Cloudflare API base')
    return value


def request_json(credential: dict[str, Any], method: str, path: str, body: Any | None = None) -> tuple[int, dict[str, Any]]:
    raw = None if body is None else json.dumps(body, separators=(',', ':')).encode('utf-8')
    req = urllib.request.Request(
        credential['api_base'].rstrip('/') + path,
        data=raw,
        method=method,
        headers={
            'Authorization': 'Bearer ' + credential['api_token'],
            'Content-Type': 'application/json',
            'User-Agent': 'ordivon-skills-cloudflare-route/1',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read(2 * 1024 * 1024))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read(2 * 1024 * 1024))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        return exc.code, payload


def require_success(status: int, payload: dict[str, Any], operation: str) -> Any:
    if status < 200 or status >= 300 or payload.get('success') is not True:
        errors = [(row.get('code'), row.get('message')) for row in payload.get('errors', []) if isinstance(row, dict)]
        raise RuntimeError(f'{operation} failed: http={status} errors={errors}')
    return payload.get('result')


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def get_tunnels(cred: dict[str, Any]) -> list[dict[str, Any]]:
    status, payload = request_json(
        cred, 'GET', f"/accounts/{cred['account_id']}/cfd_tunnel?is_deleted=false&per_page=100"
    )
    result = require_success(status, payload, 'list tunnels')
    return result if isinstance(result, list) else []


def get_config(cred: dict[str, Any], tunnel_id: str) -> dict[str, Any]:
    status, payload = request_json(
        cred, 'GET', f"/accounts/{cred['account_id']}/cfd_tunnel/{tunnel_id}/configurations"
    )
    result = require_success(status, payload, 'get tunnel config')
    return result if isinstance(result, dict) else {}


def get_dns(cred: dict[str, Any], hostname: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({'name': hostname, 'per_page': 100})
    status, payload = request_json(cred, 'GET', f"/zones/{cred['zone_id']}/dns_records?{query}")
    result = require_success(status, payload, 'get DNS record')
    return result if isinstance(result, list) else []


def safe_tunnel_row(tunnel: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': tunnel.get('id'),
        'name': tunnel.get('name'),
        'status': tunnel.get('status'),
        'remoteConfig': tunnel.get('remote_config'),
        'connections': len(tunnel.get('connections') or []),
    }


def inspect(cred: dict[str, Any], hostname: str) -> dict[str, Any]:
    tunnels_out = []
    for tunnel in get_tunnels(cred):
        tunnel_id = str(tunnel.get('id') or '')
        row = safe_tunnel_row(tunnel)
        try:
            config_result = get_config(cred, tunnel_id)
            config = config_result.get('config') or {}
            ingress = config.get('ingress') or []
            row['configDigest'] = canonical_digest(config)
            row['ingress'] = [
                {
                    'hostname': item.get('hostname'),
                    'path': item.get('path'),
                    'service': item.get('service'),
                }
                for item in ingress
                if isinstance(item, dict)
            ]
        except (RuntimeError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            row['configError'] = str(exc)[:500]
        tunnels_out.append(row)
    dns = [
        {
            'id': item.get('id'),
            'type': item.get('type'),
            'name': item.get('name'),
            'content': item.get('content'),
            'proxied': item.get('proxied'),
        }
        for item in get_dns(cred, hostname)
    ]
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.skills-cloudflare-route-inspection',
        'zoneName': cred['zone_name'],
        'hostname': hostname,
        'tunnels': tunnels_out,
        'dns': dns,
        'secretMaterialReturned': False,
    }


def apply(
    cred: dict[str, Any],
    *,
    tunnel_id: str,
    hostname: str,
    service: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    if not hostname.endswith('.' + cred['zone_name']):
        raise RuntimeError('hostname is outside configured zone')
    if service != 'http://127.0.0.1:8895':
        raise RuntimeError('this helper only admits the Skills MCP origin http://127.0.0.1:8895')

    config_result = get_config(cred, tunnel_id)
    config = config_result.get('config') or {}
    actual_digest = canonical_digest(config)
    if actual_digest != expected_config_digest:
        raise RuntimeError(f'CONFIG_CHANGED expected={expected_config_digest} actual={actual_digest}')
    ingress = list(config.get('ingress') or [])
    if not ingress or not isinstance(ingress[-1], dict) or ingress[-1].get('hostname') is not None:
        raise RuntimeError('tunnel config lacks final hostname-free catch-all rule')

    matching = [item for item in ingress if isinstance(item, dict) and item.get('hostname') == hostname]
    if matching:
        if (
            len(matching) == 1
            and matching[0].get('service') == service
            and (matching[0].get('originRequest') or {}).get('httpHostHeader') == '127.0.0.1:8895'
        ):
            ingress_changed = False
        else:
            raise RuntimeError('hostname already exists with different/ambiguous ingress')
    else:
        ingress.insert(len(ingress) - 1, {'hostname': hostname, 'service': service, 'originRequest': {'httpHostHeader': '127.0.0.1:8895'}})
        new_config = dict(config)
        new_config['ingress'] = ingress
        status, payload = request_json(
            cred,
            'PUT',
            f"/accounts/{cred['account_id']}/cfd_tunnel/{tunnel_id}/configurations",
            {'config': new_config},
        )
        require_success(status, payload, 'update tunnel config')
        ingress_changed = True

    dns = get_dns(cred, hostname)
    target = tunnel_id + '.cfargotunnel.com'
    if not dns:
        status, payload = request_json(
            cred,
            'POST',
            f"/zones/{cred['zone_id']}/dns_records",
            {'type': 'CNAME', 'name': hostname, 'content': target, 'proxied': True},
        )
        dns_result = require_success(status, payload, 'create DNS record')
        dns_changed = True
        dns_id = dns_result.get('id') if isinstance(dns_result, dict) else None
    elif len(dns) == 1:
        current = dns[0]
        if current.get('type') == 'CNAME' and current.get('content') == target and current.get('proxied') is True:
            dns_changed = False
            dns_id = current.get('id')
        else:
            raise RuntimeError('hostname already has a non-matching DNS record; refusing overwrite')
    else:
        raise RuntimeError('hostname has multiple DNS records; refusing overwrite')

    final = get_config(cred, tunnel_id)
    final_config = final.get('config') or {}
    final_dns = get_dns(cred, hostname)
    final_matches = [
        item for item in final_config.get('ingress', [])
        if isinstance(item, dict) and item.get('hostname') == hostname
        and item.get('service') == service
        and (item.get('originRequest') or {}).get('httpHostHeader') == '127.0.0.1:8895'
    ]
    if len(final_matches) != 1:
        raise RuntimeError('postcondition failed: exact ingress rule not present once')
    if len(final_dns) != 1 or final_dns[0].get('type') != 'CNAME' or final_dns[0].get('content') != target:
        raise RuntimeError('postcondition failed: DNS record mismatch')
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.skills-cloudflare-route-apply',
        'hostname': hostname,
        'service': service,
        'tunnelId': tunnel_id,
        'ingressChanged': ingress_changed,
        'dnsChanged': dns_changed,
        'dnsRecordId': dns_id,
        'finalConfigDigest': canonical_digest(final_config),
        'secretMaterialReturned': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--credential-file', type=Path, default=DEFAULT_CREDENTIAL)
    sub = parser.add_subparsers(dest='command', required=True)
    ins = sub.add_parser('inspect')
    ins.add_argument('--hostname', default='skills-mcp.ordivon.com')
    app = sub.add_parser('apply')
    app.add_argument('--tunnel-id', required=True)
    app.add_argument('--hostname', default='skills-mcp.ordivon.com')
    app.add_argument('--service', default='http://127.0.0.1:8895')
    app.add_argument('--expected-config-digest', required=True)
    args = parser.parse_args()
    cred = load_credential(args.credential_file)
    out = inspect(cred, args.hostname) if args.command == 'inspect' else apply(
        cred,
        tunnel_id=args.tunnel_id,
        hostname=args.hostname,
        service=args.service,
        expected_config_digest=args.expected_config_digest,
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
