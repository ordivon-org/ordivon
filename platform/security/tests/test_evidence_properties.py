"""Independent property oracles for opaque byte identity and public JSON comparison."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ordivon_security_v2.browser_security_observation import (
    _changed_json_paths,
    classify_browser_security_observation_validity,
)
from ordivon_security_v2.evidence import EvidenceRef

# Bounded synthetic payloads only; no production records, providers or credentials.
JSON = st.recursive(
    st.none() | st.booleans() | st.integers(-1000, 1000) | st.text(max_size=20),
    lambda child: (
        st.lists(child, max_size=4)
        | st.dictionaries(st.text(alphabet="abcxyz", min_size=1, max_size=4), child, max_size=4)
    ),
    max_leaves=20,
)


@settings(max_examples=100, derandomize=True, deadline=None, database=None)
@given(JSON, JSON)
def check_public_json_diff_is_symmetric_and_reflexive(left, right) -> None:
    assert _changed_json_paths(left, left) == []
    assert _changed_json_paths(left, right) == _changed_json_paths(right, left)


@settings(max_examples=60, derandomize=True, deadline=None, database=None)
@given(JSON)
def check_public_json_diff_is_local_to_one_named_child(value) -> None:
    assert _changed_json_paths({"stable": value}, {"stable": value, "added": None}) == [
        "$.added"
    ]


@settings(max_examples=100, derandomize=True, deadline=None, database=None)
@given(
    st.lists(
        st.text(alphabet="abcxyz", min_size=1, max_size=4)
        | st.integers(min_value=0, max_value=3),
        max_size=5,
    ),
    st.sampled_from([(0, 1), (False, 0), ("", "x"), ([], [None]), ({}, [])]),
)
@example(["a", 2], (False, 0))
@example([0, "z"], ([], [None]))
def check_public_json_diff_has_exact_constructed_path(context, leaf_pair) -> None:
    # Construct one known changed leaf, with unchanged siblings. The expected
    # path follows the generated coordinates rather than a second tree diff.
    left, right = leaf_pair
    expected = "$" + "".join(
        f"[{step}]" if isinstance(step, int) else f".{step}" for step in context
    )
    for step in reversed(context):
        if isinstance(step, int):
            left = [None] * step + [left, None]
            right = [None] * step + [right, None]
        else:
            left = {"stable": 7, step: left}
            right = {"stable": 7, step: right}
    assert _changed_json_paths(left, right) == [expected]
    assert _changed_json_paths(right, left) == [expected]


def check_public_json_diff_order_and_multiple_changes() -> None:
    left = {"z": [0, 1], "a": {"x": 0}, "m": 0}
    right = {"m": 0, "a": {"x": 1}, "z": [2, 3]}
    assert _changed_json_paths(left, right) == ["$.a.x", "$.z[0]", "$.z[1]"]
    assert _changed_json_paths([0], [0], "$.prefix") == []
    assert _changed_json_paths([0], [1], "$.prefix") == ["$.prefix[0]"]


class EvidenceProperties(unittest.TestCase):
    @settings(max_examples=80, derandomize=True, deadline=None, database=None)
    @given(st.binary(max_size=4096))
    @example(b"\x00\xff")
    @example(bytes(range(256)) * 1025)
    def test_exact_digest_and_length(self, raw: bytes) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "opaque"
            path.write_bytes(raw)
            ref = EvidenceRef.from_path(provider="fixture", format="opaque", path=path)
            self.assertEqual(ref.byte_length, len(raw))
            self.assertEqual(ref.sha256, "sha256:" + hashlib.sha256(raw).hexdigest())

    # The Hypothesis functions have no instance-specific executor. Both
    # unittest and native mutation-test repetitions consume the same oracle.
    def test_public_json_diff_is_symmetric_and_reflexive(self) -> None:
        check_public_json_diff_is_symmetric_and_reflexive()

    def test_public_json_diff_is_local_to_one_named_child(self) -> None:
        check_public_json_diff_is_local_to_one_named_child()

    def test_public_json_diff_has_exact_constructed_path(self) -> None:
        check_public_json_diff_has_exact_constructed_path()

    def test_public_json_diff_order_and_multiple_changes(self) -> None:
        check_public_json_diff_order_and_multiple_changes()

    @settings(max_examples=60, derandomize=True, deadline=None, database=None)
    @given(st.lists(st.sampled_from([" unavailable ", "error", "FAILED", "ok"]), max_size=12))
    def test_observer_classification_preserves_failure_precedence(self, values) -> None:
        observed = classify_browser_security_observation_validity(
            {"children": [{"standing": v} for v in values]}
        )
        normalized = [v.strip().upper() for v in values]
        expected = (
            "DETECTOR_FAILED"
            if set(normalized) & {"ERROR", "FAILED"}
            else "OBSERVER_UNAVAILABLE"
            if "UNAVAILABLE" in normalized
            else "VALID"
        )
        self.assertEqual(observed["standing"], expected)
        self.assertEqual(
            [entry["path"] for entry in observed["issues"]],
            [f"$.children[{i}]" for i, v in enumerate(normalized) if v != "OK"],
        )


class OpaqueFileMachine(RuleBasedStateMachine):
    """Small append/replace/truncate model for the counted-stream operator."""

    def __init__(self) -> None:
        super().__init__()
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "fixture"
        self.path.write_bytes(b"")
        self.expected = b""

    @rule(raw=st.binary(max_size=256))
    def replace(self, raw: bytes) -> None:
        self.path.write_bytes(raw)
        self.expected = raw

    @rule(raw=st.binary(max_size=256))
    def append(self, raw: bytes) -> None:
        with self.path.open("ab") as stream:
            stream.write(raw)
        self.expected += raw

    @rule(size=st.integers(min_value=0, max_value=512))
    def truncate(self, size: int) -> None:
        with self.path.open("r+b") as stream:
            stream.truncate(size)
        self.expected = self.expected[:size].ljust(size, b"\x00")

    @invariant()
    def identity_agrees_with_model(self) -> None:
        ref = EvidenceRef.from_path(provider="fixture", format="opaque", path=self.path)
        assert ref.byte_length == len(self.expected)
        assert ref.sha256 == "sha256:" + hashlib.sha256(self.expected).hexdigest()

    def teardown(self) -> None:
        self.directory.cleanup()


TestOpaqueFileMachine = OpaqueFileMachine.TestCase
TestOpaqueFileMachine.settings = settings(
    max_examples=25,
    stateful_step_count=12,
    derandomize=True,
    deadline=None,
    database=None,
)
