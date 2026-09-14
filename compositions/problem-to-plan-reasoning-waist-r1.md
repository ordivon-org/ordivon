# Composition: Problem → Validated Configuration → Plan R1

Status: **LOCAL MECHANICAL SMOKE PASS / DOMAIN-NEUTRAL SKELETON ONLY**

```text
Problem / requirements
  ↓ domain-native representation
RDF graph projection
  ↓
SHACL shape validation
  ↓
OR-Tools configuration / optimization
  + Z3 logical invariant cross-check
  ↓
Unified Planning problem
  ↓ selected planner
Plan
  ↓
execution provider chosen by task shape
```

## Applicability

Use only when the problem has enough stable structure to name candidate capabilities/actions, constraints and a goal. Do not force exploratory concept discovery into this composition.

## Execution handoff

- n8n: API/SaaS/integration automation;
- Temporal: durable long-running workflow when actually activated;
- Runtime: exact local physical execution/evidence;
- domain-native provider: domain-owned actions and facts.

## Evidence

Acceptance is recorded by `evidence/acceptance/reasoning-waist-r1-acceptance-20260914.json` produced by `scripts/check_reasoning_waist_r1.py`.

## Boundary

A valid configuration/plan proves only consistency with the encoded model. Reality/V&V remains mandatory.
