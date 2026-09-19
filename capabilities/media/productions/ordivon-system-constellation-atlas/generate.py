#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = OUT / "source"
RENDER = OUT / "render"
SOURCE.mkdir(parents=True, exist_ok=True)
RENDER.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path("/root/projects")
EXTRA_REPOS = [Path("/root/workstation-lab")]

GROUP_ORDER = ["execution", "knowledge", "creative", "external", "other"]
GROUP_LABELS = {
    "execution": "EXECUTION / COORDINATION",
    "knowledge": "KNOWLEDGE / RESEARCH",
    "creative": "CREATIVE / CULTURAL",
    "external": "EXTERNAL / DISTRIBUTION",
    "other": "OTHER RETAINED SURFACES",
}
GROUP_BY_NAME = {
    "ordivon-runtime": "execution",
    "ordivon-host-v2": "execution",
    "ordivon-harness": "execution",
    "ordivon-next": "execution",
    "ordivon-workstation-v2": "execution",
    "ordivon-artifact-v2": "execution",
    "workstation-lab": "execution",
    "ordivon-research-v2": "knowledge",
    "ordivon-data-v2": "knowledge",
    "ordivon-media": "creative",
    "ordivon-game": "creative",
    "ordivon-web": "creative",
    "ordivon-distribution-v2": "external",
    "ordivon-network-v2": "external",
    "ordivon-market-capital-next": "external",
}


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def discover() -> list[dict]:
    repos = [p for p in sorted(PROJECT_ROOT.glob("ordivon-*")) if (p / ".git").exists() or (p / ".git").is_file()]
    repos += [p for p in EXTRA_REPOS if p.exists()]
    rows = []
    for repo in repos:
        try:
            head = git(repo, "rev-parse", "HEAD")
            root = Path(git(repo, "rev-parse", "--show-toplevel"))
            status = git(repo, "status", "--porcelain=v1", "--untracked-files=no")
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        name = root.name
        group = GROUP_BY_NAME.get(name, "other")
        rows.append({
            "name": name,
            "path": str(root),
            "head": head,
            "dirty_tracked": bool(status),
            "group": group,
        })
    dedup = {r["path"]: r for r in rows}
    return sorted(dedup.values(), key=lambda r: (GROUP_ORDER.index(r["group"]), r["name"]))


def place(rows: list[dict]) -> None:
    grouped: dict[str, list[dict]] = {g: [] for g in GROUP_ORDER}
    for row in rows:
        grouped[row["group"]].append(row)
    centers = {
        "execution": (-72.0, 28.0),
        "knowledge": (58.0, 34.0),
        "creative": (-22.0, -36.0),
        "external": (77.0, -27.0),
        "other": (0.0, 0.0),
    }
    for group in GROUP_ORDER:
        items = grouped[group]
        cx, cy = centers[group]
        n = max(1, len(items))
        radius = 12.0 + min(18.0, n * 1.8)
        for i, row in enumerate(items):
            digest = hashlib.sha256(row["name"].encode()).digest()
            phase = int.from_bytes(digest[:2], "big") / 65535.0 * 0.8
            angle = 2 * math.pi * ((i + phase) / n)
            row["x"] = round(cx + radius * math.cos(angle), 5)
            row["y"] = round(cy + radius * math.sin(angle), 5)


def write_json(rows: list[dict], observed_at: str) -> None:
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.creative-work.source-snapshot",
        "workId": "media:ordivon-system-constellation-atlas",
        "observedAt": observed_at,
        "coordinateSystem": "abstract Ordivon conceptual plane; coordinates are layout positions and are not geographic claims",
        "selection": "local Git repositories under /root/projects matching ordivon-* plus /root/workstation-lab when readable",
        "repositories": rows,
    }
    (SOURCE / "repositories.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    features = []
    for row in rows:
        props = {k: v for k, v in row.items() if k not in {"x", "y", "group"}}
        props["cluster"] = row["group"]
        props["head_short"] = row["head"][:9]
        props["coordinate_semantics"] = "abstract-layout-not-geographic"
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row["x"], row["y"]]},
            "properties": props,
        })
    geo = {"type": "FeatureCollection", "name": "ordivon_repositories", "features": features}
    (SOURCE / "repositories.geojson").write_text(json.dumps(geo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_svg(rows: list[dict], observed_at: str) -> None:
    width, height = 1600, 1000
    def px(x: float) -> float: return 800 + x * 4.25
    def py(y: float) -> float: return 500 - y * 4.25

    group_r = {"execution": 118, "knowledge": 108, "creative": 105, "external": 112, "other": 80}
    centers = {"execution": (-72.0, 28.0), "knowledge": (58.0, 34.0), "creative": (-22.0, -36.0), "external": (77.0, -27.0), "other": (0.0, 0.0)}

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="1600" height="1000" fill="#0b0d10"/>
<rect x="55" y="55" width="1490" height="890" rx="28" fill="none" stroke="#2e353c" stroke-width="2"/>
<text x="88" y="120" font-family="DejaVu Sans, sans-serif" font-size="44" font-weight="700" fill="#f2f3f4" letter-spacing="3">ORDIVON / SYSTEM CONSTELLATION</text>
<text x="90" y="157" font-family="DejaVu Sans Mono, monospace" font-size="17" fill="#88919b">LOCAL REPOSITORY SNAPSHOT · ABSTRACT CARTOGRAPHIC WORK · {html.escape(observed_at)}</text>
<line x1="90" y1="184" x2="1510" y2="184" stroke="#343b43" stroke-width="1"/>
''']

    for group in GROUP_ORDER[:-1]:
        cx, cy = centers[group]
        x, y = px(cx), py(cy)
        r = group_r[group]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" stroke="#303841" stroke-width="1.5" stroke-dasharray="5 9"/>')
        parts.append(f'<text x="{x-r:.1f}" y="{y-r-18:.1f}" font-family="DejaVu Sans Mono, monospace" font-size="13" fill="#69747f" letter-spacing="1.5">{GROUP_LABELS[group]}</text>')

    # faint non-semantic visual spokes only within owner group, explicitly decorative
    for group in GROUP_ORDER:
        items = [r for r in rows if r["group"] == group]
        if not items: continue
        cx = sum(px(r["x"]) for r in items) / len(items)
        cy = sum(py(r["y"]) for r in items) / len(items)
        for r in items:
            parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{px(r["x"]):.1f}" y2="{py(r["y"]):.1f}" stroke="#20262c" stroke-width="1"/>')

    for row in rows:
        x, y = px(row["x"]), py(row["y"])
        ring = "#f2f3f4" if not row["dirty_tracked"] else "#c7cbd0"
        fill = "#0b0d10"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{fill}" stroke="{ring}" stroke-width="2"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="#f2f3f4"/>')
        name = html.escape(row["name"])
        head = html.escape(row["head"][:9])
        parts.append(f'<text x="{x+14:.1f}" y="{y-3:.1f}" font-family="DejaVu Sans, sans-serif" font-size="16" fill="#dfe2e5">{name}</text>')
        parts.append(f'<text x="{x+14:.1f}" y="{y+16:.1f}" font-family="DejaVu Sans Mono, monospace" font-size="11" fill="#68737e">{head}</text>')

    parts.append(f'''<g transform="translate(90 856)">
<line x1="0" y1="0" x2="1420" y2="0" stroke="#343b43"/>
<text x="0" y="38" font-family="DejaVu Sans Mono, monospace" font-size="14" fill="#949da6">{len(rows)} retained local Git repositories · point position = deterministic composition, not dependency or geography</text>
<text x="0" y="67" font-family="DejaVu Sans Mono, monospace" font-size="13" fill="#65707a">GPKG companion keeps queryable source identity: repository path, full HEAD, cluster, tracked-dirty observation.</text>
</g>
</svg>''')
    (RENDER / "ordivon-system-constellation.svg").write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    observed_at = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).replace(microsecond=0).isoformat()
    rows = discover()
    if len(rows) < 5:
        raise SystemExit(f"refusing thin snapshot: only {len(rows)} repositories discovered")
    place(rows)
    write_json(rows, observed_at)
    write_svg(rows, observed_at)
    print(json.dumps({"repositories": len(rows), "observedAt": observed_at, "groups": {g: sum(1 for r in rows if r['group']==g) for g in GROUP_ORDER}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
