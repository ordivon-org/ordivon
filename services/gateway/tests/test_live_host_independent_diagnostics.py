"""Source consumer: independent live blockers remain visible when Security credentials are private.

This never loads a bearer or authorizes Host/Runtime effects. Failure remains NO_GO.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "packaging" / "check_live_host_admission.py"


@pytest.fixture
def gate() -> Any:
    spec = importlib.util.spec_from_file_location("gateway_live_host_readonly_diagnostic", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unobservable_security_still_reports_independent_host_blockers_without_bearer(
    gate: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(
        gate,
        "_policy_data",
        lambda _path: (_ for _ in ()).throw(ValueError("private service credential invisible")),
    )
    monkeypatch.setattr(
        gate,
        "_qualified_systemd_environment",
        lambda _unit: "ORDIVON_GATEWAY_HOST_URL=http://127.0.0.1:8898/mcp",
    )
    monkeypatch.setattr(gate, "_rejects_unauthenticated_host_initialize", lambda: False)
    monkeypatch.setattr(gate, "_observed_non_gateway_host_tcp_clients", lambda: ["cloudflared"])

    def peers(*, anonymous_denied: bool) -> tuple[str, ...]:
        assert anonymous_denied is False
        return ("ordivon-gateway-local-r21.service",)

    monkeypatch.setattr(gate, "_unqualified_active_peer_host_consumers", peers)
    monkeypatch.setattr(
        gate,
        "_authenticated_host_initialize_accepted",
        lambda *_args, **_kwargs: pytest.fail("must never read/send a Host bearer"),
    )

    assert gate.main() == 3
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "NO_GO"
    assert result["reasons"] == ["HOST_SECURITY_PRECONDITIONS_UNOBSERVABLE"]
    observations = result["independentHostReadinessObservations"]
    assert observations["hostOwnerRouteQualified"] is True
    assert observations["hostOwnerCredentialDeclared"] is False
    assert observations["anonymousHostInitializeDenied"] is False
    assert observations["observedDirectHostTcpConsumerClasses"] == ["cloudflared"]
    assert observations["unverifiedActiveHostPeerConsumers"] == [
        "ordivon-gateway-local-r21.service"
    ]
    assert observations["independentBlockers"] == [
        "GATEWAY_HOST_OWNER_CREDENTIAL_NOT_CONFIGURED",
        "HOST_DIRECT_ANONYMOUS_MCP_NOT_PROVEN_DENIED",
        "HOST_DIRECT_NON_GATEWAY_TCP_CONSUMER_OBSERVED",
        "ACTIVE_HOST_PEER_AUTHENTICATED_MCP_NOT_PROVEN",
    ]
    assert observations["truthBoundary"].startswith("read-only independent diagnostics")


def test_independent_probe_unavailability_remains_unknown_not_false_or_go(
    gate: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_live_host_admission.py"])
    monkeypatch.setattr(
        gate, "_policy_data", lambda _path: (_ for _ in ()).throw(OSError("private"))
    )

    def unavailable(*_args: Any, **_kwargs: Any) -> Any:
        raise subprocess.CalledProcessError(1, ["unavailable"])

    monkeypatch.setattr(gate, "_qualified_systemd_environment", unavailable)
    monkeypatch.setattr(gate, "_rejects_unauthenticated_host_initialize", unavailable)
    monkeypatch.setattr(gate, "_observed_non_gateway_host_tcp_clients", unavailable)
    monkeypatch.setattr(gate, "_unqualified_active_peer_host_consumers", unavailable)
    assert gate.main() == 3
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "NO_GO"
    observations = report["independentHostReadinessObservations"]
    assert observations["hostOwnerCredentialDeclared"] is None
    assert observations["hostOwnerRouteQualified"] is None
    assert observations["anonymousHostInitializeDenied"] is None
    assert observations["observedDirectHostTcpConsumerClasses"] is None
    assert observations["unverifiedActiveHostPeerConsumers"] is None
    assert observations["independentBlockers"] == []
