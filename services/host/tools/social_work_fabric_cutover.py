#!/usr/bin/env python3
"""One-shot Social Work Fabric destructive cutover operator.

This is deliberately not an MCP surface and not a compatibility adapter.  It writes
immutable snapshot/plan/receipt files around a bounded migration transaction.
Database DSNs are accepted only through environment variables so credentials are not
placed in argv/process listings.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from ordivon_host_v2.legacy_cutover import (
    apply_cutover_plan,
    compile_cutover_plan,
    extract_legacy_snapshot,
    verify_cutover,
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _dsn(env_name: str) -> str:
    value = os.environ.get(env_name)
    if not value:
        raise SystemExit(f"required DSN environment variable is not set: {env_name}")
    return value


def _active_task_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise SystemExit("active-task manifest must be a JSON array of non-empty Task IDs")
    if len(value) != len(set(value)):
        raise SystemExit("active-task manifest contains duplicates")
    return set(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    extract = sub.add_parser("extract", help="read legacy Host into an immutable snapshot")
    extract.add_argument("--dsn-env", default="ORDIVON_HOST_V2_DSN")
    extract.add_argument("--out", required=True, type=Path)

    plan = sub.add_parser("plan", help="compile a deterministic cutover plan from a snapshot")
    plan.add_argument("--snapshot", required=True, type=Path)
    plan.add_argument("--active-task-manifest", type=Path)
    plan.add_argument("--out", required=True, type=Path)

    apply = sub.add_parser(
        "apply", help="apply a previously compiled plan to an empty schema-8 SWF target"
    )
    apply.add_argument("--dsn-env", default="ORDIVON_HOST_V2_DSN")
    apply.add_argument("--snapshot", required=True, type=Path)
    apply.add_argument("--plan", required=True, type=Path)
    apply.add_argument("--confirm-plan-digest", required=True)
    apply.add_argument("--receipt", required=True, type=Path)

    verify = sub.add_parser("verify", help="re-run differential verification without mutation")
    verify.add_argument("--dsn-env", default="ORDIVON_HOST_V2_DSN")
    verify.add_argument("--snapshot", required=True, type=Path)
    verify.add_argument("--plan", required=True, type=Path)
    verify.add_argument("--receipt", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "extract":
        snapshot = extract_legacy_snapshot(_dsn(args.dsn_env))
        _write_json(args.out, snapshot)
        print(
            json.dumps(
                {
                    "standing": "EXTRACTED",
                    "snapshotDigest": snapshot["snapshotDigest"],
                    "out": str(args.out),
                }
            )
        )
        return 0

    snapshot = _read_json(args.snapshot)
    if args.command == "plan":
        plan = compile_cutover_plan(
            snapshot, active_task_ids=_active_task_ids(args.active_task_manifest)
        )
        _write_json(args.out, plan)
        print(
            json.dumps(
                {"standing": "PLANNED", "planDigest": plan["planDigest"], "out": str(args.out)}
            )
        )
        return 0

    plan = _read_json(args.plan)
    if args.command == "apply":
        if args.confirm_plan_digest != plan.get("planDigest"):
            raise SystemExit("--confirm-plan-digest does not match the plan; refusing mutation")
        receipt = apply_cutover_plan(_dsn(args.dsn_env), snapshot, plan)
        _write_json(args.receipt, receipt)
        print(
            json.dumps(
                {
                    "standing": receipt["standing"],
                    "planDigest": plan["planDigest"],
                    "receipt": str(args.receipt),
                }
            )
        )
        return 0 if receipt["standing"] == "PASS" else 2

    if args.command == "verify":
        receipt = verify_cutover(_dsn(args.dsn_env), snapshot, plan)
        _write_json(args.receipt, receipt)
        print(
            json.dumps(
                {
                    "standing": receipt["standing"],
                    "planDigest": plan["planDigest"],
                    "receipt": str(args.receipt),
                }
            )
        )
        return 0 if receipt["standing"] == "PASS" else 2

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
