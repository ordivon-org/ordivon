#!/usr/bin/env python3
"""Read-only Provider API auth/capacity observation under Runtime CredentialAuthority.

Run this only through workspace.execCredentialBoundTrusted. The script reads exactly
one credential from systemd's CREDENTIALS_DIRECTORY, never prints it, never mutates a
Provider, and emits only sanitized auth/capacity evidence.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request


def _credential(name: str) -> str:
    directory = os.environ.get("CREDENTIALS_DIRECTORY", "")
    if not directory:
        raise SystemExit("CREDENTIALS_DIRECTORY missing")
    path = Path(directory) / name
    if not path.is_file():
        raise SystemExit("bound credential missing")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("bound credential empty")
    return value


def _microusd(value: object) -> int | None:
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if amount < 0:
        return None
    return int(amount * Decimal(1_000_000))


def _duration_ms(value: str, observed_at_ms: int) -> int | None:
    text = value.strip().lower()
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(ms|s|m|h)", text)
    if not match:
        return None
    amount = Decimal(match.group(1))
    factor = {"ms": 1, "s": 1_000, "m": 60_000, "h": 3_600_000}[match.group(2)]
    return observed_at_ms + int(amount * factor)


def _rate_limits(headers: object, observed_at_ms: int) -> list[dict[str, object]]:
    get = getattr(headers, "get", None)
    if not callable(get):
        return []
    output: list[dict[str, object]] = []
    for kind, limit_name, remaining_name, reset_name in (
        ("requests", "x-ratelimit-limit-requests", "x-ratelimit-remaining-requests", "x-ratelimit-reset-requests"),
        ("tokens", "x-ratelimit-limit-tokens", "x-ratelimit-remaining-tokens", "x-ratelimit-reset-tokens"),
    ):
        limit_raw = get(limit_name)
        remaining_raw = get(remaining_name)
        if limit_raw is None or remaining_raw is None:
            continue
        try:
            limit = int(limit_raw)
            remaining = int(remaining_raw)
        except (TypeError, ValueError):
            continue
        reset_raw = get(reset_name)
        output.append(
            {
                "kind": kind,
                "limit": limit,
                "remaining": remaining,
                "resetsAtMs": (
                    _duration_ms(str(reset_raw), observed_at_ms)
                    if reset_raw is not None
                    else None
                ),
            }
        )
    return output


def _request(
    url: str,
    *,
    credential: str,
    auth: str,
    proxy: str | None,
) -> tuple[int, object, bytes]:
    handlers: list[urllib.request.BaseHandler] = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"https": proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)
    headers = {"Accept": "application/json", "User-Agent": "ordivon-provider-capacity-probe/1"}
    if auth == "bearer":
        headers["Authorization"] = f"Bearer {credential}"
    elif auth == "query-key":
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query.append(("key", credential))
        url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
        )
    else:
        raise ValueError(f"unsupported auth mode: {auth}")
    request = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(request, timeout=20.0) as response:
            return int(response.status), response.headers, response.read(1_048_576)
    except urllib.error.HTTPError as error:
        body = error.read(8_192)
        return int(error.code), error.headers, body
    except urllib.error.URLError:
        return 0, {}, b""


def _safe_json(body: bytes) -> object:
    try:
        return json.loads(body)
    except Exception:
        return {}


def _auth_standing(status: int) -> tuple[str, str | None]:
    if 200 <= status < 300:
        return "PASS", None
    if status in {401, 403}:
        return "HOLD", f"provider_auth_http_{status}"
    if status == 429:
        return "UNKNOWN", "provider_rate_limited_during_probe"
    if status == 0:
        return "UNKNOWN", "transport_unavailable"
    return "UNKNOWN", f"provider_probe_http_{status}"


def _parse_models(value: object, configured_model: str) -> tuple[int | None, bool | None]:
    if not isinstance(value, dict):
        return None, None
    raw = value.get("data")
    if raw is None:
        raw = value.get("models")
    if not isinstance(raw, list):
        return None, None
    ids: list[str] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        candidate = item.get("id") or item.get("name")
        if isinstance(candidate, str):
            ids.append(candidate.removeprefix("models/"))
    return len(ids), configured_model in ids


def probe(args: argparse.Namespace) -> dict[str, object]:
    key = _credential(args.credential_name)
    observed_at_ms = time.time_ns() // 1_000_000
    spend: dict[str, object] = {
        "standing": "unknown",
        "reasonCode": None,
        "remainingMicroUsd": None,
        "resetsAtMs": None,
    }
    model_count: int | None = None
    configured_model_visible: bool | None = None

    if args.probe == "deepseek-balance":
        url = "https://api.deepseek.com/user/balance"
        status, headers, body = _request(
            url, credential=key, auth="bearer", proxy=args.network_proxy
        )
        value = _safe_json(body)
        auth, failure = _auth_standing(status)
        if auth == "PASS" and isinstance(value, dict):
            available = value.get("is_available")
            if available is False:
                spend["standing"] = "exhausted"
                spend["reasonCode"] = "deepseek_balance_unavailable"
            elif available is True:
                spend["standing"] = "available"
                balances = value.get("balance_infos")
                if isinstance(balances, list):
                    for item in balances:
                        if isinstance(item, dict) and item.get("currency") == "USD":
                            spend["remainingMicroUsd"] = _microusd(item.get("total_balance"))
                            break
    elif args.probe == "openrouter-key":
        url = "https://openrouter.ai/api/v1/key"
        status, headers, body = _request(
            url, credential=key, auth="bearer", proxy=args.network_proxy
        )
        value = _safe_json(body)
        auth, failure = _auth_standing(status)
        if auth == "PASS" and isinstance(value, dict):
            data = value.get("data")
            if isinstance(data, dict):
                remaining = _microusd(data.get("limit_remaining"))
                if remaining is not None:
                    spend["remainingMicroUsd"] = remaining
                    spend["standing"] = "exhausted" if remaining == 0 else "available"
                    if remaining == 0:
                        spend["reasonCode"] = "openrouter_key_limit_exhausted"
    elif args.probe == "gemini-openai-models":
        url = "https://generativelanguage.googleapis.com/v1beta/openai/models"
        status, headers, body = _request(
            url, credential=key, auth="bearer", proxy=args.network_proxy
        )
        value = _safe_json(body)
        auth, failure = _auth_standing(status)
        if auth == "PASS":
            model_count, configured_model_visible = _parse_models(value, args.model)
    elif args.probe == "openai-models":
        url = args.base_url.rstrip("/") + "/models"
        status, headers, body = _request(
            url, credential=key, auth="bearer", proxy=args.network_proxy
        )
        value = _safe_json(body)
        auth, failure = _auth_standing(status)
        if auth == "PASS":
            model_count, configured_model_visible = _parse_models(value, args.model)
    else:
        raise ValueError(f"unsupported probe: {args.probe}")

    key = ""
    return {
        "schemaVersion": 1,
        "kind": "ordivon.provider-api-readonly-probe",
        "provider": args.provider,
        "accountRef": args.account_ref,
        "authorityRef": args.authority_ref,
        "credentialName": args.credential_name,
        "observedAtMs": observed_at_ms,
        "httpStatus": status,
        "authStanding": auth,
        "failureClass": failure,
        "modelCount": model_count,
        "configuredModel": args.model,
        "configuredModelVisible": configured_model_visible,
        "rateLimits": _rate_limits(headers, observed_at_ms),
        "spend": spend,
        "secretEmitted": False,
        "effect": "read_only",
    }


def self_test() -> None:
    assert _microusd("1.25") == 1_250_000
    assert _microusd("-1") is None
    assert _duration_ms("2s", 1_000) == 3_000
    assert _duration_ms("1.5m", 0) == 90_000
    count, visible = _parse_models(
        {"data": [{"id": "model-a"}, {"id": "model-b"}]}, "model-b"
    )
    assert count == 2 and visible is True
    count, visible = _parse_models(
        {"models": [{"name": "models/gemini-x"}]}, "gemini-x"
    )
    assert count == 1 and visible is True
    assert _auth_standing(200) == ("PASS", None)
    assert _auth_standing(401)[0] == "HOLD"
    print('{"status":"PASS","kind":"ordivon.provider-api-readonly-probe-self-test"}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider")
    parser.add_argument("--account-ref")
    parser.add_argument("--authority-ref")
    parser.add_argument("--credential-name", default="api_key")
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument(
        "--probe",
        choices=("deepseek-balance", "openrouter-key", "gemini-openai-models", "openai-models"),
    )
    parser.add_argument("--network-proxy", default="http://127.0.0.1:19881")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    required = {
        "--provider": args.provider,
        "--account-ref": args.account_ref,
        "--authority-ref": args.authority_ref,
        "--base-url": args.base_url,
        "--model": args.model,
        "--probe": args.probe,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    print(json.dumps(probe(args), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
