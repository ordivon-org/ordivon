#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

STUDY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY_ROOT))

from dwc_dw12.frozen_evaluation import (
    build_evaluator_packet,
    freeze_subject,
    mechanical_prequalification_r2,
    protocol_r2,
)


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate-revision",
        help="Exact already-frozen candidate revision. Defaults to current workspace HEAD.",
    )
    parser.add_argument(
        "--candidate-builder-actor-ref",
        default="agent:chatgpt-daybreak-r21-20261001",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[4]
    study = repo / "studies/security/dwc-r21-dw12-qualification"
    out = study / "evidence/acceptance"
    out.mkdir(parents=True, exist_ok=True)

    current_head = git_head(repo)
    candidate_revision = args.candidate_revision or current_head

    subject = freeze_subject(repo, candidate_revision)
    proto = protocol_r2(subject)
    prequalification = mechanical_prequalification_r2(repo, subject, proto)

    implementation_path = study / "dwc_dw12/frozen_evaluation.py"
    qualification_path = study / "dwc_dw12/qualification.py"
    runner_path = Path(__file__).resolve()
    packet = build_evaluator_packet(
        subject=subject,
        proto=proto,
        prequalification=prequalification,
        evaluator_implementation_digest=sha(implementation_path),
        runner_digest=sha(runner_path),
        qualification_digest=sha(qualification_path),
        candidate_builder_actor_ref=args.candidate_builder_actor_ref,
    )

    files = {
        "dw12-frozen-subject-r2.json": subject,
        "dw12-protocol-r2.json": proto,
        "dw12-mechanical-prequalification-r2.json": prequalification,
        "dw12-independent-evaluator-packet-r2.json": packet,
    }
    for name, value in files.items():
        (out / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "candidateRevision": candidate_revision,
                "subjectDigest": subject["subjectDigest"],
                "protocolDigest": proto["protocolDigest"],
                "mechanicalResultDigest": prequalification["resultDigest"],
                "packetDigest": packet["packetDigest"],
                "moduleAcceptanceCount": prequalification["evidenceCoverage"][
                    "moduleAcceptanceCount"
                ],
                "caseEvidenceCount": prequalification["evidenceCoverage"][
                    "caseEvidenceCount"
                ],
                "mechanicalStanding": prequalification["mechanicalStanding"],
                "overallStanding": prequalification["overallStanding"],
                "baselineCandidateTrialStanding": prequalification[
                    "baselineCandidateTrials"
                ]["standing"],
                "independentAcceptance": prequalification["independentAcceptance"][
                    "standing"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
