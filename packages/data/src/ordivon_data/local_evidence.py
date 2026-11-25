"""Optional local distribution evidence bound to producer ODPS customProperties.

An operator selects the exact product/port, source path property, digest property,
and owner root. The owner document supplies values; no path, digest, or license
is guessed. This is a current local file read, not a persistent product registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .binding_selection import LocalEvidenceBinding
from .local_files import scoped_sha256
from .metadata_json import contains_surrogate


def _property(props: list[Any], key: str) -> str:
    matches = [
        entry.get("value")
        for entry in props
        if isinstance(entry, dict) and entry.get("property") == key
    ]
    if len(matches) != 1 or not isinstance(matches[0], str) or not matches[0]:
        raise ValueError(f"missing or ambiguous producer property: {key}")
    return matches[0]


@dataclass(frozen=True)
class PreparedLocalEvidence:
    """Qualified metadata, not an assertion that a file exists or is verified."""

    root: Path
    path: Path
    digest: str
    uri: str


def prepare_local_evidence(
    product: dict[str, Any], binding: LocalEvidenceBinding
) -> PreparedLocalEvidence:
    """Resolve declared evidence coordinates without opening a bound file."""
    props = product.get("customProperties", [])
    if not isinstance(props, list):
        raise TypeError("ODPS customProperties must be a list")
    declared_path = _property(props, binding.path_property)
    declared_digest = _property(props, binding.digest_property)
    if len(declared_digest) != 64 or any(
        ch not in "0123456789abcdef" for ch in declared_digest
    ):
        raise ValueError("producer digest must be lowercase 64-digit SHA-256")

    if contains_surrogate(declared_path):
        raise ValueError("producer relative path contains a non-Unicode scalar")
    if "\x00" in declared_path:
        raise ValueError("producer relative path contains NUL")
    relative = Path(declared_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or "\\" in declared_path
    ):
        raise ValueError("producer relative path must not escape owner root")
    root = binding.owner_root.absolute()
    if ".." in root.parts or "\x00" in str(root) or contains_surrogate(str(root)):
        raise ValueError("producer owner root has unsupported scoped path")
    actual_path = root / relative
    return PreparedLocalEvidence(
        root, actual_path, declared_digest, actual_path.as_uri()
    )


def observe_local_evidence(prepared: PreparedLocalEvidence) -> dict[str, Any]:
    """Observe current native bytes and return only a qualified DCAT evidence patch.

    A future consumer must recheck the file. This does not assert immutable
    pathnames, atomic multi-file observation, or a grant of data rights.
    """
    actual_digest, reason = scoped_sha256(
        prepared.path, (prepared.root,), hash_bytes=True
    )
    if actual_digest is None:
        # Producer binding is strict admission, not a discovery verdict.
        # Preserve existing consumer I/O failure semantics without reopening.
        message = f"producer file not verifiable under owner root: {reason}"
        if reason == "local_file_unavailable":
            raise FileNotFoundError(message)
        if reason == "local_file_unreadable":
            raise PermissionError(message)
        if reason == "local_file_read_error":
            raise OSError(message)
        raise ValueError(message)
    if actual_digest != prepared.digest:
        raise ValueError("producer file digest differs from ODPS declaration")

    # Keep content-integrity evidence separate from the producer's port ID.
    return {
        "dcat:accessURL": {"@id": prepared.uri},
        "spdx:checksum": {
            "@type": "spdx:Checksum",
            "spdx:algorithm": {
                "@id": "http://spdx.org/rdf/terms#checksumAlgorithm_sha256"
            },
            "spdx:checksumValue": {"@value": prepared.digest, "@type": "xsd:hexBinary"},
        },
    }
