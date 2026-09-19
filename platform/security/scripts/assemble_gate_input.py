#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2 import EvidenceRef, build_gate_input

PROVIDERS = (
    ("gitleaks", "sarif", "gitleaks.sarif"),
    ("semgrep", "sarif", "semgrep.sarif"),
    ("trivy", "sarif", "trivy.sarif"),
    ("syft", "cyclonedx-json", "sbom.cdx.json"),
    ("osv-scanner", "json", "osv.json"),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--subject-ref", required=True)
    parser.add_argument("--subject-revision", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/gate-input.json"))
    args = parser.parse_args()

    refs = [
        EvidenceRef.from_path(provider=provider, format=fmt, path=args.artifact_dir / filename)
        for provider, fmt, filename in PROVIDERS
    ]
    status_path = args.artifact_dir / "provider-status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    refs.append(EvidenceRef.from_path(provider="ordivon-runner", format="json", path=status_path))

    payload = build_gate_input(
        subject_ref=args.subject_ref,
        subject_revision=args.subject_revision,
        evidence=refs,
        authority="security-verification",
    )
    payload["observedSubjectRevision"] = status["observedSubjectRevision"]
    payload["providerResults"] = status["providers"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
