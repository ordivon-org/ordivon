import json
from pathlib import Path

from capabilities.evals import EvalCapability
from capabilities.reports import ReportCapability


pass


def test_eval_capability_reads_latest_run_and_computes_gate(tmp_path: Path):
    earlier = tmp_path / "2026-04-17_run_011944.json"
    later = tmp_path / "2026-04-17_run_012001.json"

    earlier.write_text(
        json.dumps({
            "run_id": "run-earlier",
            "timestamp": "2026-04-17T01:19:44Z",
            "provider": "mock",
            "dataset": "core",
            "summary": {
                "total_cases": 1,
                "passed_cases": 1,
                "failed_cases": 0,
                "avg_total_score": 0.95,
                "parse_failure_rate": 0.0,
                "aggressive_action_rate": 0.0,
            },
            "cases": [],
        }),
        encoding="utf-8",
    )
    later.write_text(
        json.dumps({
            "run_id": "run-later",
            "timestamp": "2026-04-17T01:20:01Z",
            "provider": "mock",
            "dataset": "core",
            "summary": {
                "total_cases": 1,
                "passed_cases": 0,
                "failed_cases": 1,
                "avg_total_score": 0.5,
                "parse_failure_rate": 0.2,
                "aggressive_action_rate": 0.0,
            },
            "cases": [],
        }),
        encoding="utf-8",
    )

    capability = EvalCapability(runs_dir=tmp_path)
    result = capability.get_latest()

    assert result["run_id"] == "run-later"
    assert result["gate_decision"] == "FAIL"
