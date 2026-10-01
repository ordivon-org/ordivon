#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from dwc_dw12.qualification import evaluate, freeze_corpus, protocol


def main() -> int:
    repo = Path(__file__).resolve().parents[4]
    out = repo / "studies/security/dwc-r21-dw12-qualification/evidence/acceptance"
    out.mkdir(parents=True, exist_ok=True)

    corpus = freeze_corpus(repo)
    proto = protocol(corpus["corpusDigest"])
    result = evaluate(repo, corpus, proto)

    (out / "dw12-frozen-corpus-r1.json").write_text(
        json.dumps(corpus, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "dw12-protocol-r1.json").write_text(
        json.dumps(proto, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "dw12-mechanical-qualification-r1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "corpusDigest": corpus["corpusDigest"],
                "protocolDigest": proto["protocolDigest"],
                "resultDigest": result["resultDigest"],
                "mechanicalStanding": result["mechanicalStanding"],
                "overallStanding": result["overallStanding"],
                "violations": result["violations"],
                "caseCount": result["evidenceCoverage"]["caseCount"],
                "frozenArtifactCount": result["evidenceCoverage"]["frozenArtifactCount"],
                "dw10AblationDeltaUnits": result["ablations"]["DW10"][
                    "syntheticQualificationCostUnitsDelta"
                ],
                "independentAcceptance": result["independentAcceptance"]["standing"],
                "dw10SharedPromotion": result["sharedPromotion"]["standing"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
