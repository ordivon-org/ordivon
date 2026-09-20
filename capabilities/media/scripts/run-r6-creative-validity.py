from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_studio.research_validity import (
    TrialLedger,
    build_null_registration,
    calibration_experiment,
    evaluate_sealed_holdout,
    run_registered_search,
    score_null_attack,
    search_replay_correction,
)


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def register(args: argparse.Namespace) -> None:
    registration = build_null_registration(
        mode=args.mode,
        attempt_budget=args.budget,
        visible_seed=args.visible_seed,
        holdout_seed_commitment=args.holdout_seed_commitment,
        experiment_id=args.experiment_id,
    )
    write_json(args.output, registration)
    print(json.dumps({"ok": True, "mode": "register", "output": args.output, "registrationDigest": registration["registrationDigest"]}, indent=2))


def search(args: argparse.Namespace) -> None:
    registration = read_json(args.registration)
    ledger = TrialLedger(args.ledger, search_id=str(registration["experimentId"]))
    try:
        winner = run_registered_search(registration, ledger)
    finally:
        ledger.close()
    write_json(args.output, winner)
    print(json.dumps({"ok": True, "mode": "search", "output": args.output, "winnerDigest": winner["winnerDigest"], "visibleStatisticZ": winner["visibleStatisticZ"], "naiveOneSidedP": winner["naiveOneSidedP"], "ledger": winner["trialLedger"]}, indent=2))


def correct(args: argparse.Namespace) -> None:
    result = search_replay_correction(
        read_json(args.registration),
        read_json(args.winner),
        replay_seed=args.replay_seed,
        replay_count=args.replays,
    )
    write_json(args.output, result)
    print(json.dumps({"ok": True, "mode": "correct", "output": args.output, "searchCorrectedP": result["searchCorrectedP"], "nullMaxSummary": result["nullMaxSummary"]}, indent=2))


def holdout(args: argparse.Namespace) -> None:
    registration = read_json(args.registration)
    ledger = TrialLedger(args.ledger, search_id=str(registration["experimentId"])) if args.ledger else None
    try:
        result = evaluate_sealed_holdout(
            registration,
            read_json(args.winner),
            holdout_seed=args.holdout_seed,
            ledger=ledger,
        )
    finally:
        if ledger is not None:
            ledger.close()
    write_json(args.output, result)
    print(json.dumps({"ok": True, "mode": "holdout", "output": args.output, "holdoutStatisticZ": result["holdoutStatisticZ"], "holdoutOneSidedP": result["holdoutOneSidedP"], "status": result["holdoutStatus"]}, indent=2))


def calibrate(args: argparse.Namespace) -> None:
    budgets = [int(item) for item in args.budgets.split(",") if item.strip()]
    result = calibration_experiment(
        mode=args.mode,
        budgets=budgets,
        worlds=args.worlds,
        reference_replays=args.reference_replays,
        seed=args.seed,
    )
    write_json(args.output, result)
    print(json.dumps({"ok": True, "mode": "calibrate", "output": args.output, "calibrationDigest": result["calibrationDigest"], "rows": result["rows"]}, indent=2))


def score(args: argparse.Namespace) -> None:
    result = score_null_attack(
        registration=read_json(args.registration),
        winner=read_json(args.winner),
        correction=read_json(args.correction),
        holdout=read_json(args.holdout),
        calibration=read_json(args.calibration),
    )
    write_json(args.output, result)
    print(json.dumps({"ok": True, "mode": "score", "output": args.output, "accepted": result["accepted"], "acceptanceSignals": result["acceptanceSignals"], "observed": result["observed"], "scoreDigest": result["scoreDigest"]}, indent=2))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="R6 Creative Alpha research-validity experiments.")
    sub = value.add_subparsers(dest="command", required=True)

    item = sub.add_parser("register")
    item.add_argument("--mode", choices=("static", "adaptive"), default="static")
    item.add_argument("--budget", type=int, default=5000)
    item.add_argument("--visible-seed", default="r6a-visible-null-search-20260811")
    item.add_argument("--holdout-seed-commitment", required=True)
    item.add_argument("--experiment-id")
    item.add_argument("--output", default="out/r6/r6a-registration.json")
    item.set_defaults(func=register)

    item = sub.add_parser("search")
    item.add_argument("--registration", default="out/r6/r6a-registration.json")
    item.add_argument("--ledger", default="out/r6/r6a-trials.sqlite")
    item.add_argument("--output", default="out/r6/r6a-winner.json")
    item.set_defaults(func=search)

    item = sub.add_parser("correct")
    item.add_argument("--registration", default="out/r6/r6a-registration.json")
    item.add_argument("--winner", default="out/r6/r6a-winner.json")
    item.add_argument("--replay-seed", default="r6a-search-replay-null-20260811")
    item.add_argument("--replays", type=int, default=2000)
    item.add_argument("--output", default="out/r6/r6a-correction.json")
    item.set_defaults(func=correct)

    item = sub.add_parser("holdout")
    item.add_argument("--registration", default="out/r6/r6a-registration.json")
    item.add_argument("--winner", default="out/r6/r6a-winner.json")
    item.add_argument("--holdout-seed", required=True)
    item.add_argument("--ledger")
    item.add_argument("--output", default="out/r6/r6a-holdout.json")
    item.set_defaults(func=holdout)

    item = sub.add_parser("calibrate")
    item.add_argument("--mode", choices=("static", "adaptive"), default="static")
    item.add_argument("--budgets", default="10,100,1000,5000")
    item.add_argument("--worlds", type=int, default=400)
    item.add_argument("--reference-replays", type=int, default=1600)
    item.add_argument("--seed", default="r6a-calibration-20260811")
    item.add_argument("--output", default="out/r6/r6a-calibration.json")
    item.set_defaults(func=calibrate)

    item = sub.add_parser("score")
    item.add_argument("--registration", default="out/r6/r6a-registration.json")
    item.add_argument("--winner", default="out/r6/r6a-winner.json")
    item.add_argument("--correction", default="out/r6/r6a-correction.json")
    item.add_argument("--holdout", default="out/r6/r6a-holdout.json")
    item.add_argument("--calibration", default="out/r6/r6a-calibration.json")
    item.add_argument("--output", default="out/r6/r6a-score.json")
    item.set_defaults(func=score)
    return value


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
