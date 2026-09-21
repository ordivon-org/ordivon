from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from nautilus_trader.adapters.binance import (
    BinanceDataClientConfig,
    BinanceEnvironment,
    BinanceInstrumentProviderConfig,
    BinanceProductType,
)
from nautilus_trader.adapters.okx import (
    OKXDataClientConfig,
    OKXEnvironment,
    OKXInstrumentType,
    OKXRegion,
)


def _load(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text())
    if not isinstance(doc, dict):
        raise RuntimeError("crypto lane config must be a JSON object")
    return doc


def validate(config_path: Path) -> dict[str, Any]:
    cfg = _load(config_path)
    if cfg.get("kind") != "ordivon.capital.market.crypto-execution-lane":
        raise RuntimeError("unexpected crypto lane kind")
    if cfg.get("standing") != "SHADOW_PUBLIC_DATA_ONLY":
        raise RuntimeError("crypto lane must remain SHADOW_PUBLIC_DATA_ONLY")
    if cfg.get("marketModel") != "CONTINUOUS_24_7_CRYPTO_SPOT":
        raise RuntimeError("crypto lane must not inherit equity session semantics")
    for key in (
        "privateAccountDataAllowed",
        "demoExecutionAllowed",
        "liveExecutionAllowed",
        "brokerCredentialsAllowed",
        "externalFinancialWritesAllowed",
    ):
        if cfg.get(key) is not False:
            raise RuntimeError(f"{key} must remain false")
    if cfg.get("publicMarketDataAllowed") is not True:
        raise RuntimeError("public market data must be explicitly allowed")

    venues = cfg.get("venues", {})
    if set(venues) != {"OKX", "BINANCE"}:
        raise RuntimeError("crypto lane requires exact OKX and BINANCE venue set")

    okx_ids = tuple(venues["OKX"]["instrumentIds"])
    binance_ids = tuple(venues["BINANCE"]["instrumentIds"])
    if okx_ids != ("BTC-USDT.OKX", "ETH-USDT.OKX"):
        raise RuntimeError("unexpected OKX instrument universe")
    if binance_ids != ("BTCUSDT.BINANCE", "ETHUSDT.BINANCE"):
        raise RuntimeError("unexpected Binance instrument universe")

    okx_cfg = OKXDataClientConfig(
        instrument_types=(OKXInstrumentType.SPOT,),
        environment=OKXEnvironment.LIVE,
        region=OKXRegion.GLOBAL,
    )
    binance_cfg = BinanceDataClientConfig(
        product_type=BinanceProductType.SPOT,
        environment=BinanceEnvironment.LIVE,
        instrument_provider=BinanceInstrumentProviderConfig(
            load_all=False,
            load_ids=binance_ids,
        ),
    )

    if any(
        getattr(okx_cfg, field, None) is not None
        for field in ("api_key", "api_secret", "api_passphrase")
    ):
        raise RuntimeError("OKX public-data config unexpectedly contains credentials")
    if any(
        getattr(binance_cfg, field, None) is not None
        for field in ("api_key", "api_secret")
    ):
        raise RuntimeError("Binance public-data config unexpectedly contains credentials")

    return {
        "standing": "CRYPTO_DUAL_VENUE_PUBLIC_DATA_CONFIG_READY",
        "marketModel": cfg["marketModel"],
        "venues": {
            "OKX": {
                "adapterConfig": type(okx_cfg).__name__,
                "product": "SPOT",
                "environment": "LIVE_PUBLIC_DATA",
                "credentialsPresent": False,
                "instrumentIds": list(okx_ids),
                "executionQualificationEnvironment": "DEMO",
            },
            "BINANCE": {
                "adapterConfig": type(binance_cfg).__name__,
                "product": "SPOT",
                "environment": "LIVE_PUBLIC_DATA",
                "credentialsPresent": False,
                "instrumentIds": list(binance_ids),
                "executionQualificationEnvironments": ["DEMO", "TESTNET"],
            },
        },
        "publicMarketDataAllowed": True,
        "privateAccountDataAllowed": False,
        "demoExecutionAllowed": False,
        "liveExecutionAllowed": False,
        "externalFinancialWritesAllowed": False,
        "networkTransportStanding": cfg["networkTransport"]["standing"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.config)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
