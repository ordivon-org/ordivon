"""Behavioral laws at the actual repository verification selector and sharder."""
from collections import Counter
from pathlib import Path
import sys
import tomllib

import pytest

from hypothesis import given, settings, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_owner_shards
import convergence_plan

# Read the existing declarations independently of the selector under test.
# Never derive a generator or expected consumer list from the very graph
# construction whose omission we want to detect.
HERE = Path(__file__).resolve().parent
OWNERS = tomllib.loads((HERE / "owners.toml").read_text(encoding="utf-8"))["owners"]
SEAMS = tomllib.loads((HERE / "dependency_contracts.toml").read_text(encoding="utf-8"))["seams"]
SOURCE_CONTRACTS = tuple(
    seam for seam in SEAMS if seam["kind"] == "TEST_ONLY_SOURCE_CONTRACT"
)
ROOTS = {owner["name"]: owner["root"] for owner in OWNERS}
TASKS_BY_OWNER = {
    owner["name"]: owner.get("queue_verify_task", owner["verify_task"])
    for owner in OWNERS
}
TASKS = tuple(TASKS_BY_OWNER.values())
EXACT_SEAMS = tuple(
    seam for seam in SOURCE_CONTRACTS if seam.get("selection_scope") == "PATH"
)
PATH_CASES = tuple(sorted({
    seam["allowed_fragment"] + (
        "verification-probe.py" if seam["allowed_fragment"].endswith("/") else ""
    )
    for seam in EXACT_SEAMS
} | {root + "verification-probe.py" for root in ROOTS.values()}
  | {seam["contract_ref"] for seam in SEAMS
     if seam["kind"] == "TEST_ONLY_NATIVE_RUNTIME_CONSUMER"}))

# Native Runtime/Harness test-only rules have a separate semantic
# declaration format. Restrict this independent oracle to the source
# contract provider roots, not those distinct native rules.
NATIVE_PROVIDER_ROOTS = tuple(sorted({
    ROOTS[seam["to_owner"]] for seam in SEAMS
    if seam["kind"] == "TEST_ONLY_NATIVE_RUNTIME_CONSUMER"
}))
SOURCE_CASES = tuple(
    path for path in PATH_CASES
    if any(path.startswith(ROOTS[seam["to_owner"]]) for seam in SOURCE_CONTRACTS)
    and not path.startswith(NATIVE_PROVIDER_ROOTS)
)


def expected_source_consumers(paths):
    """Independent finite set oracle for the declared source-contract scope."""
    expected = set()
    for seam in SOURCE_CONTRACTS:
        fragment = seam["allowed_fragment"]
        provider_root = ROOTS[seam["to_owner"]]
        if seam.get("selection_scope", "OWNER") == "OWNER":
            relevant = any(path.startswith(provider_root) for path in paths)
        else:
            relevant = any(
                path == fragment or (fragment.endswith("/") and path.startswith(fragment))
                for path in paths
            )
        if relevant:
            expected.add(seam["from_owner"])
    return expected


@pytest.mark.parametrize("path", SOURCE_CASES)
def test_every_declared_source_consumer_has_independent_witness(path):
    plan = convergence_plan.build_plan(changed_files=[path])
    expected = expected_source_consumers([path])
    assert set(plan["taskLocalTestConsumers"]) == expected
    assert {TASKS_BY_OWNER[owner] for owner in expected} <= set(plan["queueVerifyTasks"])


@settings(max_examples=80, deadline=None, derandomize=True)
@given(st.lists(st.sampled_from(SOURCE_CASES), min_size=1, max_size=6, unique=True))
def test_declared_source_consumers_compose_as_set_union(paths):
    expected = expected_source_consumers(paths)
    for variants in (paths, ["./" + path for path in reversed(paths)]):
        plan = convergence_plan.build_plan(changed_files=variants)
        assert set(plan["taskLocalTestConsumers"]) == expected
        assert {TASKS_BY_OWNER[owner] for owner in expected} <= set(plan["queueVerifyTasks"])
        assert plan["changedPaths"] == variants



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
