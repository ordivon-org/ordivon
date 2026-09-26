# Capital R2 Acceptance

Standing: **PASS_R2_IMPLEMENTATION**

Exact implementation commit:

```text
b077c9246bda15f032f7f0c70ba716d34752e2ec
```

Exact clean verification Runtime Job:

```text
job-01a0cd76-f7d2-7e53-8c9c-f28fb2fa399a
```

## What changed

R2 is a subtraction/ownership migration rather than an authority expansion:

```text
R1 Capital local generic composition
        ↓ differential qualification
R2 Capital financial semantic lowering
        ↓
public ordivon-composition package
```

The R1 `governance/composition_contract.py` implementation is deleted. Capital retains registry standing, prohibited-use rules, financial authority/effect taxonomy, evidence vocabulary and effect-ordering invariants; Composition owns generic DAG/gate/authority-obligation mechanics.

Four declarative financial circuit specs are current: public observation, portfolio risk, counterfactual analysis and non-live effect qualification.

Current-state projection is generated from machine authorities by `scripts/build-current-state-r2`; Git revision is provenance, not semantic currentness.

## Differential evidence

Before deletion, R1 composition behavior was frozen for four admitted canonical circuits and seven rejection classes. R2 tests continue to compare current lowering against that oracle. The substitution standing is `EQUIVALENT_FOR_CURRENT_CAPITAL_CONTRACT_SPACE`.

## Exact gates

```text
composition:verify    PASS
capital:verify        377 passed / 11 provider-bound deselected / 0 failed
repo:ci               PASS
owner-boundary        PASS
Structure R2          PASS
current-state --check PASS
```

## Authority did not widen

```text
executionLane                 NON_LIVE
productionAuthorization       BLOCK_NOT_GRANTED
externalFinancialWriteAllowed false
privateAccountDataAdmission   NOT_ADMITTED
portfolioRiskBudget           UNSET
```

Repository publication is a separate repository authority step and is not implied by this semantic/mechanical acceptance.
