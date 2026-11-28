"""Generated native protocol framing cases, independent of the frame decoder."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from ordivon_data.git_identity import qualify_batch_sizes, verify_object_batch


@given(
    st.sampled_from(["sha1", "sha256"]),
    st.lists(st.binary(min_size=1, max_size=80), min_size=1, max_size=8, unique=True),
    st.data(),
)
@settings(max_examples=120, derandomize=True, database=None, deadline=None)
def test_exact_binary_blob_frames_or_reject_changed_payload(algorithm, payloads, data):
    def encode(kind, payload):
        canonical = f"{kind} {len(payload)}".encode()
        oid = hashlib.new(algorithm, canonical + b"\0" + payload).hexdigest()
        header = oid.encode() + b" " + canonical + b"\n"
        return oid, kind, header, payload

    tree = encode("tree", b"")
    commit = encode("commit", b"tree " + tree[0].encode() + b"\n\nfixture\n")
    frames = [commit, tree] + [encode("blob", p) for p in payloads]
    checks = b"".join(frame[2] for frame in frames)
    expected = [(frame[0], frame[1]) for frame in frames]
    plan = qualify_batch_sizes(checks, expected, algorithm)
    raw = b"".join(header + payload + b"\n" for _, _, header, payload in frames)
    observed = verify_object_batch(
        raw, plan, algorithm, commit=commit[0], root_tree=tree[0]
    )
    assert observed == {f[0]: f[3] for f in frames[2:]}

    index = data.draw(st.integers(min_value=2, max_value=len(frames) - 1))
    start = sum(len(f[2]) + len(f[3]) + 1 for f in frames[:index]) + len(
        frames[index][2]
    )
    pos = start + data.draw(
        st.integers(min_value=0, max_value=len(frames[index][3]) - 1)
    )
    altered = raw[:pos] + bytes([raw[pos] ^ 1]) + raw[pos + 1 :]
    with pytest.raises(ValueError, match="ODPS blob identity mismatch"):
        verify_object_batch(
            altered, plan, algorithm, commit=commit[0], root_tree=tree[0]
        )
