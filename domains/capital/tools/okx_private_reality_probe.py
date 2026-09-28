from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import time
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from ordivon_capital.trading.okx_readonly_client import (
    OkxReadOnlyClient,
    OkxReadOnlyCredentials,
)
from ordivon_capital.trading.private_reality import normalize_okx_observer


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _provider_call(rows: list[dict]) -> dict:
    return {
        "ok": True,
        "response": {"data": {"code": "0", "msg": "", "data": rows}},
    }


def _permission_tokens(raw: object) -> set[str]:
    return {
        token.strip().lower()
        for token in str(raw or "").replace(";", ",").split(",")
        if token.strip()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--permission-only", action="store_true")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.permission_only and args.snapshot:
        raise SystemExit("choose permission-only or snapshot, not both")
    if not args.permission_only and not args.snapshot:
        args.permission_only = True

    live_cfg = json.loads((ROOT / "config/okx_live_provider.json").read_text())
    policy = json.loads((ROOT / "config/private_reality_policy.json").read_text())
    okx_policy = policy["venues"]["OKX"]
    binding = Path(policy["credentialBindings"]["OKX"]["binding"])
    if policy.get("ownerCredentialUseMandate") != "AUTHORIZED_READ_ONLY_PRIVATE_REALITY_OBSERVATION":
        raise SystemExit("owner read-only observer mandate unavailable")
    if not binding.is_file():
        raise SystemExit("OKX observer credential binding unavailable")
    if binding.stat().st_mode & 0o077:
        raise SystemExit("OKX observer credential binding is not mode 0600")

    doc = tomllib.loads(binding.read_text())
    profile_name = doc.get("default_profile")
    profile = (doc.get("profiles") or {}).get(profile_name, {})
    if profile.get("demo") is not False or profile.get("site") != "global":
        raise SystemExit("OKX observer environment mismatch")
    if profile.get("proxy_url") != live_cfg["networkAuthority"]["proxy"]:
        raise SystemExit("OKX observer proxy differs from Network v2 authority")
    for key in ("api_key", "secret_key", "passphrase"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise SystemExit(f"OKX observer credential field unavailable: {key}")

    authority_path = Path(live_cfg["networkAuthority"]["file"])
    if sha256(authority_path) != live_cfg["networkAuthority"]["digest"]:
        raise SystemExit("Network v2 OKX authority digest drift")
    authority = json.loads(authority_path.read_text())
    if authority.get("destination", {}).get("host") != live_cfg["networkAuthority"]["host"]:
        raise SystemExit("Network v2 OKX host drift")
    if authority.get("proxy") != live_cfg["networkAuthority"]["proxy"]:
        raise SystemExit("Network v2 OKX proxy drift")
    for unit in (live_cfg["networkAuthority"]["targetUnit"], live_cfg["networkAuthority"]["serviceUnit"]):
        state = subprocess.run(["/usr/bin/systemctl", "is-active", unit], text=True, capture_output=True)
        if state.returncode != 0 or state.stdout.strip() != "active":
            raise SystemExit(f"Network v2 unit not active: {unit}")
    with socket.create_connection(("127.0.0.1", 19283), timeout=2):
        pass

    client_cfg = live_cfg["readClient"]
    reader = OkxReadOnlyClient(
        base_url=live_cfg["providerApiAuthority"]["baseUrl"],
        proxy_url=live_cfg["networkAuthority"]["proxy"],
        credentials=OkxReadOnlyCredentials(
            api_key=profile["api_key"],
            secret_key=profile["secret_key"],
            passphrase=profile["passphrase"],
        ),
        timeout_seconds=float(client_cfg["timeoutSeconds"]),
        transport_attempts=int(client_cfg.get("transportAttempts", 3)),
        retry_backoff_seconds=float(client_cfg.get("retryBackoffSeconds", 0.25)),
    )

    config_rows = reader.get_account_config()
    if len(config_rows) != 1:
        raise SystemExit(f"OKX observer account config expected one row, got {len(config_rows)}")
    permissions = _permission_tokens(config_rows[0].get("perm"))
    read_present = bool(permissions & {"read", "read_only"})
    forbidden_present = bool(permissions & {"trade", "withdraw"})
    permission_safe = read_present and not forbidden_present

    permission_result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.trading.okx-observer-permission-evidence",
        "standing": (
            "PASS_OKX_OBSERVER_READ_ONLY_PERMISSION_CURRENT"
            if permission_safe
            else "FAIL_OKX_OBSERVER_NOT_READ_ONLY"
        ),
        "venue": "OKX",
        "environment": "LIVE",
        "permissionSafe": permission_safe,
        "providerPermissions": sorted(permissions),
        "networkAuthorityCurrent": True,
        "credentialBindingPresent": True,
        "credentialMode": "0600",
        "secretBytesEchoed": False,
        "externalFinancialWriteAttempted": False,
        "observedAtMs": time.time_ns() // 1_000_000,
    }
    if args.permission_only:
        rendered = json.dumps(permission_result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered)
        print(json.dumps(permission_result, sort_keys=True))
        return 0 if permission_safe else 3

    if not permission_safe:
        raise SystemExit("OKX observer permission is not read-only")
    if okx_policy.get("currentDataAdmission") != "READ_ONLY_ADMITTED":
        raise SystemExit("OKX private-Reality current data admission is not READ_ONLY_ADMITTED")

    balance_rows = reader.get_account_balance()
    position_rows = reader.get_swap_positions()
    open_order_rows = reader.get_swap_open_orders()
    fill_rows = reader.get_swap_fills()
    envelope = {
        "status": "success",
        "externalFinancialWriteAttempted": False,
        "calls": {
            "config": _provider_call(config_rows),
            "balance": _provider_call(balance_rows),
            "positions": _provider_call(position_rows),
            "openOrders": _provider_call(open_order_rows),
            "fills": _provider_call(fill_rows),
        },
    }
    snapshot = normalize_okx_observer(envelope)
    snapshot["observedAtMs"] = time.time_ns() // 1_000_000
    snapshot["providerPermissions"] = sorted(permissions)
    snapshot["networkAuthorityCurrent"] = True
    snapshot["executionAdmitted"] = False
    snapshot["externalFinancialWriteAttempted"] = False

    rendered = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(snapshot, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
