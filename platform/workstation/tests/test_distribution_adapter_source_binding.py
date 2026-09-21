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
