"""Production output byte observation, shared by validation and context.

This module selects a declared carrier, then observes bytes without granting
editorial, publication, artifact or cache authority. Consumers own their policy.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .assets import UnstableBlobError, hash_file
from .production_source_io import canonical_relative_file_path, relative_child

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def declared_source_files(sources: dict[str, Any]) -> set[str]:
    """Exact source-carrier allowlist from the Production's own descriptor."""
    paths: set[str] = set()
    for value in sources.values():
        if isinstance(value, str):
            paths.add(value)
        elif isinstance(value, list):
            paths.update(item for item in value if isinstance(item, str))
    return paths


def observe_output_blob(
    root: Path,
    output: dict[str, Any],
    *,
    declared_source_files: set[str],
    selected_file: Path | None,
) -> dict[str, Any]:
    """One bounded, read-only byte comparison, not approval or publication.

    A sourceCarrier is an exact-byte source assertion; outputCarrier names
    one owner-declared local materialization of a transformed Output.
    Neither a local path nor an explicit consumer-selected file proves
    ongoing availability, domain acceptance, or publication.
    """
    expected = output.get("blobDigest")
    carrier = output.get("sourceCarrier")
    output_carrier = output.get("outputCarrier")
    row: dict[str, Any] = {
        "outputId": output.get("id"),
        "declaredStatus": output.get("status"),
        "expectedBlobDigest": expected,
        "sourceCarrier": carrier,
        "outputCarrier": output_carrier,
        "sourceSelection": None,
        "relation": "UNKNOWN_NO_SELECTED_BYTES",
        "observedBlob": None,
    }
    selected: Path | None = None
    if carrier is not None and output_carrier is not None:
        row["relation"] = "INVALID_MULTIPLE_CARRIERS"
        return row
    if carrier is not None:
        if not isinstance(carrier, str) or carrier not in declared_source_files:
            row["relation"] = "INVALID_UNDECLARED_SOURCE_CARRIER"
            return row
        if not canonical_relative_file_path(carrier):
            row["relation"] = "INVALID_SOURCE_CARRIER_PATH"
            return row
        try:
            selected = relative_child(root, carrier)
        except ValueError:
            row["relation"] = "INVALID_ESCAPING_SOURCE_CARRIER"
            return row
        row["sourceSelection"] = "declared-exact-source-carrier"
    elif output_carrier is not None:
        if not canonical_relative_file_path(output_carrier):
            row["relation"] = "INVALID_OUTPUT_CARRIER"
            return row
        try:
            selected = relative_child(root, output_carrier)
        except ValueError:
            row["relation"] = "INVALID_ESCAPING_OUTPUT_CARRIER"
            return row
        row["sourceSelection"] = "declared-local-output-carrier"
    if selected_file is not None:
        row["sourceSelection"] = "explicit-consumer-file"
        selected = selected_file
    if selected is None:
        return row
    row["selectedPath"] = str(selected.resolve())
    if not isinstance(expected, str) or _SHA256.fullmatch(expected) is None:
        row["relation"] = "UNKNOWN_NO_VALID_DECLARED_DIGEST"
        return row
    try:
        blob = hash_file(selected)
    except UnstableBlobError:
        row["relation"] = "UNKNOWN_SELECTED_FILE_UNSTABLE"
        return row
    except (OSError, ValueError):
        row["relation"] = "UNKNOWN_SELECTED_FILE_UNAVAILABLE"
        return row
    row["observedBlob"] = blob.as_dict()
    row["relation"] = (
        "MATCHES_DECLARED_DIGEST"
        if blob.digest == expected
        else "DIFFERS_FROM_DECLARED_DIGEST"
    )
    return row
