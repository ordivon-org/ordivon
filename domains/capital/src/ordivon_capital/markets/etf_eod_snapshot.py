"""Offline admission of a committed, operator-supplied ETF closing-mark snapshot.

Markets checks the declared evidence binding and clocks; it does not verify the
operator's license, calendar or vendor assertions independently.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

_MAX_BYTES = 2 * 1024 * 1024
_MAX_SESSIONS = 366
_MAX_INSTRUMENTS = 32
_MAX_MINOR = 2**63 - 1
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
_REF = re.compile(r"[!-~]{1,256}")
_INSTRUMENT = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,63}")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z")


class SnapshotAdmissionError(ValueError):
    """An ETF mark snapshot is not admissible for the specified paper decision."""


@dataclass(frozen=True, slots=True)
class EtfCloseMark:
    session_date: str
    instrument_id: str
    price_minor: int
    session_close_at: datetime
    available_at: datetime
    availability_basis: str


@dataclass(frozen=True, slots=True)
class AdmittedEtfEodSnapshot:
    sha256: str
    source_id: str
    rights_ref: str
    corporate_actions_ref: str
    captured_at: datetime
    decision_at: datetime
    supersedes_sha256: str | None
    marks: tuple[EtfCloseMark, ...]

    def prices_for(self, session_date: str) -> dict[str, int]:
        """Return fresh USD-cent raw closes for exactly one admitted session."""
        result = {
            mark.instrument_id: mark.price_minor
            for mark in self.marks
            if mark.session_date == session_date
        }
        if not result:
            raise KeyError(session_date)
        return result


def _object(value: Any, fields: str, label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(fields.split()):
        raise SnapshotAdmissionError(f"{label} fields do not match schema")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotAdmissionError("duplicate JSON key")
        result[key] = value
    return result


def _matches(value: Any, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def _timestamp(value: Any, label: str) -> datetime:
    if _matches(value, _UTC):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    raise SnapshotAdmissionError(f"{label} must be a valid UTC timestamp ending in Z")


def _session_date(value: Any) -> date:
    if _matches(value, _DATE):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise SnapshotAdmissionError("session date must be a valid YYYY-MM-DD date")


def _require_reference(actual: Any, expected: str, label: str) -> None:
    if not _matches(expected, _REF) or actual != expected:
        raise SnapshotAdmissionError(f"snapshot {label} reference does not match operator binding")


def admit_etf_eod_snapshot(
    snapshot_bytes: bytes,
    *,
    expected_sha256: str,
    expected_source_id: str,
    expected_rights_ref: str,
    expected_corporate_actions_ref: str,
    expected_instruments: Sequence[str],
    expected_session_closes: Mapping[str, str],
    decision_at: str,
) -> AdmittedEtfEodSnapshot:
    """Admit raw USD cent marks for a trusted operator-supplied decision scope.

    The operator supplies the digest, approved references, instruments, and
    authoritative exchange session closes independently from the snapshot.
    Capture must precede or coincide with the decision even if the source
    reports earlier publication. An action-free window is required until the
    paper ledger can model the declared corporate actions.
    """
    if type(snapshot_bytes) is not bytes or not 0 < len(snapshot_bytes) <= _MAX_BYTES:
        raise SnapshotAdmissionError("snapshot must be nonempty bytes within the size limit")
    digest = "sha256:" + hashlib.sha256(snapshot_bytes).hexdigest()
    if digest != expected_sha256:
        raise SnapshotAdmissionError("snapshot digest does not match operator commitment")
    try:
        data = json.loads(snapshot_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
    except SnapshotAdmissionError:
        raise
    except (ValueError, RecursionError) as error:
        raise SnapshotAdmissionError("snapshot must be valid bounded UTF-8 JSON") from error
    data = _object(
        data,
        "schemaVersion kind sourceId currency priceBasis rights corporateActions "
        "capturedAt supersedesSha256 marks",
        "snapshot",
    )
    if type(data["schemaVersion"]) is not int or data["schemaVersion"] != 1:
        raise SnapshotAdmissionError("schemaVersion must be exactly 1")
    if data["kind"] != "ordivon.finance.markets.etf-eod-snapshot":
        raise SnapshotAdmissionError("unexpected snapshot kind")
    if data["priceBasis"] != "RAW_UNADJUSTED_CLOSE" or data["currency"] != "USD":
        raise SnapshotAdmissionError("snapshot must contain raw USD closes")
    _require_reference(data["sourceId"], expected_source_id, "source")
    rights = _object(data["rights"], "status evidenceRef", "rights")
    if rights["status"] != "AUTHORIZED_PRIVATE_PAPER_USE":
        raise SnapshotAdmissionError("private storage and paper-use rights must be declared")
    _require_reference(rights["evidenceRef"], expected_rights_ref, "rights")
    actions = _object(data["corporateActions"], "coverage evidenceRef events", "corporate actions")
    if actions["coverage"] != "COMPLETE":
        raise SnapshotAdmissionError("corporate actions coverage must be declared complete")
    _require_reference(actions["evidenceRef"], expected_corporate_actions_ref, "corporate actions")
    if actions["events"] != []:
        raise SnapshotAdmissionError("corporate action events cannot be processed by paper R1")

    captured = _timestamp(data["capturedAt"], "capturedAt")
    decision = _timestamp(decision_at, "decisionAt")
    if captured > decision:
        raise SnapshotAdmissionError("snapshot was captured after the decision")
    supersedes = data["supersedesSha256"]
    if supersedes is not None and (not _matches(supersedes, _SHA256) or supersedes == digest):
        raise SnapshotAdmissionError("superseded snapshot digest is invalid")

    if (
        not isinstance(expected_instruments, (list, tuple))
        or not 1 <= len(expected_instruments) <= _MAX_INSTRUMENTS
        or any(not _matches(value, _INSTRUMENT) for value in expected_instruments)
        or len(set(expected_instruments)) != len(expected_instruments)
    ):
        raise SnapshotAdmissionError("operator must bind a bounded unique set of instrument IDs")
    if (
        not isinstance(expected_session_closes, Mapping)
        or not 1 <= len(expected_session_closes) <= _MAX_SESSIONS
    ):
        raise SnapshotAdmissionError("operator must bind a bounded exchange session schedule")
    eastern = ZoneInfo("America/New_York")
    closes = {}
    for day, value in expected_session_closes.items():
        session = _session_date(day)
        close = _timestamp(value, "session close")
        if close.astimezone(eastern).date() != session:
            raise SnapshotAdmissionError("session close is outside the bound exchange date")
        closes[day] = close

    raw_marks = data["marks"]
    if type(raw_marks) is not list or len(raw_marks) > _MAX_SESSIONS * _MAX_INSTRUMENTS:
        raise SnapshotAdmissionError("snapshot marks must be a bounded array")
    marks: dict[tuple[str, str], EtfCloseMark] = {}
    for raw in raw_marks:
        mark = _object(raw, "sessionDate instrumentId priceMinor availableAt availabilityBasis", "mark")
        day, instrument, price = mark["sessionDate"], mark["instrumentId"], mark["priceMinor"]
        if type(day) is not str or day not in closes:
            raise SnapshotAdmissionError("mark belongs to an unbound session")
        if type(instrument) is not str or instrument not in expected_instruments:
            raise SnapshotAdmissionError("mark belongs to an unbound instrument")
        key = (day, instrument)
        if key in marks:
            raise SnapshotAdmissionError("snapshot contains a duplicate session/instrument mark")
        if type(price) is not int or not 0 < price <= _MAX_MINOR:
            raise SnapshotAdmissionError("mark price must be positive integer USD cents up to int64")
        available = _timestamp(mark["availableAt"], "availableAt")
        basis = mark["availabilityBasis"]
        if basis not in ("SOURCE_REPORTED", "FIRST_OBSERVED"):
            raise SnapshotAdmissionError("mark availability basis is unknown")
        if available < closes[day]:
            raise SnapshotAdmissionError("mark was available before session close")
        if available > captured:
            raise SnapshotAdmissionError("mark availability is after capture")
        if basis == "FIRST_OBSERVED" and available != captured:
            raise SnapshotAdmissionError("first-observed availability must equal capture")
        marks[key] = EtfCloseMark(day, instrument, price, closes[day], available, basis)
    if len(marks) != len(closes) * len(expected_instruments):
        raise SnapshotAdmissionError("snapshot is missing an expected session/instrument mark")
    return AdmittedEtfEodSnapshot(
        digest,
        expected_source_id,
        expected_rights_ref,
        expected_corporate_actions_ref,
        captured,
        decision,
        supersedes,
        tuple(marks[key] for key in sorted(marks)),
    )
