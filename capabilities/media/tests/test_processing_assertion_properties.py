"""Generated independent controls for selected TTML assertion policy."""
from __future__ import annotations

import copy
import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_studio.processing_assertions import validate_assertion_contract

NAMES = (
    "timedText.cueCount", "timedText.nonnegativeStart", "timedText.positiveDurations",
    "timedText.nonemptyPackets", "timedText.maxEndSeconds", "timedText.language",
)


class AssertionProperties(unittest.TestCase):
    @settings(max_examples=100, deadline=None)
    @given(st.booleans(), st.booleans(), st.booleans(), st.booleans(),
           st.integers(min_value=0, max_value=100), st.integers(min_value=0, max_value=100),
           st.permutations(NAMES), st.sampled_from(NAMES))
    def test_optional_policy_permutation_and_missing_member(
        self, require_positive, require_nonempty, positive, nonempty, count, actual_count, order, deleted,
    ):
        profile = {
            "expectedCueCount": count, "maxEndSeconds": 78, "expectedLanguage": None,
            "requirePositiveDurations": require_positive, "requireNonemptyPackets": require_nonempty,
        }
        rows = [
            dict(name=NAMES[0], expected=count, actual=actual_count, ok=count == actual_count),
            dict(name=NAMES[1], expected=">=0", actual=0, ok=True),
            dict(name=NAMES[2], expected=True if require_positive else None, actual=positive,
                 required=require_positive, ok=(not require_positive or positive)),
            dict(name=NAMES[3], expected=True if require_nonempty else None, actual=nonempty,
                 required=require_nonempty, ok=(not require_nonempty or nonempty)),
            dict(name=NAMES[4], expected={"max": 78}, actual=78.0, ok=True),
            dict(name=NAMES[5], expected=None, actual="en", ok=True),
        ]
        lookup = {row["name"]: row for row in rows}
        ordered = [lookup[name] for name in order]
        validate_assertion_contract("timed-text", profile, ordered)
        with self.assertRaises(ValueError):
            validate_assertion_contract("timed-text", profile, [row for row in ordered if row["name"] != deleted])
        changed = copy.deepcopy(ordered)
        changed[0]["ok"] = not changed[0]["ok"]
        with self.assertRaises(ValueError):
            validate_assertion_contract("timed-text", profile, changed)
        changed = copy.deepcopy(ordered)
        next(row for row in changed if row["name"] == NAMES[0])["expected"] = True
        with self.assertRaises(ValueError):
            validate_assertion_contract("timed-text", profile, changed)
