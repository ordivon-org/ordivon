from __future__ import annotations

import argparse
import collections
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
EVIDENCE_DIR = HERE.parent / "evidence" / "20260928-r1"


def load_runner():
    path = HERE.with_name("run_factorial_pilot_r1.py")
    spec = importlib.util.spec_from_file_location("pilot_r1_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen R1 runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_trials(evidence_dir: Path) -> list[dict[str, Any]]:
    files = sorted((evidence_dir / "trials").glob("trial-*.json"))
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    if len(rows) != 12:
        raise RuntimeError(f"expected 12 frozen R1 trials, found {len(rows)}")
    return rows


def provider_calls(row: dict[str, Any]) -> list[dict[str, Any]]:
    usage = row.get("result", {}).get("usage")
    if not isinstance(usage, dict):
        raise RuntimeError(f"trial lacks usage map: {row.get('trialId')}")
    calls = usage.get("providerUsage")
    if not isinstance(calls, list) or not calls:
        raise RuntimeError(f"trial lacks Provider call evidence: {row.get('trialId')}")
    return [call for call in calls if isinstance(call, dict)]


def build_qualification(evidence_dir: Path) -> dict[str, Any]:
    pilot = load_runner()
    rows = load_trials(evidence_dir)
    result_set = json.loads((evidence_dir / "results.json").read_text(encoding="utf-8"))
    analysis = json.loads((evidence_dir / "analysis.json").read_text(encoding="utf-8"))
    acceptance = json.loads((evidence_dir / "acceptance.json").read_text(encoding="utf-8"))

    requested_levels = sorted({str(row["model"]) for row in rows})
    if requested_levels != ["deepseek-flash", "deepseek-v4-flash"]:
        raise RuntimeError(f"unexpected frozen requested model levels: {requested_levels}")

    by_requested: dict[str, Any] = {}
    all_effective: set[str] = set()
    all_fingerprints: set[str] = set()
    total_calls = 0
    for requested in requested_levels:
        trials = [row for row in rows if row["model"] == requested]
        identities: collections.Counter[tuple[str, str, str]] = collections.Counter()
        fingerprints: collections.Counter[str] = collections.Counter()
        for row in trials:
            for call in provider_calls(row):
                requested_id = call.get("requestedModelId")
                effective_id = call.get("effectiveModelId")
                provider_model = call.get("providerModel")
                if not all(isinstance(value, str) and value for value in (requested_id, effective_id, provider_model)):
                    raise RuntimeError(f"incomplete Provider model identity in {row['trialId']}")
                if requested_id != requested:
                    raise RuntimeError(
                        f"trial/requested model mismatch in {row['trialId']}: {requested_id} != {requested}"
                    )
                identities[(requested_id, effective_id, provider_model)] += 1
                all_effective.add(effective_id)
                fingerprint = call.get("systemFingerprint")
                if isinstance(fingerprint, str) and fingerprint:
                    fingerprints[fingerprint] += 1
                    all_fingerprints.add(fingerprint)
                total_calls += 1
        by_requested[requested] = {
            "trialCount": len(trials),
            "providerCallCount": sum(identities.values()),
            "observedIdentities": [
                {
                    "requestedModelId": identity[0],
                    "effectiveModelId": identity[1],
                    "providerModel": identity[2],
                    "callCount": count,
                }
                for identity, count in sorted(identities.items())
            ],
            "systemFingerprints": [
                {"value": value, "callCount": count}
                for value, count in sorted(fingerprints.items())
            ],
        }

    collapsed = len(requested_levels) > 1 and len(all_effective) == 1
    standing = "COLLAPSED_EFFECTIVE_IDENTITY" if collapsed else "DISTINCT_EFFECTIVE_IDENTITIES"
    consequences = {
        "modelMainEffect": "NOT_ESTIMABLE" if collapsed else "ESTIMABLE_WITHIN_PILOT_SCOPE",
        "modelByHarnessInteraction": "NOT_ESTIMABLE" if collapsed else "ESTIMABLE_WITHIN_PILOT_SCOPE",
        "harnessMainEffect": "DESCRIPTIVE_WITHIN_EFFECTIVE_MODEL_REGIME",
        "protocolMechanics": "UNAFFECTED",
        "outcomeProcessSeparation": "UNAFFECTED",
        "recoveryAndForkMechanics": "UNAFFECTED",
    }
    qualification = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-factor-qualification",
        "experimentId": result_set["experimentId"],
        "factorId": "factor:model",
        "factorRole": "treatment",
        "standing": standing,
        "requestedLevels": requested_levels,
        "effectiveModelIds": sorted(all_effective),
        "providerCallCount": total_calls,
        "providerIdentityEvidence": by_requested,
        "observedSystemFingerprints": sorted(all_fingerprints),
        "boundArtifacts": {
            "resultSetDigest": result_set["resultSetDigest"],
            "analysisDigest": analysis["analysisDigest"],
            "acceptanceDigest": acceptance["acceptanceDigest"],
        },
        "interpretability": consequences,
        "supersedesInterpretation": [
            "analysis.primaryEffects.modelHiddenPassDifference",
            "analysis.primaryEffects.modelByCodecHiddenPassInteraction",
        ] if collapsed else [],
        "nonClaims": [
            "This append-only qualification does not modify the frozen preregistration, TrialRecords, Episodes, EvaluationRecords, analysis artifact, or mechanical acceptance.",
            "Requested model identifiers are not sufficient treatment evidence when Provider effective identity collapses them.",
            "A zero requested-model contrast under collapsed effective identity is not evidence of model equivalence.",
            "Harness observations remain pilot-scale and scoped to the single observed effective Provider model regime.",
        ],
    }
    qualification["qualificationDigest"] = pilot.canonical_digest(qualification)
    return qualification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    qualification = build_qualification(args.evidence_dir.resolve())
    output = args.output or args.evidence_dir / "model-factor-qualification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(qualification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(qualification, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
