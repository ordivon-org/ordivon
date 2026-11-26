"""Independent properties at shared Artifact boundaries, not source-string assertions."""

import hashlib
import io
import json
import struct
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from artifact_core.file_stream import observe_stream
from artifact_core.json_validation import decode_json
from artifact_operations.receipt import ReceiptFence
from artifact_verification.claim_coverage import assess_required_statuses
from artifact_verification.native_identity import assess_native_identity
from artifact_verifiers.glb_closure import inspect_glb_stream

CI = settings(max_examples=100, derandomize=True, deadline=None)
JSON = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda child: st.lists(child, max_size=4) | st.dictionaries(st.text(), child, max_size=4),
    max_leaves=12,
)


@CI
@given(JSON)
def test_json_roundtrip_and_encoding_equivalence(value):
    assert decode_json(json.dumps(value, ensure_ascii=True)) == value
    assert decode_json(json.dumps(value, ensure_ascii=False)) == value


@CI
@given(st.text(), JSON, JSON, st.integers(0, 4))
def test_duplicate_members_rejected_at_every_depth(key, a, b, depth):
    raw = (
        "{"
        + json.dumps(key)
        + ":"
        + json.dumps(a)
        + ","
        + json.dumps(key)
        + ":"
        + json.dumps(b)
        + "}"
    )
    for _ in range(depth):
        raw = '{"nested":[' + raw + "]}"
    with pytest.raises(ValueError):
        decode_json(raw)


@CI
@given(st.sampled_from(["NaN", "Infinity", "-Infinity"]), st.integers(0, 4))
def test_non_json_numeric_constants_rejected(token, depth):
    raw = token
    for _ in range(depth):
        raw = '{"nested":[' + raw + "]}"
    with pytest.raises(ValueError):
        decode_json(raw)


@CI
@given(st.binary(max_size=4096), st.integers(1, 128))
def test_stream_copy_digest_independent_of_read_partition(data, chunk):
    class Partitioned(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, chunk))

    sink = io.BytesIO()
    digest, size = observe_stream(Partitioned(data), sink)
    assert (digest, size, sink.getvalue()) == (hashlib.sha256(data).hexdigest(), len(data), data)


@CI
@given(
    st.lists(st.sampled_from(["a", "b", "c", "d"]), max_size=8),
    st.dictionaries(
        st.sampled_from(["a", "b", "c", "d", "other"]),
        st.sampled_from(["PASS", "FAIL", "NOT_EVALUATED", "UNKNOWN"]),
    ),
    st.booleans(),
)
def test_standing_agrees_with_independent_oracle_and_permutation(required, observed, malformed):
    issues = ["unqualified"] if malformed else []
    values = [observed.get(name) for name in set(required)]
    expected = (
        "UNKNOWN"
        if malformed or not values
        else "FAIL"
        if "FAIL" in values
        else "PASS"
        if all(value == "PASS" for value in values)
        else "UNKNOWN"
    )
    first = assess_required_statuses(required, observed, issues=issues)
    second = assess_required_statuses(
        list(reversed(required)), dict(reversed(list(observed.items()))), issues=issues
    )
    assert first == second
    assert first["verificationStatus"] == expected


@CI
@given(
    st.integers(0, 100),
    st.sampled_from(["missing", "correct", "wrong", "bool", "float"]),
    st.booleans(),
)
def test_native_size_identity_strict_type_and_missing(size, mode, strict):
    native = {"profileId": "p", "artifact": {"sha256": "a" * 64}}
    if mode != "missing":
        native["artifact"]["size"] = {
            "correct": size,
            "wrong": size + 1,
            "bool": bool(size),
            "float": float(size),
        }[mode]
    result = assess_native_identity(
        native,
        profile_id="p",
        subject_sha256="a" * 64,
        subject_size=size,
        contract_sha256=None,
        require_complete=strict,
    )
    assert result["complete"] == (mode == "correct")
    assert result["rejected"] == (
        mode in ("wrong", "bool", "float") or (strict and mode == "missing")
    )


def glb(value, binary):
    raw = json.dumps(value).encode()
    raw += b" " * (-len(raw) % 4)
    body = struct.pack("<I4s", len(raw), b"JSON") + raw
    if binary:
        binary += b"\0" * (-len(binary) % 4)
        body += struct.pack("<I4s", len(binary), b"BIN\0") + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


@CI
@given(
    st.binary(max_size=256),
    st.text(max_size=20),
    st.sampled_from(["uri", "image", "texture", "extension"]),
)
def test_glb_resource_injection_cannot_pass(binary, value, attack):
    valid = {"asset": {"version": "2.0"}, "extras": {"arbitrary": value}}
    assert (
        inspect_glb_stream(io.BytesIO(glb(valid, binary)), len(glb(valid, binary)))["status"]
        == "PASS"
    )
    if attack == "uri":
        valid["buffers"] = [{"uri": value}]
    elif attack == "image":
        valid["images"] = [{"uri": value}]
    elif attack == "texture":
        valid["textures"] = [{}]
    else:
        valid["nodes"] = [{"extensions": {"unqualified": {}}}]
    blob = glb(valid, binary)
    assert inspect_glb_stream(io.BytesIO(blob), len(blob))["status"] == "FAIL"


class ReceiptModel(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.temp = tempfile.TemporaryDirectory()
        self.fence = ReceiptFence(Path(self.temp.name))
        self.expected = None
        self.calls = 0
        self.damaged = False
        self.output = None

    def produce(self, directory):
        self.calls += 1
        (directory / "result.bin").write_bytes(b"observed")
        return {"result": "result.bin"}, {}

    @rule(source=st.integers(0, 3))
    def execute(self, source):
        if self.expected is None:
            result = self.fence.run("verify", "one", {"source": source}, self.produce)
            self.expected = source
            self.output = Path(result["roles"]["result"]["path"])
            assert not result["replayed"]
        elif source != self.expected or self.damaged:
            with pytest.raises(RuntimeError):
                self.fence.run("verify", "one", {"source": source}, self.produce)
        else:
            result = self.fence.run("verify", "one", {"source": source}, self.produce)
            assert result["replayed"]

    @rule()
    def damage(self):
        if self.output is not None:
            self.output.write_bytes(b"tampered")
            self.damaged = True

    @invariant()
    def no_duplicate_effect(self):
        assert self.calls == int(self.expected is not None)

    def teardown(self):
        self.temp.cleanup()


TestReceiptModel = ReceiptModel.TestCase
TestReceiptModel.settings = settings(
    max_examples=40, stateful_step_count=15, derandomize=True, deadline=None
)


@CI
@given(st.sampled_from([(1, True), (0, False), (1, 1.0), (0, 0.0)]), st.integers(0, 4))
def test_receipt_rejects_type_distinct_inputs_even_when_python_equality_holds(pair, depth):
    a, b = pair
    for _ in range(depth):
        a, b = {"nested": [a]}, {"nested": [b]}
    with tempfile.TemporaryDirectory() as temp:
        fence = ReceiptFence(Path(temp))
        calls = 0

        def produce(directory):
            nonlocal calls
            calls += 1
            (directory / "result.bin").write_bytes(b"observed")
            return {"result": "result.bin"}, {}

        first = fence.run("verify", "typed", {"value": a}, produce)
        assert not first["replayed"]
        with pytest.raises(RuntimeError, match="different immutable inputs"):
            fence.run("verify", "typed", {"value": b}, produce)
        assert calls == 1


@CI
@given(st.sampled_from(["schemaVersion", "kind", "outputs"]))
def test_receipt_malformed_authority_never_replays(field):
    with tempfile.TemporaryDirectory() as temp:
        fence = ReceiptFence(Path(temp))

        def produce(directory):
            (directory / "result.bin").write_bytes(b"x")
            return {"result": "result.bin"}, {}

        first = fence.run("verify", "typed", {}, produce)
        receipt = Path(first["operationDirectory"]) / "activity-receipt.json"
        data = json.loads(receipt.read_text())
        if field == "schemaVersion":
            data[field] = True
        elif field == "kind":
            data[field] = "unrelated"
        else:
            data[field]["result.bin"]["size"] = True
        receipt.write_text(json.dumps(data))
        with pytest.raises(RuntimeError):
            fence.run("verify", "typed", {}, produce)
