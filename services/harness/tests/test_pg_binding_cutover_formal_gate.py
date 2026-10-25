"""H04 PG role cutover must run official TLC in the existing Owner native gate."""

from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_h04_pg_role_cutover_is_in_queue_and_verify_with_nonvacuity() -> None:
    tasks = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
    assert "mise run formal:verify" in tasks["queue"]["run"]
    assert "mise run formal:verify" in tasks["verify"]["run"]
    gate = tasks["formal:verify"]["run"]
    assert '"$runtime_root/scripts/tla-formal" verify' in gate
    assert "ConversationBindingCutoverR1.cfg" in gate
    for label, invariant in (
        ("admission", "PgAdmissionIsUnreachable"),
        ("interrupted", "InterruptedImportIsUnreachable"),
        ("growth", "PostCutoverGrowthReplayIsUnreachable"),
    ):
        cfg = ROOT / "formal" / f"ConversationBindingCutoverR1.{label}-probe.cfg"
        assert cfg.is_file()
        assert f"INVARIANT {invariant}" in cfg.read_text()
        assert '"ConversationBindingCutoverR1.$label-probe.cfg"' in gate
        assert "Error: Invariant $predicate is violated." in gate


def test_pg_model_expresses_two_commits_as_distinct_transitions() -> None:
    model = (ROOT / "formal" / "ConversationBindingCutoverR1.tla").read_text()
    for required in (
        "CommitPgImport ==",
        "SealOldWriter ==",
        "LoseMigrationResponse ==",
        "RecoverMigration ==",
        "PgOnlyAdoption ==",
        "ReplaySourceCutover ==",
        "NoPGAdmissionBeforeSourceSeal ==",
        "NoOldWriterAfterSealing ==",
    ):
        assert required in model
