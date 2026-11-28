"""Finite risk controls for independent native recovery oracles."""
from __future__ import annotations

import os

import pytest
from test_pgbackrest_native_retention_contract import (
    assert_expiration_plan,
    expected_witness,
    repository_identity,
)

FIRST = ("20261126-054131F", "20261126-054131F_20261126-054137I")
SECOND = (
    "20261126-054138F", "20261126-054138F_20261126-054144D",
    "20261126-054138F_20261126-054145I", "20261126-054138F_20261126-054146D",
    "20261126-054138F_20261126-054147I", "20261126-054138F_20261126-054148I",
)
LATEST = "20261126-054149F"
PREFIX = "2026-11-26 05:41:54.950 P00   INFO: [DRY-RUN] "
END = PREFIX + "expire command end: completed successfully (4ms)"


def report(groups):
    lines = []
    for group in groups:
        lines.append(PREFIX + "repo1: expire full backup set " + ", ".join(group))
    for label in reversed([label for group in groups for label in group]):
        lines.append(PREFIX + "repo1: remove expired backup " + label)
    return "\n".join([*lines, END])


def legacy_accepts(bad, good):
    # Exact prior predicates, deliberately not imported from the new oracle.
    return (SECOND[0] in bad and FIRST[0] in good and
            SECOND[0] not in "\n".join(
                line for line in good.splitlines() if "expire full backup set" in line
            ))


def altered(case):
    good = report([FIRST])
    if case == "missing-dependent":
        return report([(FIRST[0],)])
    if case == "extra-removal":
        return good + "\n" + PREFIX + "repo1: remove expired backup " + LATEST
    if case == "duplicate-removal":
        return good + "\n" + PREFIX + "repo1: remove expired backup " + FIRST[0]
    if case == "wrong-repository":
        return good.replace("repo1:", "repo2:")
    if case == "no-dry-run":
        return good.replace("[DRY-RUN] ", "")
    if case == "missing-completion":
        return good.replace(END, "")
    if case == "duplicate-completion":
        return good + "\n" + END
    if case == "unrelated-generation":
        return report([FIRST, (LATEST,)])
    if case == "diagnostic-only":
        return PREFIX + "debug mention " + FIRST[0] + "\n" + END
    if case == "wrong-group":
        return report([(FIRST[0],), (FIRST[1],)])
    raise AssertionError(case)


@pytest.mark.parametrize("case", [
    "missing-dependent", "extra-removal", "duplicate-removal",
    "wrong-repository", "no-dry-run", "missing-completion",
    "duplicate-completion", "unrelated-generation", "diagnostic-only", "wrong-group",
])
def test_named_plan_risk_obligations(case):
    bad, good = report([FIRST, SECOND]), altered(case)
    assert legacy_accepts(bad, good), "old predicate should reproduce false acceptance"
    with pytest.raises(AssertionError):
        assert_expiration_plan(good, [FIRST])


def test_native_plan_positive_and_unsafe_policy():
    assert_expiration_plan(report([FIRST]), [FIRST])
    assert_expiration_plan(report([FIRST, SECOND]), [FIRST, SECOND])
    with pytest.raises(AssertionError):
        assert_expiration_plan(report([FIRST, SECOND]), [FIRST])


def test_equal_size_mtime_does_not_prove_no_effect(tmp_path):
    p = tmp_path / "manifest"
    p.write_bytes(b"aaaa")
    before = p.stat()
    original = repository_identity(tmp_path)
    p.write_bytes(b"bbbb")
    os.utime(p, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    assert repository_identity(tmp_path) != original


@pytest.mark.parametrize("step", range(1, 10))
def test_independent_fixture_witness(step):
    expected = expected_witness(step)
    assert len(expected) == step
    assert expected[0] == {"id": 1, "body": f"revision-{step}"}
    assert [row["id"] for row in expected] == list(range(1, step + 1))
    assert all(row["body"] == f"point-{row['id']}" for row in expected[1:])
    # Identical wrong primary/restored data must not satisfy the model.
    wrong = [dict(row) for row in expected]
    wrong[0]["body"] = "incorrect"
    assert wrong != expected
