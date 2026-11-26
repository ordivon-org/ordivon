"""Independent abstract-set oracle, not a detector or live observation test."""

import unittest
from collections import Counter

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_security_v2.change_partition import partition_changes


@settings(max_examples=150, derandomize=True, database=None, deadline=None)
@given(st.dictionaries(
    st.sampled_from(tuple("ABCDEFGH")),
    st.sets(st.sampled_from(tuple("uvwxyz")), max_size=6),
    min_size=1, max_size=8,
))
def check_partition_matches_independent_counting_oracle(groups):
    # Count occurrences, independently from the implementation's intersection.
    counts = Counter(item for items in groups.values() for item in items)
    expected_shared = sorted(item for item, count in counts.items() if count == len(groups))
    expected_local = {
        group: sorted(item for item in items if counts[item] != len(groups))
        for group, items in sorted(groups.items())
        if any(counts[item] != len(groups) for item in items)
    }
    before = {key: set(value) for key, value in groups.items()}
    shared, local = partition_changes(groups)
    assert (shared, local) == (expected_shared, expected_local)
    assert list(local) == sorted(local)
    assert groups == before
    assert partition_changes(dict(reversed(list(groups.items())))) == (shared, local)
    for key, values in groups.items():
        assert set(shared).isdisjoint(local.get(key, []))
        assert set(shared).union(local.get(key, [])) == values


class ChangePartitionTests(unittest.TestCase):
    def test_independent_counting_oracle(self):
        check_partition_matches_independent_counting_oracle()

    def test_absence_is_not_empty_observation(self):
        with self.assertRaisesRegex(ValueError, "observed group"):
            partition_changes({})
        self.assertEqual(partition_changes({"A": {"x"}, "B": set()}), ([], {"A": ["x"]}))

    def test_shared_and_local_are_disjoint(self):
        self.assertEqual(
            partition_changes({"B": {"x", "z"}, "A": {"x", "y"}}),
            (["x"], {"A": ["y"], "B": ["z"]}),
        )
