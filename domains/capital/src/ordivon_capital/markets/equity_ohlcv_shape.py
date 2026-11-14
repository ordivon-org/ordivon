"""Thin Markets daily OHLCV shape gate before high/low-derived Research features.

A source digest only authenticates the supplied bytes, not their bar semantics.
This checks an internal OHLCV invariant on the very same already-admitted
source DataFrame. It does not replace price/vendor/exchange/PIT/rights evidence,
correct bars, drop rows, compute returns or invent a second data catalogue.
"""

from __future__ import annotations

from typing import Any


class EquityOhlcvShapeError(ValueError):
    """One or more vendor OHLCV rows cannot safely supply HILO features."""


def require_ohlcv_shape_for_hilo(source: Any, *, symbol: str) -> dict[str, object]:
    """Reject internally inconsistent high/low features, never repair prices.

    The caller already owns the exact byte capture, XNYS session grid, and
    corporate-action semantics. Only economic OHLC bar shape is checked here.
    """
    if not isinstance(symbol, str) or not (1 <= len(symbol) <= 32):
        raise EquityOhlcvShapeError("missing bounded market instrument identity")
    import numpy as np
    import pandas as pd

    if not isinstance(source, pd.DataFrame) or source.empty or len(source) > 100_000:
        raise EquityOhlcvShapeError("bounded nonempty daily OHLCV DataFrame required")
    required = ("open", "high", "low", "close", "volume")
    if any(source.columns.tolist().count(key) != 1 for key in required):
        raise EquityOhlcvShapeError("exactly one OHLCV column for each primitive is required")
    try:
        numbers = source.loc[:, list(required)].apply(
            pd.to_numeric, errors="raise"
        ).astype(float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise EquityOhlcvShapeError("OHLCV primitive contains nonnumeric value") from exc

    if not bool(np.isfinite(numbers.to_numpy()).all()):
        raise EquityOhlcvShapeError("nonfinite OHLCV price/volume cannot be a HILO source")
    o, h, l, c, v = (numbers[key] for key in required)
    invalid = (
        (o <= 0) | (h <= 0) | (l <= 0) | (c <= 0) | (v < 0)
        | (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
    )
    if bool(invalid.any()):
        indices = list(numbers.index[invalid][:4].map(str))
        raise EquityOhlcvShapeError(
            f"{symbol}: OHLC_BOUNDS_INVALID_FOR_HILO rows={int(invalid.sum())} "
            f"example_sessions={indices}; source must be independently requalified"
        )
    return {
        "kind": "ordivon.capital.markets.ohlcv-shape-check",
        "symbol": symbol,
        "rows": len(numbers),
        "standing": "STRUCTURALLY_COHERENT_OHLCV_SOURCE_UNATTESTED",
        "priceIssuerAdjustmentVerified": False,
        "issuerHistoricalPITVerified": False,
        "externalDataRightsVerified": False,
        "capitalAuthority": False,
    }
