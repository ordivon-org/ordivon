"""Compose replaceable cultural reference providers and CLI snapshot entry.

Only the snapshot/orchestration and CLI live here. Provider-specific
acquisition is owned by observatory_hacker_news, observatory_apple_music,
and observatory_guardian; shared source boundaries live in observatory_source.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .observatory_analysis import analyze_snapshot
from .observatory_apple_music import collect_apple_music
from .observatory_contracts import SNAPSHOT_KIND, _canonical_digest, _utc_now
from .observatory_guardian import DEFAULT_GUARDIAN_SECTIONS, collect_guardian
from .observatory_hacker_news import collect_hacker_news
from .observatory_source import CAPABILITIES


def collect_snapshot(
    *,
    hn_top: int = 160,
    hn_new: int = 240,
    apple_limit: int = 100,
    guardian_sections: Iterable[str] = DEFAULT_GUARDIAN_SECTIONS,
    guardian_newest: int = 40,
    timeout: float = 20.0,
) -> dict[str, Any]:
    observed_at = _utc_now()
    observations: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    collectors = (
        ("hacker-news", lambda: collect_hacker_news(top_limit=hn_top, new_limit=hn_new, timeout=timeout)),
        ("apple-music", lambda: collect_apple_music(limit=apple_limit, timeout=timeout)),
        (
            "guardian",
            lambda: collect_guardian(sections=guardian_sections, newest_per_section=guardian_newest, timeout=timeout),
        ),
    )
    for provider, collector in collectors:
        try:
            observations.extend(collector())
        except Exception as error:  # provider failure is evidence; do not erase other observations
            failures.append({"provider": provider, "errorType": type(error).__name__, "message": str(error)[:500]})
    counts: dict[str, int] = {}
    for item in observations:
        counts[item["provider"]] = counts.get(item["provider"], 0) + 1
    payload = {
        "schemaVersion": 1,
        "kind": SNAPSHOT_KIND,
        "observedAt": observed_at,
        "capabilities": [item.as_dict() for item in CAPABILITIES],
        "countsByProvider": counts,
        "failures": failures,
        "observations": observations,
    }
    payload["snapshotDigest"] = _canonical_digest(payload)
    return payload


def _write_json(path: Path | None, value: Any) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        sys.stdout.write(rendered)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def _command_capabilities(_: argparse.Namespace) -> int:
    _write_json(None, {"schemaVersion": 1, "kind": "ordivon.studio-cultural-source-capabilities", "sources": [item.as_dict() for item in CAPABILITIES]})
    return 0


def _command_collect(args: argparse.Namespace) -> int:
    snapshot = collect_snapshot(
        hn_top=args.hn_top,
        hn_new=args.hn_new,
        apple_limit=args.apple,
        guardian_sections=args.guardian_section or DEFAULT_GUARDIAN_SECTIONS,
        guardian_newest=args.guardian_newest,
        timeout=args.timeout,
    )
    _write_json(Path(args.output) if args.output else None, snapshot)
    if args.output:
        _write_json(None, {"ok": not snapshot["failures"], "output": args.output, "snapshotDigest": snapshot["snapshotDigest"], "countsByProvider": snapshot["countsByProvider"], "failures": snapshot["failures"]})
    return 0 if not snapshot["failures"] else 1


def _command_analyze(args: argparse.Namespace) -> int:
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    report = analyze_snapshot(snapshot, clusters=args.clusters)
    _write_json(Path(args.output) if args.output else None, report)
    if args.output:
        _write_json(None, {"ok": True, "output": args.output, "reportDigest": report["reportDigest"], "corpus": report["corpus"], "matchedControls": {"pairCount": report["matchedControls"]["pairCount"], "pairsByProvider": report["matchedControls"]["pairsByProvider"]}})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ordivon_studio.observatory")
    commands = parser.add_subparsers(dest="command", required=True)
    capabilities = commands.add_parser("capabilities", help="show admitted cultural observation surfaces and access boundaries")
    capabilities.set_defaults(handler=_command_capabilities)
    collect = commands.add_parser("collect", help="collect a bounded live metadata/reference snapshot")
    collect.add_argument("--output")
    collect.add_argument("--hn-top", type=int, default=160)
    collect.add_argument("--hn-new", type=int, default=240)
    collect.add_argument("--apple", type=int, default=100)
    collect.add_argument("--guardian-section", action="append")
    collect.add_argument("--guardian-newest", type=int, default=40)
    collect.add_argument("--timeout", type=float, default=20.0)
    collect.set_defaults(handler=_command_collect)
    analyze = commands.add_parser("analyze", help="cluster a snapshot and run matched-control structural contrasts")
    analyze.add_argument("snapshot")
    analyze.add_argument("--output")
    analyze.add_argument("--clusters", type=int, default=8)
    analyze.set_defaults(handler=_command_analyze)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        raise SystemExit(args.handler(args))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
