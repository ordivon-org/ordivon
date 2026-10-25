"""Ensure native Network CI really invokes formal Owner contract."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_network_ci_runs_exact_bounded_tlc_model() -> None:
    tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
    assert "mise run formal:verify" in tasks["ci"]["run"]
    cmd = tasks["formal:verify"]["run"]
    assert '"$runtime_root/scripts/tla-formal" verify' in cmd
    assert "SupplyChainReadinessR1.cfg" in cmd
    for label, predicate in (
        ("success", "ReadyIsUnreachable"),
        ("transport", "TransportLossIsUnreachable"),
        ("auth", "ProxyAuthIsUnreachable"),
        ("origin", "ReachedOriginForbiddenIsUnreachable"),
        ("deadline", "DeadlineFailureIsUnreachable"),
    ):
        cfg = ROOT / "formal" / f"SupplyChainReadinessR1.{label}-probe.cfg"
        assert cfg.is_file()
        assert f"INVARIANT {predicate}" in cfg.read_text()
        assert "Error: Invariant $predicate is violated." in cmd


def test_network_to_runtime_seam_is_only_public_formal_tool() -> None:
    repo = ROOT.parents[1]
    seams = tomllib.loads((repo / "tools/repo/dependency_contracts.toml").read_text())["seams"]
    assert any(
        item["from_owner"] == "network"
        and item["to_owner"] == "runtime"
        and item["source_glob"] == "platform/network/mise.toml"
        and item["kind"] == "PUBLIC_PINNED_FORMAL_TOOLCHAIN"
        for item in seams
    )
