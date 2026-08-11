from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_studio.rich_perception import canonical_digest, run_guardian_article_experiment


DEFAULT_SECTIONS = ("world", "technology", "culture", "business", "science", "lifeandstyle")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the R4-A Guardian full-content matched-control experiment.")
    parser.add_argument("--section", action="append", dest="sections")
    parser.add_argument("--pairs-per-section", type=int, default=8)
    parser.add_argument("--newest-per-section", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--output", default="out/r4/r4a-guardian-rich-article.json")
    args = parser.parse_args()

    report = run_guardian_article_experiment(
        sections=args.sections or DEFAULT_SECTIONS,
        pairs_per_section=args.pairs_per_section,
        newest_per_section=args.newest_per_section,
        timeout=args.timeout,
        permutations=args.permutations,
    )
    report["permutationMethod"] = f"paired whole-vector sign flip; {args.permutations} permutations"
    report["reportDigest"] = canonical_digest(report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(output),
                "pairCount": report["pairCount"],
                "pairsBySection": report["pairsBySection"],
                "contentFetchFailures": report["contentFetchFailures"],
                "shallowAccuracy": report["shallow"]["accuracy"],
                "richOnlyAccuracy": report["richOnly"]["accuracy"],
                "combinedAccuracy": report["combined"]["accuracy"],
                "accuracyGainOverShallow": report["accuracyGainOverShallow"],
                "equipmentDecision": report["equipmentDecision"],
                "reportDigest": report["reportDigest"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
