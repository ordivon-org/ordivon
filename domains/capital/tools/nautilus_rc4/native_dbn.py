"""Offline native Databento DBN decoding without promoting source truth.

The mature NautilusTrader adapter owns DBN parsing and symbol resolution.
This boundary binds the *actual input bytes*, decoder version and quote clocks.
Decoded bytes are never, by themselves, approved for Paper fills or PIT research.
"""

from __future__ import annotations

import hashlib
import tempfile
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from nautilus_trader import __version__ as nautilus_version
from nautilus_trader.adapters.databento import DatabentoDataLoader
from nautilus_trader.model import QuoteTick

_MAX_DBN_BYTES = 8 * 1024 * 1024
_MAX_PUBLISHERS_BYTES = 128 * 1024
_MAX_QUOTES = 100_000


@dataclass(frozen=True, slots=True)
class DecodedDbnQuotes:
    """An immutable original-byte commitment, NOT an executable market source."""

    dbn_sha256: str
    publishers_sha256: str
    source_instrument_id: str
    decoded_schema: str
    native_version: str
    first_observed_ns: int
    quotes: tuple[QuoteTick, ...]

    @property
    def standing(self) -> str:
        return "NATIVE_DECODE_ONLY_RIGHTS_AND_PIT_UNVERIFIED"

    @property
    def timestamp_semantics(self) -> str:
        return "NAUTILUS_TS_EVENT_IS_DATABENTO_TS_RECV_NOT_VENUE_TS_EVENT"


def _verify(raw: bytes, expected_sha256: str, max_bytes: int, label: str) -> None:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= max_bytes:
        raise ValueError(f"{label} must be bounded immutable input bytes")
    if not isinstance(expected_sha256, str) or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError(f"{label} digest does not match independent commitment")


def decode_mbp1_quotes(
    dbn_bytes: bytes,
    publisher_bytes: bytes,
    *,
    expected_dbn_sha256: str,
    expected_publishers_sha256: str,
    expected_instrument_id: str,
) -> DecodedDbnQuotes:
    """Decode MBP-1 with native Rust; never override the DBN-derived instrument ID.

    The returned quote timestamps are Databento *receive* timestamps, not venue
    event timestamps. The local first observation is NOW, not the vintage's
    historical availability date. No vendor rights or economic use is admitted.
    """
    _verify(dbn_bytes, expected_dbn_sha256, _MAX_DBN_BYTES, "DBN")
    _verify(publisher_bytes, expected_publishers_sha256, _MAX_PUBLISHERS_BYTES, "publishers")
    if not isinstance(expected_instrument_id, str) or not expected_instrument_id.strip():
        raise ValueError("independent expected native instrument ID is required")
    if nautilus_version != "2.0.0rc9":
        raise ValueError("native DBN decoder version is not qualified")

    # The decoder never sees a mutable external source path. It consumes the
    # exact committed in-memory bytes written to this private temporary area.
    with tempfile.TemporaryDirectory(prefix="finance-dbn-native-") as root:
        folder = Path(root)
        dbn = folder / "input.dbn.zst"
        publishers = folder / "publishers.json"
        dbn.write_bytes(dbn_bytes)
        publishers.write_bytes(publisher_bytes)
        loader = DatabentoDataLoader(publishers_filepath=str(publishers))
        if loader.schema_for_file(str(dbn)) != "mbp-1":
            raise ValueError("only native MBP-1 quote records are qualified")
        # Do NOT pass instrument_id here: Nautilus allows overriding the
        # DBN's actual source identity, which would permit ESH21 -> SPY spoofing.
        observed = tuple(loader.load_quotes(filepath=str(dbn), price_precision=9))
    seen_at = time.time_ns()
    if not 0 < len(observed) <= _MAX_QUOTES:
        raise ValueError("native DBN quote batch must be nonempty and bounded")
    timestamps = tuple(row.ts_event for row in observed)
    if (
        any(type(row) is not QuoteTick for row in observed)
        or any(str(row.instrument_id) != expected_instrument_id for row in observed)
        or timestamps != tuple(sorted(timestamps))
        or timestamps[0] <= 0
        or timestamps[-1] > seen_at
        or any(row.ts_init < row.ts_event for row in observed)
    ):
        raise ValueError("native DBN identity or receive-time contract violated")
    return DecodedDbnQuotes(
        expected_dbn_sha256,
        expected_publishers_sha256,
        expected_instrument_id,
        "mbp-1",
        nautilus_version,
        seen_at,
        observed,
    )


def price_usd_cents_exact(price) -> int:
    """Exact arithmetic only; this does not establish USD currency or price rights."""
    numeric = price.as_decimal()
    cents = numeric * Decimal(100)
    if (
        numeric <= 0
        or cents != cents.to_integral_value()
        or not 0 < cents <= Decimal(2**63 - 1)
    ):
        raise ValueError("price is not exactly representable in USD cents")
    return int(cents)
