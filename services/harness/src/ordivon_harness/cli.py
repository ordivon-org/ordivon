from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from .ordivon.deepseek import DEFAULT_DEEPSEEK_SECRET_PATH
from .postgres_store import PostgresHarnessStore, configured_postgres


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ordivon-harness",
        description="Caller-neutral Harness Run execution and durable recovery.",
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        help="Harness Journal/CAS root",
    )
    parser.add_argument(
        "--deepseek-secret",
        type=Path,
        default=DEFAULT_DEEPSEEK_SECRET_PATH,
        help="DeepSeek settings for the built-in no-Tool execution profile",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    status = commands.add_parser("status")
    status.add_argument("harness_run_id")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("harness_run_id")
    explain = commands.add_parser(
        "explain",
        help="inspect one durable Run with explicit proof boundaries",
    )
    explain.add_argument("harness_run_id")
    run = commands.add_parser("run")
    run.add_argument("contract", type=Path)
    _add_input_options(run)
    resume = commands.add_parser("resume")
    resume.add_argument("harness_run_id")
    _add_input_options(resume)
    commands.add_parser("store-init")
    commands.add_parser("store-doctor")
    store_backup = commands.add_parser("store-backup")
    store_backup.add_argument("destination", type=Path)
    store_verify = commands.add_parser("store-verify-backup")
    store_verify.add_argument("backup", type=Path)
    store_restore = commands.add_parser("store-restore")
    store_restore.add_argument("backup", type=Path)
    store_restore.add_argument("destination", type=Path)
    store_inspect = commands.add_parser("store-inspect")
    store_inspect.add_argument("harness_run_id")
    store_events = commands.add_parser("store-events")
    store_events.add_argument("harness_run_id")
    store_events.add_argument("--after-sequence", type=int, default=0)
    return parser


def _add_input_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--message", action="append", default=[])
    parser.add_argument("--messages-json", type=Path)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command.startswith("store-"):
            result = _dispatch_store(args)
        else:
            from .independent_cli import dispatch
            result = dispatch(args, clock_ms=_wall_clock_ms)
    except (
        FileNotFoundError,
        KeyError,
        PermissionError,
        ValueError,
        RuntimeError,
    ) as error:
        print(
            json.dumps(
                {"ok": False, "error": type(error).__name__, "message": str(error)},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result.get("ok", True) is True else 1


def _dispatch_store(args: argparse.Namespace) -> dict[str, object]:
    if args.state_root is not None:
        raise ValueError("--state-root is retired; Harness uses PostgreSQL only")
    dsn, schema = configured_postgres()
    if args.command in {"store-backup", "store-verify-backup", "store-restore"}:
        raise ValueError("legacy SQLite backup and restore are retired; use native PostgreSQL recovery")
    with PostgresHarnessStore(dsn, schema=schema, initialize=args.command == "store-init") as store:
        if args.command in {"store-init", "store-doctor"}:
            return {"ok": True, "backend": "postgresql",
                "stateRoot": None,
                "storageBackend": "postgresql", "schema": schema,
                    "store": store.doctor(full=True)}
        if args.command == "store-inspect":
            return {"ok": True, "backend": "postgresql",
                "stateRoot": None,
                "storageBackend": "postgresql", "schema": schema,
                    "run": store.load_run(args.harness_run_id).to_dict()}
        if args.command == "store-events":
            events = store.list_run_events(
                args.harness_run_id, after_sequence=args.after_sequence
            )
            return {"ok": True, "backend": "postgresql",
                "stateRoot": None,
                "storageBackend": "postgresql", "schema": schema,
                    "events": [event.to_dict() for event in events]}
    raise ValueError("unsupported Harness PG store command")


def _wall_clock_ms() -> int:
    return time.time_ns() // 1_000_000


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
