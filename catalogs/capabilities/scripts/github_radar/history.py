from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


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
