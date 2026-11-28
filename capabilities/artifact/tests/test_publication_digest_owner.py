from __future__ import annotations

from pathlib import Path

from artifact_capabilities.publication import attestation


def test_publication_attestation_digest_delegates_to_canonical_core(monkeypatch) -> None:
    path = Path("carrier.pdf")
    raw_digest = "ab" * 32
    calls: list[Path] = []

    def fake_raw_sha256_file(candidate: Path) -> str:
        calls.append(candidate)
        return raw_digest

    monkeypatch.setattr(attestation, "_raw_sha256_file", fake_raw_sha256_file)

    assert attestation.sha256_file(path) == "sha256:" + raw_digest
    assert calls == [path]
