from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def build_publication_carrier_attestation(
    *,
    carrier_sha256: str,
    venue_contract_sha256: str,
    evidence: dict[str, str],
    release_standing: str,
    page_coverage: tuple[int, int],
    figure_coverage: tuple[int, int],
    table_coverage: tuple[int, int],
) -> dict[str, Any]:
    for label, value in {
        "carrierSha256": carrier_sha256,
        "venueContractSha256": venue_contract_sha256,
        **evidence,
    }.items():
        if not _SHA.fullmatch(value):
            raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    for reviewed, expected, label in (
        (*page_coverage, "pages"),
        (*figure_coverage, "figures"),
        (*table_coverage, "tables"),
    ):
        if reviewed < 0 or expected < 0 or reviewed > expected:
            raise ValueError(f"invalid {label} coverage")
    if release_standing != "PASS":
        raise ValueError("carrier attestation may only be emitted for release standing PASS")

    return {
        "schemaVersion": 1,
        "kind": "publication-carrier-attestation",
        "truthRole": "carrier-conformance-attestation-not-scientific-truth",
        "carrierSha256": carrier_sha256,
        "venueContractSha256": venue_contract_sha256,
        "evidence": dict(sorted(evidence.items())),
        "coverage": {
            "pages": {"reviewed": page_coverage[0], "expected": page_coverage[1]},
            "figures": {"reviewed": figure_coverage[0], "expected": figure_coverage[1]},
            "tables": {"reviewed": table_coverage[0], "expected": table_coverage[1]},
        },
        "releaseStanding": release_standing,
        "standing": "PASS_PUBLICATION_CARRIER_ATTESTATION",
        "nonClaims": [
            "this attestation does not establish scientific correctness",
            "this attestation does not authorize venue submission",
            "this attestation does not replace human authorship or legal declarations",
        ],
    }
