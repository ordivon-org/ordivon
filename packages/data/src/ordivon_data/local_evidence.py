"""Optional local distribution evidence bound to producer ODPS customProperties.

An operator selects the exact product/port, source path property, digest property,
and owner root. The owner document supplies values; no path, digest, or license
is guessed. This is a current local file read, not a persistent product registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .local_files import scoped_sha256
from .verification import SPDX_SHA256_ALGORITHM, is_sha256_hexdigest

_FILE_PORT_MEDIA_TYPES = {
    "file/json": "application/json",
    "file/parquet": "application/vnd.apache.parquet",
    "file/csv": "text/csv",
}


def file_port_media_type(port_type: object) -> str | None:
    """Project the file-port types supported by local evidence binding."""
    return _FILE_PORT_MEDIA_TYPES.get(port_type) if isinstance(port_type, str) else None


@dataclass(frozen=True)
class LocalEvidenceBinding:
    product_id: str
    port_name: str
    path_property: str
    digest_property: str
    owner_root: Path
    # Optional because Bitol ODPS 1.1 permits unversioned ports. None
    # preserves the legacy behavior: require a unique port name.
    port_version: str | None = None


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
) -> None:
    """Mutate an in-memory DCAT port after qualified local-byte observation.

    Correctness boundary: exact bytes at the open handle were hashed against
    producer metadata. A future consumer must recheck the file; this does NOT
    assert that the pathname remains immutable, or that data rights are granted.
    """
    if binding.product_id != product["id"]:
        raise ValueError("binding refers to another owner product")
    ports = product["outputPorts"]
    if binding.port_version is not None and (
        not isinstance(binding.port_version, str) or not binding.port_version.strip()
    ):
        raise ValueError("binding port version must be a nonempty string")
    selected = [
        i
        for i, port in enumerate(ports)
        if port.get("name") == binding.port_name
        and (
            binding.port_version is None or port.get("version") == binding.port_version
        )
    ]
    if len(selected) != 1:
        if binding.port_version is not None:
            raise ValueError(
                "binding requires exactly one named output port at requested version"
            )
        raise ValueError("binding requires exactly one named output port")
    index = selected[0]
    # The selected distribution is already identified by ODPS (name, version).
    # Reuse it as the one binding authority; name-only de-duplication would
    # incorrectly block independent consumers of coexisting port versions.
    distribution = projected["dcat:distribution"][index]
    if "dcat:accessURL" in distribution or "spdx:checksum" in distribution:
        raise ValueError("duplicate local evidence binding for output port")
    if file_port_media_type(ports[index].get("type")) is None:
        raise ValueError("binding requires a supported file output port")
    props = product.get("customProperties", [])
    if not isinstance(props, list):
        raise TypeError("ODPS customProperties must be a list")
    declared_path = _property(props, binding.path_property)
    declared_digest = _property(props, binding.digest_property)
    if not is_sha256_hexdigest(declared_digest):
        raise ValueError("producer digest must be lowercase 64-digit SHA-256")

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
        "spdx:algorithm": {"@id": SPDX_SHA256_ALGORITHM},
        "spdx:checksumValue": {"@value": declared_digest, "@type": "xsd:hexBinary"},
    }
