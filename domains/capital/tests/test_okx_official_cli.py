from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from okx_private_reality_probe import official_rows


def test_official_cli_json(monkeypatch):
    observed = []

    def fake(args, **kw):
        observed.append((args, kw))
        return subprocess.CompletedProcess(args, 0, json.dumps({"data": [{"ccy": "TEST"}]}), "")

    monkeypatch.setattr(subprocess, "run", fake)
    result = official_rows(
        ["account", "balance"],
        home=Path("/tmp/example"),
        profile="observer",
        base_url="https://openapi.okx.com",
    )
    assert result == [{"ccy": "TEST"}]
    args, kw = observed[0]
    assert args[1:4] == ["--profile", "observer", "--json"]
    assert kw["env"]["OKX_API_BASE_URL"] == "https://openapi.okx.com"
    assert kw["env"]["HOME"] == "/tmp/example"


def test_official_cli_error_is_not_silent(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run", lambda args, **kw: subprocess.CompletedProcess(args, 1, "", "secret")
    )
    with pytest.raises(RuntimeError, match="failed"):
        official_rows(
            ["account", "balance"],
            home=Path("/tmp/example"),
            profile="observer",
            base_url="https://openapi.okx.com",
        )


def test_no_custom_okx_http_client():
    assert not (ROOT / "src/ordivon_capital/trading/okx_readonly_client.py").exists()
