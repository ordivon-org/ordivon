from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "social_fabric_signaling_r3", SCRIPTS / "social_fabric_signaling_r3.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

CUT = ROOT / "evidence/acceptance/social-fabric-signaling-r3-vhd-cut-20260923.json"
HISTORY = (
    ROOT / "evidence/acceptance/social-fabric-attention-history-manifest-20260923.json"
)


def load_cut():
    return json.loads(CUT.read_text(encoding="utf-8"))


def test_vhd_projection_separates_scope_propagation_and_compartment():
    result = mod.compile_signaling(load_cut())
    assert len(result["signals"]) == 5
    candidate = next(
        row
        for row in result["signals"]
        if row["eventId"] == "candidate:vhd-compact:capital"
    )
    assert candidate["legacyVisibilityScope"] == "system"
    assert candidate["semanticScope"] == "maintenance:wsl-vhd"
    assert candidate["propagationMode"] == "local"
    assert "resource:windows:wsl:archlinux:ext4-vhdx" in candidate["compartmentRefs"]


def test_legacy_scope_cannot_supply_missing_semantics():
    cut = load_cut()
    cut["signalSemantics"] = cut["signalSemantics"][:-1]
    with pytest.raises(mod.SocialFabricError, match="every event requires explicit"):
        mod.compile_signaling(cut)


def test_propagation_mode_is_independent_from_legacy_visibility_scope():
    cut = load_cut()
    cut["signalSemantics"][0]["propagationMode"] = "direct"
    result = mod.compile_signaling(cut)
    signal = next(
        row
        for row in result["signals"]
        if row["eventId"] == cut["signalSemantics"][0]["eventId"]
    )
    assert signal["propagationMode"] == "direct"
    assert signal["legacyVisibilityScope"] == "system"


def test_compartment_refs_are_explicit_and_unique():
    cut = load_cut()
    cut["signalSemantics"][0]["compartmentRefs"] = ["domain:x", "domain:x"]
    with pytest.raises(mod.SocialFabricError, match="must be unique"):
        mod.compile_signaling(cut)


def test_receptor_matches_orthogonal_dimensions():
    result = mod.compile_signaling(load_cut())
    deliveries = {
        row["receptorId"]: row["signalIds"] for row in result["receptorDeliveries"]
    }
    assert deliveries["receptor:r3-wsl-maintenance"] == [
        "candidate:vhd-compact:capital",
        "candidate:vhd-compact:gris",
        "candidate:wslservice-restart",
        "damage:diskpart-rpc-unavailable",
    ]
    assert deliveries["receptor:r3-storage-pressure"] == ["modulatory:d-drive-pressure"]


def test_receptor_has_no_expression_or_score_dsl():
    for forbidden in ("expression", "policy", "weight", "score", "threshold", "negate"):
        cut = load_cut()
        cut["receptors"][0][forbidden] = "x"
        with pytest.raises(mod.SocialFabricError, match="simple interest filters"):
            mod.compile_signaling(cut)


def test_anomaly_origin_requires_damage_signal_and_source_ref():
    cut = load_cut()
    candidate = next(
        row for row in cut["signalSemantics"] if row["eventId"].startswith("candidate:")
    )
    candidate["anomalyOrigin"] = "exogenous"
    candidate["originSourceRef"] = "owner:x"
    with pytest.raises(mod.SocialFabricError, match="valid only for damage"):
        mod.compile_signaling(cut)

    cut = load_cut()
    damage = next(
        row for row in cut["signalSemantics"] if row["eventId"].startswith("damage:")
    )
    del damage["originSourceRef"]
    with pytest.raises(mod.SocialFabricError, match="originSourceRef"):
        mod.compile_signaling(cut)


def test_unknown_anomaly_origin_is_preserved_without_security_verdict():
    result = mod.compile_signaling(load_cut())
    damage = next(
        row for row in result["signals"] if row["eventId"].startswith("damage:")
    )
    assert damage["anomalyOrigin"] == "unknown"
    raw = json.dumps(result).lower()
    assert '"threat"' not in raw and '"malicious"' not in raw


def test_projection_is_deterministic():
    cut = load_cut()
    assert mod.compile_signaling(cut) == mod.compile_signaling(deepcopy(cut))


def test_attention_measurement_collapses_duplicate_views_of_same_horizon():
    manifest = json.loads(HISTORY.read_text(encoding="utf-8"))
    result = mod.measure_attention_history(manifest, HISTORY.resolve().parents[1])
    assert result["rawDocumentCount"] == 5
    assert result["distinctHorizonCount"] == 2
    assert result["duplicateViewCountCollapsed"] == 3


def test_current_history_does_not_authorize_adaptation():
    manifest = json.loads(HISTORY.read_text(encoding="utf-8"))
    result = mod.measure_attention_history(manifest, HISTORY.resolve().parents[1])
    assert result["findingIdsRepeatedAcrossDistinctHorizons"] == []
    assert result["standing"] == "INSUFFICIENT_LONGITUDINAL_EVIDENCE_HOLD"
    assert result["promotionGate"]["adaptationImplementationAuthorized"] is False


def test_same_code_is_not_same_stimulus_identity():
    manifest = json.loads(HISTORY.read_text(encoding="utf-8"))
    result = mod.measure_attention_history(manifest, HISTORY.resolve().parents[1])
    codes = []
    for horizon in result["horizons"]:
        codes.extend(horizon["findingIds"])
    assert len(codes) >= 6
    assert result["findingIdsRepeatedAcrossDistinctHorizons"] == []
