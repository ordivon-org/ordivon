from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

from ordivon_capital.trading.okx_readonly_client import (
    OkxReadOnlyClient,
    OkxReadOnlyCredentials,
)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(argv: list[str], *, env: dict[str, str] | None = None, timeout: int = 25) -> Any:
    p = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"provider command failed: {Path(argv[0]).name} exit={p.returncode}")
    return json.loads(p.stdout)


def rows_of(value: Any) -> list[dict[str, Any]]:
    rows: Any
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict) and isinstance(value.get("data"), list):
        rows = value["data"]
    elif isinstance(value, dict) and isinstance(value.get("data"), dict) and isinstance(value["data"].get("data"), list):
        rows = value["data"]["data"]
    else:
        rows = []
    return [r for r in rows if isinstance(r, dict)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config/okx_live_provider.json"), type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    secret_path = Path(cfg["credentialBinding"])
    if not secret_path.is_file():
        raise SystemExit("OKX live credential binding unavailable")
    if secret_path.stat().st_mode & 0o077:
        raise SystemExit("OKX live credential binding is not mode 0600")
    secret = tomllib.loads(secret_path.read_text())
    if secret.get("default_profile") != cfg["profile"]:
        raise SystemExit("OKX live credential default profile mismatch")
    profile = secret.get("profiles", {}).get(cfg["profile"], {})
    if profile.get("demo") is not False or profile.get("site") != "global":
        raise SystemExit("OKX provider environment mismatch")
    if profile.get("proxy_url") != cfg["networkAuthority"]["proxy"]:
        raise SystemExit("OKX credential proxy binding differs from Network v2 authority")
    for key in ("api_key", "secret_key", "passphrase"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise SystemExit(f"OKX credential field unavailable: {key}")

    authority_path = Path(cfg["networkAuthority"]["file"])
    if sha256(authority_path) != cfg["networkAuthority"]["digest"]:
        raise SystemExit("Network v2 OKX authority digest drift")
    authority = json.loads(authority_path.read_text())
    if authority.get("destination", {}).get("host") != cfg["networkAuthority"]["host"]:
        raise SystemExit("Network v2 OKX host drift")
    if authority.get("proxy") != cfg["networkAuthority"]["proxy"]:
        raise SystemExit("Network v2 OKX proxy drift")
    for unit in (cfg["networkAuthority"]["targetUnit"], cfg["networkAuthority"]["serviceUnit"]):
        state = subprocess.run(["/usr/bin/systemctl", "is-active", unit], text=True, capture_output=True)
        if state.returncode != 0 or state.stdout.strip() != "active":
            raise SystemExit(f"Network v2 unit not active: {unit}")
    with socket.create_connection(("127.0.0.1", 19283), timeout=2):
        pass

    client_cfg = cfg["readClient"]
    reader = OkxReadOnlyClient(
        base_url=cfg["providerApiAuthority"]["baseUrl"],
        proxy_url=cfg["networkAuthority"]["proxy"],
        credentials=OkxReadOnlyCredentials(
            api_key=profile["api_key"],
            secret_key=profile["secret_key"],
            passphrase=profile["passphrase"],
        ),
        timeout_seconds=float(client_cfg["timeoutSeconds"]),
    )
    account_rows = reader.get_account_config()
    if len(account_rows) != 1:
        raise SystemExit(f"OKX account config expected one row, got {len(account_rows)}")
    raw_perm = str(account_rows[0].get("perm") or "")
    perms = sorted(
        {x.strip().lower() for x in raw_perm.replace(";", ",").split(",") if x.strip()}
    )
    missing = sorted(set(cfg["requiredPermissions"]) - set(perms))
    forbidden = sorted(set(cfg["forbiddenPermissions"]) & set(perms))
    if missing or forbidden:
        raise SystemExit(f"OKX permission mismatch missing={missing} forbidden={forbidden}")
    balance_rows = reader.get_account_balance()
    order_rows = reader.get_spot_open_orders()

    execution = cfg["executionProvider"]
    nautilus = run_json([
        execution["python"],
        str(ROOT / "tools/okx_live_nautilus_config_probe.py"),
        "--provider-config",
        str(args.config),
    ])
    if not nautilus.get("ok"):
        raise SystemExit("Nautilus live execution config probe failed")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.okx-live-provider-binding-evidence",
        "standing": "PASS_OKX_LIVE_PROVIDER_BOUND_CURRENT_NO_EFFECT_ADMISSION",
        "credentialClass": cfg["credentialClass"],
        "providerCapabilityAuditOnly": cfg["providerCapabilityAuditOnly"],
        "privateRealityAdmissionGranted": cfg["privateRealityAdmissionGranted"],
        "venue": "OKX",
        "environment": "LIVE",
        "credentialBindingPresent": True,
        "credentialMode": "0600",
        "credentialCopiedIntoRepository": False,
        "networkAuthorityCurrent": True,
        "networkTargetActive": True,
        "networkServiceActive": True,
        "networkProxyReachable": True,
        "readClient": {"name": client_cfg["name"], "runtime": client_cfg["runtime"], "authenticated": True},
        "externalReferenceClient": cfg["externalReferenceClient"],
        "authenticatedProviderReadAudit": {
            "accountConfigCurrent": True,
            "balanceQueryCurrent": True,
            "openOrdersQueryCurrent": True,
            "balanceRowCount": len(balance_rows),
            "openOrderCount": len(order_rows),
            "sensitiveValuesDisclosed": False,
        },
        "providerPermissions": perms,
        "providerReadPermissionCurrent": "read_only" in perms or "read" in perms,
        "providerTradePermissionCurrent": "trade" in perms,
        "providerWithdrawPermissionCurrent": "withdraw" in perms,
        "providerTradeCapabilityCurrent": "trade" in perms,
        "nautilusLiveExecutionConfigBound": True,
        "nautilus": nautilus,
        "externalWritePolicyStanding": cfg["externalWritePolicyStanding"],
        "providerTradeCapabilityBoundToExternalEffect": False,
        "orderSubmissionAllowed": False,
        "externalFinancialWriteAttempted": False,
        "orderSubmissionAttempted": False,
        "secretBytesEchoed": False,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
