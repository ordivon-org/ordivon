from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "workstation" / "providers" / "wsl_sparse_guest_health.py"

def test_sparse_guest_health_is_observation_only_and_tiered():
    text = SCRIPT.read_text(encoding="utf-8").lower()
    assert "sparse_healthy" in text
    assert "integrity_unknown" in text
    assert "sparse_incident" in text
    assert "statvfs" in text
    assert "findmnt" in text
    assert "tune2fs" in text
    assert "dmesg" in text
    for forbidden in ("fstrim", "e2fsck", "rm -", "--compact", "set-sparse", "optimize-vhd"):
        assert forbidden not in text


def test_single_sample_d_state_is_advisory_not_global_degraded_state():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'advisories.append("D_STATE_PRESENT_SINGLE_SAMPLE")' in text
    assert 'dStateStanding' in text
    assert 'elif ds:' not in text
    assert 'standing = "SPARSE_DEGRADED"' not in text
