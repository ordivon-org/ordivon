#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from ordivon_security_v2.attestations import (
    reference_statement,
    sha256_file,
    subject_descriptor,
    vsa_statement,
)
from ordivon_security_v2.evidence import verified_evidence_path


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_policy_decision(gate: dict[str, object], decision: dict[str, object], policy: Path) -> None:
    """The signed-claim precursor must match a fresh native OPA evaluation."""
    executable = shutil.which("opa")
    if executable is None:
        raise RuntimeError("OPA required to verify the source policy decision")
    result = subprocess.run(
        [
            executable,
            "eval",
            "--format=raw",
            "--data",
            str(policy),
            "--stdin-input",
            "data.ordivon.security.v2.decision",
        ],
        input=json.dumps(gate, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"OPA decision evaluation failed: {result.stderr.strip()}")
    try:
        evaluated = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OPA did not return a valid decision") from exc
    if not isinstance(evaluated, dict) or evaluated != decision:
        raise ValueError("provided decision does not match current policy on bound gate input")


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
    if not isinstance(gate, dict) or not isinstance(decision, dict):
        raise ValueError("gate and decision must be JSON objects")
    subject = subject_descriptor(name=args.subject_name, git_commit=gate["subjectRevision"])

    # Validate ALL sources before emitting any artifact; never reuse a prior
    # admission decision for a changed report or provider receipt.
    refs = gate.get("evidenceRefs")
    if not isinstance(refs, list):
        raise ValueError("gate evidenceRefs must be an array")
    verified = [(ref, verified_evidence_path(ref)) for ref in refs]
    runner = [(ref, path) for ref, path in verified if ref["provider"] == "ordivon-runner"]
    if len(runner) != 1:
        raise ValueError("exactly one bound provider-status receipt is required")
    provider_status = json.loads(runner[0][1].read_text(encoding="utf-8"))
    if provider_status.get("observedSubjectRevision") != gate.get("observedSubjectRevision"):
        raise ValueError("provider receipt subject revision changed")
    if provider_status.get("providers") != gate.get("providerResults"):
        raise ValueError("provider receipt and gate results differ")
    verify_policy_decision(gate, decision, args.policy)

    reference_descriptors: list[dict[str, object]] = []
    for index, (evidence, evidence_path) in enumerate(verified):
        statement = reference_statement(
            subject=subject,
            attester_id="https://ordivon.local/security-v2/evidence-binder",
            reference_path=evidence_path,
        )
        actual_digest = statement["predicate"]["references"][0]["digest"]["sha256"]
        if "sha256:" + actual_digest != evidence["sha256"]:
            raise ValueError(f"evidence changed during reference emission: {evidence['provider']}")
        ref_path = args.output_dir / f"input-{index:02d}-{evidence['provider']}.reference.intoto.json"
        write_json(ref_path, statement)
        reference_descriptors.append(
            {
                "uri": ref_path.resolve().as_uri(),
                "digest": {"sha256": sha256_file(ref_path)},
            }
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
