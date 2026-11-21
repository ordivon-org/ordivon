from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime

from .constants import GH, WINDOWS
from .parser import parse_trending


def fetch_json(repo: str) -> dict:
    try:
        p = subprocess.run(["gh", "api", "repos/" + repo], capture_output=True, text=True, timeout=25, check=False)
        if p.returncode:
            return {"totalStars": None, "licenseMetadata": None, "apiStatus": "FAILED", "note": p.stderr.strip()[:200]}
        record = json.loads(p.stdout)
        return {"totalStars": record.get("stargazers_count"), "licenseMetadata": (record.get("license") or {}).get("spdx_id"),
                "pushedAt": record.get("pushed_at"), "headBranch": record.get("default_branch"), "apiStatus": "OK"}
    except (OSError, subprocess.TimeoutExpired, ValueError) as e:
        return {"totalStars": None, "licenseMetadata": None, "apiStatus": "FAILED", "note": str(e)[:160]}


def live_observation(limit: int) -> dict:
    observed = datetime.now(UTC).isoformat()
    windows = []
    failures: dict[str, str] = {}
    repos: set[str] = set()
    # Try all three official pages. A temporary failure in one window must not
    # discard verified observations from the others or masquerade as full coverage.
    for win in WINDOWS:
        url = GH + "/trending?since=" + win
        try:
            response = subprocess.run(
                ["curl", "--fail", "--location", "--silent", "--show-error",
                 "--connect-timeout", "10", "--max-time", "45", "--retry", "2",
                 "--user-agent", "Mozilla/5.0 Ordivon-Radar/1.0", url],
                capture_output=True, timeout=130, check=False)
            if response.returncode != 0 or len(response.stdout) < 1000:
                raise RuntimeError(
                    "official GitHub Trending " + win + " fetch failed: " +
                    response.stderr.decode("utf-8", errors="replace")[-250:])
            body = response.stdout[:2_000_000].decode("utf-8", errors="replace")
            records = parse_trending(body, win)[:limit]
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            failures[win] = str(exc)[:300]
            continue
        windows.append({"window": win, "sourceUrl": url,
                        "retrievedAt": datetime.now(UTC).isoformat(),
                        "sourceBodySha256": "sha256:" + hashlib.sha256(response.stdout).hexdigest(),
                        "entries": records})
        repos.update(x["repo"] for x in records)
    if not windows:
        raise RuntimeError("all official GitHub Trending windows failed: " +
                           "; ".join(win + ": " + failures[win] for win in WINDOWS))
    return {"kind": "ordivon.github-trending-observation-r1", "snapshotDay": observed[:10],
            "observedAt": observed, "origin": "github-official-trending-pages",
            "windows": windows, "windowFailures": failures,
            "repositories": {r: fetch_json(r) for r in sorted(repos)}}
