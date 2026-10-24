"""Native Prometheus scrape timeouts must actually admit Blackbox's declared time budget."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_yaml(path: Path) -> dict:
    # Reuse the repository's existing yq, not a custom YAML parser.
    return json.loads(subprocess.check_output(
        ["/usr/bin/yq", "-o=json", ".", str(path)], text=True,
    ))


def _seconds(value: str) -> int:
    assert value.endswith("s"), value
    return int(value.removesuffix("s"))


def test_dualstack_blackbox_scrapes_have_real_module_timeout_headroom() -> None:
    prometheus = _read_yaml(ROOT / "config/prometheus/prometheus.yml")
    blackbox = _read_yaml(ROOT / "config/blackbox/blackbox.yml")
    jobs = {job["job_name"]: job for job in prometheus["scrape_configs"]}
    for family in ("ipv4", "ipv6"):
        job = jobs[f"blackbox-http-{family}"]
        module = blackbox["modules"][f"http_2xx_{family}"]
        # A successful 4.5s Prometheus scrape cannot prove a configured 10s probe.
        assert "scrape_interval" in job, (family, job)
        assert "scrape_timeout" in job, (family, job)
        interval = _seconds(job["scrape_interval"])
        scrape_budget = _seconds(job["scrape_timeout"])
        module_budget = _seconds(module["timeout"])
        assert scrape_budget >= module_budget + 1, (family, scrape_budget, module_budget)
        assert interval >= scrape_budget + 1, (family, interval, scrape_budget)
