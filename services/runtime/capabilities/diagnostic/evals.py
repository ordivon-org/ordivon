from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvalCapability:
    """Diagnostic read adapter for regression eval summaries."""

    abstraction_type = "diagnostic"

    def __init__(self, runs_dir: str | Path = "data/evals/runs") -> None:
        self.runs_dir = Path(runs_dir)

    def get_latest(self) -> dict[str, Any]:
        if not self.runs_dir.exists():
            raise FileNotFoundError("Evals directory not found")

        run_files = list(self.runs_dir.glob("*.json"))
        if not run_files:
            raise FileNotFoundError("No evaluation runs found")

        latest_run_file = max(run_files, key=lambda path: (path.stat().st_mtime, path.name))
        with latest_run_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        summary = data.get("summary", {})
        gate_decision = "PASS"
        if summary.get("parse_failure_rate", 0) > 0.05 or summary.get("avg_total_score", 0) < 0.8:
            gate_decision = "FAIL"

        cases = []
        for case in data.get("cases", []):
            scores = case.get("scores", {})
            notes = self._normalize_notes(case.get("notes", []))

            sanitized_scores = {}
            for key, value in scores.items():
                if key == "notes":
                    notes.extend(self._normalize_notes(value))
                    continue
                if isinstance(value, (int, float)):
                    sanitized_scores[key] = float(value)
                else:
                    notes.append(f"{key}: {value}")

            cases.append(
                {
                    "case_id": case["case_id"],
                    "status": case["status"],
                    "risk_decision": case.get("risk_decision", "unknown"),
                    "scores": sanitized_scores,
                    "notes": notes,
                }
            )

        return {
            "run_id": data["run_id"],
            "timestamp": data["timestamp"],
            "provider": data["provider"],
            "dataset": data["dataset"],
            "summary": summary,
            "cases": cases,
            "gate_decision": gate_decision,
        }

    def _normalize_notes(self, raw_notes: Any) -> list[str]:
        if raw_notes in (None, "", [], {}):
            return []

        if isinstance(raw_notes, str):
            candidate = raw_notes.strip()
            if candidate in {"notes: []", "[]"}:
                return []
            return [candidate]

        if isinstance(raw_notes, list):
            cleaned: list[str] = []
            for item in raw_notes:
                cleaned.extend(self._normalize_notes(item))
            return cleaned

        return [str(raw_notes)]
