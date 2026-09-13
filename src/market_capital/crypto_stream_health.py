from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STREAM_KEYS = ("OKX:BTC", "OKX:ETH", "BINANCE:BTC", "BINANCE:ETH")


@dataclass(frozen=True)
class StreamHealthPolicy:
    max_receive_age_ms: float = 5000.0
    max_source_span_ms: float = 1200.0
    max_receive_span_ms: float = 1200.0


def evaluate_stream_health(
    latest: dict[str, dict[str, Any]],
    *,
    now_mono_ns: int,
    policy: StreamHealthPolicy = StreamHealthPolicy(),
) -> dict[str, Any]:
    missing = [key for key in STREAM_KEYS if key not in latest]
    if missing:
        return {
            "standing": "BLOCK_MISSING_STREAM",
            "crossVenueObservationAllowed": False,
            "missing": missing,
        }

    ages = {
        key: (now_mono_ns - int(latest[key]["recvMonoNs"])) / 1_000_000
        for key in STREAM_KEYS
    }
    stale = [key for key, age in ages.items() if age > policy.max_receive_age_ms]
    if stale:
        return {
            "standing": "BLOCK_STALE_STREAM",
            "crossVenueObservationAllowed": False,
            "stale": stale,
            "receiveAgeMs": ages,
            "maxReceiveAgeMs": policy.max_receive_age_ms,
        }

    source_times = [int(latest[key]["sourceTimeMs"]) for key in STREAM_KEYS]
    receive_times = [int(latest[key]["recvMonoNs"]) for key in STREAM_KEYS]
    source_span_ms = float(max(source_times) - min(source_times))
    receive_span_ms = (max(receive_times) - min(receive_times)) / 1_000_000

    if source_span_ms > policy.max_source_span_ms or receive_span_ms > policy.max_receive_span_ms:
        return {
            "standing": "BLOCK_TIME_DIVERGENCE",
            "crossVenueObservationAllowed": False,
            "sourceTimeSpanMs": source_span_ms,
            "receiveTimeSpanMs": receive_span_ms,
            "sourceTimeSpanMaxMs": policy.max_source_span_ms,
            "receiveTimeSpanMaxMs": policy.max_receive_span_ms,
        }

    return {
        "standing": "PASS_STREAM_HEALTHY",
        "crossVenueObservationAllowed": True,
        "sourceTimeSpanMs": source_span_ms,
        "receiveTimeSpanMs": receive_span_ms,
        "receiveAgeMs": ages,
        "maxReceiveAgeMs": policy.max_receive_age_ms,
    }
