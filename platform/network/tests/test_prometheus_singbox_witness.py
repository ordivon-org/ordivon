"""A sampled Prometheus value is not necessarily a current, owner-scoped witness."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "acceptance/observability/live-prometheus-ready.sh"


def response(*, status: str = "success", job: str = "blackbox-singbox",
             name: str = "probe_success", instance: str = "127.0.0.1:28080",
             epoch: int | None = None, value: str = "1") -> dict:
    return {
        "status": status,
        "data": {
            "resultType": "vector",
            "result": [{
                "metric": {"__name__": name, "job": job, "instance": instance},
                "value": [int(time.time()) if epoch is None else epoch, value],
            }],
        },
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("valid", True),
        ("stale", False),
        ("wrong_job", False),
        ("wrong_metric", False),
        ("wrong_target", False),
        ("api_error", False),
        ("zero", False),
        ("malformed", False),
    ],
)
def test_live_prometheus_readiness_requires_current_matching_sample(
    tmp_path: Path, mutation: str, expected: bool
) -> None:
    payload = response()
    item = payload["data"]["result"][0]
    if mutation == "stale":
        item["value"][0] -= 600
    elif mutation == "wrong_job":
        item["metric"]["job"] = "unrelated-job"
    elif mutation == "wrong_metric":
        item["metric"]["__name__"] = "up"
    elif mutation == "wrong_target":
        item["metric"]["instance"] = "127.0.0.1:9999"
    elif mutation == "api_error":
        payload["status"] = "error"
    elif mutation == "zero":
        item["value"][1] = "0"
    elif mutation == "malformed":
        item["value"] = ["1"]  # no timestamp or valid sample shape
    response_file = tmp_path / "prometheus.json"
    response_file.write_text(json.dumps(payload), encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_curl = bin_dir / "curl"
    fake_curl.write_text('#!/bin/sh\ncat "$PROMETHEUS_TEST_RESPONSE"\n', encoding="utf-8")
    fake_curl.chmod(0o755)
    fake_sleep = bin_dir / "sleep"
    fake_sleep.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_sleep.chmod(0o755)
    result = subprocess.run(
        ["/usr/bin/bash", str(READY)],
        env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
             "PROMETHEUS_TEST_RESPONSE": str(response_file)},
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert (result.returncode == 0) is expected, (
        mutation, result.returncode, result.stdout, result.stderr[-300:]
    )


@pytest.mark.parametrize(("kind", "expected"), (("new", True), ("before_recovery", False)))
def test_recovered_singbox_needs_post_recovery_prometheus_witness(
    tmp_path: Path, kind: str, expected: bool
) -> None:
    """Run the actual process-recovery Bash consumer with fake external effects.

    Systemd, kill, HTTP, and clock are injected; no real process/network is touched.
    """
    now_ms = int(time.time() * 1000)
    recovery_ms = now_ms - 5000
    payload = response(epoch=(now_ms // 1000) - (1 if kind == "new" else 60))
    response_file = tmp_path / "prom.json"
    response_file.write_text(json.dumps(payload), encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    paths = {
        "systemctl": """#!/bin/sh
case "$*" in
  *NRestarts*)
    if [ ! -f "$FAKE_RESTARTS" ]; then
      touch "$FAKE_RESTARTS"
      echo 3
    else
      echo 4
    fi;;
  *MainPID*)
    if [ ! -f "$FAKE_PID" ]; then
      touch "$FAKE_PID"
      echo 4544
    else
      echo 4545
    fi;;
  *"is-active --quiet"*) exit 0;;
  *"is-active"*) echo active;;
  *) exit 65;;
esac
""",
        "kill": "#!/bin/sh\nexit 0\n",
        "sleep": "#!/bin/sh\nexit 0\n",
        "curl": """#!/bin/sh
case "$*" in
  *"/api/v1/query"*) cat "$PROMETHEUS_TEST_RESPONSE";;
  *"/probe?"*) printf 'probe_success 1\\n';;
  *"--proxy"*)
    case "$*" in
      *"--connect-timeout 1"*) exit 7;;
    esac
    exit 0;;
  *) exit 65;;
esac
""",
        "date": """#!/bin/sh
if [ "$*" = "+%s%3N" ]; then
  c=0
  if [ -f "$FAKE_DATE_CALLS" ]; then c=$(cat "$FAKE_DATE_CALLS"); fi
  c=$((c+1))
  echo "$c" > "$FAKE_DATE_CALLS"
  if [ "$c" = 1 ]; then echo "$((RECOVERY_FAKE_MS - 2000))"
  elif [ "$c" = 2 ]; then echo "$RECOVERY_FAKE_MS"
  else echo "$REAL_TEST_NOW_MS"
  fi
else
  /usr/bin/date "$@"
fi
""",
    }
    for name, source in paths.items():
        exe = bin_dir / name
        exe.write_text(source, encoding="utf-8")
        exe.chmod(0o755)
    bash_env = tmp_path / "functions.sh"
    # Bash kill is a builtin; use a sourced function, never signal a real PID.
    bash_env.write_text("kill() { :; }\n", encoding="utf-8")
    result = subprocess.run(
        ["/usr/bin/bash", str(ROOT / "acceptance/lifecycle/process-recovery.sh")],
        env={
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "PROMETHEUS_TEST_RESPONSE": str(response_file),
            "RECOVERY_FAKE_MS": str(recovery_ms),
            "REAL_TEST_NOW_MS": str(now_ms),
            "FAKE_DATE_CALLS": str(tmp_path / "date_calls"),
            "FAKE_RESTARTS": str(tmp_path / "restarts"),
            "FAKE_PID": str(tmp_path / "pids"),
            "BASH_ENV": str(bash_env),
        },
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert (result.returncode == 0) is expected, (
        kind, result.returncode, result.stdout, result.stderr[-380:]
    )


def test_prometheus_singbox_sample_rejects_multi_document_and_future_inputs(
    tmp_path: Path,
) -> None:
    """Proof input is exactly one parsed response, not concatenated stale blobs."""
    witness = ROOT / "acceptance/observability/prometheus-singbox-sample.sh"
    now = int(time.time() * 1000)
    valid = json.dumps(response())
    for payload in (valid + "\n" + valid, "not-json", json.dumps(
        response(epoch=int(time.time()) + 300)
    )):
        result = subprocess.run(
            ["/usr/bin/bash", str(witness), str(now - 20000)],
            input=payload, capture_output=True, text=True,
            timeout=8, check=False,
        )
        assert result.returncode != 0, payload[:80]
