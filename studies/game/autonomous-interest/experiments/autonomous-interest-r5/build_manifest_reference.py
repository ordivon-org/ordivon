#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import evaluator_reference as er
import selection_reference as sr
import renderer_reference as rr
import study_runner_reference as hr

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_KIND = "ordivon.game-autonomous-interest-r5-human-build-manifest"


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def source_digest(module) -> str:
    return sha256_bytes(Path(module.__file__).resolve().read_bytes())


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def evidence_digest(value: object) -> str:
    return sha256_bytes(er.canonical_json(value).encode("utf-8"))


def source_bindings() -> dict:
    return {
        "evaluator": source_digest(er),
        "selection": source_digest(sr),
        "renderer": source_digest(rr),
        "studyRunner": source_digest(hr),
        "buildManifestReference": file_digest(Path(__file__).resolve()),
        "modelSchema": file_digest(ROOT / "domains/game/game-autonomous-interest-model-r5.schema.json"),
        "machineProtocol": file_digest(ROOT / "domains/game/game-autonomous-interest-protocol-r5.json"),
    }


def _body(candidate_models: Sequence[Mapping], *, allow_selftest: bool=False) -> dict:
    tournament=sr.tournament_select(candidate_models,allow_selftest=allow_selftest)
    winner=tournament["winnerModel"]
    ablation=sr.choose_ablation(winner,allow_selftest=allow_selftest)
    selected=ablation["couplingId"]
    if selected not in winner["causalCouplings"]:
        raise ValueError("selected coupling not declared by winner")
    winner_eval=tournament["winnerEvaluation"]
    if winner_eval["modelDigest"]!=ablation["winnerEvaluation"]["modelDigest"]:
        raise ValueError("winner/ablation model mismatch")
    return {
        "schemaVersion":1,
        "kind":MANIFEST_KIND,
        "winnerCandidateId":winner["candidateId"],
        "winnerModelDigest":winner_eval["modelDigest"],
        "winnerEvaluationDigest":evidence_digest(winner_eval),
        "tournamentEvidenceDigest":evidence_digest({"stats":tournament["tournamentStats"],"evaluations":tournament["allEvaluations"]}),
        "selectedCouplingId":selected,
        "ablationEvaluationDigest":evidence_digest(ablation["ablationEvaluation"]),
        "armBindings":{
            "winner":{"disabledCoupling":None},
            "ablation":{"disabledCoupling":selected},
        },
        "rendererId":rr.RENDERER_ID,
        "studyRunnerId":hr.STUDY_RUNNER_ID,
        "candidateControlledVisibleTextAllowed":False,
        "sourceBindings":source_bindings(),
    }


def make_manifest(candidate_models: Sequence[Mapping], *, allow_selftest: bool=False) -> dict:
    body=_body(candidate_models,allow_selftest=allow_selftest)
    return {**body,"manifestDigest":evidence_digest(body)}


def validate_manifest(manifest: Mapping, candidate_models: Sequence[Mapping], *, allow_selftest: bool=False) -> dict:
    expected=make_manifest(candidate_models,allow_selftest=allow_selftest)
    if er.canonical_json(manifest)!=er.canonical_json(expected):
        raise ValueError("build manifest does not equal authoritative recomputation")
    return expected


def winner_model_for_manifest(manifest: Mapping, candidate_models: Sequence[Mapping], *, allow_selftest: bool=False) -> Mapping:
    checked=validate_manifest(manifest,candidate_models,allow_selftest=allow_selftest)
    target=checked["winnerModelDigest"]
    matches=[]
    for m in candidate_models:
        ev=sr.evaluate_authoritatively(m,allow_selftest=allow_selftest)
        if ev["modelDigest"]==target: matches.append(m)
    if len(matches)!=1: raise ValueError("manifest winner model digest not uniquely resolved")
    return matches[0]


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("models",nargs="+",help="exact three candidate model JSON files")
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    models=[er.load_model(p) for p in args.models]
    if len(models)!=3: raise SystemExit("exactly three candidate models required")
    manifest=make_manifest(models)
    Path(args.output).write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(manifest["manifestDigest"])


if __name__=="__main__": main()
