#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from artifact_capabilities.publication import (
    evaluate_publication_contract,
    load_publication_contract,
    probe_pdf_carrier,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe a PDF with mature PDF tools and evaluate an authority-bound publication contract."
    )
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--compiler-log", type=Path)
    parser.add_argument("--human-perceptual-signoff", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = load_publication_contract(args.contract)
    observation = probe_pdf_carrier(
        args.pdf,
        compiler_log_path=args.compiler_log,
        human_perceptual_signoff=args.human_perceptual_signoff,
    )
    result = evaluate_publication_contract(observation, contract)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["standing"] in {"PASS", "PENDING_HUMAN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
