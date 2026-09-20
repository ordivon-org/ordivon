from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_studio.creative_alpha import (
    build_holdout_observer_bundle,
    build_holdout_protocol,
    build_observer_bundle,
    build_visible_protocol,
    creative_portfolio_counterfactual,
    descriptive_contrast_uncertainty,
    freeze_visible_contrast,
    score_content_oos,
    score_observer_receipt,
)


def read(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path: str | Path, value: object) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_visible(args: argparse.Namespace) -> None:
    protocol = build_visible_protocol(holdout_seed_commitment=args.holdout_commitment)
    root = Path(args.output_dir); write(root / "protocol.json", protocol)
    for item in protocol["mechanisms"]:
        write(root / f"mechanism-{item['mechanismId'].lower()}.manifest.json", item["manifest"])
    print(json.dumps({"ok": True, "protocolDigest": protocol["protocolDigest"], "holdoutCommitment": protocol["holdout"]["seedCommitment"], "manifests": [str(root / f"mechanism-{item['mechanismId'].lower()}.manifest.json") for item in protocol["mechanisms"]]}, indent=2))


def build_observer(args: argparse.Namespace) -> None:
    bundle = build_observer_bundle(protocol=read(args.protocol), web_receipts=[read(path) for path in args.web_receipt], replicates=args.replicates)
    write(args.output, bundle)
    print(json.dumps({"ok": True, "bundleDigest": bundle["bundleDigest"], "tasks": len(bundle["tasks"]), "providerCalls": sum(task["replicates"] for task in bundle["tasks"]), "output": args.output}, indent=2))


def score_visible(args: argparse.Namespace) -> None:
    score = score_observer_receipt(bundle=read(args.bundle), receipt=read(args.receipt)); write(args.output, score)
    selection = freeze_visible_contrast(score); write(args.selection_output, selection)
    print(json.dumps({"ok": True, "scoreDigest": score["scoreDigest"], "primaryContrast": score["primaryContrast"], "guardrails": score["guardrails"], "selection": selection}, indent=2))


def build_holdout(args: argparse.Namespace) -> None:
    protocol = build_holdout_protocol(holdout_seed=args.holdout_seed, expected_commitment=args.expected_commitment, visible_selection=read(args.selection))
    write(args.output, protocol); write(args.manifest_output, protocol["manifest"])
    print(json.dumps({"ok": True, "holdoutProtocolDigest": protocol["holdoutProtocolDigest"], "seedCommitment": protocol["seedCommitment"], "manifest": args.manifest_output}, indent=2))


def build_holdout_observer(args: argparse.Namespace) -> None:
    bundle = build_holdout_observer_bundle(holdout_protocol=read(args.holdout_protocol), web_receipt=read(args.web_receipt), replicates=args.replicates)
    write(args.output, bundle)
    print(json.dumps({"ok": True, "bundleDigest": bundle["bundleDigest"], "tasks": len(bundle["tasks"]), "providerCalls": sum(task["replicates"] for task in bundle["tasks"])}, indent=2))


def score_holdout(args: argparse.Namespace) -> None:
    score = score_observer_receipt(bundle=read(args.bundle), receipt=read(args.receipt)); write(args.output, score)
    oos = score_content_oos(visible_selection=read(args.selection), holdout_score=score); write(args.oos_output, oos)
    print(json.dumps({"ok": True, "scoreDigest": score["scoreDigest"], "primaryContrast": score["primaryContrast"], "oos": oos}, indent=2))


def uncertainty(args: argparse.Namespace) -> None:
    result = descriptive_contrast_uncertainty(
        visible_bundle=read(args.visible_bundle),
        visible_receipt=read(args.visible_receipt),
        holdout_bundle=read(args.holdout_bundle),
        holdout_receipt=read(args.holdout_receipt),
        bootstrap_draws=args.draws,
        seed=args.seed,
    ); write(args.output, result)
    print(json.dumps({"ok": True, "uncertaintyDigest": result["uncertaintyDigest"], "visible": result["visible"], "pristineContentHoldout": result["pristineContentHoldout"], "effectShrinkage": result["effectShrinkage"]}, indent=2))


def portfolio(args: argparse.Namespace) -> None:
    result = creative_portfolio_counterfactual(visible_score=read(args.visible_score), holdout_score=read(args.holdout_score)); write(args.output, result)
    print(json.dumps({"ok": True, "portfolioDigest": result["portfolioDigest"], "measured": result["measuredVariantAdaptationAccuracy"], "scenarios": result["scenarios"]}, indent=2))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="R6 grounded creative intervention, observer consequence, OOS, and portfolio experiments.")
    sub = value.add_subparsers(dest="command", required=True)
    p = sub.add_parser("build-visible"); p.add_argument("--holdout-commitment", required=True); p.add_argument("--output-dir", default="out/r6/c/visible"); p.set_defaults(func=build_visible)
    p = sub.add_parser("build-observer"); p.add_argument("--protocol", default="out/r6/c/visible/protocol.json"); p.add_argument("--web-receipt", action="append", required=True); p.add_argument("--replicates", type=int, default=8); p.add_argument("--output", default="out/r6/c/provider-bundle.json"); p.set_defaults(func=build_observer)
    p = sub.add_parser("score-visible"); p.add_argument("--bundle", default="out/r6/c/provider-bundle.json"); p.add_argument("--receipt", required=True); p.add_argument("--output", default="out/r6/c/provider-score.json"); p.add_argument("--selection-output", default="out/r6/c/selection.json"); p.set_defaults(func=score_visible)
    p = sub.add_parser("build-holdout"); p.add_argument("--holdout-seed", required=True); p.add_argument("--expected-commitment", required=True); p.add_argument("--selection", default="out/r6/c/selection.json"); p.add_argument("--output", default="out/r6/d/holdout-protocol.json"); p.add_argument("--manifest-output", default="out/r6/d/mechanism-c.manifest.json"); p.set_defaults(func=build_holdout)
    p = sub.add_parser("build-holdout-observer"); p.add_argument("--holdout-protocol", default="out/r6/d/holdout-protocol.json"); p.add_argument("--web-receipt", required=True); p.add_argument("--replicates", type=int, default=8); p.add_argument("--output", default="out/r6/d/provider-bundle.json"); p.set_defaults(func=build_holdout_observer)
    p = sub.add_parser("score-holdout"); p.add_argument("--bundle", default="out/r6/d/provider-bundle.json"); p.add_argument("--receipt", required=True); p.add_argument("--selection", default="out/r6/c/selection.json"); p.add_argument("--output", default="out/r6/d/provider-score.json"); p.add_argument("--oos-output", default="out/r6/d/oos-score.json"); p.set_defaults(func=score_holdout)
    p = sub.add_parser("uncertainty"); p.add_argument("--visible-bundle", default="out/r6/c/provider-bundle.json"); p.add_argument("--visible-receipt", default="out/r6/c/provider-receipt.json"); p.add_argument("--holdout-bundle", default="out/r6/d/provider-bundle.json"); p.add_argument("--holdout-receipt", default="out/r6/d/provider-receipt.json"); p.add_argument("--draws", type=int, default=20000); p.add_argument("--seed", default="r6-descriptive-bootstrap-20260811-v1"); p.add_argument("--output", default="out/r6/d/uncertainty.json"); p.set_defaults(func=uncertainty)
    p = sub.add_parser("portfolio"); p.add_argument("--visible-score", default="out/r6/c/provider-score.json"); p.add_argument("--holdout-score", default="out/r6/d/provider-score.json"); p.add_argument("--output", default="out/r6/e/portfolio.json"); p.set_defaults(func=portfolio)
    return value


def main() -> None:
    args = parser().parse_args(); args.func(args)


if __name__ == "__main__": main()
