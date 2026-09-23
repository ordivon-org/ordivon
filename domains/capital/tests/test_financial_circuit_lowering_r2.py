from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ordivon_capital.governance.circuit_lowering import (
    FinancialCircuitError,
    load_and_lower,
    lower_financial_circuit,
)

ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
@pytest.mark.parametrize('path',[
 'circuits/public-market-observation-r2.json','circuits/portfolio-risk-analysis-r2.json','circuits/counterfactual-analysis-r2.json','circuits/nonlive-effect-qualification-r2.json'])
def test_canonical_r2_specs_lower_to_shared_non_authoritative_circuit(path):
    out=load_and_lower(path)
    assert out['standing']=='FINANCIAL_SEMANTICS_ADMITTED_MECHANICAL_COMPOSITION_COMPILED'
    assert out['authorityGranted'] is False
    assert out['executionPerformed'] is False
    assert out['semanticCompletionEvaluated'] is False
    assert out['sharedCompiled']['truthRole']=='task-local-non-authoritative-composition-projection'
    assert out['authorityObligations']['authorityGranted'] is False
    assert out['authorityObligations']['executionAuthorityGranted'] is False

def test_nonlive_effect_retains_financial_ordering_and_explicit_authority_obligations():
    out=load_and_lower('circuits/nonlive-effect-qualification-r2.json')
    assert out['effectClasses']==['SIMULATED_EXCHANGE_ORDER_EFFECT']
    assert out['sharedCompiled']['stageOrder']==['reserve','effect','reconcile','account']
    ids=out['authorityObligations']['requiredObligationIds']
    assert ids==['authority:account:local_state','authority:effect:simulated_effect','authority:reserve:local_state']
    assert out['authorityObligations']['effectCoverageEstablished'] is False

def test_missing_reserve_fails_in_capital_not_shared_composition():
    spec=load('circuits/nonlive-effect-qualification-r2.json')
    spec['stages']=[row for row in spec['stages'] if row['id']!='reserve']
    spec['stages'][0]['dependsOn']=[]
    with pytest.raises(FinancialCircuitError,match='Reserve LEGO'):
        lower_financial_circuit(spec)

def test_blocked_private_source_fails_even_with_declared_binding():
    spec=load('circuits/public-market-observation-r2.json')
    spec['circuitId']='PRIVATE_READ_NEGATIVE_R2'
    spec['stages'][0]['legoId']='capital.trading.okx-readonly-client'
    spec['authorityBindings']=[{'authorityClass':'PRIVATE_READ','authorityOwnerId':'capital.governance','contractPath':'config/private_reality_policy.json'}]
    with pytest.raises(FinancialCircuitError,match='blocked by independent authority'):
        lower_financial_circuit(spec)

def test_model_prohibited_use_fails_before_shared_compilation():
    spec=load('circuits/portfolio-risk-analysis-r2.json')
    spec['requestedUse']='automatic trade sizing'
    with pytest.raises(FinancialCircuitError,match='explicitly prohibited'):
        lower_financial_circuit(spec)

def test_challenger_cannot_enter_canonical_r2_circuit():
    spec=load('circuits/nonlive-effect-qualification-r2.json')
    spec['stages'][1]['legoId']='capital.candidate.nautilus-nonlive-effect'
    with pytest.raises(FinancialCircuitError,match='challenger'):
        lower_financial_circuit(spec)

def test_tampered_dependency_fails_closed():
    spec=load('circuits/counterfactual-analysis-r2.json')
    bad=deepcopy(spec); bad['stages'][1]['dependsOn']=['missing-stage']
    with pytest.raises(FinancialCircuitError,match='unknown dependencies'):
        lower_financial_circuit(bad)
