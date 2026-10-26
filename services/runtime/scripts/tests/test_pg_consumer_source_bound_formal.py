from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "formal" / "RuntimePgCutoverR1.tla"
CFG = ROOT / "formal" / "RuntimePgCutoverR1.cfg"
RUNNER = ROOT / "scripts" / "tla-formal"


def test_pg_consumer_receipt_is_typed_and_source_bound_before_qualification():
    model = MODEL.read_text(encoding="utf-8")
    qualification = model[model.index("QualifyConsumers =="):model.index("Promote ==")]
    assert "consumerReceipt" in model
    assert 'consumerReceipt.issuer = "trusted"' in qualification
    assert "consumerReceipt.revision = sqliteRevision" in qualification
    assert "consumerReceipt.content = sqliteContent" in qualification
    assert "ObserveConsumerReceipt ==" in model
    assert "QualifiedConsumersMatchSource ==" in model
    assert "QualifiedConsumersMatchSource" in CFG.read_text(encoding="utf-8")


def test_pg_receipt_model_has_named_tlc_counterexamples_and_keeps_oracle_bounded():
    runner = RUNNER.read_text(encoding="utf-8")
    assert "PG source-bound consumer receipt negative control PASS" in runner
    assert "Invariant QualifiedConsumersMatchSource is violated." in runner
    assert "for label in revision content issuer" in runner
    model = MODEL.read_text(encoding="utf-8")
    assert "an unverified external oracle" in model.lower()
