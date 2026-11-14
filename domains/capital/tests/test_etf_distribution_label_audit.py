"""Falsify lookahead, bogus dates and total-return overclaims in H5/H20 labels."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date

import exchange_calendars as xcals
import pytest

from ordivon_capital.research.etf_distribution_label_audit import (
    DistributionLabelAuditError,
    audit_native_price_label_dividend_overlap,
)


def fixture():
    dates = [t.date().isoformat() for t in xcals.get_calendar("XNYS").sessions_in_range(
        "2026-06-01", "2026-07-01"
    )]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["session_date", "SPY", "QQQ", "IWM"])
    for day in dates:
        w.writerow([day, "100", "100", "100"])
    panel = buf.getvalue().encode()
    observed = {
        "kind": "ordivon.finance.issuer-distribution-observations-r1",
        "observedAt": "2026-11-14T10:00:00+00:00",
        "coverage": "OBSERVED_ONLY_NOT_COMPLETE",
        "events": [{
            "symbol": "IWM", "exDate": "2026-06-15",
            "payableDate": "2026-06-18",
            "cashUSDPerShare": "0.695129",
            "issuerUrl": "https://www.ishares.com/us/products/239710/iwm-ishares-russell-2000-etf",
        }],
    }
    return panel, observed, dates


def run(panel, observed, *, hold=5, first="2026-06-01", last="2026-06-29"):
    return audit_native_price_label_dividend_overlap(
        panel_bytes=panel,
        observed_events_bytes=json.dumps(observed).encode(),
        expected_panel_sha256=hashlib.sha256(panel).hexdigest(),
        decision_start=first,
        decision_end=last,
        hold_sessions=hold,
    )


def test_h5_exdate_affects_exactly_five_hypothetical_next_open_windows():
    raw, events, _ = fixture()
    result = run(raw, events)
    symbol = result["symbols"]["IWM"]
    assert symbol["candidateExposedWindows"] == 5
    assert symbol["perObservedExDate"] == [
        {"exDate": "2026-06-15", "affectedCandidateWindows": 5}
    ]
    assert result["standing"] == "OBSERVED_ISSUER_EVENT_EXPOSURE_NOT_TOTAL_RETURN"
    for key in (
        "marketPriceAdjustmentAndDividendsVerified", "issuerEventCoverageVerified",
        "issuerHistoricalPointInTimeVerified", "dataRightsVerified",
        "realMoneyOrdersAuthorized",
    ):
        assert result[key] is False
    assert result["accountingEffect"] == "NONE"


def test_last_session_does_not_enable_lookahead_and_h20_windows_are_bounded():
    raw, events, dates = fixture()
    result = run(raw, events, hold=20)
    assert result["candidateWindows"] == len(dates) - 21
    assert result["symbols"]["IWM"]["candidateExposedWindows"] <= result["candidateWindows"]


@pytest.mark.parametrize("mutation", ["fake_holiday", "missing_session", "stale_digest"])
def test_source_mismatch_and_fake_exchange_days_fail_closed(mutation):
    panel, events, _ = fixture()
    if mutation == "fake_holiday":
        panel = panel.replace(b"2026-06-15", b"2026-06-19", 1)
    elif mutation == "missing_session":
        lines = panel.splitlines(keepends=True)
        panel = b"".join(row for row in lines if not row.startswith(b"2026-06-15"))
    if mutation == "stale_digest":
        with pytest.raises(DistributionLabelAuditError, match="SHA-256"):
            audit_native_price_label_dividend_overlap(
                panel_bytes=panel, observed_events_bytes=json.dumps(events).encode(),
                expected_panel_sha256="1"*64, decision_start="2026-06-01",
                decision_end="2026-06-29", hold_sessions=5,
            )
    else:
        with pytest.raises(DistributionLabelAuditError):
            run(panel, events)


def test_event_claiming_complete_cannot_self_certify_sources():
    raw, events, _ = fixture()
    events["coverage"] = "VERIFIED_COMPLETE"
    with pytest.raises(DistributionLabelAuditError, match="cannot self-certify"):
        run(raw, events)


def test_pre_ex_date_entry_is_required_and_ex_date_exit_keeps_entitlement():
    raw, events, dates = fixture()
    ex = date.fromisoformat("2026-06-15")
    source = [date.fromisoformat(d) for d in dates]
    pos = source.index(ex)
    assert pos >= 6
    # If sell at the ex-date open, shares held the previous close remain
    # dividend-eligible; entry at the ex-date open is too late.
    entered_before = source[pos-5]
    decision_before = source[pos-6]
    entry_on_ex = source[pos]
    assert entered_before < ex <= source[pos]
    assert entry_on_ex == ex
    result = run(raw, events, first=decision_before.isoformat(),
                 last=decision_before.isoformat())
    assert result["symbols"]["IWM"]["candidateExposedWindows"] == 1
    on_ex_decision = source[pos-1]
    result = run(raw, events, first=on_ex_decision.isoformat(),
                 last=on_ex_decision.isoformat())
    assert result["symbols"]["IWM"]["candidateExposedWindows"] == 0


def test_unknown_issuer_events_cannot_become_qualified_zero_events():
    raw, events, _ = fixture()
    events["events"] = []
    with pytest.raises(DistributionLabelAuditError, match="events are required"):
        run(raw, events)
