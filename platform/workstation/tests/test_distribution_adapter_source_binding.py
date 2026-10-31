from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "accept-n8n-distribution-adapter-smoke.sh"


def test_distribution_adapter_smoke_defaults_to_monorepo_distribution_owner() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'MONOREPO_ROOT=$(cd "$ROOT/../.." && pwd)' in text
    assert (
        'DIST_INTENT=${DIST_INTENT:-$MONOREPO_ROOT/capabilities/distribution/evidence/'
        'r7-artifact-development-publication-intent.json}'
    ) in text
    assert "/root/projects/ordivon-distribution-v2" not in text


def test_default_distribution_intent_exists_in_monorepo_tree() -> None:
    monorepo_root = ROOT.parents[1]
    intent = (
        monorepo_root
        / "capabilities"
        / "distribution"
        / "evidence"
        / "r7-artifact-development-publication-intent.json"
    )
    assert intent.is_file()


def test_r7_actual_workstation_event_preserves_blocked_no_effect() -> None:
    import runpy

    script = ROOT / "scripts" / "invoke-n8n-distribution-adapter-smoke.py"
    event_for = runpy.run_path(str(script))["event_for"]
    intent = (
        ROOT.parents[1]
        / "capabilities"
        / "distribution"
        / "evidence"
        / "r7-artifact-development-publication-intent.json"
    )
    event = event_for("blocked", "consumer-slice-r7", intent)
    assert event["specversion"] == "1.0"
    assert event["id"] == "consumer-slice-r7"
    assert event["type"] == "io.ordivon.distribution.admission.v1"
    assert event["data"]["decision"]["action"] == "artifact_release_not_ready"
    assert event["data"]["decision"]["externalEffectPerformed"] is False
    assert event["data"]["intent"]["occurrenceRef"]


def test_r7_readback_event_does_not_fabricate_provider_authority() -> None:
    import runpy

    script = ROOT / "scripts" / "invoke-n8n-distribution-adapter-smoke.py"
    event_for = runpy.run_path(str(script))["event_for"]
    event = event_for("readback", "read-only-probe", None)
    assert event["data"]["decision"]["action"] == "preflight_ready"
    assert event["data"]["decision"]["externalEffectPerformed"] is False
    assert event["data"]["intent"]["effectName"] == "provider_readback"
