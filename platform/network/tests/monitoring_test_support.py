"""Shared source-bound native monitoring test inputs, no production effects."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/monitoring-sourcecut-preflight.py"


def _load():
    spec = importlib.util.spec_from_file_location("network_monitor_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPT.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _native_target_fixture():
    from urllib.parse import urlencode
    owner = _load()
    declared = owner._all_scrape_jobs(ROOT / "config")
    pool_data = {"data": {"scrapePools": [job["job_name"] for job in declared]}}
    active = []
    for job in declared:
        target = job["static_configs"][0]["targets"][0]
        module = (job.get("params") or {}).get("module")
        if module:
            exporter = next(
                rule["replacement"] for rule in job["relabel_configs"]
                if rule.get("target_label") == "__address__"
            )
            url = f"http://{exporter}/probe?" + urlencode(
                {"module": module[0], "target": target}
            )
        else:
            url = f"http://{target}/metrics"
        active.append({
            "scrapePool": job["job_name"],
            "labels": {"job": job["job_name"], "instance": target},
            "discoveredLabels": {"__address__": target, **({"__param_module": module[0]} if module else {})},
            "scrapeUrl": url,
        })
    target_data = {"data": {"activeTargets": active}}
    return owner, declared, pool_data, target_data
