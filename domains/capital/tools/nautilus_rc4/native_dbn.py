"""Offline native Databento DBN decoding without promoting source truth.

The mature NautilusTrader adapter owns DBN parsing and symbol resolution.
This boundary binds the *actual input bytes*, decoder version and quote clocks.
Decoded bytes are never, by themselves, approved for Paper fills or PIT research.
"""

from __future__ import annotations

import hashlib
import tempfile
import time
from compression.zstd import ZstdError, ZstdFile
from decimal import Decimal, localcontext
from io import BytesIO
from pathlib import Path
from typing import NamedTuple

from databento_dbn import Compression, DBNDecoder, DBNError, MBP1Msg, Metadata, Schema
from nautilus_trader import __version__ as nautilus_version
from nautilus_trader.adapters.databento import DatabentoDataLoader
from nautilus_trader.model import Price, QuoteTick

_MAX_DBN_BYTES = 8 * 1024 * 1024
_MAX_DECOMPRESSED_BYTES = 8 * 1024 * 1024
_MAX_PUBLISHERS_BYTES = 128 * 1024
_MAX_QUOTES = 100_000


class DecodedQuoteFact(NamedTuple):
    """Immutable, primitive copy of BOTH original venue and received clocks."""

    instrument_id: str
    bid_price_nanos: int
    ask_price_nanos: int
    bid_size: int
    ask_size: int
    venue_event_ns: int
    vendor_receive_ns: int
    native_init_ns: int


class DecodedDbnQuotes(NamedTuple):
    """A byte-bound native decode, NOT publisher attestation or execution authority."""

    dbn_sha256: str
    publishers_sha256: str
    source_instrument_id: str
    decoded_schema: str
    native_version: str
    first_observed_ns: int
    quotes: tuple[DecodedQuoteFact, ...]

    @property
    def standing(self) -> str:
        return "NATIVE_DECODE_ONLY_PUBLISHER_RIGHTS_AND_PIT_UNVERIFIED"

    @property
    def timestamp_semantics(self) -> str:
        return "NAUTILUS_TS_EVENT_IS_DATABENTO_TS_RECV_NOT_VENUE_TS_EVENT"


def _verify(raw: bytes, expected_sha256: str, max_bytes: int, label: str) -> None:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= max_bytes:
        raise ValueError(f"{label} must be bounded immutable input bytes")
    # Caller-supplied digests prove equality to the caller's commitment, not
    # the independent authenticity of a financial vendor or its publisher map.
    if not isinstance(expected_sha256, str) or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError(f"{label} digest does not match independent commitment")


def _native_bounded_records(dbn_bytes: bytes) -> tuple[MBP1Msg, ...]:
    """Use Python 3.15 Zstandard + the official Rust DBN decoder as an EOF gate.

    Native Nautilus' batch loader can silently drop an incomplete final DBN
    record. Validate the complete compressed frame and DBN trailing bytes
    BEFORE handing anything to its unbounded batch-loading API.
    """
    try:
        with ZstdFile(BytesIO(dbn_bytes), "rb") as compressed:
            decoded_bytes = compressed.read(_MAX_DECOMPRESSED_BYTES + 1)
            if len(decoded_bytes) > _MAX_DECOMPRESSED_BYTES or compressed.read(1):
                raise ValueError("DBN decompressed size exceeds native qualification limit")
    except (EOFError, OSError, ZstdError) as error:
        raise ValueError("DBN compressed frame is truncated or invalid") from error
    decoder = DBNDecoder(compression=Compression.NONE)
    try:
        records = decoder.write_and_decode(decoded_bytes)
    except DBNError as error:
        raise ValueError("DBN native structural decoder rejected input") from error
    if decoder.buffer():
        raise ValueError("DBN contains an incomplete final record")
    if not records or not isinstance(records[0], Metadata):
        raise ValueError("DBN native metadata is missing")
    if records[0].schema != Schema.MBP_1:
        raise ValueError("only native MBP-1 quote records are qualified")
    messages = tuple(records[1:])
    if (not 0 < len(messages) <= _MAX_QUOTES
            or any(not isinstance(msg, MBP1Msg) for msg in messages)):
        raise ValueError("DBN native MBP-1 record count or type is unqualified")
    # A provider-supplied limit can prove a missing suffix for bounded fixtures;
    # where absent, only structural EOF (NOT full historical coverage) is known.
    if records[0].limit is not None and records[0].limit != len(messages):
        raise ValueError("DBN native metadata record limit does not match decoded input")
    return messages


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

    native_records = _native_bounded_records(dbn_bytes)
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
        len(observed) != len(native_records)
        or any(type(row) is not QuoteTick for row in observed)
        or any(str(row.instrument_id) != expected_instrument_id for row in observed)
        or timestamps != tuple(sorted(timestamps))
        or timestamps[0] <= 0
        or timestamps[-1] > seen_at
        or any(row.ts_init < row.ts_event for row in observed)
        or any(row.ts_event != raw.ts_recv for row, raw in zip(observed, native_records))
    ):
        raise ValueError("native DBN identity or receive-time contract violated")
    # Do not leak Cython QuoteTick objects into a supposedly immutable fact:
    # upstream QuoteTick.__setstate__ can mutate native prices/timestamps.
    quote_facts = []
    with localcontext() as context:
        context.prec = 80
        for row, raw in zip(observed, native_records):
            bid_nano = int(Decimal(str(row.bid_price)) * 1_000_000_000)
            ask_nano = int(Decimal(str(row.ask_price)) * 1_000_000_000)
            if (bid_nano != raw.bid_px_00 or ask_nano != raw.ask_px_00
                    or bid_nano <= 0 or ask_nano < bid_nano
                    or raw.bid_sz_00 <= 0 or raw.ask_sz_00 <= 0):
                raise ValueError("native DBN raw quote fidelity failed")
            quote_facts.append(DecodedQuoteFact(
                str(row.instrument_id), bid_nano, ask_nano,
                int(raw.bid_sz_00), int(raw.ask_sz_00),
                int(raw.ts_event), int(raw.ts_recv), int(row.ts_init),
            ))
    return DecodedDbnQuotes(
        expected_dbn_sha256,
        expected_publishers_sha256,
        expected_instrument_id,
        "mbp-1",
        nautilus_version,
        seen_at,
        tuple(quote_facts),
    )


def price_usd_cents_exact(price) -> int:
    """Exact arithmetic only; this does not establish USD currency or price rights."""
    if not isinstance(price, Price):
        raise ValueError("price must be an original native Price")
    # Ambient decimal precision can round 110.000000001 to 110.00 before
    # validation. Force sufficient precision and start from the exact native
    # 9-decimal string; never inspect a rounded 2-decimal Price.
    with localcontext() as context:
        context.prec = 80
        numeric = Decimal(str(price))
        cents = numeric * Decimal(100)
    if (
        numeric <= 0
        or cents != cents.to_integral_value()
        or not 0 < cents <= Decimal(2**63 - 1)
    ):
        raise ValueError("price is not exactly representable in USD cents")
    return int(cents)
