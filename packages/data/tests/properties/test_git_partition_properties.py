"""Independent finite optimum oracle for ordered frame partitioning."""

from __future__ import annotations

import sys
from itertools import pairwise
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from ordivon_data.git_identity import partition_object_batches


@given(st.lists(st.integers(min_value=0, max_value=40), min_size=1, max_size=25))
@settings(max_examples=300, derandomize=True, database=None, deadline=None)
def test_partition_preserves_order_bound_and_minimal_number_of_batches(sizes):
    # Independent DP enumerates all possible preceding contiguous cuts.
    # Distinct labels ensure repeated sizes do not conceal dropped entries.
    headers = [(f"{index:02}".encode(), size) for index, size in enumerate(sizes)]
    weights = [size + 4 for size in sizes]
    budget = 50
    costs = [0] + [len(weights) + 1] * len(weights)
    for end in range(1, len(weights) + 1):
        for start in range(end):
            if sum(weights[start:end]) <= budget:
                costs[end] = min(costs[end], costs[start] + 1)
    with patch("ordivon_data.git_identity._MAX_BATCH_BYTES", budget):
        chunks = partition_object_batches(headers)
    assert [item for chunk in chunks for item in chunk] == headers
    assert all(
        chunk and sum(len(h) + n + 2 for h, n in chunk) <= budget for chunk in chunks
    )
    assert len(chunks) == costs[-1]
    assert all(
        sum(len(h) + n + 2 for h, n in left) + len(right[0][0]) + right[0][1] + 2
        > budget
        for left, right in pairwise(chunks)
    )
