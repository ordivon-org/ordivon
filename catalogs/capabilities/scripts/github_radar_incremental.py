#!/usr/bin/env python3
"""Official GitHub Trending -> evidence-only, seven-day deduplicated candidates.

This script never installs software, promotes a provider or fabricates star deltas.
For daily use: --live --limit-per-window 5 --history-dir PATH --output PATH.
For replay: --input pinned-observation.json --history-dir PATH --output PATH.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from github_radar.constants import GAIN as GAIN  # noqa: PLC0414 - compatibility reexport
from github_radar.constants import GH as GH  # noqa: PLC0414 - compatibility reexport
from github_radar.constants import REPO as REPO  # noqa: PLC0414 - compatibility reexport
from github_radar.constants import WINDOWS as WINDOWS  # noqa: PLC0414 - compatibility reexport
from github_radar.history import previous_repositories
from github_radar.normalization import normalize
from github_radar.parser import TrendingParser as TrendingParser  # noqa: PLC0414 - compatibility reexport
from github_radar.parser import parse_trending as parse_trending  # noqa: PLC0414 - compatibility reexport
from github_radar.provider import fetch_json as fetch_json  # noqa: PLC0414 - compatibility reexport
from github_radar.provider import live_observation


def main() -> int:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--live", action="store_true")
    src.add_argument("--input", type=Path)
    ap.add_argument("--limit-per-window", type=int, default=5)
    ap.add_argument("--history-dir", type=Path, default=Path("catalogs/capabilities/evidence/github-radar"))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if not 1 <= args.limit_per_window <= 30:
        ap.error("--limit-per-window must be between 1 and 30")
    raw = live_observation(args.limit_per_window) if args.live else json.loads(args.input.read_text(encoding="utf-8"))
    older = previous_repositories(args.history_dir, date.fromisoformat(raw["snapshotDay"]), args.output)
    result = normalize(raw, older)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "candidateCount": len(result["candidates"]),
                      "repeatCount": sum(x["repeatedWithin7Days"] for x in result["candidates"]),
                      "standing": "DISCOVERY_ONLY",
                      "sourceCoverage": result["sourceCoverage"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
