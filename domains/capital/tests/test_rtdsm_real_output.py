"""Time boundaries and same-vintage arithmetic, not file-retention tests."""

from __future__ import annotations

import hashlib
import os
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from ordivon_capital.markets.rtdsm_real_output import (
    admit_routput_rows,
    parse_routput_archive,
    routput_asof,
)

SOURCE = [
    ["DATE", "ROUTPUT25M1", "ROUTPUT25M2", "ROUTPUT25M3"],
    ["2024:Q3", 23400.3, 23400.3, 23400.3],
    ["2024:Q4", "#N/A", 23530.9, 23536.3],
    ["2025:Q1", "#N/A", "#N/A", "#N/A"],
]
DIGEST = "a" * 64


def admit(rows=None):
    return admit_routput_rows(deepcopy(SOURCE if rows is None else rows), source_sha256=DIGEST)


def at(instant, quarter="2024:Q4", archive=None):
    return routput_asof(
        archive if archive is not None else admit(),
        when=datetime.fromisoformat(instant),
        observation_quarter=quarter,
    )


def test_no_eligible_vintage_before_following_month_new_york():
    out = at("2025-02-01T04:59:59+00:00")
    assert out["reason"] == "NO_ELIGIBLE_VINTAGE"
    out = at("2025-02-01T05:00:00+00:00")
    assert out["vintageColumn"] == "ROUTPUT25M1"
    assert out["reason"] == "MISSING_IN_ELIGIBLE_VINTAGE"
    assert out["levelRealUsdBillions"] is None


def test_actual_monthly_vintage_example_never_backfills_missing_value():
    out = at("2025-02-28T23:59:59-05:00")
    assert out["standing"] == "UNKNOWN"
    assert out["vintageColumn"] == "ROUTPUT25M1"
    out = at("2025-03-01T00:00:00-05:00")
    assert out["levelRealUsdBillions"] == "23530.9"
    assert out["previousQuarterLevelSameVintage"] == "23400.3"
    assert abs(Decimal(out["quarterOverQuarterGrowthFraction"]) -
               (Decimal("23530.9") / Decimal("23400.3") - 1)) < Decimal("1e-26")
    assert out["publicationTimestampAttested"] is False
    assert out["capitalAndTradingAuthority"] is False


def test_future_revision_does_not_change_historical_projection():
    changed = deepcopy(SOURCE)
    changed[1][3] = 9999.0
    changed[2][3] = 99999.0
    assert at("2025-03-01T00:00:00-05:00") == at(
        "2025-03-01T00:00:00-05:00", archive=admit(changed)
    )
    later = at("2025-04-01T00:00:00-04:00", archive=admit(changed))
    assert later["levelRealUsdBillions"] == "99999.0"
    assert later["previousQuarterLevelSameVintage"] == "9999.0"


def test_latest_known_quarter_and_explicit_missing_are_distinct():
    assert at("2025-02-01T05:00:00+00:00", quarter=None)["observationQuarter"] == "2024:Q3"
    assert at("2025-03-01T05:00:00+00:00", quarter=None)["observationQuarter"] == "2024:Q4"
    assert at("2025-04-01T04:00:00+00:00", quarter="2025:Q1")["standing"] == "UNKNOWN"


def test_missing_latest_cell_does_not_fallback_to_prior_vintage():
    changed = deepcopy(SOURCE)
    changed[2][3] = "#N/A"
    out = at("2025-04-01T00:00:00-04:00", archive=admit(changed))
    assert out["reason"] == "MISSING_IN_ELIGIBLE_VINTAGE"
    assert out["levelRealUsdBillions"] is None


@pytest.mark.parametrize("mutate", [
    lambda d: d[0].__setitem__(2, "ROUTPUT25M1"),
    lambda d: d[0].__setitem__(2, "ROUTPUT25M4"),
    lambda d: d[1].__setitem__(0, "2024:Q1"),
    lambda d: d[2].__setitem__(0, "2024:Q3"),
    lambda d: d[2].pop(),
])
def test_ambiguous_matrix_rejected(mutate):
    rows = deepcopy(SOURCE)
    mutate(rows)
    with pytest.raises(ValueError):
        admit(rows)


@pytest.mark.parametrize("value", [0, -1, float("inf"), "0", "#VALUE!", True])
def test_bad_economic_cell_is_not_unknown_or_zero(value):
    rows = deepcopy(SOURCE)
    rows[2][2] = value
    with pytest.raises(ValueError):
        at("2025-03-01T00:00:00-05:00", archive=admit(rows))


def test_naive_time_and_wrong_source_digest_rejected():
    with pytest.raises(ValueError, match="timezone"):
        at("2025-03-01T00:00:00")
    with pytest.raises(ValueError, match="SHA-256"):
        parse_routput_archive(b"not original bytes", expected_sha256=DIGEST)


@pytest.mark.provider_qualification
def test_actual_philadelphia_fed_workbook_and_consumer():
    path = os.environ.get("ORDIVON_FINANCE_ROUTPUT_XLSX")
    if not path:
        pytest.skip("exact original ROUTPUT workbook not supplied")
    raw = Path(path).read_bytes()
    digest = "ae854a7518bf3a0504e4c477344bd7ed98c4321326ed2b1952b69ffaa1a7adce"
    assert hashlib.sha256(raw).hexdigest() == digest
    archive = parse_routput_archive(raw, expected_sha256=digest)
    assert at("2025-02-01T05:00:00+00:00", archive=archive)["reason"] == "MISSING_IN_ELIGIBLE_VINTAGE"
    assert at("2025-03-01T05:00:00+00:00", archive=archive)["levelRealUsdBillions"] == "23530.9"
    assert at("2025-04-01T04:00:00+00:00", archive=archive)["levelRealUsdBillions"] == "23536.3"
