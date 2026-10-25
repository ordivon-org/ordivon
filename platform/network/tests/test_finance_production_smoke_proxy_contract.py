"""Exercise Finance production-smoke transport functions without running live systemctl.

The real production script intentionally stops and restarts carrier services.
Source only its existing bounded probe functions and intercept curl before any
physical network or systemd action.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "consumers/finance/acceptance/production-smoke.sh"
)


@pytest.mark.parametrize(
    ("name", "arguments"),
    (
        ("probe_okx", ""),
        ("probe_binance_spot", ""),
        ("probe_binance_usdm", ""),
        ("probe_wallet", ""),
        ("probe_treasury", ""),
        ("probe_fred", ""),
        ("probe_ws", "19285 https://data-stream.binance.vision/ '200,400,403'"),
        ("blocked", "19283 https://example.com/"),
    ),
)
def test_all_finance_production_probes_force_declared_proxy(tmp_path, name, arguments):
    lines = SOURCE.read_text().splitlines()
    definitions = [line for line in lines if line.startswith(f"{name}(){{")]
    assert len(definitions) == 1, name

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        '#!/bin/sh\n'
        'printf "%s|" "$@" >> "$FINANCE_CURL_ARGV"\n'
        'printf \'{"code":"0","data":[{"ts":"1"}],"serverTime":1}\\n\'\n',
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    log = tmp_path / "argv.txt"
    subprocess.run(
        ["/usr/bin/bash", "-c", definitions[0] + f"\n{name} {arguments}\n"],
        env={
            **os.environ,
            "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
            "FINANCE_CURL_ARGV": str(log),
            "NO_PROXY": "*",
            "no_proxy": "*",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=4,
    )
    assert log.exists(), f"{name} never invoked curl"
    argv = log.read_text().split("|")[:-1]
    assert argv[0] == "-q", (name, argv)
    assert "--proxy" in argv and "--noproxy" in argv, (name, argv)
    assert argv[argv.index("--noproxy") + 1] == "", (name, argv)
