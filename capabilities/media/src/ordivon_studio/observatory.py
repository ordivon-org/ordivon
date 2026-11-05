from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .observatory_analysis import (
    CLUSTER_FEATURES as CLUSTER_FEATURES,
)
from .observatory_analysis import (
    TITLE_FEATURES as TITLE_FEATURES,
)
from .observatory_analysis import (
    analyze_snapshot,
)
from .observatory_analysis import (
    build_matched_pairs as build_matched_pairs,
)
from .observatory_analysis import (
    cluster_observations as cluster_observations,
)
from .observatory_analysis import (
    paired_feature_contrasts as paired_feature_contrasts,
)
from .observatory_analysis import (
    title_features as title_features,
)
from .observatory_apple_music import collect_apple_music as collect_apple_music
from .observatory_contracts import (
    REPORT_KIND as REPORT_KIND,
)
from .observatory_contracts import (
    SNAPSHOT_KIND,
    _canonical_digest,
    _utc_now,
)
from .observatory_guardian import (
    DEFAULT_GUARDIAN_SECTIONS as DEFAULT_GUARDIAN_SECTIONS,
)
from .observatory_guardian import (
    collect_guardian as collect_guardian,
)
from .observatory_hacker_news import collect_hacker_news as collect_hacker_news


@dataclass(frozen=True)
class SourceCapability:
    provider: str
    surface: str
    access: str
    byte_policy: str
    status: str
    note: str

    def as_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "surface": self.surface,
            "access": self.access,
            "bytePolicy": self.byte_policy,
            "status": self.status,
            "note": self.note,
        }


CAPABILITIES = (
    SourceCapability(
        "hacker-news",
        "topstories/newstories",
        "public official Firebase API; no credential",
        "metadata/reference only",
        "live",
        "Near-real-time ranked-link observation with public score/comment signals.",
    ),
    SourceCapability(
        "apple-music",
        "Marketing Tools RSS / Top Songs",
        "public official RSS feed; no credential",
        "metadata/reference/artwork URL only; no media ownership implied",
        "live",
        "Chart rank is an attention signal, not an intrinsic music-quality label.",
    ),
    SourceCapability(
        "guardian",
        "Open Platform section mostViewed/editorsPicks/newest",
        "official API; public test developer key works for bounded research probes",
        "metadata/reference only by default",
        "live",
        "Most-viewed, editorial selection, and newest controls remain distinct selection mechanisms.",
    ),
    SourceCapability(
        "youtube",
        "Data API videos.list chart=mostPopular",
        "official API key required",
        "reference/metadata; audiovisual bytes are not acquired by this apparatus",
        "capability-only",
        "Do not fake a live acceptance when no YouTube API credential is configured.",
    ),
    SourceCapability(
        "douyin",
        "data.external.billboard_hot_video",
        "official client token plus approved scope required",
        "reference/metadata; audiovisual bytes are not acquired by this apparatus",
        "capability-only",
        "Official hot-video statistics are a recent-24h offline product and require permission.",
    ),
    SourceCapability(
        "tiktok",
        "Creative Center / TikTok One inspiration",
        "public human-facing surface; no stable public research ingestion API assumed here",
        "reference/metadata only unless a future admitted API grants more",
        "capability-only",
        "Keep platform-specific observation replaceable; do not scrape a brittle private interface into core authority.",
    ),
    SourceCapability(
        "google-trends",
        "Trends API Alpha",
        "limited alpha access",
        "aggregated attention signal only",
        "capability-only",
        "Useful attention-world context once access exists; not required for R0-R3 acceptance.",
    ),
)


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
