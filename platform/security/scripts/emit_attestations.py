#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.attestations import (
    reference_statement,
    sha256_file,
    subject_descriptor,
    vsa_statement,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-input", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--subject-name", required=True)
    parser.add_argument("--verifier-revision", required=True)
    parser.add_argument("--policy", type=Path, default=Path("policies/admission.rego"))
    args = parser.parse_args()

    gate = json.loads(args.gate_input.read_text(encoding="utf-8"))
    decision = json.loads(args.decision.read_text(encoding="utf-8"))
    subject = subject_descriptor(name=args.subject_name, git_commit=gate["subjectRevision"])

    reference_descriptors: list[dict[str, object]] = []
    for index, evidence in enumerate(gate["evidenceRefs"]):
        evidence_path = Path(evidence["path"])
        statement = reference_statement(
            subject=subject,
            attester_id="https://ordivon.local/security-v2/evidence-binder",
            reference_path=evidence_path,
        )
        ref_path = args.output_dir / f"input-{index:02d}-{evidence['provider']}.reference.intoto.json"
        write_json(ref_path, statement)
        reference_descriptors.append(
            {
                "uri": ref_path.resolve().as_uri(),
                "digest": {"sha256": sha256_file(ref_path)},
            }
        )

    provider_status = json.loads(
        (args.gate_input.parent / "provider-status.json").read_text(encoding="utf-8")
    )
    versions = {
        "ordivon-security-v2": args.verifier_revision,
        "profile": provider_status.get("profile", "default"),
    }
    if provider_status.get("gitleaksConfigSha256"):
        versions["gitleaks-config"] = provider_status["gitleaksConfigSha256"]

    vsa = vsa_statement(
        subject=subject,
        verifier_id="https://ordivon.local/security-v2",
        verifier_versions=versions,
        resource_uri=f"git+file://{args.subject_name}@{gate['subjectRevision']}",
        policy_uri=args.policy.resolve().as_uri(),
        policy_sha256=sha256_file(args.policy),
        input_attestations=reference_descriptors,
        passed=decision.get("standing") == "CURRENT" and decision.get("allow") is True,
    )
    write_json(args.output_dir / "verification-summary.vsa.intoto.json", vsa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
