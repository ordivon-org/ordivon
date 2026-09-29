from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "qualify_model_factor_r1.py"
EVIDENCE = ROOT / "evidence" / "20260928-r1"


def load_tool():
    spec = importlib.util.spec_from_file_location("r1_factor_qualification", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_r1_requested_model_factor_collapsed_at_provider_effective_identity() -> None:
    module = load_tool()
    qualification = module.build_qualification(EVIDENCE)
    assert qualification["standing"] == "COLLAPSED_EFFECTIVE_IDENTITY"
    assert qualification["requestedLevels"] == ["deepseek-flash", "deepseek-v4-flash"]
    assert qualification["effectiveModelIds"] == ["deepseek-flash"]
    assert qualification["providerCallCount"] == 57
    assert qualification["interpretability"]["modelMainEffect"] == "NOT_ESTIMABLE"
    assert qualification["interpretability"]["modelByHarnessInteraction"] == "NOT_ESTIMABLE"
    assert qualification["interpretability"]["protocolMechanics"] == "UNAFFECTED"
    assert qualification["providerIdentityEvidence"]["deepseek-flash"]["providerCallCount"] == 29
    assert qualification["providerIdentityEvidence"]["deepseek-v4-flash"]["providerCallCount"] == 28
    assert qualification["observedSystemFingerprints"] == ["aeb56401ca74e127821c4f9126dcb669"]


def test_qualification_digest_is_stable_and_append_only() -> None:
    module = load_tool()
    qualification = module.build_qualification(EVIDENCE)
    pilot = module.load_runner()
    expected = pilot.canonical_digest(
        {key: value for key, value in qualification.items() if key != "qualificationDigest"}
    )
    assert qualification["qualificationDigest"] == expected
    acceptance = json.loads((EVIDENCE / "acceptance.json").read_text())
    assert acceptance["standing"] == "PASS_PILOT_MECHANICS"
