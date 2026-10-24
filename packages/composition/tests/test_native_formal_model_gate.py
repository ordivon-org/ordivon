"""Composition Formal is executable Owner evidence, not a documentation-only PASS."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONFIGS = (
    "Lego21OwnerBoundary.cfg",
    "Lego21OwnerBoundary.direct-local.cfg",
    "Lego21OwnerBoundary.direct-egress.cfg",
    "Lego21OwnerBoundary.harness-local.cfg",
)


def test_four_mode_tlc_is_mandatory_in_composition_owner_verify():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    assert "mise run formal:verify" in tasks["verify"]["run"]
    formal = tasks["formal:verify"]["run"]
    assert "tlc2.TLC" in formal
    assert "Lego21OwnerBoundary.tla" in formal
    for config in CONFIGS:
        assert (ROOT / "formal" / config).is_file()
        assert config in formal


def test_admission_witness_model_requires_a_real_network_change_counterexample():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    formal = tasks["formal:verify"]["run"]
    probe = ROOT / "formal" / "Lego21OwnerBoundary.readiness-probe.cfg"
    assert probe.is_file()
    assert "INVARIANT NetworkNeverDegradesAfterAdmission" in probe.read_text()
    assert probe.name in formal
    assert "Error: Invariant NetworkNeverDegradesAfterAdmission is violated." in formal


def test_typed_foreign_consumer_evidence_has_a_live_tlc_negative_witness():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    formal = tasks["formal:verify"]["run"]
    probe = ROOT / "formal" / "Lego21OwnerBoundary.foreign-evidence-probe.cfg"
    assert probe.is_file()
    assert "INVARIANT ForeignEvidenceIsUnreachable" in probe.read_text()
    assert probe.name in formal
    assert "Error: Invariant ForeignEvidenceIsUnreachable is violated." in formal


def test_formal_toolchain_is_digest_checked_and_explicitly_admitted():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    formal = tasks["formal:verify"]["run"]
    assert '"$runtime_root/scripts/tla-formal" verify' in formal
    repo = ROOT.parents[1]
    policy = tomllib.loads((repo / "tools/repo/dependency_contracts.toml").read_text())
    assert any(
        row["from_owner"] == "composition"
        and row["to_owner"] == "runtime"
        and row["source_glob"] == "packages/composition/mise.toml"
        and row["kind"] == "PUBLIC_PINNED_FORMAL_TOOLCHAIN"
        for row in policy["seams"]
    )


def test_same_work_wrong_source_cut_reachable_and_rejected():
    tasks = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    formal = tasks["formal:verify"]["run"]
    probe = ROOT / "formal" / "Lego21OwnerBoundary.sourcecut-probe.cfg"
    model = (ROOT / "formal" / "Lego21OwnerBoundary.tla").read_text()
    assert probe.is_file()
    assert "INVARIANT WrongSourceEvidenceIsUnreachable" in probe.read_text()
    assert "NoHostAcceptanceWithWrongSource" in model
    assert 'sourceEvidenceBinding = "admission-bound"' in model
    assert probe.name in formal
    assert "Error: Invariant WrongSourceEvidenceIsUnreachable is violated." in formal
