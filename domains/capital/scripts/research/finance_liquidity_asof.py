"""One real cross-source US dollar liquidity as-of research consumer.

Input: already captured official H.4.1 dated-release HTML, FiscalData DTS JSON,
NYFed SOFR CSV. Output: source-qualified as-of state, not financial advice.
Only source observation identity, publication clock and accounting mathematics
are admitted. No global liquidity index or historical first-vintage authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
H41_EXPECTED_RELEASE_TIME = time(16, 30)
H41_MAX_BYTES = 2_000_000
DTS_MAX_BYTES = 100_000
SOFR_MAX_BYTES = 2_000_000

DEALER_CATALOG_MAX_BYTES = 600_000
DEALER_SERIES_MAX_BYTES = 200_000
DEALER_REPORTED_SERIES_BREAK = "SBN2024"
DEALER_SERIES_BREAK_START = date(2024, 7, 3)
DEALER_KEYS = {
    "PDPOSGST-TOT": ("treasuryExTipsNetDealerPosition", "DEALER POSITION - LONG."),
    "PDSIOSB-UTSETTOT": (
        "treasuryExTipsSecuritiesBorrowed",
        "DEALER FINANCING SECURITIES BORROWED",
    ),
    "PDSOOS-UTSETTOT": ("treasuryExTipsSecuritiesLent", "DEALER FINANCING SECURITIES LENT"),
}

H41_ROWS = {
    "reserveSupply": ("t1", "Total factors supplying reserve funds"),
    "reserveAbsorption": (
        "t2",
        "Total factors, other than reserve balances, absorbing reserve funds",
    ),
    "bankReserves": ("t2", "Reserve balances with Federal Reserve Banks"),
    "treasuryGeneralAccount": ("t2", "U.S. Treasury, General Account"),
    "reverseRepo": ("t2", "Reverse repurchase agreements"),
    "reverseRepoForeignOfficial": ("t2", "Foreign official and international accounts"),
    "reverseRepoOthers": ("t2", "Others"),
}

DTS_ROWS = {
    "opening": "Treasury General Account (TGA) Opening Balance",
    "deposits": "Total TGA Deposits (Table II)",
    "withdrawals": "Total TGA Withdrawals (Table II) (-)",
    "closing": "Treasury General Account (TGA) Closing Balance",
}


def _read(path: Path, maximum: int) -> bytes:
    if not path.is_file() or path.stat().st_size > maximum:
        raise ValueError("missing or unbounded financial source input")
    return path.read_bytes()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _HTMLCells(HTMLParser):
    """Read only existing Fed table cell IDs, no third-party HTML dependency."""

    def __init__(self):
        super().__init__()
        self.cells: dict[str, str] = {}
        self._active: str | None = None
        self._chunks: list[str] = []
        self.all_text: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in {"td", "th"}:
            identity = dict(attrs).get("id")
            if identity and re.fullmatch(r"t[12](?:r\d+c[15]|h1c3)", identity):
                if identity in self.cells:
                    raise ValueError("duplicate Federal Reserve H41 HTML cell identity")
                self._active = identity
                self._chunks = []

    def handle_data(self, data: str):
        if self._active is not None:
            self._chunks.append(data)
        self.all_text.append(data)

    def handle_endtag(self, tag: str):
        if tag in {"td", "th"} and self._active is not None:
            self.cells[self._active] = " ".join(" ".join(self._chunks).split())
            self._active = None
            self._chunks = []


@dataclass(frozen=True)
class H41:
    release_date: date
    observed_date: date
    values: dict[str, int]
    sha256: str


@dataclass(frozen=True)
class DTS:
    record_date: date
    closing: int
    rounding_residual: int
    sha256: str


def _valid_iso_day(raw: str) -> date:
    day = date.fromisoformat(raw)
    if day.isoformat() != raw:
        raise ValueError("noncanonical source date")
    return day


def parse_h41(raw: bytes, *, file_label: str) -> H41:
    if not raw or len(raw) > H41_MAX_BYTES:
        raise ValueError("invalid H41 archive size")
    p = _HTMLCells()
    p.feed(raw.decode("utf-8-sig"))
    text = " ".join(" ".join(p.all_text).split())
    m = re.search(r"Release Date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    if m is None:
        raise ValueError("H41 dated release label not present")
    release_date = datetime.strptime(m.group(1), "%B %d, %Y").date()
    if file_label != f"h41-{release_date:%Y%m%d}.html":
        raise ValueError("H41 file/date content disagreement")
    header = p.cells.get("t2h1c3")
    if header is None:
        raise ValueError("H41 Wednesday point-in-time column header missing")
    m = re.fullmatch(r"Wednesday\s*([A-Z][a-z]+ \d{1,2}, \d{4})", header)
    if m is None:
        raise ValueError("H41 cannot identify Wednesday stock-date column")
    observed = datetime.strptime(m.group(1), "%b %d, %Y").date()
    if not observed < release_date <= observed + timedelta(days=7):
        raise ValueError("H41 observation/release chronology invalid")

    values: dict[str, int] = {}
    for key, (prefix, label) in H41_ROWS.items():
        candidates = []
        for cell_id, content in p.cells.items():
            m = re.fullmatch(rf"{prefix}r(\d+)c1", cell_id)
            # Footnote suffixes occur e.g. Reverse repurchase agreements12.
            if m and (
                content == label
                or (key == "reverseRepo" and re.fullmatch(re.escape(label) + r"\s*\d+", content))
            ):
                candidates.append(m.group(1))
        if len(candidates) != 1:
            raise ValueError(f"H41 source row ambiguous/missing: {key}")
        value = p.cells.get(f"{prefix}r{candidates[0]}c5")
        if value is None or not re.fullmatch(r"-?\d{1,3}(?:,\d{3})*|0", value):
            raise ValueError(f"H41 Wednesday actual-stock missing: {key}")
        values[key] = int(value.replace(",", ""))
    if values["reverseRepo"] != (
        values["reverseRepoForeignOfficial"] + values["reverseRepoOthers"]
    ):
        raise ValueError("H41 reverse repo foreign-official plus others subdivision mismatch")
    if values["reserveSupply"] - values["reserveAbsorption"] != values["bankReserves"]:
        raise ValueError("H41 reserve conservation disagrees with official figures")
    if any(values[k] < 0 for k in ("bankReserves", "treasuryGeneralAccount", "reverseRepo")):
        raise ValueError("H41 negative observed financial stock")
    return H41(release_date, observed, values, _sha(raw))


def _treasury_next_scheduled_publication(record_date: date) -> datetime:
    """DTS: next US FEDERAL business day, published by 16:00 New York.

    Historical source docs describe the following-business-day release.
    A 16:30 local-time eligibility buffer is a scheduled-bound estimate,
    not an independently authenticated first HTTP observation.
    """
    import pandas as pd
    from pandas.tseries.holiday import USFederalHolidayCalendar
    from pandas.tseries.offsets import CustomBusinessDay

    federal_day = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    stamp = pd.Timestamp(record_date)
    if not federal_day.is_on_offset(stamp):
        raise ValueError("DTS observation date is not a US federal business day")
    following = (stamp + federal_day).date()
    return datetime.combine(following, time(16, 30), tzinfo=NY)


def parse_dts(raw: bytes) -> DTS:
    if not raw or len(raw) > DTS_MAX_BYTES:
        raise ValueError("invalid DTS source size")
    content = json.loads(raw)
    if not isinstance(content, dict) or not isinstance(content.get("data"), list):
        raise ValueError("DTS source JSON envelope invalid")
    rows = content["data"]
    if len(rows) != 4:
        raise ValueError("DTS one-day operating cash table must have 4 real rows")
    data = {}
    dates = set()
    for row in rows:
        if row.get("account_type") in data or row.get("account_type") not in DTS_ROWS.values():
            raise ValueError("unexpected or duplicate DTS account type")
        dates.add(_valid_iso_day(row["record_date"]))
        if row["close_today_bal"] != "null":
            raise ValueError("post-2022 DTS schema unexpected closing column")
        value = row.get("open_today_bal")
        if not isinstance(value, str) or not value.isdecimal():
            raise ValueError("DTS unknown financial amount must not default to zero")
        data[row["account_type"]] = int(value)
    if len(dates) != 1:
        raise ValueError("DTS mixed reporting dates")
    day = next(iter(dates))
    if day < date(2022, 4, 18):
        raise ValueError("unsupported pre-2022 DTS source layout")
    _treasury_next_scheduled_publication(day)  # rejects US federal-holiday rows
    delta = (
        data[DTS_ROWS["opening"]]
        + data[DTS_ROWS["deposits"]]
        - data[DTS_ROWS["withdrawals"]]
        - data[DTS_ROWS["closing"]]
    )
    if abs(delta) > 2:  # all four public amounts rounded independently to USD millions
        raise ValueError("DTS reported amounts fail rounded accounting conservation")
    return DTS(day, data[DTS_ROWS["closing"]], delta, _sha(raw))


def parse_sofr(raw: bytes) -> dict[date, dict[str, str]]:
    if not raw or len(raw) > SOFR_MAX_BYTES:
        raise ValueError("invalid SOFR source size")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    must = {
        "Effective Date",
        "Rate Type",
        "Rate (%)",
        "Volume ($Billions)",
        "1st Percentile (%)",
        "99th Percentile (%)",
        "Revision Indicator (Y/N)",
    }
    if not reader.fieldnames or not must.issubset(reader.fieldnames):
        raise ValueError("missing SOFR source fields")
    result = {}
    for row in reader:
        d = datetime.strptime(row["Effective Date"], "%m/%d/%Y").date()
        if d in result or row["Rate Type"] != "SOFR":
            raise ValueError("duplicate or mismatched SOFR source")
        if row["Revision Indicator (Y/N)"].strip().upper() == "Y":
            raise ValueError("revised SOFR row has no first-vintage qualification")
        try:
            rate = Decimal(row["Rate (%)"])
            volume = Decimal(row["Volume ($Billions)"])
            lo = Decimal(row["1st Percentile (%)"])
            hi = Decimal(row["99th Percentile (%)"])
        except InvalidOperation as exc:
            raise ValueError("missing SOFR value in selected bounded source window") from exc
        if (
            not all(x.is_finite() for x in (lo, rate, hi, volume))
            or not (-10 <= lo <= rate <= hi < 100)
            or not (0 < volume < 1e7)
        ):
            raise ValueError("invalid SOFR rate/volume/percentile data")
        result[d] = {
            "ratePct": str(rate),
            "volumeUsdBillions": str(volume),
            "range99Minus1Pct": str(hi - lo),
        }
    if not result:
        raise ValueError("empty SOFR history")
    return result


def parse_dealer_sources(*, catalog: bytes, series: dict[str, bytes]) -> dict[str, dict]:
    """NY Fed FR2004 weekly time series, preserving '*' as NOT_PUBLISHED.

    Source catalog is required to bind an official Key Id, a human economic
    definition and its published SBN2024 structural series break.
    """
    if not catalog or len(catalog) > DEALER_CATALOG_MAX_BYTES:
        raise ValueError("invalid primary-dealer catalog bytes")
    if set(series) != set(DEALER_KEYS):
        raise ValueError("primary-dealer native source series set incomplete")
    metadata = list(csv.DictReader(io.StringIO(catalog.decode("utf-8-sig"))))
    if not metadata or set(metadata[0]) != {"Key Id", "Label", "Series Break"}:
        raise ValueError("unrecognized primary-dealer official metadata")
    rows_by_key = {}
    for row in metadata:
        key = row["Key Id"]
        if key in DEALER_KEYS:
            if key in rows_by_key:
                raise ValueError("duplicate primary dealer catalog definition")
            rows_by_key[key] = row
    result = {}
    for key, (name, label_evidence) in DEALER_KEYS.items():
        row = rows_by_key.get(key)
        if row is None or row["Series Break"] != DEALER_REPORTED_SERIES_BREAK:
            raise ValueError(f"unqualified dealer source series break: {key}")
        if label_evidence not in row["Label"]:
            raise ValueError(f"changed dealer economic definition: {key}")
        data = series[key]
        if not data or len(data) > DEALER_SERIES_MAX_BYTES:
            raise ValueError(f"unbounded dealer financial source: {key}")
        parsed = json.loads(data)
        raw_rows = parsed.get("pd", {}).get("timeseries")
        if not isinstance(raw_rows, list) or not raw_rows:
            raise ValueError("dealer series native structure invalid")
        values = {}
        for point in raw_rows:
            d = _valid_iso_day(point["asofdate"])
            if point["keyid"] != key or d.weekday() != 2 or d in values:
                raise ValueError("dealer source weekly identity/date disagreement")
            if d < DEALER_SERIES_BREAK_START:
                continue
            raw_value = point.get("value")
            if raw_value == "*":
                # NY Fed does not publish categories with too few
                # respondents. No imputation and NOT a zero-valued balance.
                value = None
            else:
                if not isinstance(raw_value, str):
                    raise ValueError("dealer financial amount not an official string")
                try:
                    amount = Decimal(raw_value)
                except InvalidOperation as exc:
                    raise ValueError("dealer financial amount unreported/invalid") from exc
                if not amount.is_finite() or abs(amount) > Decimal("1e10"):
                    raise ValueError("dealer financial amount outside bounded unit")
                if key != "PDPOSGST-TOT" and amount < 0:
                    raise ValueError("dealer financed securities amount negative")
                value = str(amount)
            values[d] = value
        if not values:
            raise ValueError("no dealer observations in qualified 2024 series break")
        result[key] = {
            "name": name,
            "values": values,
            "sourceSha256": _sha(data),
            "seriesBreak": DEALER_REPORTED_SERIES_BREAK,
        }
    return result


def _dealer_scheduled_publication(week_ended: date) -> datetime:
    """Next week's Thursday ~16:15 ET, buffered to 16:30 ET.

    The Federal business day on or after that Thursday is the earliest
    schedule-qualified instant, not proof of actual historical release.
    """
    if week_ended.weekday() != 2:
        raise ValueError("NY Fed primary-dealer week ended must be Wednesday")
    import pandas as pd
    from pandas.tseries.holiday import USFederalHolidayCalendar
    from pandas.tseries.offsets import CustomBusinessDay

    day = pd.Timestamp(week_ended + timedelta(days=8))
    fed_business = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    if not fed_business.is_on_offset(day):
        day = day + fed_business
    return datetime.combine(day.date(), time(16, 30), tzinfo=NY)


def _dealer_asof(*, local: datetime, series: dict[str, dict]) -> dict:
    result = {}
    for key, source in series.items():
        eligible = [d for d in source["values"] if _dealer_scheduled_publication(d) <= local]
        latest = max(eligible) if eligible else None
        value = source["values"][latest] if latest is not None else None
        result[source["name"]] = {
            "seriesKey": key,
            "seriesBreak": source["seriesBreak"],
            "weekEnded": latest.isoformat() if latest else None,
            "scheduledAvailableAtNewYork": (
                _dealer_scheduled_publication(latest).isoformat() if latest else None
            ),
            "valueUsdMillions": value,
            "availability": (
                "NO_WEEK_YET_RELEASE_ELIGIBLE"
                if latest is None
                else "PUBLISHED_VALUE_WITHHELD"
                if value is None
                else "PUBLISHED_NUMERIC_LATEST_SNAPSHOT"
            ),
            "sourceSha256": source["sourceSha256"],
        }
    weeks = {r["weekEnded"] for r in result.values()}
    return {
        "weeklySeries": result,
        "weekAlignment": (
            "NO_ELIGIBLE_DEALER_WEEK"
            if weeks == {None}
            else "SAME_REPORTED_WEEK"
            if len(weeks) == 1
            else "DIFFERENT_OBSERVATION_WEEKS"
        ),
        "firstPublishedVintageAttested": False,
    }


def asof_snapshot(
    *,
    when: datetime,
    h41: list[H41],
    dts: list[DTS],
    sofr: dict[date, dict[str, str]],
    sofr_sha256: str,
    dealer_series: dict[str, dict] | None = None,
) -> dict:
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("as-of instant must be timezone aware")
    local = when.astimezone(NY)
    h41_eligible = [
        r
        for r in h41
        if datetime.combine(r.release_date, H41_EXPECTED_RELEASE_TIME, tzinfo=NY) <= local
    ]
    latest_h41 = max(h41_eligible, key=lambda x: x.release_date) if h41_eligible else None

    # Official DTS states "by 4pm the following business day".
    # USE THE US FEDERAL HOLIDAY CALENDAR: XNYS is open on Veterans Day
    # when Treasury is closed. This is scheduled availability, NOT an
    # independently signed original HTTP publication-time receipt.
    eligible_dts = [r for r in dts if _treasury_next_scheduled_publication(r.record_date) <= local]
    latest_dts = max(eligible_dts, key=lambda x: x.record_date) if eligible_dts else None

    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    calendar = cal.sessions_in_range(local.date() - timedelta(days=45), local.date())
    if len(calendar) < 3:
        raise ValueError("insufficient official XNYS sessions for conservative SOFR cutoff")
    cutoff = calendar[-3].date()
    possible_sofr = [d for d in sofr if d <= cutoff]
    last_sofr = max(possible_sofr) if possible_sofr else None
    # Match only identical OBSERVATION dates; publication dates are not
    # measurement dates. No arbitrary "latest source wins" reconciliation.
    consistency = "CROSS_SOURCE_DAY_NOT_ELIGIBLE"
    if latest_dts is not None and latest_h41 is not None:
        if latest_dts.record_date != latest_h41.observed_date:
            consistency = "DIFFERENT_OBSERVATION_DAY"
        else:
            consistency = (
                "MATCHED_SAME_DAY_MILLION_USD"
                if latest_dts.closing == latest_h41.values["treasuryGeneralAccount"]
                else "CONFLICT_DO_NOT_COMBINE"
            )
    return {
        "kind": "ordivon.finance.research.monetary-liquidity-asof-snapshot",
        "standing": "RELEASE_CALENDAR_ALIGNED_LATEST_PROVIDER_SNAPSHOT_NOT_INDEPENDENT_PIT",
        "decisionAtUtc": when.astimezone(ZoneInfo("UTC")).isoformat(),
        "decisionAtNewYork": local.isoformat(),
        "sourceQualification": {
            "h41": "DATED_OFFICIAL_ARCHIVE_SCHEDULED_1630_ET_NOT_EXTERNAL_FIRST_CAPTURE_PROOF",
            "dts": "LATEST_API_NEXT_FEDERAL_BUSINESS_DAY_1630_ET_SCHEDULE_NOT_FIRST_VINTAGE",
            "sofr": "LATEST_CSV_EFFECTIVE_DATE_AT_LEAST_TWO_XNYS_SESSIONS_OLD",
            "dealer": "LATEST_API_PREVIOUS_WEEK_THURSDAY_1630_ET_SCHEDULE_NOT_FIRST_VINTAGE"
            if dealer_series is not None
            else "NOT_REQUESTED",
        },
        "h41": (
            {
                "releasedOn": latest_h41.release_date.isoformat(),
                "observedOn": latest_h41.observed_date.isoformat(),
                "valuesUsdMillions": latest_h41.values,
                "sourceSha256": latest_h41.sha256,
            }
            if latest_h41
            else None
        ),
        "dts": (
            {
                "recordDate": latest_dts.record_date.isoformat(),
                "tgaClosingUsdMillions": latest_dts.closing,
                "roundingResidualUsdMillions": latest_dts.rounding_residual,
                "sourceSha256": latest_dts.sha256,
            }
            if latest_dts
            else None
        ),
        "sofr": (
            {
                "effectiveDate": last_sofr.isoformat(),
                "conservativeCutoffEffectiveDate": cutoff.isoformat(),
                **sofr[last_sofr],
                "sourceSha256": sofr_sha256,
            }
            if last_sofr
            else None
        ),
        "crossSourceTga": consistency,
        "dealer": _dealer_asof(local=local, series=dealer_series)
        if dealer_series is not None
        else None,
        "compositeLiquidityScore": None,
        "capitalAndTradingAuthority": False,
    }


def run(
    *,
    raw_h41: dict[str, bytes],
    raw_dts: list[bytes],
    raw_sofr: bytes,
    at: list[str],
    raw_dealer_catalog: bytes | None = None,
    raw_dealer_series: dict[str, bytes] | None = None,
) -> dict:
    releases = [parse_h41(raw, file_label=name) for name, raw in raw_h41.items()]
    dts = [parse_dts(raw) for raw in raw_dts]
    if len({r.release_date for r in releases}) != len(releases):
        raise ValueError("duplicate weekly release date")
    if len({r.record_date for r in dts}) != len(dts):
        raise ValueError("duplicate Treasury source record date")
    rates = parse_sofr(raw_sofr)
    if (raw_dealer_catalog is None) != (raw_dealer_series is None):
        raise ValueError("dealer catalog and series inputs must be provided together")
    dealer = (
        parse_dealer_sources(catalog=raw_dealer_catalog, series=raw_dealer_series)
        if raw_dealer_catalog is not None and raw_dealer_series is not None
        else None
    )
    snapshots = [
        asof_snapshot(
            when=datetime.fromisoformat(day),
            h41=releases,
            dts=dts,
            sofr=rates,
            sofr_sha256=_sha(raw_sofr),
            dealer_series=dealer,
        )
        for day in at
    ]
    return {
        "kind": "ordivon.finance.research.monetary-liquidity-asof-observation",
        "standing": "RELEASE_CALENDAR_ALIGNED_SOURCE_HISTORY_UNATTESTED",
        "snapshots": snapshots,
        "sourceCounts": {
            "h41DatedReleases": len(releases),
            "dtsDays": len(dts),
            "sofrObservations": len(rates),
            "dealerNativeSeries": len(dealer) if dealer is not None else 0,
        },
        "limitations": [
            "Historical H41 release archive page is dated but independent HTTP first-publication proof is not provided.",
            "Treasury DTS API is latest table, not a proved first-published vintage; next federal business day 16:30 ET buffer is a schedule assumption.",
            "SOFR effective date is not first publication; two XNYS session lag differs from the NYFed repo calendar.",
            "A matched same-day TGA amount is economic consistency, NOT publication-time certification.",
            "Dealer series are weekly reports published following-week Thursday ~16:15 ET, with 16:30 ET buffer; * is unpublished, not zero.",
            "Dealer 2024 structural series break prevents naive comparison with earlier data; current API values may be revised.",
            "No ETF total return, broker fills, portfolio alpha or financial effect authority.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--h41", type=Path, required=True, action="append")
    parser.add_argument("--dts", type=Path, required=True, action="append")
    parser.add_argument("--sofr", type=Path, required=True)
    parser.add_argument("--dealer-catalog", type=Path, help="Official NY Fed series metadata CSV")
    parser.add_argument(
        "--dealer-series",
        type=Path,
        action="append",
        help="Official NY Fed /api/pd/get/KEY.json, named KEY.json",
    )
    parser.add_argument(
        "--at",
        required=True,
        action="append",
        help="ISO8601 timezone-qualified research as-of instant",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.dealer_series and len({p.stem for p in args.dealer_series}) != len(args.dealer_series):
        parser.error("duplicate dealer source ID is not an independent source")
    captures = {f.name: _read(f, H41_MAX_BYTES) for f in args.h41}
    if len(captures) != len(args.h41):
        raise SystemExit("duplicate H41 capture filename")
    data = run(
        raw_h41=captures,
        raw_dts=[_read(p, DTS_MAX_BYTES) for p in args.dts],
        raw_sofr=_read(args.sofr, SOFR_MAX_BYTES),
        raw_dealer_catalog=(
            _read(args.dealer_catalog, DEALER_CATALOG_MAX_BYTES) if args.dealer_catalog else None
        ),
        raw_dealer_series=(
            {p.stem: _read(p, DEALER_SERIES_MAX_BYTES) for p in args.dealer_series}
            if args.dealer_series
            else None
        ),
        at=args.at,
    )
    serialized = json.dumps(data, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(serialized + "\n")
    print(serialized)


if __name__ == "__main__":
    main()
