"""Independent integer-time and Cartesian coverage oracles for Markets.

These are synthetic operator bindings, not publisher, rights or PIT evidence
for actual securities. The oracle uses integer offsets, not the implementation's
datetime comparisons or exchange calendar.
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from test_etf_eod_snapshot import admit, fixture

from ordivon_capital.markets.etf_eod_snapshot import SnapshotAdmissionError

# Fixed independent controls: winter, DST regular session, and early close.
SESSIONS = (
    ("2026-01-08", "2026-01-08T21:00:00Z"),
    ("2026-04-02", "2026-04-02T20:00:00Z"),
    ("2026-11-27", "2026-11-27T18:00:00Z"),
)
OFFSETS = st.one_of(st.integers(-4, 4), st.integers(-3_600_000_000, 3_600_000_000))


def clock(close, offset_us):
    return (
        (datetime.fromisoformat(close) + timedelta(microseconds=offset_us))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


@settings(max_examples=256, derandomize=True, deadline=None)
@given(
    session=st.sampled_from(SESSIONS),
    availability=OFFSETS,
    capture=OFFSETS,
    decision=OFFSETS,
    basis=st.sampled_from(("SOURCE_REPORTED", "FIRST_OBSERVED")),
)
@example(session=SESSIONS[0], availability=0, capture=0, decision=0, basis="FIRST_OBSERVED")
@example(session=SESSIONS[1], availability=-1, capture=0, decision=0, basis="SOURCE_REPORTED")
@example(session=SESSIONS[1], availability=1, capture=0, decision=1, basis="SOURCE_REPORTED")
@example(session=SESSIONS[2], availability=0, capture=1, decision=0, basis="SOURCE_REPORTED")
@example(session=SESSIONS[2], availability=0, capture=1, decision=1, basis="FIRST_OBSERVED")
def test_clock_contract_matches_independent_integer_order(
    session, availability, capture, decision, basis
):
    day, close = session
    payload = fixture()
    payload["capturedAt"] = clock(close, capture)
    payload["marks"][0].update(
        sessionDate=day,
        availableAt=clock(close, availability),
        availabilityBasis=basis,
    )
    # Integer-time oracle independent of the admission's parsed datetimes.
    eligible = 0 <= availability <= capture <= decision and (
        basis == "SOURCE_REPORTED" or availability == capture
    )
    if eligible:
        snapshot = admit(
            payload, expected_session_closes={day: close}, decision_at=clock(close, decision)
        )
        assert snapshot.prices_for(day) == {"TEST": 18342}
        assert snapshot.marks[0].availability_basis == basis
        # Advancing the decision alone cannot turn this accepted mark into a future mark.
        assert (
            admit(
                payload,
                expected_session_closes={day: close},
                decision_at=clock(close, decision + 1),
            ).marks
            == snapshot.marks
        )
    else:
        with pytest.raises(SnapshotAdmissionError):
            admit(payload, expected_session_closes={day: close}, decision_at=clock(close, decision))


@settings(max_examples=128, derandomize=True, deadline=None)
@given(
    instruments=st.lists(
        st.sampled_from(("AAA", "BBB", "CCC", "DDD")), min_size=1, max_size=4, unique=True
    ),
    sessions=st.lists(st.sampled_from(SESSIONS), min_size=1, max_size=3, unique=True),
    data=st.data(),
)
def test_permutation_and_cartesian_coverage_are_independent_of_input_order(
    instruments, sessions, data
):
    closes = dict(sessions)
    keys = [(day, instrument) for day, _ in sessions for instrument in instruments]
    prices = data.draw(st.lists(st.integers(1, 2**63 - 1), min_size=len(keys), max_size=len(keys)))
    expected = dict(zip(keys, prices, strict=True))
    payload = fixture()
    capture = "2026-11-27T20:00:00Z"
    payload["capturedAt"] = capture
    payload["marks"] = [
        {
            "sessionDate": day,
            "instrumentId": symbol,
            "priceMinor": expected[day, symbol],
            "availableAt": closes[day],
            "availabilityBasis": "SOURCE_REPORTED",
        }
        for day, symbol in keys
    ]
    kwargs = {
        "expected_instruments": tuple(instruments),
        "expected_session_closes": closes,
        "decision_at": capture,
    }
    canonical = admit(payload, **kwargs)
    permuted = payload | {"marks": list(data.draw(st.permutations(payload["marks"])))}
    alternate = admit(
        permuted,
        **(
            kwargs
            | {
                "expected_instruments": tuple(reversed(instruments)),
                "expected_session_closes": dict(reversed(sessions)),
            }
        ),
    )
    # The digest binds the byte order; the canonical economics do not.
    assert alternate.marks == canonical.marks
    for day in closes:
        assert canonical.prices_for(day) == {
            symbol: expected[day, symbol] for symbol in instruments
        }
    index = data.draw(st.integers(0, len(keys) - 1))
    for marks in (
        payload["marks"][:index] + payload["marks"][index + 1 :],
        payload["marks"] + [payload["marks"][index]],
    ):
        with pytest.raises(SnapshotAdmissionError):
            admit(payload | {"marks": marks}, **kwargs)
