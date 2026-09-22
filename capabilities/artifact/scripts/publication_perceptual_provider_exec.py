#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from artifact_capabilities.publication.provider_adapter import (
    ProviderExecutionSpec,
    run_observer_provider,
    write_provider_execution_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one isolated publication perceptual observer provider."
    )
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--provider-executable", required=True)
    parser.add_argument("--provider-arg", action="append", default=[])
    parser.add_argument("--task-envelope", required=True, type=Path)
    parser.add_argument("--packet-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--carrier-sha256", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=["BLIND_VISION", "VENUE_AWARE_VISION", "SEMANTIC_LAYOUT"],
    )
    parser.add_argument("--independence-key", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()

    spec = ProviderExecutionSpec(
        provider_id=args.provider_id,
        executable=args.provider_executable,
        args=tuple(args.provider_arg),
        timeout_seconds=args.timeout_seconds,
    )
    report, receipt = run_observer_provider(
        spec=spec,
        task_envelope_path=args.task_envelope,
        packet_root=args.packet_root,
        output_path=args.output,
        expected_carrier_sha256=args.carrier_sha256,
        expected_role=args.role,
        independence_key=args.independence_key,
    )
    write_provider_execution_receipt(args.receipt, receipt)
    print(
        json.dumps(
            {
                "schemaVersion": 1,
                "kind": "publication-perceptual-provider-exec-summary",
                "providerId": args.provider_id,
                "observerId": report.observer_id,
                "role": report.role,
                "standing": report.standing,
                "receipt": str(args.receipt),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
