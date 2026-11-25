"""Native Git framing and independently generated metadata admission obligations."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from ordivon_data.git_identity import qualify_batch_sizes


@pytest.mark.parametrize("algorithm", ["sha1", "sha256"])
def test_native_git_header_bytes_are_not_universal_newlines(tmp_path, algorithm):
    def git(*args, data=None):
        return subprocess.run(
            ["/usr/bin/git", "-C", str(tmp_path), *args],
            input=data,
            check=True,
            capture_output=True,
        ).stdout

    git("init", "-q", "--object-format=" + algorithm)
    payload = b"abc\n\r\x00"
    oid = git("hash-object", "-w", "--stdin", data=payload).strip()
    raw = git("cat-file", "--batch-check", data=oid + b"\n")
    expected = [(oid.decode("ascii"), "blob")]
    assert raw == oid + b" blob 6\n"
    assert qualify_batch_sizes(raw, expected, algorithm) == [(raw[:-1], 6)]
    for malformed in (
        raw.replace(b"\n", b"\r\n"),
        raw.replace(b"\n", b"\r"),
        raw.replace(b"\n", b"\0"),
        raw[:-1],
        raw + b"\n",
        raw + b"x",
        raw + raw,
    ):
        with pytest.raises(ValueError):
            qualify_batch_sizes(malformed, expected, algorithm)


@pytest.mark.parametrize("algorithm", ["sha1", "sha256"])
@given(st.lists(st.integers(1, 100), min_size=1, max_size=10, unique=True))
@settings(max_examples=100, derandomize=True, database=None, deadline=None)
def test_generated_ordered_rows_have_exact_lf_geometry(algorithm, sizes):
    width = 40 if algorithm == "sha1" else 64
    expected = [(f"{index + 1:0{width}x}", "blob") for index in range(len(sizes))]
    lines = [
        f"{oid} blob {size}".encode("ascii")
        for (oid, _), size in zip(expected, sizes, strict=True)
    ]
    raw = b"\n".join(lines) + b"\n"
    assert qualify_batch_sizes(raw, expected, algorithm) == list(
        zip(lines, sizes, strict=True)
    )

    # Exhaust the finite framing axes for every generated value vector.
    for index in range(len(lines)):
        changed = lines.copy()
        changed[index] += b"\r"
        with pytest.raises(ValueError):
            qualify_batch_sizes(b"\n".join(changed) + b"\n", expected, algorithm)

    # Exact combined budget: header + LF + payload + LF per frame.
    budget = sum(len(line) + size + 2 for line, size in zip(lines, sizes, strict=True))
    with patch("ordivon_data.git_identity._MAX_CUT_BYTES", budget):
        assert qualify_batch_sizes(raw, expected, algorithm) == list(
            zip(lines, sizes, strict=True)
        )
    with (
        patch("ordivon_data.git_identity._MAX_CUT_BYTES", budget - 1),
        pytest.raises(ValueError, match="bounded object bytes"),
    ):
        qualify_batch_sizes(raw, expected, algorithm)


def test_overlong_metadata_is_rejected_before_row_split():
    class SplitProbe(bytes):
        def split(self, *args, **kwargs):
            pytest.fail("overlong metadata must not reach row splitting")

        splitlines = split

    expected = [("a" * 40, "blob")]
    raw = SplitProbe(b"\n" * 100_000)
    with pytest.raises(ValueError, match="incomplete Git object batch"):
        qualify_batch_sizes(raw, expected, "sha1")
