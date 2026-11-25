"""Optional local distribution evidence bound to producer ODPS customProperties.

An operator selects the exact product/port, source path property, digest property,
and owner root. The owner document supplies values; no path, digest, or license
is guessed. This is a current local file read, not a persistent product registry.
"""

from __future__ import annotations

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


def qualified_local_distribution(
    product: dict[str, Any],
    projected: dict[str, Any],
    binding: LocalEvidenceBinding,
    *,
    port_index: int,
) -> None:
    """Mutate an in-memory DCAT port after qualified local-byte observation.

    Correctness boundary: exact bytes at the open handle were hashed against
    producer metadata. A future consumer must recheck the file; this does NOT
    assert that the pathname remains immutable, or that data rights are granted.
    """
    # Selection is already qualified by the pure binding planner.
    distribution = projected["dcat:distribution"][port_index]
    if "dcat:accessURL" in distribution or "spdx:checksum" in distribution:
        raise ValueError("duplicate local evidence binding for output port")
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
    relative = Path(declared_path)
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or "\\" in declared_path
    ):
        raise ValueError("producer relative path must not escape owner root")
    root = binding.owner_root.absolute()
    actual_path = root / relative
    actual_digest, reason = scoped_sha256(actual_path, (root,), hash_bytes=True)
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
    if actual_digest != declared_digest:
        raise ValueError("producer file digest differs from ODPS declaration")

    distribution["dcat:accessURL"] = {"@id": actual_path.as_uri()}
    # DCAT 3 uses SPDX checksums, keeping the producer's port identifier
    # (dct:identifier) separate from content-integrity evidence.
    distribution["spdx:checksum"] = {
        "@type": "spdx:Checksum",
        "spdx:algorithm": {"@id": "http://spdx.org/rdf/terms#checksumAlgorithm_sha256"},
        "spdx:checksumValue": {"@value": declared_digest, "@type": "xsd:hexBinary"},
    }
