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
