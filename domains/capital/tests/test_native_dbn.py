"""Pinned upstream DBN files prove decoding, never vendor execution authority."""

from __future__ import annotations

import hashlib
import json
from compression import zstd
from decimal import localcontext
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures/databento"
DBN = (FIXTURES / "mbp-1.v3.dbn.zst").read_bytes()
PUBLISHERS = (FIXTURES / "publishers-rc9.json").read_bytes()
DEFINITION = (FIXTURES / "definition.v3.dbn.zst").read_bytes()
DBN_SHA = "a4646539f456b58abda0d748c170cb5e4e908351c4ce4ab5cb90b34eaabd576c"
PUB_SHA = "5046ff7a3c646c32667d59ef9d7503b527cd9c88574ee86efb20e9077038f8d9"

pytestmark = [pytest.mark.provider_qualification, pytest.mark.native_nonlive]


@pytest.fixture(autouse=True)
def native_adapter_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tools/nautilus_rc4"))


def read(**overrides):
    from native_dbn import decode_mbp1_quotes

    return decode_mbp1_quotes(
        overrides.get("dbn_bytes", DBN), overrides.get("publisher_bytes", PUBLISHERS),
        expected_dbn_sha256=overrides.get("expected_dbn_sha256", DBN_SHA),
        expected_publishers_sha256=overrides.get("expected_publishers_sha256", PUB_SHA),
        expected_instrument_id=overrides.get("expected_instrument_id", "ESH21.GLBX"),
    )


def test_real_official_dbn_is_decoded_natively_but_never_admitted_as_executable():
    tape = read()
    assert tape.native_version == "2.0.0rc9"
    assert tape.dbn_sha256 == hashlib.sha256(DBN).hexdigest()
    assert tape.publishers_sha256 == hashlib.sha256(PUBLISHERS).hexdigest()
    assert tape.decoded_schema == "mbp-1"
    assert tape.source_instrument_id == "ESH21.GLBX"  # CME future; not an ETF
    assert len(tape.quotes) == 2
    assert tuple(q.vendor_receive_ns for q in tape.quotes) == (
        1609160400006136329, 1609160400006246513,
    )
    assert tape.quotes[0].venue_event_ns == 1609160400006001487
    assert tape.first_observed_ns > tape.quotes[-1].vendor_receive_ns
    assert "PIT_UNVERIFIED" in tape.standing
    assert "PUBLISHER" in tape.standing  # Digest is not vendor attestation.
    assert "TS_RECV_NOT_VENUE" in tape.timestamp_semantics
    assert [q.ask_price_nanos for q in tape.quotes] == [
        3720500000000, 3720500000000,
    ]
    # No native Cython QuoteTick.__setstate__ mutation behind a frozen wrapper.
    assert not hasattr(tape.quotes[0], "__setstate__")
    with pytest.raises(AttributeError):
        tape.quotes[0].ask_price_nanos = 1000000000


def test_publisher_record_and_instrument_id_cannot_be_spoofed():
    with pytest.raises(ValueError, match="identity"):
        read(expected_instrument_id="SPY.EQUS")
    with pytest.raises(ValueError, match="digest"):
        read(dbn_bytes=DBN + b"fake")
    with pytest.raises(ValueError, match="digest"):
        read(publisher_bytes=PUBLISHERS + b"fake")
    with pytest.raises(ValueError, match="digest"):
        read(expected_dbn_sha256=PUB_SHA)
    with pytest.raises(ValueError, match="only native MBP-1"):
        read(dbn_bytes=DEFINITION, expected_dbn_sha256=hashlib.sha256(DEFINITION).hexdigest())


def test_price_cents_gate_preserves_subpenny_before_any_conversion():
    from native_dbn import price_usd_cents_exact
    from nautilus_trader.model import Price

    assert price_usd_cents_exact(Price.from_str("110.020000000")) == 11002
    assert read().quotes[0].ask_price_nanos == 3720500000000
    assert price_usd_cents_exact(Price.from_str("3720.500000000")) == 372050
    for price in ("110.021000000", "110.000000001", "-1.000000000", "0.000000000"):
        with pytest.raises(ValueError, match="exactly representable"):
            price_usd_cents_exact(Price.from_str(price))



def test_official_native_decoder_rejects_partial_dbn_and_truncated_zstd_frame():
    original = zstd.decompress(DBN)
    for corrupted, error in (
        (DBN[:-1], "truncated or invalid"),
        (zstd.compress(original[:-1]), "incomplete final record"),
        (zstd.compress(original[:-80]), "record limit"),
    ):
        with pytest.raises(ValueError, match=error):
            read(dbn_bytes=corrupted, expected_dbn_sha256=hashlib.sha256(corrupted).hexdigest())


def test_compressed_input_cannot_evade_predecode_resource_budget():
    original = zstd.decompress(DBN)
    # Mature Zstd encoder builds a legitimate, highly compressible >8MiB
    # stream; reject before the native Nautilus loader can allocate quotes.
    amplified = zstd.compress(original + original[-80:] * 110_000)
    assert len(amplified) < len(original) * 5
    with pytest.raises(ValueError, match="decompressed size"):
        read(dbn_bytes=amplified, expected_dbn_sha256=hashlib.sha256(amplified).hexdigest())


def test_subpenny_gate_is_independent_of_decimal_caller_context():
    from native_dbn import price_usd_cents_exact
    from nautilus_trader.model import Price

    with localcontext() as context:
        context.prec = 5
        assert price_usd_cents_exact(Price.from_str("110.020000000")) == 11002
        with pytest.raises(ValueError, match="exactly representable"):
            price_usd_cents_exact(Price.from_str("110.000000001"))



def test_caller_supplied_publisher_map_cannot_attest_vendor_identity():
    # A caller can supply a different map with a matching new commitment:
    # successful native decode is STILL untrusted, never executable.
    rows = json.loads(PUBLISHERS)
    original = next(row for row in rows if row["publisher_id"] == 1)
    assert original["venue"] == "GLBX"
    original["venue"] = "EQUS"
    forged = json.dumps(rows).encode()
    decoded = read(
        publisher_bytes=forged,
        expected_publishers_sha256=hashlib.sha256(forged).hexdigest(),
        expected_instrument_id="ESH21.EQUS",
    )
    assert decoded.source_instrument_id == "ESH21.EQUS"
    assert decoded.standing == "NATIVE_DECODE_ONLY_PUBLISHER_RIGHTS_AND_PIT_UNVERIFIED"
