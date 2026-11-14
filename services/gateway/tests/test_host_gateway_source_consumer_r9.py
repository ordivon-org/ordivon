"""R9 bounded adversarial proof of original-Host consumer tool closure.

Source qualification is not live auth, installation, or external Plugin migration.
"""

from __future__ import annotations

import importlib.util
from itertools import product
from pathlib import Path

AUDIT = (
    Path(__file__).resolve().parents[3] / "tools/repo/check_host_gateway_mcp_consumer_surface.py"
)


def _audit():
    spec = importlib.util.spec_from_file_location("gateway_host_source_r9", AUDIT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tool(name: str) -> dict:
    return {
        "inputSchema": {
            "type": "object",
            "properties": {"ref": {"type": "string"}},
            "required": ["ref"],
        },
        "outputSchema": {"type": "object"},
    }


def test_a_new_host_business_tool_missing_gateway_blocks_source_coverage() -> None:
    m = _audit()
    host = {n: _tool(n) for n in ("work.get", "message.get", "host.pool.stats")}
    gateway = {"work.get": _tool("work.get")}
    result = m.summarize(host, gateway)
    assert result["sourceInputNameRequiredParity"] is True
    assert result["hostOnlyTools"] == ["host.pool.stats", "message.get"]
    assert result["missingHostBusinessTools"] == ["message.get"]
    assert result["sourceHostBusinessSurfaceCovered"] is False
    assert result["sourceConsumerSurfaceQualified"] is False
    assert result["migrationStanding"].startswith("UNKNOWN")


def test_exposing_host_pool_stats_as_agent_tool_blocks_source_coverage() -> None:
    m = _audit()
    host = {n: _tool(n) for n in ("work.get", "host.pool.stats")}
    gateway = {n: _tool(n) for n in ("work.get", "host.pool.stats")}
    result = m.summarize(host, gateway)
    assert result["sourceInputNameRequiredParity"] is True
    assert result["exposedHostOperatorDiagnostics"] == ["host.pool.stats"]
    assert result["sourceConsumerSurfaceQualified"] is False


def test_existing_operator_diagnostic_is_excluded_without_claiming_migration() -> None:
    m = _audit()
    host = {n: _tool(n) for n in ("work.get", "host.pool.stats")}
    gateway = {"work.get": _tool("work.get"), "execution.submit": _tool("execution.submit")}
    result = m.summarize(host, gateway)
    assert result["operatorDiagnosticsExcluded"] == ["host.pool.stats"]
    assert result["missingHostBusinessTools"] == []
    assert result["exposedHostOperatorDiagnostics"] == []
    assert result["sourceConsumerSurfaceQualified"] is True
    assert result["installedConsumersQualified"] is None
    assert result["securityAuthorized"] is None
    assert result["domainConsumerMigrated"] is None
    assert result["migrationStanding"].startswith("UNKNOWN")


def test_finite_all_business_subsets_satisfy_coverage_iff_contained() -> None:
    m = _audit()
    names = ("work.get", "topic.resume", "message.post")
    verified = 0
    rejected = 0
    for host_mask, gw_mask in product(range(8), repeat=2):
        host_business = {name for i, name in enumerate(names) if host_mask & 1 << i}
        gw_business = {name for i, name in enumerate(names) if gw_mask & 1 << i}
        host = {n: _tool(n) for n in host_business | {"host.pool.stats"}}
        gateway = {n: _tool(n) for n in gw_business}
        report = m.summarize(host, gateway)
        expected = bool(host_business & gw_business) and host_business <= gw_business
        assert report["sourceConsumerSurfaceQualified"] is expected
        assert report["missingHostBusinessTools"] == sorted(host_business - gw_business)
        assert report["operatorDiagnosticsExcluded"] == ["host.pool.stats"]
        assert report["installedConsumersQualified"] is None
        if expected:
            verified += 1
        else:
            rejected += 1
    assert verified > 0 and rejected > 0
    assert verified + rejected == 64


def test_mismatched_required_fields_remain_blocking_even_with_full_tool_coverage() -> None:
    m = _audit()
    host = {"work.get": _tool("work.get"), "host.pool.stats": _tool("host.pool.stats")}
    gateway = {"work.get": _tool("work.get")}
    gateway["work.get"]["inputSchema"]["required"] = ["ref", "untrustedPrincipal"]
    report = m.summarize(host, gateway)
    assert report["missingHostBusinessTools"] == []
    assert report["sourceHostBusinessSurfaceCovered"] is True
    assert report["sourceInputNameRequiredParity"] is False
    assert report["sourceConsumerSurfaceQualified"] is False


def test_native_cli_exit_rejects_missing_business_tool(monkeypatch, capsys) -> None:
    import sys
    from types import SimpleNamespace

    mod = _audit()
    host = {"work.get": _tool("work.get"), "message.get": _tool("message.get")}
    gateway = {"work.get": _tool("work.get")}
    monkeypatch.setattr(mod, "_child_source", lambda name: host if name == "host" else gateway)
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="a" * 40),
    )
    monkeypatch.setattr(sys, "argv", ["native-host-surface"])
    assert mod.main() == 3
    import json

    result = json.loads(capsys.readouterr().out)
    assert result["missingHostBusinessTools"] == ["message.get"]
    assert result["sourceConsumerSurfaceQualified"] is False
    assert result["installedConsumersQualified"] is None


def test_source_observation_error_remains_unknown_not_false(monkeypatch, capsys) -> None:
    import json
    import sys

    mod = _audit()

    def unavailable(_name):
        raise FileNotFoundError("locked native owner environment missing")

    monkeypatch.setattr(mod, "_child_source", unavailable)
    monkeypatch.setattr(sys, "argv", ["native-host-surface"])
    assert mod.main() == 3
    result = json.loads(capsys.readouterr().out)
    assert result["migrationStanding"] == "UNKNOWN_SOURCE_OBSERVATION_FAILED"
    assert result["installedConsumersQualified"] is None
