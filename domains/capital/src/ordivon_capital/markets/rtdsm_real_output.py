"""Read the Philadelphia Fed ROUTPUT monthly-vintage matrix with Calamine.

A current official historical archive is not a signed first-publication
receipt. Use only completed vintage months in New York time. Keep a missing
cell unknown instead of substituting a later revision.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, localcontext
from typing import Any
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
MAX_WORKBOOK_BYTES = 8_000_000
_MAX_UNCOMPRESSED_BYTES = 64_000_000
_MONTH = re.compile(r"ROUTPUT(\d{2})M([1-9]|1[0-2])\Z")
_QUARTER = re.compile(r"(\d{4}):Q([1-4])\Z")


def _next_month(day: date) -> date:
    return date(day.year + (day.month == 12), day.month % 12 + 1, 1)


def _vintage(value: Any) -> date:
    match = _MONTH.fullmatch(value) if type(value) is str else None
    if match is None:
        raise ValueError("invalid ROUTPUT monthly vintage identity")
    yy, month = map(int, match.groups())
    return date(1900 + yy if yy >= 65 else 2000 + yy, month, 1)


def _quarter(value: Any) -> tuple[int, int]:
    match = _QUARTER.fullmatch(value) if type(value) is str else None
    if match is None:
        raise ValueError("invalid ROUTPUT observation quarter")
    return tuple(map(int, match.groups()))


def _quarter_next_start(quarter: tuple[int, int]) -> date:
    year, q = quarter
    return date(year + (q == 4), (q * 3) % 12 + 1, 1)


def _previous_quarter(value: str) -> str:
    year, q = _quarter(value)
    return f"{year - (q == 1):04d}:Q{(q - 2) % 4 + 1}"


def _cell(value: Any) -> Decimal | None:
    if value is None or value in ("", "#N/A"):
        return None
    if type(value) not in (int, float):
        raise ValueError("unsupported ROUTPUT numeric cell")
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ValueError("ROUTPUT level must be finite and positive")
    return number


@dataclass(frozen=True)
class RoutputArchive:
    source_sha256: str
    vintages: tuple[date, ...]
    labels: tuple[str, ...]
    quarters: tuple[str, ...]
    cells: tuple[tuple[Any, ...], ...]
    source_bytes_digest_verified: bool = False


def admit_routput_rows(rows: list[list[Any]], *, source_sha256: str) -> RoutputArchive:
    """Pure schema admission after XLSX decoding; does not authenticate a source."""
    if type(source_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("invalid ROUTPUT SHA-256 identity")
    if not 2 <= len(rows) <= 2000 or not 2 <= len(rows[0]) <= 1200:
        raise ValueError("ROUTPUT matrix outside supported dimensions")
    header = rows[0]
    if header[0] != "DATE" or len(set(header)) != len(header):
        raise ValueError("missing or duplicate ROUTPUT column identities")
    labels = tuple(header[1:])
    vintages = tuple(map(_vintage, labels))
    if any(_next_month(a) != b for a, b in zip(vintages, vintages[1:])):
        raise ValueError("ROUTPUT vintage months must be strictly contiguous")
    quarters = []
    values = []
    previous = None
    for row in rows[1:]:
        if len(row) != len(header):
            raise ValueError("ragged ROUTPUT matrix")
        quarter = _quarter(row[0])
        if previous is not None and _quarter_next_start(previous) != date(
            quarter[0], (quarter[1] - 1) * 3 + 1, 1
        ):
            raise ValueError("ROUTPUT observation quarters must be strictly contiguous")
        previous = quarter
        quarters.append(row[0])
        values.append(tuple(row[1:]))
    return RoutputArchive(source_sha256, vintages, labels, tuple(quarters), tuple(values))


def parse_routput_archive(raw: bytes, *, expected_sha256: str) -> RoutputArchive:
    if not 0 < len(raw) <= MAX_WORKBOOK_BYTES:
        raise ValueError("ROUTPUT workbook outside byte limit")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError("ROUTPUT workbook SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as package:
        members = package.infolist()
        if len(members) > 128 or sum(x.file_size for x in members) > _MAX_UNCOMPRESSED_BYTES:
            raise ValueError("ROUTPUT XLSX expansion outside bounds")
        if len({x.filename for x in members}) != len(members):
            raise ValueError("duplicate XLSX members")
    # Mature Rust-backed reader, not a hand-written XLSX parser.
    from python_calamine import CalamineWorkbook

    workbook = CalamineWorkbook.from_filelike(io.BytesIO(raw))
    if workbook.sheet_names != ["routput"]:
        raise ValueError("unexpected ROUTPUT workbook sheets")
    rows = workbook.get_sheet_by_index(0).to_python()
    return replace(
        admit_routput_rows(rows, source_sha256=actual), source_bytes_digest_verified=True
    )


def routput_asof(
    archive: RoutputArchive, *, when: datetime, observation_quarter: str | None = None
) -> dict[str, Any]:
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("ROUTPUT as-of must have timezone")
    if observation_quarter is not None:
        _quarter(observation_quarter)
    local = when.astimezone(NY)
    eligible = [i for i, month in enumerate(archive.vintages) if _next_month(month) <= local.date()]
    base = {
        "standing": "UNKNOWN",
        "sourceSha256": archive.source_sha256,
        "source": "PHILADELPHIA_FED_RTDSM_ROUTPUT",
        "sourceAuthentication": "DECLARED_SOURCE_NOT_ORIGIN_ATTESTATION",
        "sourceBytesDigestStanding": (
            "MATCHED_EXPECTED_SHA256" if archive.source_bytes_digest_verified
            else "UNATTESTED_ROW_INPUT"
        ),
        "decisionAtNewYork": local.isoformat(),
        "vintageEligibility": "FOLLOWING_MONTH_START_NEW_YORK_CONSERVATIVE_BOUND",
        "publicationTimestampAttested": False,
        "capitalAndTradingAuthority": False,
        "observationQuarter": observation_quarter,
        "levelRealUsdBillions": None,
        "quarterOverQuarterGrowthFraction": None,
        "growthStanding": "UNKNOWN",
    }
    if not eligible:
        return {**base, "reason": "NO_ELIGIBLE_VINTAGE"}
    index = eligible[-1]
    month = archive.vintages[index]
    base.update(
        vintageMonth=month.isoformat()[:7],
        vintageColumn=archive.labels[index],
        eligibleFromNewYork=datetime.combine(_next_month(month), datetime.min.time(), NY).isoformat(),
        latestArchiveVintageMonth=archive.vintages[-1].isoformat()[:7],
    )
    if observation_quarter is None:
        for q, cells in zip(reversed(archive.quarters), reversed(archive.cells)):
            if _quarter_next_start(_quarter(q)) <= month and _cell(cells[index]) is not None:
                observation_quarter = q
                break
    if observation_quarter is None:
        return {**base, "reason": "NO_OBSERVED_QUARTER_IN_ELIGIBLE_VINTAGE"}
    base["observationQuarter"] = observation_quarter
    if _quarter_next_start(_quarter(observation_quarter)) > month:
        return {**base, "reason": "OBSERVATION_QUARTER_NOT_COMPLETED_BEFORE_VINTAGE_MONTH"}
    if observation_quarter not in archive.quarters:
        return {**base, "reason": "OBSERVATION_QUARTER_NOT_IN_ARCHIVE"}
    row = archive.quarters.index(observation_quarter)
    level = _cell(archive.cells[row][index])
    if level is None:
        return {**base, "reason": "MISSING_IN_ELIGIBLE_VINTAGE"}
    previous_q = _previous_quarter(observation_quarter)
    previous = (
        _cell(archive.cells[archive.quarters.index(previous_q)][index])
        if previous_q in archive.quarters else None
    )
    if previous is not None:
        with localcontext() as ctx:
            ctx.prec = 34
            growth = format(level / previous - 1, "f")
    else:
        growth = None
    return {
        **base,
        "standing": "DECLARED_RTDSM_MONTHLY_VINTAGE_CONSERVATIVE_BOUND",
        "levelRealUsdBillions": format(level, "f"),
        "previousQuarter": previous_q,
        "previousQuarterLevelSameVintage": format(previous, "f") if previous is not None else None,
        "quarterOverQuarterGrowthFraction": growth,
        "growthStanding": "SAME_VINTAGE_NONANNUALIZED" if growth is not None else "UNKNOWN",
        "reason": None,
    }
