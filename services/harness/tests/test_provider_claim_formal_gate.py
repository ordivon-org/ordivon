"""Owner native formal model is mandatory, not prose-only."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_harness_queue_and_verify_require_formal_claim_model():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
    for mode in ("verify", "queue"):
        assert "mise run formal:verify" in tasks[mode]["run"]
    formal = tasks["formal:verify"]["run"]
    assert '"$runtime_root/scripts/tla-formal" verify' in formal
    assert "ProviderClaimR1.cfg" in formal
    assert "tlc2.TLC" in formal
    for label, invariant in (
        ("ack", "UnacknowledgedPhysicalCallIsUnreachable"),
        ("expiry", "ClaimReplacementIsUnreachable"),
        ("delivery", "DeliveryIsUnreachable"),
        ("privacy-fresh", "MetadataOnlyFreshAckIsUnreachable"),
        ("privacy-redacted", "MetadataOnlyRedactionIsUnreachable"),
    ):
        cfg = ROOT / "formal" / f"ProviderClaimR1.{label}-probe.cfg"
        assert cfg.is_file()
        assert f"INVARIANT {invariant}" in cfg.read_text()
        assert "Error: Invariant $predicate is violated." in formal


def test_public_pinned_formal_toolchain_is_explicit():
    repo = ROOT.parents[1]
    seams = tomllib.loads((repo / "tools/repo/dependency_contracts.toml").read_text())["seams"]
    assert any(
        row["from_owner"] == "harness"
        and row["to_owner"] == "runtime"
        and row["source_glob"] == "services/harness/mise.toml"
        and row["kind"] == "PUBLIC_PINNED_FORMAL_TOOLCHAIN"
        for row in seams
    )
