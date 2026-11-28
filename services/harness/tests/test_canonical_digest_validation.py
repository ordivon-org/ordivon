"""Canonical digest syntax is independent of the calling domain."""
import pytest

from anc_canonical import validate_digest


@pytest.mark.parametrize("value", ["sha256:" + "0" * 64, "sha256:" + "abcdef01" * 8])
def test_canonical_digest_preserves_exact_identity(value):
    assert validate_digest(value) == value
    assert validate_digest(value, "consumer digest") == value


@pytest.mark.parametrize("value", [
    None, 123, True, b"sha256:" + b"a" * 64,
    "", "sha256:" + "a" * 63, "sha256:" + "a" * 65,
    "SHA256:" + "a" * 64, "sha256:" + "A" * 64,
    "sha256:" + "g" * 64, "sha256:" + "a" * 63 + "０",
    "sha256:" + "a" * 64 + "\n", " sha256:" + "a" * 64,
])
def test_canonical_digest_preserves_caller_diagnostic_and_strict_syntax(value):
    for label in ("digest", "consumer digest"):
        with pytest.raises(ValueError) as error:
            validate_digest(value, label)
        assert str(error.value) == f"{label} must be sha256:<64 lowercase hex>"
    with pytest.raises(ValueError) as error:
        validate_digest(value)
    assert str(error.value) == "digest must be sha256:<64 lowercase hex>"
