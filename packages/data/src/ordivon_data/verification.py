"""Pure digest-evidence classification. No filesystem, network or authority effects.

CrossHair PEP-316 postconditions encode the observable three-way verdict.
The symbolic analyzer checks reachable Python paths within its time budget;
its success is *not* a machine-checked proof of the implementation.
"""

from __future__ import annotations

from typing import TypeGuard

SPDX_SHA256_ALGORITHM = "http://spdx.org/rdf/terms#checksumAlgorithm_sha256"


def is_sha256_hexdigest(value: object) -> TypeGuard[str]:
    """The lowercase, unprefixed SHA-256 representation in local evidence."""
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def digest_verdict(declared: str | None, observed: str | None) -> str:
    """
    post: __return__ in ("UNKNOWN", "VERIFIED", "FALSIFIED")
    post: (__return__ == "UNKNOWN") == (declared is None or observed is None)
    post: (__return__ == "VERIFIED") == (declared is not None and observed is not None and declared == observed)
    post: (__return__ == "FALSIFIED") == (declared is not None and observed is not None and declared != observed)
    """
    if declared is None or observed is None:
        return "UNKNOWN"
    return "VERIFIED" if declared == observed else "FALSIFIED"
