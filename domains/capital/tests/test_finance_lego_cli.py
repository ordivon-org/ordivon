"""Agent-facing CLI consumes only bounded JSON and has no trading authority."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/finance_lego.py"


def _invoke(operation: str, request: dict) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(
        [sys.executable, str(CLI), operation],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
    )


def _frozen_plan_input() -> dict:
    identity = "sha256:" + "a" * 64
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "hypothesisId": "finance-momentum-prospective-r4",
        "effectBoundary": "RESEARCH_ONLY",
        "frozenAt": "2026-01-01T12:00:00+00:00",
        "codeRevision": "a" * 40,
        "configDigest": identity,
        "environmentDigest": identity,
        "trialsPlanned": 2,
        "baselineId": "total-return-index",
        "metricDefinition": "benchmark-relative net growth",
        "partitions": {
            "train": {"start": "2020-01-01", "end": "2022-12-31"},
            "validation": {"start": "2023-01-01", "end": "2025-12-31"},
            "holdout": {"start": "2026-01-02", "end": "2026-06-30"},
        },
        "historicalSources": [{
            "sourceId": "provider:total-return-index",
            "snapshotDigest": identity,
            "observedThrough": "2025-12-31T20:00:00+00:00",
            "availableAt": "2026-01-01T06:00:00+00:00",
        }],
    }


def test_agent_cli_freezes_then_assesses_without_order_authority() -> None:
    result = _invoke("freeze-experiment", _frozen_plan_input())
    assert result.returncode == 0, result.stderr
    frozen = json.loads(result.stdout)
    assert frozen["planDigest"].startswith("sha256:")
    assessed = _invoke("assess-holdout", {"frozen": frozen, "result": None})
    assert assessed.returncode == 0, assessed.stderr
    evidence = json.loads(assessed.stdout)
    assert evidence["standing"] == "UNKNOWN"
    assert evidence["externalWriteAllowed"] is False
    assert evidence["capitalAllocationAuthorized"] is False


def test_agent_cli_rejects_nonresearch_effect_without_json_receipt() -> None:
    result = _invoke("freeze-experiment", {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "effectBoundary": "LIVE",
    })
    assert result.returncode == 2
    assert result.stdout == ""
    assert "INVALID_FINANCE_LEGO_INPUT" in result.stderr


def test_agent_cli_rejects_duplicate_keys_as_ambiguous_authority() -> None:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    raw = '{"quotes":[], "feeBps":"0", "feeBps":"10000"}'
    output = subprocess.run(
        [sys.executable, str(CLI), "freeze-experiment"],
        input=raw, text=True, capture_output=True, cwd=ROOT, env=env, check=False,
    )
    assert output.returncode == 2
    assert output.stdout == ""
    assert "duplicate JSON key" in output.stderr
