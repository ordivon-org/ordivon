"""Pinned upstream DBN files prove decoding, never vendor execution authority."""

from __future__ import annotations

import hashlib
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
    assert tuple(q.ts_event for q in tape.quotes) == (
        1609160400006136329, 1609160400006246513,
    )
    assert tape.first_observed_ns > tape.quotes[-1].ts_event
    assert "PIT_UNVERIFIED" in tape.standing
    assert "TS_RECV_NOT_VENUE" in tape.timestamp_semantics
    assert [str(q.ask_price) for q in tape.quotes] == [
        "3720.500000000", "3720.500000000",
    ]


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
    assert price_usd_cents_exact(read().quotes[0].ask_price) == 372050
    for price in ("110.021000000", "110.000000001", "-1.000000000", "0.000000000"):
        with pytest.raises(ValueError, match="exactly representable"):
            price_usd_cents_exact(Price.from_str(price))
