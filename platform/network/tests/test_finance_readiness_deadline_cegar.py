"""Finance readiness deadline CEGAR: prove rejection of expired concrete admission."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

READY = Path(__file__).resolve().parents[1] / "consumers/finance/ready.sh"


def run_ready(
    tmp_path: Path,
    seconds: str,
    *,
    advance_clock: bool,
    mode: str = "okx",
    probe_delay: bool = False,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    tools = tmp_path / "bin"
    tools.mkdir()
    logfile = tmp_path / "probes.log"
    clock = tmp_path / "clock.bash"
    modifier = "SECONDS=$((SECONDS + 1000)); " if advance_clock else ""
    clock.write_text(f"systemctl() {{ {modifier}return 0; }}\n", encoding="utf-8")
    curl = tools / "curl"
    curl.write_text(
        '#!/bin/sh\n'
        'printf "%s\\n" "$*" >> "$FINANCE_PROBE_LOG"\n'
        'printf "%s|" "$@" >> "$FINANCE_PROBE_ARGV_LOG"\n'
        + ("sleep 2\n" if probe_delay else "")
        + "printf '%s\\n' '{\"code\":\"0\",\"data\":[{\"ts\":\"1\"}]}'\n",
        encoding="utf-8",
    )
    curl.chmod(0o755)
    result = subprocess.run(
        ["/usr/bin/bash", str(READY), mode, seconds],
        env={
            **os.environ, "BASH_ENV": str(clock),
            "FINANCE_PROBE_LOG": str(logfile),
            "FINANCE_PROBE_ARGV_LOG": str(tmp_path / "probe-argv.txt"),
            "NO_PROXY": "*",
            "no_proxy": "*",
            "PATH": str(tools) + os.pathsep + os.environ.get("PATH", ""),
        },
        capture_output=True, text=True, timeout=6, check=False,
    )
    return result, logfile.read_text().splitlines() if logfile.exists() else []


@pytest.mark.parametrize(
    "invalid", ("08", "00", "0001", "9999999999999999999999", "-1", "1.0")
)
def test_reject_noncanonical_or_unbounded_timeout_before_external_probe(
    tmp_path: Path, invalid: str
) -> None:
    outcome, probes = run_ready(tmp_path, invalid, advance_clock=False)
    assert outcome.returncode == 2, (invalid, outcome.stdout, outcome.stderr)
    assert probes == []


def test_expired_finance_budget_cannot_publish_ready(tmp_path: Path) -> None:
    """Advance actual parent Bash SECONDS in the prerequisites before curl."""
    outcome, probes = run_ready(tmp_path, "1", advance_clock=True)
    assert outcome.returncode != 0, (outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' not in outcome.stdout
    assert probes == [], "expired admission must not initiate an external probe"


def test_valid_finance_probe_still_reports_ready(tmp_path: Path) -> None:
    outcome, probes = run_ready(tmp_path, "30", advance_clock=False)
    assert outcome.returncode == 0, (outcome.stdout, outcome.stderr)
    assert json.loads(outcome.stdout)["standing"] == "READY"
    assert len(probes) == 1


def test_expired_after_first_success_cannot_publish_ready_or_call_next_owner(
    tmp_path: Path,
) -> None:
    """The first valid provider result arrives after the shared deadline.

    CEGAR negative trace: mode public has five independent providers; a
    successful first probe must not authorize downstream probes after expiry.
    """
    outcome, probes = run_ready(
        tmp_path, "1", advance_clock=False, mode="public", probe_delay=True
    )
    assert outcome.returncode != 0, (outcome.stdout, outcome.stderr)
    assert '"standing":"READY"' not in outcome.stdout
    assert len(probes) == 1, probes
    assert "openapi.okx.com" in probes[0]


@pytest.mark.parametrize(
    "mode", ("okx", "binance-usdm", "binance-spot", "binance-wallet", "treasury", "fred")
)
def test_finance_readiness_forces_proxy_even_with_ambient_no_proxy(tmp_path: Path, mode: str) -> None:
    """Physical Finance egress must never inherit a direct-bypass exception."""
    _, probes = run_ready(tmp_path, "0", advance_clock=False, mode=mode)
    assert len(probes) == 1, (mode, probes)
    args = (tmp_path / "probe-argv.txt").read_text().split("|")[:-1]
    assert args[0] == "-q", (mode, args)  # do not load ambient ~/.curlrc
    assert "--proxy" in args and "--noproxy" in args, (mode, args)
    assert args[args.index("--noproxy") + 1] == "", (mode, args)
