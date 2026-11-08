"""Markets ETF EOD -> Research PIT -> existing Portfolio: first-observed boundary.

The fixture is synthetic and operator-declared, NOT primary source attestation.
No live market data, accounting or exchange effects are exercised.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime

import pytest

from ordivon_capital.markets.etf_eod_snapshot import (
    SnapshotAdmissionError,
    admit_etf_eod_snapshot,
)
from ordivon_capital.research.pit_joint_forecast import (
    PointInTimeError,
    PriceVintage,
    empirical_joint_forecast,
    etf_eod_capture_to_pit_vintages,
    from_json_payload,
    point_in_time_prices,
    solve_pit_payload,
)

SOURCE = "synthetic-source-not-attested"
RIGHTS = "operator-evidence:private-paper"
ACTIONS = "operator-evidence:actions-empty-unverified"
DAYS = ("2026-01-30", "2026-02-27", "2026-03-31", "2026-04-30")
CLOSES = (
    "2026-01-30T21:00:00Z", "2026-02-27T21:00:00Z",
    "2026-03-31T20:00:00Z", "2026-04-30T20:00:00Z",
)
CAPTURE = "2026-05-02T12:00:00Z"
VALUES = ((10000, 10000), (10500, 9500), (9450, 10450), (10395, 9405))


def source(capture=CAPTURE, *, last_a=None, supersedes=None):
    marks = []
    for index, day in enumerate(DAYS):
        for j, asset in enumerate(("A", "B")):
            value = VALUES[index][j] if last_a is None or (index, j) != (3, 0) else last_a
            marks.append({
                "sessionDate": day, "instrumentId": asset,
                "priceMinor": value, "availableAt": CLOSES[index],
                "availabilityBasis": "SOURCE_REPORTED",
            })
    return {
        "schemaVersion": 1, "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": SOURCE, "currency": "USD", "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": RIGHTS},
        "corporateActions": {"coverage": "COMPLETE", "evidenceRef": ACTIONS, "events": []},
        "capturedAt": capture, "supersedesSha256": supersedes, "marks": marks,
    }


def admit(payload, *, decision=None):
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    return admit_etf_eod_snapshot(
        raw, expected_sha256=digest, expected_source_id=SOURCE,
        expected_rights_ref=RIGHTS, expected_corporate_actions_ref=ACTIONS,
        expected_instruments=("A", "B"),
        expected_session_closes=dict(zip(DAYS, CLOSES, strict=True)),
        decision_at=decision or payload["capturedAt"],
    )


def test_operator_reported_mark_time_is_not_retroactively_available():
    snapshot = admit(source())
    assert snapshot.marks[0].available_at.isoformat().startswith("2026-01-30")
    records = etf_eod_capture_to_pit_vintages(snapshot)
    assert len(records) == 8
    assert {x.published_at for x in records} == {datetime.fromisoformat(CAPTURE)}
    assert {x.source_standing for x in records} == {"SECONDARY_VENDOR_NOT_ATTESTED"}
    assert {x.price_basis for x in records} == {"RAW_UNADJUSTED_ACTION_FREE_DECLARED"}
    assert {x.raw_source_sha256 for x in records} == {snapshot.sha256.removeprefix("sha256:")}
    assert point_in_time_prices(records, as_of=datetime.fromisoformat("2026-04-30T22:00:00Z")) == {}
    assert len(point_in_time_prices(records, as_of=datetime.fromisoformat(CAPTURE))) == 8


def test_later_correction_does_not_rewrite_frozen_investment_information():
    old = admit(source())
    revised = admit(source("2026-05-03T14:00:00Z", last_a=99999,
                           supersedes=old.sha256))
    both = (
        *etf_eod_capture_to_pit_vintages(old),
        *etf_eod_capture_to_pit_vintages(revised),
    )
    key = ("A", date.fromisoformat(DAYS[-1]))
    before = point_in_time_prices(both, as_of=datetime(2026, 5, 2, 13, tzinfo=UTC))
    after = point_in_time_prices(both, as_of=datetime(2026, 5, 3, 15, tzinfo=UTC))
    assert before[key].adjusted_close == 103.95
    assert after[key].adjusted_close == 999.99


def test_admitted_capture_reaches_existing_empirical_and_optimizer_consumer():
    snapshot = admit(source())
    records = etf_eod_capture_to_pit_vintages(snapshot)
    asof = datetime(2026, 5, 2, 14, tzinfo=UTC)
    dates = tuple(date.fromisoformat(x) for x in DAYS)
    forecast = empirical_joint_forecast(
        records=records, assets=("A", "B"), valuation_sessions=dates,
        as_of=asof, valuation_session=dates[-1],
    )
    assert forecast.training_return_count == 3
    assert len(forecast.scenarios) == 3
    assert forecast.source_digests == (snapshot.sha256.removeprefix("sha256:"),)
    assert forecast.to_dict()["price_bases"] == ["RAW_UNADJUSTED_ACTION_FREE_DECLARED"]
    assert forecast.to_dict()["source_standings"] == ["SECONDARY_VENDOR_NOT_ATTESTED"]
    payload = {
        "as_of": asof.isoformat(), "valuation_session": DAYS[-1],
        "assets": ["A", "B"], "valuation_sessions": list(DAYS),
        "prices": [
            dict(asset=r.asset, session=r.session.isoformat(),
                 published_at=r.published_at.isoformat(),
                 adjusted_close=r.adjusted_close,
                 raw_source_sha256=r.raw_source_sha256,
                 source_standing=r.source_standing, price_basis=r.price_basis)
            for r in records
        ],
        "economic_contract": {
            "gamma": 2, "initial_margin": [0.5, 0.5],
            "turnover_cost": [0.001, 0.001],
            "maintenance_by_asset": [0.3, 0.3],
            "cash_gross": 1.0, "debt_gross": 1.01,
        },
    }
    result = solve_pit_payload(payload)
    assert result["forecast_evidence"]["training_return_count"] == 3
    assert result["effects"] == "NONE_NO_TRADE_NO_ACCOUNTING"
    assert result["conditional_allocation"]["inequality_residual"] < 1e-6


def test_untrusted_caller_cannot_self_assert_verified_provider_origin():
    with pytest.raises(PointInTimeError, match="verified|attest"):
        PriceVintage(
            asset="A", session=date(2026, 1, 30),
            published_at=datetime(2026, 1, 30, 21, tzinfo=UTC),
            adjusted_close=100, raw_source_sha256="a" * 64,
            source_standing="PROVIDER_ORIGIN_VERIFIED",
        )


def test_price_basis_mixing_in_one_return_interval_fails_closed():
    records = [
        PriceVintage("A", date(2026, 1, 30), datetime(2026, 1, 30, 21, tzinfo=UTC),
                     100.0, "a" * 64, "SECONDARY_VENDOR_NOT_ATTESTED"),
        PriceVintage("A", date(2026, 2, 27), datetime(2026, 2, 27, 21, tzinfo=UTC),
                     110.0, "b" * 64, "SECONDARY_VENDOR_NOT_ATTESTED",
                     price_basis="RAW_UNADJUSTED_ACTION_FREE_DECLARED"),
    ]
    with pytest.raises(PointInTimeError, match="price basis"):
        empirical_joint_forecast(
            records=records, assets=("A",),
            valuation_sessions=(date(2026, 1, 30), date(2026, 2, 27)),
            as_of=datetime(2026, 3, 1, tzinfo=UTC),
            valuation_session=date(2026, 2, 27),
        )


def test_corporate_actions_and_capture_boundaries_remain_market_owner_authority():
    request = source()
    request["corporateActions"]["events"] = [{"type": "DIVIDEND"}]
    with pytest.raises(SnapshotAdmissionError, match="corporate action"):
        admit(request)
    with pytest.raises(SnapshotAdmissionError, match="captured after"):
        admit(source(), decision="2026-04-30T22:00:00Z")



def test_python_bool_cannot_become_a_price_vintage():
    with pytest.raises(PointInTimeError, match="positive finite"):
        PriceVintage(
            asset="A", session=date(2026, 1, 30),
            published_at=datetime(2026, 1, 30, 21, tzinfo=UTC),
            adjusted_close=True, raw_source_sha256="a" * 64,
            source_standing="SECONDARY_VENDOR_NOT_ATTESTED",
        )


@pytest.mark.parametrize("coercible", [True, False, "100", "1e4"])
def test_research_json_does_not_coerce_invalid_price_types(coercible):
    payload = {
        "as_of": "2026-02-28T12:00:00Z",
        "valuation_session": "2026-02-27",
        "assets": ["A"],
        "valuation_sessions": ["2026-01-30", "2026-02-27"],
        "prices": [
            {
                "asset": "A", "session": "2026-01-30",
                "published_at": "2026-01-30T21:00:00Z",
                "adjusted_close": coercible,
                "raw_source_sha256": "a" * 64,
                "source_standing": "SECONDARY_VENDOR_NOT_ATTESTED",
            },
            {
                "asset": "A", "session": "2026-02-27",
                "published_at": "2026-02-27T21:00:00Z",
                "adjusted_close": 110.0,
                "raw_source_sha256": "b" * 64,
                "source_standing": "SECONDARY_VENDOR_NOT_ATTESTED",
            },
        ],
        "economic_contract": {
            "gamma": 2.0, "initial_margin": [0.5], "turnover_cost": [0.001],
            "maintenance_by_asset": [0.3], "cash_gross": 1.0,
            "debt_gross": 1.01,
        },
    }
    with pytest.raises(PointInTimeError, match="JSON price"):
        from_json_payload(payload)
