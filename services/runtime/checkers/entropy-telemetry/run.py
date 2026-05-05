"""Entropy Telemetry — measures and tracks system entropy metrics.

Counts files, imports, documentation health, debt, and checker coverage.
Calculates velocity from historical data. Logs to entropy-telemetry.jsonl.

Always advisory (escalation). Never blocks.
"""

from __future__ import annotations
import json, re, sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_FILE = ROOT / "docs" / "governance" / "entropy-telemetry.jsonl"
DOC_REGISTRY = ROOT / "docs" / "governance" / "document-registry.jsonl"
DEBT_LEDGER = ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl"

# ── Configuration ───────────────────────────────────────────────────

# Directories scanned for file counts
SCAN_SPEC = {
    "docs": ROOT / "docs",
    "src": ROOT / "src",
    "tests": ROOT / "tests",
    "checkers": ROOT / "checkers",
    "scripts": ROOT / "scripts",
    "domains": ROOT / "domains",
    "packs": ROOT / "packs",
}

# File extensions counted as "source"
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml"}

# Directories excluded from line counts (vendored, generated)
EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv",
                ".archive", ".mypy_cache", ".pytest_cache", "dist", "build"}

# ── Data types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class TelemetrySnapshot:
    timestamp: str
    metrics: dict  # metric_name -> {value, unit}

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

# ── Measurement functions ───────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _count_files(directory: Path, exts: set = None) -> int:
    """Count files in directory, optionally filtered by extension."""
    if not directory.exists():
        return 0
    count = 0
    for f in directory.rglob("*"):
        if any(ex in f.parts for ex in EXCLUDE_DIRS):
            continue
        if f.is_file():
            if exts is None or f.suffix in exts:
                count += 1
    return count

def _count_lines(directory: Path) -> int:
    """Approximate line count (fast — just count newlines)."""
    if not directory.exists():
        return 0
    total = 0
    for f in directory.rglob("*"):
        if any(ex in f.parts for ex in EXCLUDE_DIRS):
            continue
        if f.is_file() and f.suffix in SOURCE_EXTS:
            try:
                total += len(f.read_text(encoding="utf-8", errors="replace").split("\n"))
            except Exception:
                pass
    return total

def _count_imports() -> tuple[int, int]:
    """Count cross-boundary imports and unique import sources in Python files."""
    cross = 0
    unique_sources = set()
    boundary_prefixes = ("domains.", "packs.", "apps.", "shared.", "src.")
    search_dirs = [ROOT / "src", ROOT / "domains", ROOT / "packs",
                   ROOT / "scripts", ROOT / "checkers"]
    import_pat = re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE)

    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if any(ex in f.parts for ex in EXCLUDE_DIRS):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for m in import_pat.finditer(text):
                mod = m.group(1)
                unique_sources.add(mod)
                for prefix in boundary_prefixes:
                    if mod.startswith(prefix) and not mod.startswith("src.ordivon_verify"):
                        cross += 1
                        break
    return cross, len(unique_sources)

def _analyze_doc_registry() -> dict:
    """Analyze document-registry.jsonl for freshness and cross-references."""
    if not DOC_REGISTRY.exists():
        return {"entries": 0, "stale": 0, "missing_freshness": 0, "cross_refs": 0}

    entries = []
    with open(DOC_REGISTRY) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    stale = 0
    missing_freshness = 0
    cross_refs = 0
    now = datetime.now(timezone.utc)

    for e in entries:
        if "last_verified" not in e:
            missing_freshness += 1
        else:
            try:
                lv = datetime.fromisoformat(e["last_verified"].replace("Z", "+00:00"))
                stale_days = e.get("stale_after_days", 90)
                if (now - lv).days > stale_days:
                    stale += 1
            except (ValueError, TypeError):
                pass

        cross_refs += len(e.get("related_docs", []))
        cross_refs += len(e.get("related_ledgers", []))
        cross_refs += len(e.get("related_receipts", []))

    return {
        "entries": len(entries),
        "stale": stale,
        "missing_freshness": missing_freshness,
        "cross_refs": cross_refs,
    }

def _count_debt_entries() -> int:
    """Count open debt entries in verification-debt-ledger.jsonl."""
    if not DEBT_LEDGER.exists():
        return 0
    count = 0
    with open(DEBT_LEDGER) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("status", "open") not in ("resolved", "closed", "wontfix"):
                    count += 1
            except json.JSONDecodeError:
                pass
    return count

# ── Velocity calculation ────────────────────────────────────────────

def _load_history() -> list[dict]:
    """Load previous telemetry snapshots."""
    if not TELEMETRY_FILE.exists():
        return []
    snapshots = []
    with open(TELEMETRY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    snapshots.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return snapshots

def _calc_velocity(current: dict, history: list[dict]) -> dict:
    """Calculate velocity (% change per 30 days) for each metric."""
    if len(history) < 2:
        return {}

    # Find oldest snapshot within 90 days
    now = datetime.now(timezone.utc)
    cutoff = None
    for s in reversed(history):
        try:
            t = datetime.fromisoformat(s["timestamp"].replace("Z", "+00:00"))
            if (now - t).days <= 90:
                cutoff = s
                break
        except (ValueError, TypeError, KeyError):
            pass

    if cutoff is None:
        return {}

    velocity = {}
    try:
        t_cutoff = datetime.fromisoformat(cutoff["timestamp"].replace("Z", "+00:00"))
        delta = now - t_cutoff
        # Require at least 24 hours between snapshots for meaningful velocity
        if delta.total_seconds() < 86400:  # 24 hours
            return {}
        days = max(delta.days, 1)
    except (ValueError, TypeError):
        return {}

    prev_metrics = cutoff.get("metrics", {})
    for name, cur_data in current.items():
        cur_val = cur_data["value"]
        prev_data = prev_metrics.get(name, {})
        prev_val = prev_data.get("value", cur_val)
        if prev_val == 0:
            continue
        pct_change = ((cur_val - prev_val) / prev_val) * 100
        pct_per_30d = pct_change * (30 / days)
        velocity[name] = {
            "pct_change": round(pct_change, 2),
            "pct_per_30d": round(pct_per_30d, 2),
            "days": days,
            "previous_value": prev_val,
        }

    return velocity

# ── Main ────────────────────────────────────────────────────────────

def run() -> CheckerResult:
    timestamp = _now_iso()

    # ── Size metrics ────────────────────────────────────────────
    metrics = {}
    for name, path in SCAN_SPEC.items():
        metrics[f"{name}_files"] = {
            "value": _count_files(path),
            "unit": "files",
        }

    total_files = sum(m["value"] for k, m in metrics.items() if k.endswith("_files"))
    metrics["total_files"] = {"value": total_files, "unit": "files"}

    # Lines (expensive — only count src/ and domains/)
    metrics["src_lines"] = {
        "value": _count_lines(ROOT / "src") + _count_lines(ROOT / "domains"),
        "unit": "lines",
    }

    # ── Checker count ───────────────────────────────────────────
    checkers_dir = ROOT / "checkers"
    checker_count = 0
    if checkers_dir.exists():
        for p in checkers_dir.iterdir():
            if p.is_dir() and (p / "CHECKER.md").exists():
                checker_count += 1
    metrics["checkers_count"] = {"value": checker_count, "unit": "checkers"}

    # ── Complexity metrics ──────────────────────────────────────
    cross_imports, unique_sources = _count_imports()
    metrics["cross_boundary_imports"] = {"value": cross_imports, "unit": "imports"}
    metrics["unique_import_sources"] = {"value": unique_sources, "unit": "modules"}

    # ── Doc registry analysis ───────────────────────────────────
    doc = _analyze_doc_registry()
    metrics["doc_registry_entries"] = {"value": doc["entries"], "unit": "entries"}
    metrics["stale_docs"] = {"value": doc["stale"], "unit": "docs"}
    metrics["docs_missing_freshness"] = {"value": doc["missing_freshness"], "unit": "docs"}
    metrics["cross_references"] = {"value": doc["cross_refs"], "unit": "refs"}

    # ── Health metrics ──────────────────────────────────────────
    metrics["debt_entries"] = {"value": _count_debt_entries(), "unit": "entries"}

    # Coverage ratio: checkers / sqrt(total_files)
    import math
    if total_files > 0:
        coverage = checker_count / math.sqrt(total_files)
    else:
        coverage = 0.0
    metrics["checker_coverage_ratio"] = {"value": round(coverage, 4), "unit": "ratio"}

    # ── Velocity ────────────────────────────────────────────────
    history = _load_history()
    velocity = _calc_velocity(metrics, history)

    # ── Build snapshot ──────────────────────────────────────────
    snapshot = {
        "timestamp": timestamp,
        "metrics": metrics,
        "velocity": velocity,
    }

    # Append to telemetry file
    mode = "a" if TELEMETRY_FILE.exists() else "w"
    with open(TELEMETRY_FILE, mode) as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    # ── Findings ────────────────────────────────────────────────
    findings = []
    stats = {
        "total_files": total_files,
        "checkers": checker_count,
        "stale_docs": doc["stale"],
        "debt_entries": metrics["debt_entries"]["value"],
        "cross_imports": cross_imports,
        "coverage_ratio": round(coverage, 4),
    }

    findings.append(f"Total files: {total_files} | Checkers: {checker_count}")
    findings.append(f"Stale docs: {doc['stale']} | Debt entries: {metrics['debt_entries']['value']}")
    findings.append(f"Cross-boundary imports: {cross_imports} | Coverage ratio: {coverage:.4f}")

    if velocity:
        for name, v in velocity.items():
            pct = v["pct_per_30d"]
            if abs(pct) > 10:
                findings.append(
                    f"VELOCITY ALERT: {name} changing at {pct:+.1f}%/30d "
                    f"(threshold: ±10%)"
                )
        findings.append(f"Velocity tracked for {len(velocity)} metrics over "
                        f"{velocity.get(list(velocity.keys())[0] if velocity else '', {}).get('days', '?')} days")
    else:
        findings.append("Velocity: insufficient history (< 2 snapshots)")

    findings.append(f"Logged to {TELEMETRY_FILE}")

    # Always pass — telemetry is advisory
    return CheckerResult("pass", 0, findings, dict(stats))


if __name__ == "__main__":
    r = run()
    for f in r.findings:
        print(f"  {f}")
    print(f"\nStats: {json.dumps(r.stats, indent=2)}")
    sys.exit(r.exit_code)
