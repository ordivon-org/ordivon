import hashlib
import json

import pytest

from ordivon_capital.markets.etf_eod_snapshot import SnapshotAdmissionError, admit_etf_eod_snapshot

DAY = "2026-04-02"
CLOSE = "2026-04-02T20:00:00Z"
AVAILABLE = "2026-04-02T20:15:00Z"
CAPTURE = "2026-04-02T21:00:00Z"
SOURCE = "synthetic-source"
RIGHTS = "operator-record:rights-1"
ACTIONS = "operator-record:corporate-actions-1"


def fixture():
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.markets.etf-eod-snapshot",
        "sourceId": SOURCE,
        "currency": "USD",
        "priceBasis": "RAW_UNADJUSTED_CLOSE",
        "rights": {"status": "AUTHORIZED_PRIVATE_PAPER_USE", "evidenceRef": RIGHTS},
        "corporateActions": {"coverage": "COMPLETE", "evidenceRef": ACTIONS, "events": []},
        "capturedAt": CAPTURE,
        "supersedesSha256": None,
        "marks": [
            {"sessionDate": DAY, "instrumentId": "TEST", "priceMinor": 18342,
             "availableAt": AVAILABLE, "availabilityBasis": "SOURCE_REPORTED"}
        ],
    }


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def admit(value, **options):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return admit_etf_eod_snapshot(
        raw,
        **(
            {
                "expected_sha256": digest(raw),
                "expected_source_id": SOURCE,
                "expected_rights_ref": RIGHTS,
                "expected_corporate_actions_ref": ACTIONS,
                "expected_instruments": ("TEST",),
                "expected_session_closes": {DAY: CLOSE},
                "decision_at": CAPTURE,
            }
            | options
        ),
    )


def test_admits_exact_snapshot_and_projects_only_raw_minor_marks():
    value = fixture()
    raw = json.dumps(value).encode()
    snapshot = admit(raw)
    assert snapshot.sha256 == digest(raw)
    assert snapshot.source_id == SOURCE
    assert snapshot.captured_at.isoformat() == "2026-04-02T21:00:00+00:00"
    assert snapshot.marks[0].available_at.isoformat() == "2026-04-02T20:15:00+00:00"
    assert snapshot.marks[0].price_minor == 18342
    assert snapshot.prices_for(DAY) == {"TEST": 18342}
    with pytest.raises(KeyError):
        snapshot.prices_for("2026-04-03")


def test_does_not_treat_a_historic_bar_as_known_before_its_capture():
    with pytest.raises(SnapshotAdmissionError, match="captured after"):
        admit(fixture(), decision_at=AVAILABLE)


def test_correction_is_admitted_only_with_a_new_committed_digest_and_decision_cut():
    old = json.dumps(fixture()).encode()
    revised = fixture()
    revised["capturedAt"] = "2026-04-02T22:00:00Z"
    revised["supersedesSha256"] = digest(old)
    revised["marks"][0]["priceMinor"] += 1
    with pytest.raises(SnapshotAdmissionError, match="digest"):
        admit(revised, expected_sha256=digest(old), decision_at=revised["capturedAt"])
    with pytest.raises(SnapshotAdmissionError, match="captured after"):
        admit(revised)
    snapshot = admit(revised, decision_at=revised["capturedAt"])
    assert snapshot.prices_for(DAY) == {"TEST": 18343}
    assert snapshot.supersedes_sha256 == digest(old)
    assert admit(old).prices_for(DAY) == {"TEST": 18342}


@pytest.mark.parametrize(
    ("section", "field", "value", "reason"),
    [
        (None, "priceBasis", "ADJUSTED_CLOSE", "raw"),
        (None, "sourceId", "unbound", "source"),
        ("rights", "status", "UNKNOWN", "rights"),
        ("rights", "evidenceRef", "unbound", "rights"),
        ("corporateActions", "coverage", "UNKNOWN", "corporate actions"),
        ("corporateActions", "evidenceRef", "unbound", "corporate actions"),
        ("corporateActions", "events", [{"type": "SPLIT"}], "corporate action events"),
        ("marks", "priceMinor", True, "integer USD cents"),
        ("marks", "priceMinor", 10.5, "integer USD cents"),
        ("marks", "availableAt", "2026-04-02T19:59:59Z", "before session close"),
        ("marks", "availableAt", "2026-04-02T21:00:01Z", "after capture"),
        ("marks", "availableAt", "2026-04-02T20:15:00", "UTC"),
        ("marks", "availabilityBasis", "FIRST_OBSERVED", "equal capture"),
    ],
)
def test_rejects_unattested_or_unsafe_input(section, field, value, reason):
    request = fixture()
    target = request if section is None else request[section]
    if section == "marks":
        target = target[0]
    target[field] = value
    with pytest.raises(SnapshotAdmissionError, match=reason):
        admit(request)


def test_exact_coverage_rejects_gaps_and_duplicate_or_unscheduled_marks():
    request = fixture()
    with pytest.raises(SnapshotAdmissionError, match="missing"):
        admit(request, expected_instruments=("OTHER", "TEST"))
    request["marks"] += request["marks"]
    with pytest.raises(SnapshotAdmissionError, match="duplicate"):
        admit(request)
    request = fixture()
    request["marks"][0]["sessionDate"] = "2026-04-03"
    with pytest.raises(SnapshotAdmissionError, match="unbound session"):
        admit(request)


def test_first_observed_does_not_invent_a_provider_publication_time():
    request = fixture()
    request["marks"][0]["availabilityBasis"] = "FIRST_OBSERVED"
    request["marks"][0]["availableAt"] = CAPTURE
    assert admit(request).marks[0].availability_basis == "FIRST_OBSERVED"


def test_rejects_duplicate_json_keys_even_when_the_digest_is_correct():
    raw = json.dumps(fixture()).replace('"USD"', '"EUR", "currency": "USD"').encode()
    with pytest.raises(SnapshotAdmissionError, match="duplicate JSON key"):
        admit(raw)
