from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_studio.grounded_meaning import build_provider_bundle, canonical_digest, score_provider_receipt


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parents[1]
    bundle = build_provider_bundle(root=root, replicates=args.replicates)
    output = Path(args.output)
    _write(output, bundle)
    print(json.dumps({"ok": True, "mode": "build", "output": str(output), "tasks": len(bundle["tasks"]), "replicates": args.replicates, "bundleDigest": bundle["bundleDigest"]}, indent=2))


def score(args: argparse.Namespace) -> None:
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    if canonical_digest({k: v for k, v in bundle.items() if k != "bundleDigest"}) != bundle.get("bundleDigest"):
        raise SystemExit("bundle digest mismatch")
    result = score_provider_receipt(bundle, receipt)
    output = Path(args.output)
    _write(output, result)
    print(json.dumps({"ok": True, "mode": "score", "output": str(output), "scoreDigest": result["scoreDigest"], "acceptanceSignals": result["acceptanceSignals"], "missingTasks": result["missingTasks"], "extraTasks": result["extraTasks"]}, indent=2))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Build and independently score the R5 Grounded Meaning Provider experiment.")
    sub = value.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--replicates", type=int, default=2)
    build_parser.add_argument("--output", default="out/r5/provider-bundle.json")
    build_parser.set_defaults(func=build)
    score_parser = sub.add_parser("score")
    score_parser.add_argument("--bundle", default="out/r5/provider-bundle.json")
    score_parser.add_argument("--receipt", required=True)
    score_parser.add_argument("--output", default="out/r5/provider-score.json")
    score_parser.set_defaults(func=score)
    return value


def main() -> None:
    args = parser().parse_args()
    if getattr(args, "replicates", 1) < 1 or getattr(args, "replicates", 1) > 8:
        raise SystemExit("replicates must be between 1 and 8")
    args.func(args)


if __name__ == "__main__":
    main()
