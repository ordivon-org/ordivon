from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    provider: str
    format: str
    path: str
    sha256: str
    byte_length: int

    @classmethod
    def from_path(cls, *, provider: str, format: str, path: Path) -> EvidenceRef:
        data = path.read_bytes()
        return cls(
            provider=provider,
            format=format,
            path=str(path),
            sha256="sha256:" + sha256(data).hexdigest(),
            byte_length=len(data),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def verified_evidence_path(record: dict[str, object]) -> Path:
    """Read current bytes and require they match the immutable gate reference.

    This does not authenticate the provider or establish file path authority.
    The caller must use a trusted local evidence directory and source.
    """
    if not isinstance(record, dict) or set(record) != {
        "provider", "format", "path", "sha256", "byte_length"
    }:
        raise ValueError("invalid evidence reference fields")
    provider, format_name, path_value = (
        record["provider"], record["format"], record["path"]
    )
    length = record["byte_length"]
    if not all(isinstance(value, str) and value for value in (
        provider, format_name, path_value, record["sha256"]
    )):
        raise ValueError("evidence reference strings must be nonempty")
    if type(length) is not int or length <= 0:
        raise ValueError("evidence reference length must be positive integer")
    path = Path(path_value)
    observed = EvidenceRef.from_path(provider=provider, format=format_name, path=path)
    if observed.sha256 != record["sha256"] or observed.byte_length != length:
        raise ValueError(f"evidence bytes changed after gate binding: {provider}")
    return path


def build_gate_input(
    *,
    subject_ref: str,
    subject_revision: str,
    evidence: Iterable[EvidenceRef],
    authority: str,
) -> dict[str, object]:
    refs = [item.to_dict() for item in evidence]
    if not subject_ref or not subject_revision or not authority:
        raise ValueError("subject_ref, subject_revision, and authority are required")
    if not refs:
        raise ValueError("at least one evidence reference is required")
    return {
        "schemaVersion": 1,
        "subjectRef": subject_ref,
        "subjectRevision": subject_revision,
        "authority": authority,
        "evidenceRefs": refs,
    }
