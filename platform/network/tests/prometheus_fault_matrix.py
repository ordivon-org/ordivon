"""Finite observation-role differential test using the real Prometheus engine.

The oracle is a conjunction of named role requirements, not PromQL arithmetic.
All series are synthetic, with separate fixture state per vector.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "config/prometheus/consumer.rules.yml"
ROLES = (
    "blackbox-vpn-pypi",
    "blackbox-scoped-codex-mcp",
    "blackbox-scoped-claude-api",
    "blackbox-http-ipv4",
    "blackbox-http-ipv4-alternate",
)
ALERTS = (
    ("NetworkCorrelatedConsumerOutage", (0, 0, 0, None, None)),
    ("NetworkSharedUnderlaySuspected", (0, 0, 0, 0, 0)),
    ("NetworkVPNPathFailureWithDirectHealthy", (0, 0, 0, 1, 1)),
)
STATES = {"failed": (0,), "healthy": (1,), "missing": (),
          "duplicate_failed": (0, 0), "duplicate_healthy": (1, 1)}


def vectors():
    # Exhaust every healthy/failed/missing combination; additionally cover
    # every pair of roles and all five states in two meaningful contexts.
    basic = ("failed", "healthy", "missing")
    cases = set(itertools.product(basic, repeat=len(ROLES)))
    for background in (("failed",) * 5, ("failed",) * 3 + ("healthy",) * 2):
        for i, j in itertools.combinations(range(len(ROLES)), 2):
            for a, b in itertools.product(STATES, repeat=2):
                case = list(background)
                case[i], case[j] = a, b
                cases.add(tuple(case))
    # Check the promised coverage independently of generation order.
    for i, j in itertools.combinations(range(len(ROLES)), 2):
        if {(case[i], case[j]) for case in cases} != set(itertools.product(STATES, repeat=2)):
            raise AssertionError(f"missing role-pair coverage: {i}, {j}")
    if not set(itertools.product(basic, repeat=len(ROLES))) <= cases:
        raise AssertionError("missing exhaustive basic state combination")
    return sorted(cases)


def fixture(rules=RULES):
    tests = []
    for case in vectors():
        inputs = []
        for role, state in zip(ROLES, case, strict=True):
            for index, value in enumerate(STATES[state]):
                inputs.append({
                    "series": f'probe_success{{job="{role}",instance="synthetic-{index}"}}',
                    "values": f"{value}x4",
                })
        checks = []
        for alert, required in ALERTS:
            expected = all(want is None or STATES[state] == (want,)
                           for state, want in zip(case, required, strict=True))
            checks.append({
                "expr": f'count(ALERTS{{alertname="{alert}",alertstate="firing"}}) or vector(0)',
                "eval_time": "4m",
                "exp_samples": [{"labels": "{}", "value": int(expected)}],
            })
        tests.append({"name": "/".join(case), "interval": "1m",
                      "input_series": inputs, "promql_expr_test": checks})
    return {"rule_files": [str(rules.resolve())], "evaluation_interval": "1m",
            "tests": tests}


def run(rules=RULES):
    data = fixture(rules)
    print(f"NETWORK_FAULT_MATRIX vectors={len(data['tests'])} "
          f"assertions={len(data['tests']) * len(ALERTS)}", flush=True)
    with tempfile.TemporaryDirectory(prefix="network-fault-matrix-") as tmp:
        path = Path(tmp) / "matrix.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        subprocess.run(["promtool", "test", "rules", str(path)], check=True)


if __name__ == "__main__":
    run()

