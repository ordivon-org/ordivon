from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "workstation/providers/wsl_substrate_resilience/wsl_substrate_resilience.py"
MATERIALIZER = ROOT / "workstation/providers/wsl_substrate_resilience/materialize.py"


def load_provider():
    spec = importlib.util.spec_from_file_location("wsl_substrate_resilience", PROVIDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_buddy_parser_preserves_resource_topology():
    module = load_provider()
    rows = module.parse_buddyinfo(
        "Node 0, zone DMA32  10 9 8 7 6 5 4 3 2 1 0\n"
        "Node 0, zone Normal  1 2 3 4 5 6 7 8 9 10 11\n"
    )
    assert rows[0]["order7Blocks"] == 3
    assert rows[0]["order7PlusBlocks"] == 6
    assert rows[1]["order7Blocks"] == 8
    assert rows[1]["order7PlusBlocks"] == 38


def test_classifier_marks_verified_fresh_session_healthy():
    module = load_provider()
    probe = {"admissionProbe": {"status": "READY", "verified": True}}
    linux = {"snapshotSha256": "sha256:x", "kernel": {}}
    result = module.classify(probe, linux)
    assert result["failureClass"] == "HEALTHY"
    assert result["confidence"] == "high"
    assert result["recommendedEffect"] == "none"


def test_classifier_requires_mechanism_evidence_before_fragmentation_recovery():
    module = load_provider()
    probe = {"admissionProbe": {"status": "TIMEOUT", "verified": False}}
    linux = {
        "snapshotSha256": "sha256:x",
        "kernel": {
            "pageAllocationFailureOrders": [7],
            "vmbusAllocRingObserved": True,
        },
    }
    result = module.classify(probe, linux)
    assert result["failureClass"] == "F1_HIGH_ORDER_FRAGMENTATION"
    assert result["confidence"] == "high"
    assert result["recommendedEffect"] == "compact_memory"


def test_classifier_fails_closed_when_timeout_has_no_proven_mechanism():
    module = load_provider()
    probe = {"admissionProbe": {"status": "TIMEOUT", "verified": False}}
    linux = {
        "snapshotSha256": "sha256:x",
        "kernel": {
            "pageAllocationFailureOrders": [],
            "vmbusAllocRingObserved": False,
            "utilAcceptVsockTimeoutObserved": True,
        },
    }
    result = module.classify(probe, linux)
    assert result["failureClass"] == "UNKNOWN"
    assert result["confidence"] == "insufficient"
    assert result["recommendedEffect"] == "collect_forensics"


def test_kernel_evidence_is_time_bounded_so_stale_f1_does_not_authorize_recovery():
    text = PROVIDER.read_text(encoding="utf-8")
    assert 'KERNEL_LOOKBACK = "5 minutes ago"' in text
    assert '"--since", KERNEL_LOOKBACK' in text


def test_compaction_effect_is_narrow_and_drop_caches_is_not_a_provider_effect():
    text = PROVIDER.read_text(encoding="utf-8")
    assert 'Path("/proc/sys/vm/compact_memory")' in text
    assert 'COMPACT_MEMORY.write_text("1\\n", encoding="ascii")' in text
    assert "/proc/sys/vm/drop_caches" not in text
    assert "F1_HIGH_ORDER_FRAGMENTATION" in text
    assert "classification digest mismatch" in text


def test_materializer_is_content_addressed_and_does_not_install_a_daemon():
    text = MATERIALIZER.read_text(encoding="utf-8").lower()
    assert "sha256" in text
    assert "/usr/local/libexec/ordivon/workstation-v2/wsl-substrate-resilience" in text
    for forbidden in ("systemctl", "cron", "timer", "daemon", "subprocess"):
        assert forbidden not in text
