from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

from nautilus_trader.adapters.okx import (
    OKXEnvironment,
    OKXExecutionClientConfig,
    OKXExecutionClientFactory,
)
from nautilus_trader.model import AccountId


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-config", required=True, type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.provider_config.read_text())
    secret_path = Path(cfg["credentialBinding"])
    secret = tomllib.loads(secret_path.read_text())
    profile = secret["profiles"][cfg["profile"]]
    if profile.get("demo") is not False:
        raise SystemExit("live credential profile unexpectedly marked demo")
    if profile.get("site") != "global":
        raise SystemExit("OKX live provider currently requires site=global")
    for key in ("api_key", "secret_key", "passphrase"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise SystemExit(f"credential field unavailable: {key}")

    execution = cfg["executionProvider"]
    net = cfg["networkAuthority"]
    value = OKXExecutionClientConfig(
        account_id=AccountId("OKX-LIVE-ORDIVON-CAPITAL"),
        environment=OKXEnvironment.LIVE,
        api_key=profile["api_key"],
        api_secret=profile["secret_key"],
        api_passphrase=profile["passphrase"],
        base_url_http=cfg["providerApiAuthority"]["baseUrl"],
        proxy_url=net["proxy"],
    )
    if type(value).__name__ != execution["configClass"]:
        raise SystemExit("unexpected Nautilus OKX execution config class")
    print(json.dumps({
        "ok": True,
        "provider": execution["name"],
        "version": execution["version"],
        "environment": execution["environment"],
        "configClass": type(value).__name__,
        "factoryPresent": bool(OKXExecutionClientFactory),
        "credentialInputBound": True,
        "baseUrlHttp": cfg["providerApiAuthority"]["baseUrl"],
        "proxyUrl": net["proxy"],
        "networkSessionOpened": False,
        "orderSubmissionAttempted": False,
        "secretBytesEchoed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
