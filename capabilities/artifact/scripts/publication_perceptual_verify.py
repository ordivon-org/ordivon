#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from artifact_capabilities.publication.perceptual import (
    combine_carrier_and_perceptual,
    evaluate_perceptual_conformance,
    load_observer_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adjudicate independent perceptual observer receipts for one publication carrier."
    )
    parser.add_argument("--carrier-evaluation", required=True, type=Path)
    parser.add_argument("--observer-report", required=True, action="append", type=Path)
    parser.add_argument("--pages", required=True, type=int)
    parser.add_argument("--figures", required=True, type=int)
    parser.add_argument("--tables", required=True, type=int)
    parser.add_argument("--visual-regression-standing", default="PASS")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    carrier = json.loads(args.carrier_evaluation.read_text(encoding="utf-8"))
    reports = tuple(load_observer_report(path) for path in args.observer_report)
    perceptual = evaluate_perceptual_conformance(
        carrier_sha256=carrier["pdfSha256"],
        deterministic_standing=carrier["machineStanding"],
        expected_pages=args.pages,
        expected_figures=args.figures,
        expected_tables=args.tables,
        observer_reports=reports,
        visual_regression_standing=args.visual_regression_standing,
    )
    release = combine_carrier_and_perceptual(carrier, perceptual)
    result = {
        "schemaVersion": 1,
        "kind": "publication-perceptual-release-evaluation",
        "perceptual": perceptual,
        "release": release,
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if release["standing"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
