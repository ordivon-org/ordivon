#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

ACCOUNT_TOKEN_FILE = Path('/root/.config/ordivon/secrets/cloudflare-account-api-token.json')
DEFAULT_TTL_SECONDS = 300
MAX_TTL_SECONDS = 900
DEFAULT_MAX_BYTES = 8 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def validate_digest(value: str) -> str:
    if not isinstance(value, str) or not value.startswith('sha256:'):
        raise ValueError('digest must use sha256:<hex>')
    raw = value[7:]
    if len(raw) != 64 or any(ch not in '0123456789abcdef' for ch in raw):
        raise ValueError('sha256 digest must be 64 lowercase hex characters')
    return raw


def load_operator_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if value.get('schemaVersion') != 1 or value.get('kind') != 'ordivon.artifact-r2-mailbox-operator-config':
        raise ValueError('R2 mailbox operator config kind/version is invalid')
    if value.get('provider') != 'cloudflare-r2':
        raise ValueError('R2 mailbox provider must be cloudflare-r2')
    if value.get('bucket') != 'ordivon-artifacts':
        raise ValueError('R2 mailbox bucket is not the frozen bounded bucket')
    if value.get('credentialRef') != 'cloudflare-account-api-token':
        raise ValueError('R2 mailbox credential ref is not the Cloudflare account API-token authority')
    if value.get('credentialFile') != str(ACCOUNT_TOKEN_FILE):
        raise ValueError('R2 mailbox credential file does not match the account API-token authority')
    if value.get('objectPrefix') != 'objects/sha256':
        raise ValueError('R2 mailbox object prefix is not content-addressed')
    if value.get('maxBytes') != DEFAULT_MAX_BYTES:
        raise ValueError('R2 mailbox maxBytes drifted')
    bounded_ttl(value.get('defaultCapabilityTtlSeconds'))
    authorities = value.get('allowedTargetAuthorities')
    if authorities != ['artifact-golden-r1']:
        raise ValueError('R2 mailbox target authority scope drifted')
    return value


def content_descriptor(data: bytes, media_type: str) -> dict[str, Any]:
    if not isinstance(media_type, str) or not media_type or '/' not in media_type:
        raise ValueError('mediaType must be a non-empty media type')
    return {
        'mediaType': media_type,
        'digest': 'sha256:' + sha256_bytes(data),
        'size': len(data),
    }


def validate_descriptor(value: dict[str, Any], *, max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError('descriptor must be an object')
    validate_digest(value.get('digest'))
    size = value.get('size')
    if not isinstance(size, int) or size < 0:
        raise ValueError('descriptor size must be a non-negative integer')
    if size > max_bytes:
        raise ValueError('descriptor exceeds configured maximum bytes')
    media = value.get('mediaType')
    if not isinstance(media, str) or not media or '/' not in media:
        raise ValueError('descriptor mediaType is invalid')
    return {'mediaType': media, 'digest': value['digest'], 'size': size}


def object_key(descriptor: dict[str, Any]) -> str:
    descriptor = validate_descriptor(descriptor)
    return 'objects/sha256/' + validate_digest(descriptor['digest'])


def verify_exact_bytes(data: bytes, descriptor: dict[str, Any], *, max_bytes: int = DEFAULT_MAX_BYTES) -> dict[str, Any]:
    descriptor = validate_descriptor(descriptor, max_bytes=max_bytes)
    if len(data) > max_bytes:
        raise ValueError('download exceeds configured maximum bytes')
    if len(data) != descriptor['size']:
        raise ValueError(f'exact size mismatch expected={descriptor["size"]} observed={len(data)}')
    observed = 'sha256:' + sha256_bytes(data)
    if observed != descriptor['digest']:
        raise ValueError('exact sha256 mismatch')
    return {'status': 'EXACT', 'digest': observed, 'size': len(data)}


def reconcile_existing(existing: bytes | None, candidate: bytes, descriptor: dict[str, Any]) -> dict[str, Any]:
    verify_exact_bytes(candidate, descriptor)
    if existing is None:
        return {'standing': 'CREATE_ALLOWED', 'effect': 'CREATE_ONCE'}
    try:
        verify_exact_bytes(existing, descriptor)
    except ValueError:
        return {'standing': 'CORRUPT_CONFLICT', 'effect': 'DO_NOT_OVERWRITE'}
    if existing != candidate:
        return {'standing': 'CORRUPT_CONFLICT', 'effect': 'DO_NOT_OVERWRITE'}
    return {'standing': 'RECOVERED_EXISTING', 'effect': 'NO_WRITE'}


def bounded_ttl(seconds: int) -> int:
    if not isinstance(seconds, int) or seconds < 1 or seconds > MAX_TTL_SECONDS:
        raise ValueError(f'ttlSeconds must be between 1 and {MAX_TTL_SECONDS}')
    return seconds


def temp_credential_request(*, bucket: str, parent_access_key_id: str, key: str, permission: str, ttl_seconds: int) -> dict[str, Any]:
    if not bucket or '/' in bucket:
        raise ValueError('bucket is invalid')
    if not parent_access_key_id:
        raise ValueError('parent access key id is required')
    if not key.startswith('objects/sha256/'):
        raise ValueError('temporary credential path must be content-addressed')
    if permission not in {'object-read-only', 'object-read-write'}:
        raise ValueError('unsupported temporary credential permission')
    return {
        'bucket': bucket,
        'parentAccessKeyId': parent_access_key_id,
        'permission': permission,
        'ttlSeconds': bounded_ttl(ttl_seconds),
        'objects': [key],
    }


def _aws_encode(value: str, *, path: bool = False) -> str:
    return urllib.parse.quote(value, safe='/-_.~' if path else '-_.~')


def _hmac(key: bytes, value: str) -> bytes:
    return hmac.new(key, value.encode(), hashlib.sha256).digest()


def sigv4_presign(
    *,
    method: str,
    url: str,
    access_key_id: str,
    secret_access_key: str,
    region: str,
    service: str = 's3',
    expires_seconds: int,
    timestamp: dt.datetime,
    session_token: str | None = None,
    signed_headers: dict[str, str] | None = None,
) -> str:
    if not access_key_id or not secret_access_key:
        raise ValueError('temporary S3 credentials are incomplete')
    if timestamp.tzinfo is None:
        raise ValueError('timestamp must be timezone-aware')
    if not isinstance(expires_seconds, int) or expires_seconds < 1 or expires_seconds > 604800:
        raise ValueError('SigV4 expires must be between 1 and 604800 seconds')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('presign target must be an HTTPS URL without userinfo or fragment')
    amz_date = timestamp.astimezone(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    date_stamp = amz_date[:8]
    scope = f'{date_stamp}/{region}/{service}/aws4_request'
    headers = {'host': parsed.netloc.lower()}
    for name, value in (signed_headers or {}).items():
        lname = name.strip().lower()
        if lname == 'host':
            raise ValueError('host header is derived from URL')
        headers[lname] = ' '.join(str(value).strip().split())
    signed_names = ';'.join(sorted(headers))
    canonical_headers = ''.join(f'{name}:{headers[name]}\n' for name in sorted(headers))
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.extend([
        ('X-Amz-Algorithm', 'AWS4-HMAC-SHA256'),
        ('X-Amz-Credential', f'{access_key_id}/{scope}'),
        ('X-Amz-Date', amz_date),
        ('X-Amz-Expires', str(expires_seconds)),
        ('X-Amz-SignedHeaders', signed_names),
    ])
    if session_token:
        query.append(('X-Amz-Security-Token', session_token))
    canonical_query = '&'.join(
        f'{_aws_encode(str(k))}={_aws_encode(str(v))}'
        for k, v in sorted(query, key=lambda item: (_aws_encode(str(item[0])), _aws_encode(str(item[1]))))
    )
    canonical_uri = _aws_encode(urllib.parse.unquote(parsed.path or '/'), path=True)
    canonical_request = '\n'.join([
        method.upper(), canonical_uri, canonical_query, canonical_headers, signed_names, 'UNSIGNED-PAYLOAD'
    ])
    string_to_sign = '\n'.join([
        'AWS4-HMAC-SHA256', amz_date, scope, hashlib.sha256(canonical_request.encode()).hexdigest()
    ])
    k_date = _hmac(('AWS4' + secret_access_key).encode(), date_stamp)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    k_signing = _hmac(k_service, 'aws4_request')
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    final_query = canonical_query + '&X-Amz-Signature=' + signature
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path or '/', final_query, ''))


def r2_object_url(account_id: str, bucket: str, key: str) -> str:
    if len(account_id) != 32 or any(ch not in '0123456789abcdef' for ch in account_id.lower()):
        raise ValueError('Cloudflare account id must be 32 hex characters')
    if not bucket or '/' in bucket:
        raise ValueError('bucket is invalid')
    if not key.startswith('objects/sha256/'):
        raise ValueError('R2 mailbox key must be content-addressed')
    return f'https://{account_id}.r2.cloudflarestorage.com/{_aws_encode(bucket, path=True)}/{_aws_encode(key, path=True)}'


def validate_r2_object_url(
    url: str, *, account_id: str, bucket: str, key: str
) -> dict[str, str]:
    parsed = urllib.parse.urlsplit(url)
    expected_host = f'{account_id}.r2.cloudflarestorage.com'.lower()
    expected_path = '/' + _aws_encode(bucket, path=True) + '/' + _aws_encode(key, path=True)
    if parsed.scheme != 'https' or parsed.hostname != expected_host:
        raise ValueError('R2 capability URL host is not the exact account R2 endpoint')
    if parsed.port not in (None, 443) or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('R2 capability URL contains forbidden authority components')
    if parsed.path != expected_path:
        raise ValueError('R2 capability URL path does not match exact bucket/object scope')
    return {'scheme': 'https', 'host': expected_host, 'path': expected_path}


def transfer_intent(
    *, descriptor: dict[str, Any], target_authority: str, relative_object: str
) -> dict[str, Any]:
    descriptor = validate_descriptor(descriptor)
    if not target_authority or not isinstance(target_authority, str):
        raise ValueError('target authority is required')
    if not relative_object or not isinstance(relative_object, str) or relative_object.startswith('/') or '..' in Path(relative_object).parts:
        raise ValueError('relative object must be a safe relative path')
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.artifact-r2-mailbox-transfer-intent',
        'content': descriptor,
        'targetAuthority': target_authority,
        'relativeObject': relative_object,
        'transport': {
            'provider': 'cloudflare-r2',
            'objectKey': object_key(descriptor),
        },
    }


def capability_projection(*, operation: str, url: str, descriptor: dict[str, Any], required_headers: dict[str, str], expires_at: str) -> dict[str, Any]:
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.artifact-r2-mailbox-capability',
        'truthRole': 'ephemeral-transport-capability-not-artifact-authority',
        'operation': operation,
        'url': url,
        'content': validate_descriptor(descriptor),
        'objectKey': object_key(descriptor),
        'requiredHeaders': required_headers,
        'expiresAt': expires_at,
        'nonClaims': ['artifact-acceptance', 'input-authority-commit', 'provider-credential-identity'],
    }


def durable_capability_summary(capability: dict[str, Any]) -> dict[str, Any]:
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.artifact-r2-mailbox-capability-summary',
        'truthRole': 'durable-transport-intent-without-bearer-capability',
        'operation': capability['operation'],
        'content': capability['content'],
        'objectKey': capability['objectKey'],
        'expiresAt': capability['expiresAt'],
        'requiredHeaderNames': sorted(capability.get('requiredHeaders', {})),
        'capabilityUrlPersisted': False,
    }


def parse_utc_timestamp(value: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('timestamp must be UTC Z form')
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as error:
        raise ValueError('timestamp is invalid') from error
    return parsed.astimezone(dt.timezone.utc)


def capability_standing(capability: dict[str, Any], *, now: dt.datetime | None = None) -> dict[str, Any]:
    if capability.get('kind') != 'ordivon.artifact-r2-mailbox-capability':
        raise ValueError('capability kind is invalid')
    timestamp = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    expires = parse_utc_timestamp(capability.get('expiresAt'))
    fresh = timestamp < expires
    return {
        'standing': 'FRESH' if fresh else 'EXPIRED',
        'usableNow': fresh,
        'replayStanding': 'BOUNDED_REPLAYABLE_BEARER_CAPABILITY_NOT_SINGLE_USE',
        'expiresAt': capability['expiresAt'],
    }


def reconcile_put_effect(
    *,
    observed_existing: bytes | None,
    candidate: bytes,
    descriptor: dict[str, Any],
    observation_available: bool,
) -> dict[str, Any]:
    verify_exact_bytes(candidate, descriptor)
    if not observation_available:
        return {
            'standing': 'UNKNOWN_PROVIDER_EFFECT',
            'retryStanding': 'RECONCILE_BEFORE_RETRY',
            'safeToOverwrite': False,
        }
    disposition = reconcile_existing(observed_existing, candidate, descriptor)
    if disposition['standing'] == 'CREATE_ALLOWED':
        return {
            'standing': 'ABSENT_AFTER_OBSERVATION',
            'retryStanding': 'CREATE_ONCE_ALLOWED',
            'safeToOverwrite': False,
        }
    if disposition['standing'] == 'RECOVERED_EXISTING':
        return {
            'standing': 'COMMITTED_EXACT',
            'retryStanding': 'NO_WRITE_REQUIRED',
            'safeToOverwrite': False,
        }
    return {
        'standing': 'CONFLICTING_REMOTE_BYTES',
        'retryStanding': 'HOLD',
        'safeToOverwrite': False,
    }


def reconcile_get_effect(
    *, data: bytes | None, descriptor: dict[str, Any], observation_available: bool
) -> dict[str, Any]:
    if not observation_available:
        return {'standing': 'UNKNOWN_PROVIDER_EFFECT', 'admitToIngress': False}
    if data is None:
        return {'standing': 'REMOTE_OBJECT_ABSENT', 'admitToIngress': False}
    try:
        exact = verify_exact_bytes(data, descriptor)
    except ValueError as error:
        return {
            'standing': 'REMOTE_OBJECT_MISMATCH',
            'admitToIngress': False,
            'reason': str(error),
        }
    return {'standing': 'EXACT_BYTES_OBSERVED', 'admitToIngress': True, **exact}


def transfer_receipt(
    *, descriptor: dict[str, Any], object_key_value: str, operation: str, standing: str
) -> dict[str, Any]:
    descriptor = validate_descriptor(descriptor)
    expected_key = object_key(descriptor)
    if object_key_value != expected_key:
        raise ValueError('receipt object key does not match descriptor digest')
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.artifact-r2-mailbox-transfer-receipt',
        'truthRole': 'transport-effect-observation-not-input-authority-or-artifact-acceptance',
        'operation': operation,
        'content': descriptor,
        'objectKey': expected_key,
        'standing': standing,
        'nonClaims': [
            'presigned-url-persistence',
            'temporary-s3-credential-persistence',
            'input-authority-commit',
            'artifact-acceptance',
        ],
    }


def parse_account_token(path: Path = ACCOUNT_TOKEN_FILE) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if value.get('token_type') != 'account':
        raise RuntimeError('Cloudflare credential is not the account API-token profile')
    if any(k in value for k in ('client_id','client_secret','CF-Access-Client-Id','CF-Access-Client-Secret')):
        raise RuntimeError('Zero Trust Access service-token fields are forbidden')
    if not value.get('api_token') or not value.get('account_id'):
        raise RuntimeError('Cloudflare account API token material is incomplete')
    return value


def _provider_json(method: str, url: str, token: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body, separators=(',', ':')).encode()
    headers = {'Authorization': 'Bearer ' + token, 'User-Agent': 'ordivon-r2-mailbox/1'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read(1024 * 1024))
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read(1024 * 1024))
        except Exception:
            payload = {}
        return error.code, payload


def r2_bucket_inventory(credential_file: Path = ACCOUNT_TOKEN_FILE) -> dict[str, Any]:
    authority = parse_account_token(credential_file)
    base = str(authority.get('api_base', 'https://api.cloudflare.com/client/v4')).rstrip('/')
    code, verification = _provider_json(
        'GET',
        base + '/accounts/' + authority['account_id'] + '/tokens/verify',
        authority['api_token'],
    )
    token_result = verification.get('result') if isinstance(verification, dict) else None
    if code != 200 or verification.get('success') is not True or not isinstance(token_result, dict) or token_result.get('status') != 'active':
        raise RuntimeError('Cloudflare account API token is not currently verified active')
    code, response = _provider_json(
        'GET',
        base + '/accounts/' + authority['account_id'] + '/r2/buckets?per_page=100',
        authority['api_token'],
    )
    result = response.get('result') if isinstance(response, dict) else None
    if code != 200 or response.get('success') is not True or not isinstance(result, dict):
        raise RuntimeError('Cloudflare R2 bucket inventory is unavailable or unauthorized')
    buckets = []
    for row in result.get('buckets') or []:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str):
            continue
        buckets.append({
            key: row.get(key)
            for key in ('name', 'jurisdiction', 'location', 'storage_class', 'creation_date')
            if row.get(key) is not None
        })
    return {
        'schemaVersion': 1,
        'kind': 'ordivon.artifact-r2-mailbox-bucket-inventory',
        'truthRole': 'point-in-time-provider-resource-observation-not-bucket-selection-or-write-authority',
        'credentialKind': 'cloudflare-account-api-token',
        'accountTokenStanding': 'ACTIVE',
        'r2ReadStanding': 'READ_AUTHORIZED',
        'buckets': sorted(buckets, key=lambda row: row['name']),
        'bucketCount': len(buckets),
        'nonClaims': ['r2-write-authority', 'mailbox-bucket-selection', 'object-write-authority', 'artifact-transport-acceptance'],
    }


def mint_temporary_credentials(*, bucket: str, key: str, permission: str, ttl_seconds: int, credential_file: Path = ACCOUNT_TOKEN_FILE) -> dict[str, str]:
    authority = parse_account_token(credential_file)
    base = str(authority.get('api_base', 'https://api.cloudflare.com/client/v4')).rstrip('/')
    code, verification = _provider_json('GET', base + '/accounts/' + authority['account_id'] + '/tokens/verify', authority['api_token'])
    result = verification.get('result') if isinstance(verification, dict) else None
    if code != 200 or verification.get('success') is not True or not isinstance(result, dict) or result.get('status') != 'active' or not result.get('id'):
        raise RuntimeError('Cloudflare account API token is not currently verified active')
    request = temp_credential_request(bucket=bucket, parent_access_key_id=result['id'], key=key, permission=permission, ttl_seconds=ttl_seconds)
    code, response = _provider_json('POST', base + '/accounts/' + authority['account_id'] + '/r2/temp-access-credentials', authority['api_token'], request)
    creds = response.get('result') if isinstance(response, dict) else None
    if code != 200 or response.get('success') is not True or not isinstance(creds, dict):
        raise RuntimeError('Cloudflare R2 temporary credential mint failed')
    required = ('accessKeyId', 'secretAccessKey', 'sessionToken')
    if not all(isinstance(creds.get(k), str) and creds[k] for k in required):
        raise RuntimeError('Cloudflare R2 temporary credential response is incomplete')
    return {k: creds[k] for k in required}


def issue_capability(*, operation: str, bucket: str, descriptor: dict[str, Any], ttl_seconds: int, credential_file: Path = ACCOUNT_TOKEN_FILE, now: dt.datetime | None = None) -> dict[str, Any]:
    descriptor = validate_descriptor(descriptor)
    key = object_key(descriptor)
    if operation not in {'PUT', 'GET'}:
        raise ValueError('operation must be PUT or GET')
    permission = 'object-read-write' if operation == 'PUT' else 'object-read-only'
    ttl_seconds = bounded_ttl(ttl_seconds)
    credentials = mint_temporary_credentials(bucket=bucket, key=key, permission=permission, ttl_seconds=ttl_seconds, credential_file=credential_file)
    authority = parse_account_token(credential_file)
    timestamp = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    headers = {'If-None-Match': '*'} if operation == 'PUT' else {}
    url = sigv4_presign(
        method=operation,
        url=r2_object_url(authority['account_id'], bucket, key),
        access_key_id=credentials['accessKeyId'],
        secret_access_key=credentials['secretAccessKey'],
        session_token=credentials['sessionToken'],
        region='auto',
        expires_seconds=ttl_seconds,
        timestamp=timestamp,
        signed_headers=headers,
    )
    validate_r2_object_url(
        url, account_id=authority['account_id'], bucket=bucket, key=key
    )
    expires = timestamp + dt.timedelta(seconds=ttl_seconds)
    return capability_projection(operation=operation, url=url, descriptor=descriptor, required_headers=headers, expires_at=expires.isoformat().replace('+00:00','Z'))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    describe = sub.add_parser('describe')
    describe.add_argument('--file', type=Path, required=True)
    describe.add_argument('--media-type', required=True)
    inventory = sub.add_parser('inventory')
    inventory.add_argument('--credential-file', type=Path, default=ACCOUNT_TOKEN_FILE)
    args = parser.parse_args()
    if args.command == 'describe':
        data = args.file.read_bytes()
        print(json.dumps(content_descriptor(data, args.media_type), sort_keys=True, indent=2))
        return 0
    print(json.dumps(r2_bucket_inventory(args.credential_file), sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
