"""Behavioral laws at the actual repository verification selector and sharder."""
from collections import Counter
from pathlib import Path
import sys

from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import affected_owners
import ci_owner_shards
import convergence_plan

# Use the actual declared consumer seams, plus a stable independent witness
# for the previously missed Composition consumer.
CONSUMERS = []
convergence_plan.load_dependency_graph(test_only_consumers=CONSUMERS)
PATH_CASES = tuple(sorted({
    fragment + "verification-probe.py" if fragment.endswith("/") else fragment
    for _, _, fragment, scope in CONSUMERS if scope == "PATH"
} | {owner.root + "verification-probe.py" for owner in affected_owners.OWNERS}))
TASKS = tuple(owner.queue_task for owner in affected_owners.OWNERS)


def selection(paths):
    plan = convergence_plan.build_plan(changed_files=paths)
    return (
        plan["directOwners"], plan["verificationOwners"],
        plan["taskLocalTestConsumers"], plan["queueVerifyTasks"],
    )


def test_exact_finance_consumer_survives_equivalent_path():
    path = "domains/capital/scripts/strategic_contribution_brief.py"
    original = selection([path])
    assert "composition:verify" in original[3]
    assert selection(["./" + path]) == original


@settings(max_examples=80, deadline=None, derandomize=True)
@given(st.lists(st.sampled_from(PATH_CASES), min_size=1, max_size=5, unique=True),
       st.sampled_from(["prefix", "inner-dot", "double-slash"]))
def test_path_alias_preserves_consumer_selection(paths, alias):
    def transform(path):
        if alias == "prefix":
            return "./" + path
        if alias == "inner-dot":
            return path.replace("/", "/./", 1)
        return path.replace("/", "//", 1)
    assert selection([transform(path) for path in paths]) == selection(paths)


@settings(max_examples=80, deadline=None, derandomize=True)
@given(st.lists(st.sampled_from(TASKS), unique=True),
       st.integers(min_value=1, max_value=ci_owner_shards.MAX_SHARDS),
       st.booleans())
def test_sharding_is_a_lossless_order_independent_partition(tasks, count, formal):
    selected = tasks + (["formal:verify"] if formal else [])
    rows = ci_owner_shards.shard_queue(selected, count)["include"]
    assert 1 <= len(rows) <= count
    assert len({row["shard"] for row in rows}) == len(rows)
    assert Counter(task for row in rows for task in row["tasks"]) == Counter(tasks)
    assert rows == ci_owner_shards.shard_queue(list(reversed(selected)), count)["include"]
