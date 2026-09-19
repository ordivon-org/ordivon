from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence
from urllib.parse import urlencode

from .portfolio_risk import PortfolioRiskError, build_factor_observatory, completed_log_returns


BASE_URL = "https://openapi.okx.com"
HISTORY_CANDLES = "/api/v5/market/history-candles"


class OkxFactorObserverError(RuntimeError):
    pass


def parse_completed_daily_returns(
    *,
    instrument_id: str,
    payload: Mapping[str, Any],
) -> dict[int, float]:
    if payload.get("code") != "0":
        raise OkxFactorObserverError("OKX candle response code is not zero")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise OkxFactorObserverError("OKX candle data must be a list")

    observations: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) < 9:
            raise OkxFactorObserverError(f"candle[{i}] is malformed")
        try:
            ts = int(row[0])
            confirm = int(row[8])
        except (TypeError, ValueError) as exc:
            raise OkxFactorObserverError(f"candle[{i}] has invalid timestamp/confirm") from exc
        if confirm != 1:
            continue
        observations.append({"observedAtMs": ts, "close": row[4]})

    observations.sort(key=lambda x: x["observedAtMs"])
    try:
        return completed_log_returns(observations, instrument_id=instrument_id)
    except PortfolioRiskError as exc:
        raise OkxFactorObserverError(str(exc)) from exc


def _request(proxy: str, instrument_id: str, limit: int) -> dict[str, Any]:
    url = BASE_URL + HISTORY_CANDLES + "?" + urlencode({
        "instId": instrument_id,
        "bar": "1D",
        "limit": str(limit),
    })
    last_error = ""
    for attempt in range(4):
        proc = subprocess.run(
            [
                "/usr/bin/curl",
                "-sS",
                "--proxy",
                proxy,
                "--connect-timeout",
                "3",
                "--max-time",
                "15",
                url,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            try:
                value = json.loads(proc.stdout)
            except json.JSONDecodeError:
                last_error = "invalid JSON"
            else:
                if isinstance(value, dict) and value.get("code") == "0":
                    return value
                last_error = f"provider code={value.get('code') if isinstance(value, dict) else 'invalid'}"
        else:
            last_error = proc.stderr.strip()
        time.sleep(0.3 * (attempt + 1))
    raise OkxFactorObserverError(f"{instrument_id}: {last_error}")


def capture_okx_factor_observatory(
    *,
    base_instrument_id: str,
    factor_proxies: Sequence[Mapping[str, str]],
    proxy: str,
    limit: int = 180,
) -> dict[str, Any]:
    if not base_instrument_id.strip():
        raise OkxFactorObserverError("base_instrument_id is required")
    if not proxy.startswith("http://127.0.0.1:"):
        raise OkxFactorObserverError("proxy must be a loopback Network v2 HTTP proxy")
    if not isinstance(limit, int) or limit < 20 or limit > 300:
        raise OkxFactorObserverError("limit must be in [20, 300]")

    instruments = [base_instrument_id]
    specs: list[tuple[str, str]] = []
    for i, row in enumerate(factor_proxies):
        factor = str(row.get("factor") or "").strip()
        inst = str(row.get("instrumentId") or "").strip()
        if not factor or not inst:
            raise OkxFactorObserverError(f"factor_proxies[{i}] requires factor and instrumentId")
        specs.append((factor, inst))
        instruments.append(inst)

    unique_instruments = list(dict.fromkeys(instruments))
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(unique_instruments))) as pool:
        futures = {
            inst: pool.submit(_request, proxy, inst, limit)
            for inst in unique_instruments
        }
        payloads = {inst: future.result() for inst, future in futures.items()}

    returns = {
        inst: parse_completed_daily_returns(instrument_id=inst, payload=payloads[inst])
        for inst in unique_instruments
    }
    observatory = build_factor_observatory(
        base_instrument_id=base_instrument_id,
        base_returns=returns[base_instrument_id],
        factor_proxies=[
            {
                "factor": factor,
                "instrumentId": inst,
                "returns": returns[inst],
            }
            for factor, inst in specs
        ],
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.market-capital.okx-public-factor-observatory",
        "sourceAuthority": "OKX_PUBLIC_COMPLETED_1D_CANDLES",
        "baseInstrumentId": base_instrument_id,
        "requestedCandleLimit": limit,
        "factorObservatory": observatory,
        "brokerCredentialsUsed": False,
        "privateAccountDataUsed": False,
        "tradeRecommendationProduced": False,
        "externalFinancialWriteAttempted": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--proxy", required=True)
    ap.add_argument("--factor", action="append", default=[], help="FACTOR=INSTRUMENT")
    ap.add_argument("--limit", type=int, default=180)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    specs = []
    for value in args.factor:
        if "=" not in value:
            raise SystemExit("--factor must be FACTOR=INSTRUMENT")
        factor, inst = value.split("=", 1)
        specs.append({"factor": factor, "instrumentId": inst})

    result = capture_okx_factor_observatory(
        base_instrument_id=args.base,
        factor_proxies=specs,
        proxy=args.proxy,
        limit=args.limit,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
