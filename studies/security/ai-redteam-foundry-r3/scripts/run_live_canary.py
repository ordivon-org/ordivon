#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
HARNESS_SRC = REPO_ROOT / "services" / "harness" / "src"
for path in (ROOT, HARNESS_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from foundry_r3 import run_canary_probe  # noqa: E402
from ordivon_harness.ordivon.deepseek import DeepSeekSettings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one live-safe synthetic canary evaluation.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=("secret-config", "deepseek-v4-flash", "deepseek-flash", "deepseek-v4-pro"), default="secret-config")
    args = parser.parse_args()

    settings = DeepSeekSettings.from_secret_file(
        timeout_seconds=30.0,
        max_response_bytes=1_048_576,
        max_output_tokens=512,
    )
    if args.model != "secret-config":
        settings = DeepSeekSettings(
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=args.model,
            credential_scope_id=settings.credential_scope_id,
            timeout_seconds=settings.timeout_seconds,
            max_response_bytes=settings.max_response_bytes,
            max_output_tokens=settings.max_output_tokens,
        )

    receipt = run_canary_probe(settings).to_dict()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "path": str(args.output),
                "receiptDigest": receipt["receiptDigest"],
                "effectiveModelId": receipt["effective_model_id"],
                "identityStrength": receipt["realized_target"]["identityStrength"],
                "canaryLeaked": receipt["canary_leaked"],
                "finding": receipt["finding"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
