from __future__ import annotations

import copy

import pytest

from ordivon_composition import CircuitContractError, inspect_lego_declaration

COORDS = ("I", "O", "S", "pre", "post", "inv", "eff", "c", "epsilon", "prov", "unfold")


def _decl() -> dict:
    return {
        "identity": "method:sample-r21",
        "responsibility": "select one compatible candidate for a named consumer",
        "goal": "choose a composition with explicit obligations",
        "consumerRef": "consumer:agent-composition-cli",
        "semanticProfile": "finite typed contract projection",
        "publicObservation": "inputs, outputs, errors, effects, and authority",
        "sourceRef": "git:source-cut:sample",
        "acceptance": {
            "criterion": "reject incomplete declarations without declaring proof",
            "baseline": "no strict public contract qualifier",
            "oracle": "bounded positive and negative native calls",
        },
        "ell": {
            key: {"type": "DeclaredSemantic", "standing": "DECLARED", "statement": "scope: " + key}
            for key in COORDS
        },
    }


def test_complete_declaration_never_promotes_verification_or_authority():
    r = inspect_lego_declaration(_decl())
    assert r["declarationStanding"] == "DECLARATION_COMPLETE_UNPROVED"
    assert r["nonvacuityEstablished"] is False
    assert r["modelProofEstablished"] is False
    assert r["implementationRefined"] is False
    assert r["installedCurrent"] is False
    assert r["safeToInvoke"] is False
    assert r["domainAcceptanceEstablished"] is False


@pytest.mark.parametrize("removed", COORDS)
def test_every_r21_coordinate_is_mandatory(removed):
    decl = _decl()
    del decl["ell"][removed]
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(decl)


def test_typed_unknown_is_explicit_and_blocks_numeric_claim():
    decl = _decl()
    decl["ell"]["c"] = {
        "type": "CostBound",
        "standing": "UNKNOWN",
        "reason": "no measured source bound",
    }
    result = inspect_lego_declaration(decl)
    assert result["declarationStanding"] == "DECLARATION_COMPLETE_WITH_UNKNOWNS"
    assert result["unknownCoordinates"] == ["c"]
    assert result["safeToInvoke"] is False


def test_unqualified_unknown_and_false_zeros_are_rejected():
    decl = _decl()
    decl["ell"]["epsilon"] = {"type": "ErrorBound", "standing": "UNKNOWN"}
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(decl)
    decl = _decl()
    decl["ell"]["c"] = 0
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(decl)


def test_declaration_with_vacuous_pre_not_mistaken_for_usable_contract():
    decl = _decl()
    decl["ell"]["pre"]["statement"] = "False"
    result = inspect_lego_declaration(decl)
    assert result["nonvacuityEstablished"] is False
    assert result["safeToInvoke"] is False


def test_missing_effect_or_consumer_acceptance_rejected():
    d = _decl()
    d["ell"]["eff"]["statement"] = ""
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(d)
    d = _decl()
    d["consumerRef"] = ""
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(d)
    d = _decl()
    del d["acceptance"]["oracle"]
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(d)


def test_unknown_surface_may_not_be_smuggled_in_declared_field():
    d = _decl()
    d["ell"]["c"]["statement"] = "UNKNOWN"
    with pytest.raises(CircuitContractError):
        inspect_lego_declaration(d)


def test_canonical_evidence_is_deterministic_and_source_sensitive():
    first = inspect_lego_declaration(_decl())
    second = inspect_lego_declaration(copy.deepcopy(_decl()))
    assert first["declarationDigest"] == second["declarationDigest"]
    changed = _decl()
    changed["sourceRef"] = "git:different"
    assert inspect_lego_declaration(changed)["declarationDigest"] != first["declarationDigest"]


def test_existing_interface_cli_qualify_real_entrypoint(tmp_path, monkeypatch, capsys):
    import json

    from ordivon_composition.interface_contract_r2 import main

    path = tmp_path / "complete-lego.json"
    path.write_text(json.dumps(_decl()), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["ordivon-interface-contract", "qualify", str(path)])
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["declarationStanding"] == "DECLARATION_COMPLETE_UNPROVED"
    assert result["safeToInvoke"] is False


def test_existing_interface_cli_fail_closed_missing_effect(tmp_path, monkeypatch):
    import json

    from ordivon_composition.interface_contract_r2 import main

    d = _decl()
    del d["ell"]["eff"]
    path = tmp_path / "missing-effect.json"
    path.write_text(json.dumps(d), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["ordivon-interface-contract", "qualify", str(path)])
    with pytest.raises(SystemExit, match="R2.1 LEGO declaration schema violation"):
        main()


def test_cli_refuses_ambiguous_duplicate_lego_keys(tmp_path, monkeypatch):
    from ordivon_composition.interface_contract_r2 import main

    path = tmp_path / "duplicate.json"
    path.write_text('{"identity":"one","identity":"two"}', encoding="utf8")
    monkeypatch.setattr("sys.argv", ["ordivon-interface-contract", "qualify", str(path)])
    with pytest.raises(SystemExit, match="duplicate JSON key"):
        main()
