"""Malformed file locator spellings must not become native file observations."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from ordivon_data.catalog import inspect_distribution
from ordivon_data.local_files import _SCOPED_OPEN_SUPPORTED


@given(
    st.one_of(
        st.integers(0, 32).map(chr),
        st.integers(0xD800, 0xDFFF).map(chr),
        st.sampled_from(["\x7f", "%", "%x", "%GG", "?", "#"]),
    )
)
@settings(max_examples=250, derandomize=True, database=None, deadline=None)
def test_invalid_uri_lexemes_never_observe_bytes(lexeme):
    distribution = {
        "dct:identifier": "sha256:" + "0" * 64,
        "dcat:accessURL": {"@id": "file:///unused/a" + lexeme + "z"},
    }
    with patch(
        "ordivon_data.catalog.scoped_sha256", return_value=("0" * 64, "observed")
    ) as observe:
        result = inspect_distribution(distribution, (Path("/unused"),), True)
    assert result["verification"] == "UNKNOWN"
    assert "observedDigest" not in result
    observe.assert_not_called()


@given(
    st.text(alphabet="abc 数据é😀#%?+", min_size=1, max_size=12),
    st.binary(max_size=128),
    st.booleans(),
)
@settings(max_examples=80, derandomize=True, database=None, deadline=None)
def test_native_utf8_uri_readback_preserves_exact_digest(name, payload, matching):
    if not _SCOPED_OPEN_SUPPORTED:
        return
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / ("evidence-" + name)
        path.write_bytes(payload)
        actual = hashlib.sha256(payload).hexdigest()
        declared = (
            actual if matching else ("1" if actual[0] == "0" else "0") + actual[1:]
        )
        distribution = {
            "dct:identifier": "sha256:" + declared,
            "dcat:accessURL": {"@id": path.as_uri()},
        }
        result = inspect_distribution(distribution, (root,), True)
        assert result["observedDigest"] == "sha256:" + actual
        assert result["verification"] == ("VERIFIED" if matching else "FALSIFIED")
