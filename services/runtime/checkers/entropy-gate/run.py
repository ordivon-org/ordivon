"""Entropy Gate — enforces structural entropy ceilings.

Reads the latest telemetry snapshot and checks against hard constraints:
file ceiling, import depth, freshness SLO, coverage minimum, growth velocity.

Hard gate: BLOCKS when constraints are violated.
"""

from __future__ import annotations
import json, re, math, sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TELEMETRY_FILE = ROOT / "docs" / "governance" / "entropy-telemetry.jsonl"

# ── Gate definitions ────────────────────────────────────────────────
# (name, metric_key, threshold, operator, hardness, description)
# operator: "lt" = less than, "gt" = greater than
GATES = [
    ("file_ceiling", "total_files", 2500, "lt",
     "hard", "Total files must remain below 2500"),
    ("freshness_slo", "stale_docs_pct", 10.0, "lt",
     "degraded", "Stale docs must be <10% of registry"),
    ("coverage_minimum", "checker_coverage_ratio", 0.5, "gt",
     "degraded", "Checkers/sqrt(files) must stay above 0.5"),
    ("growth_velocity", "total_files_pct_30d", 10.0, "lt",
     "hard", "File growth must stay below 10%/month"),
    ("debt_ceiling", "debt_entries", 100, "lt",
     "degraded", "Open debt entries must stay below 100"),
]

# These directories are excluded from import depth analysis
EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv",
                ".archive", ".mypy_cache", ".pytest_cache", "dist", "build"}

# ── Data types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

# ── Telemetry reading ───────────────────────────────────────────────

def _load_latest_telemetry() -> dict | None:
    """Load the most recent telemetry snapshot."""
    if not TELEMETRY_FILE.exists():
        return None
    last = None
    with open(TELEMETRY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)
                except json.JSONDecodeError:
                    pass
    return last

# ── Import depth analysis ───────────────────────────────────────────

def _max_import_depth() -> int:
    """Calculate maximum import chain depth in the codebase.

    Builds a directed graph of imports and finds the longest path.
    Simple BFS-based approach — doesn't handle cycles (treats them as
    already-visited to avoid infinite loops).
    """
    import_graph: dict[str, set[str]] = {}
    import_pat = re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE)
    file_module_pat = re.compile(r"^(?:from|import)\s+([\w.]+)", re.MULTILINE)

    search_dirs = [ROOT / "src", ROOT / "domains", ROOT / "packs", ROOT / "checkers"]
    file_to_mods: dict[str, set[str]] = {}

    # Build module → file mapping (approximate)
    mod_to_file: dict[str, str] = {}

    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if any(ex in f.parts for ex in EXCLUDE_DIRS):
                continue
            try:
                rel = str(f.relative_to(ROOT))
                mod_name = rel.replace("/", ".").replace(".py", "")
                mod_to_file[mod_name] = rel
            except ValueError:
                continue

    # Build import graph
    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if any(ex in f.parts for ex in EXCLUDE_DIRS):
                continue
            try:
                rel = str(f.relative_to(ROOT))
                mod_name = rel.replace("/", ".").replace(".py", "")
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            deps = set()
            for m in import_pat.finditer(text):
                imported = m.group(1)
                if imported in mod_to_file:
                    deps.add(imported)
            if deps:
                import_graph[mod_name] = deps

    # Find longest path via topological ordering + DP
    # Since we may have cycles, use iterative deepening BFS
    if not import_graph:
        return 0

    max_depth = 0
    for start in import_graph:
        visited = {start}
        queue = deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            max_depth = max(max_depth, depth)
            if depth > 20:  # safety limit
                return depth
            for dep in import_graph.get(node, set()):
                if dep not in visited and dep in import_graph:
                    visited.add(dep)
                    queue.append((dep, depth + 1))

    return max_depth

# ── Gate evaluation ─────────────────────────────────────────────────

def _evaluate_gate(name: str, value: float, threshold: float,
                   operator: str, hardness: str, description: str,
                   metrics: dict) -> tuple[bool, str, str]:
    """Evaluate a single gate. Returns (pass, status, message)."""
    if operator == "lt":
        passed = value < threshold
        symbol = "<"
    else:  # "gt"
        passed = value > threshold
        symbol = ">"

    status = "PASS" if passed else ("BLOCKED" if hardness == "hard" else "DEGRADED")
    msg = (f"{name}: {value:.1f} {symbol} {threshold} → {status}"
           if not passed else
           f"{name}: {value:.1f} {symbol} {threshold} → OK")

    return passed, status, msg


def run() -> CheckerResult:
    telemetry = _load_latest_telemetry()
    if telemetry is None:
        return CheckerResult(
            "pass", 0,
            ["No telemetry data yet — entropy gates inactive (first run). "
             "Run entropy-telemetry checker to initialize."],
            {"error": "no_telemetry", "gates_active": False},
        )

    metrics_raw = telemetry.get("metrics", {})
    velocity = telemetry.get("velocity", {})

    # Build derived metrics
    derived = {}

    # Extract raw values
    for k, v in metrics_raw.items():
        derived[k] = v["value"]

    # Derived: stale_docs_pct
    entries = derived.get("doc_registry_entries", 1)
    stale = derived.get("stale_docs", 0)
    derived["stale_docs_pct"] = (stale / entries * 100) if entries > 0 else 0

    # Derived: total_files growth rate
    tv = velocity.get("total_files", {})
    derived["total_files_pct_30d"] = tv.get("pct_per_30d", 0)

    # Import depth
    max_depth = _max_import_depth()
    derived["max_import_depth"] = max_depth

    # ── Evaluate gates ──────────────────────────────────────────
    findings = []
    all_pass = True
    gate_results = {}

    for name, metric_key, threshold, operator, hardness, desc in GATES:
        value = derived.get(metric_key)
        if value is None:
            findings.append(f"{name}: metric '{metric_key}' not available")
            continue

        passed, status, msg = _evaluate_gate(
            name, value, threshold, operator, hardness, desc, metrics_raw
        )
        findings.append(msg)
        gate_results[name] = {"passed": passed, "status": status, "value": value}

        if not passed and hardness == "hard":
            all_pass = False

    # ── Import depth gate (separate — not in telemetry yet) ─────
    depth_passed = max_depth < 6
    depth_status = "OK" if depth_passed else "BLOCKED"
    findings.append(
        f"import_depth: max={max_depth} < 6 → {depth_status}"
    )
    if not depth_passed:
        all_pass = False

    # ── Summary ─────────────────────────────────────────────────
    blocked = sum(1 for g in gate_results.values() if g["status"] == "BLOCKED")
    degraded = sum(1 for g in gate_results.values() if g["status"] == "DEGRADED")

    stats = {
        "gates_total": len(GATES) + 1,
        "gates_passed": sum(1 for g in gate_results.values() if g["passed"]),
        "gates_blocked": blocked + (0 if depth_passed else 1),
        "gates_degraded": degraded,
        "snapshot_ts": telemetry.get("timestamp", "unknown"),
        "derived_metrics": {k: round(v, 2) if isinstance(v, float) else v
                            for k, v in derived.items()},
    }

    if not all_pass:
        findings.append(
            f"ENTROPY GATE: {blocked} BLOCKED, {degraded} DEGRADED "
            f"— system entropy exceeds governance thresholds"
        )

    return CheckerResult(
        "pass" if all_pass else "fail",
        0 if all_pass else 1,
        findings,
        dict(stats),
    )


if __name__ == "__main__":
    r = run()
    for f in r.findings:
        print(f"  {f}")
    print(f"\nStats: {json.dumps(r.stats, indent=2)}")
    sys.exit(r.exit_code)
