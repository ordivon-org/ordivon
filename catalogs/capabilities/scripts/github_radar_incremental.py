#!/usr/bin/env python3
"""Official GitHub Trending -> evidence-only, seven-day deduplicated candidates.

This script never installs software, promotes a provider or fabricates star deltas.
For daily use: --live --limit-per-window 5 --history-dir PATH --output PATH.
For replay: --input pinned-observation.json --history-dir PATH --output PATH.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import hashlib
from pathlib import Path
import re
import subprocess
import urllib.request

WINDOWS = {"daily": "today", "weekly": "this week", "monthly": "this month"}
GH = "https://github.com"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GAIN = re.compile(r"([0-9][0-9,]*)\s+stars?\s+(today|this week|this month)", re.I)


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.h2_depth = 0
        self.hrefs: list[str] = []
        self.bits: list[str] = []
        self.results: list[dict] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and "Box-row" in a.get("class", "").split():
            self.depth = 1
            self.h2_depth = 0
            self.hrefs, self.bits = [], []
            return
        if not self.depth:
            return
        self.depth += 1
        if tag == "h2":
            self.h2_depth += 1
        if self.h2_depth and tag == "a":
            self.hrefs.append(a.get("href", ""))

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "h2" and self.h2_depth:
            self.h2_depth -= 1
        self.depth -= 1
        if self.depth != 0:
            return
        repo = next((v.strip("/") for v in self.hrefs if REPO.fullmatch(v.strip("/"))), None)
        if not repo:
            return
        desc = " ".join("".join(self.bits).split())
        match = GAIN.search(desc)
        self.results.append({"repo": repo, "newStars": int(match.group(1).replace(",", "")) if match else None,
                             "sourceWindowLabel": match.group(2).lower() if match else None})

    def handle_data(self, text):
        if self.depth:
            self.bits.append(text)


def parse_trending(html: str, window: str) -> list[dict]:
    if window not in WINDOWS:
        raise ValueError("unknown Trending window")
    parser = TrendingParser()
    parser.feed(html)
    if not parser.results:
        raise ValueError("GitHub Trending article markup missing; cannot silently fall back")
    return [{"repo": e["repo"], "newStars": e["newStars"],
             "sourceWindowLabel": e["sourceWindowLabel"] if e["sourceWindowLabel"] == WINDOWS[window] else None}
            for e in parser.results]


def fetch_json(repo: str) -> dict:
    try:
        p = subprocess.run(["gh", "api", "repos/" + repo], capture_output=True, text=True, timeout=25)
        if p.returncode:
            return {"totalStars": None, "licenseMetadata": None, "apiStatus": "FAILED", "note": p.stderr.strip()[:200]}
        record = json.loads(p.stdout)
        return {"totalStars": record.get("stargazers_count"), "licenseMetadata": (record.get("license") or {}).get("spdx_id"),
                "pushedAt": record.get("pushed_at"), "headBranch": record.get("default_branch"), "apiStatus": "OK"}
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        return {"totalStars": None, "licenseMetadata": None, "apiStatus": "FAILED", "note": str(e)[:160]}


def live_observation(limit: int) -> dict:
    observed = datetime.now(timezone.utc).isoformat()
    windows = []
    repos: set[str] = set()
    for win in WINDOWS:
        url = GH + "/trending?since=" + win
        response = subprocess.run(
            ["curl", "--fail", "--location", "--silent", "--show-error",
             "--connect-timeout", "10", "--max-time", "45", "--retry", "2",
             "--user-agent", "Mozilla/5.0 Ordivon-Radar/1.0", url],
            capture_output=True, timeout=130)
        if response.returncode != 0 or len(response.stdout) < 1000:
            raise RuntimeError("official GitHub Trending " + win + " failed: " +
                               response.stderr.decode("utf-8", errors="replace")[-250:])
        body = response.stdout[:2_000_000].decode("utf-8", errors="replace")
        records = parse_trending(body, win)[:limit]
        windows.append({"window": win, "sourceUrl": url, "retrievedAt": datetime.now(timezone.utc).isoformat(),
                        "sourceBodySha256": "sha256:" + hashlib.sha256(response.stdout).hexdigest(),
                        "entries": records})
        repos.update(x["repo"] for x in records)
    return {"kind": "ordivon.github-trending-observation-r1", "snapshotDay": observed[:10],
            "observedAt": observed, "origin": "github-official-trending-pages",
            "windows": windows, "repositories": {r: fetch_json(r) for r in sorted(repos)}}


def previous_repositories(history: Path, today: date, out: Path) -> set[str]:
    seen: set[str] = set()
    if not history.is_dir():
        return seen
    for file in history.glob("*.json"):
        if file.resolve() == out.resolve():
            continue
        try:
            value = json.loads(file.read_text(encoding="utf-8"))
            if value.get("kind") != "ordivon.github-radar-candidates-r1":
                continue
            d = date.fromisoformat(value["snapshotDay"])
            if not timedelta(0) < today - d <= timedelta(days=7):
                continue
            seen.update(x["repo"] for x in value.get("candidates", []))
        except (ValueError, KeyError, TypeError, OSError):
            continue
    return seen


def normalize(raw: dict, history: set[str]) -> dict:
    if raw.get("kind") != "ordivon.github-trending-observation-r1":
        raise ValueError("input is not a declared GitHub Trending observation")
    day = date.fromisoformat(raw["snapshotDay"])
    indexed: dict[str, dict] = {}
    for window in raw["windows"]:
        win = window["window"]
        if win not in WINDOWS or window.get("sourceUrl") != GH + "/trending?since=" + win:
            raise ValueError("not an official window URL")
        for item in window.get("entries", []):
            repo = item["repo"]
            if not REPO.fullmatch(repo):
                raise ValueError("invalid GitHub repository name")
            gain = item.get("newStars")
            if gain is not None and (type(gain) is not int or gain < 0 or item.get("sourceWindowLabel") != WINDOWS[win]):
                raise ValueError("star increment has wrong window or an unverified metric")
            c = indexed.setdefault(repo, {"repo": repo, "url": GH + "/" + repo, "officialTrending": [],
                                          "origin": raw["origin"]})
            c["officialTrending"].append({"window": win, "stars": gain, "label": item.get("sourceWindowLabel"),
                                           "sourceUrl": window["sourceUrl"], "retrievedAt": window["retrievedAt"],
                                           "sourceBodySha256": window.get("sourceBodySha256")})
    for repo, value in indexed.items():
        api = raw.get("repositories", {}).get(repo, {})
        value["totalStars"] = api.get("totalStars")
        value["totalStarsSource"] = "GitHub REST repository metadata" if api.get("apiStatus") == "OK" else None
        value["licenseMetadata"] = api.get("licenseMetadata")
        value["metadataCurrentness"] = api.get("pushedAt")
        value["apiStatus"] = api.get("apiStatus", "UNVERIFIED")
        value["licenseVerification"] = "METADATA_ONLY_NOT_LICENSE_FILE"
        value["repeatedWithin7Days"] = repo in history
        value["recommendationDisposition"] = "REVIEW_CHANGE_BEFORE_REPEAT" if repo in history else "NEW_CANDIDATE"
        value["adoptionStanding"] = "DISCOVERY_ONLY"
    return {"kind": "ordivon.github-radar-candidates-r1", "snapshotDay": day.isoformat(),
            "observedAt": raw["observedAt"], "origin": raw["origin"],
            "candidates": [indexed[k] for k in sorted(indexed)],
            "nonClaims": ["Official Trending display windows are not UTC rolling windows",
                          "No arbitrary GitHub API historical star delta inferred",
                          "Discovery candidates do not confer software installation or adoption"]}


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
                      "standing": "DISCOVERY_ONLY"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
