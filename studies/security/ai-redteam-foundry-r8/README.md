# AI Red-Team Foundry R8 — Attack Search Adapter

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R7 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-27

## Objective

R8 makes external attack-search engines replaceable without flattening them into a new Ordivon mega-framework.
Provider-native parsers and artifacts from R1 remain authoritative for provider mechanics; R8 binds their
normalized projections to the R4 experiment environment and R7 observer contract.

```text
PyRIT / garak / Inspect / AgentDojo / future engine
                    |
                    v
        R1 provider-native adapter
                    |
          ProviderFindingProjection
                    |
                    v
          R8 AttackSearchRunSpec
      budget + seed + adaptivity + target
      R4 environment + R7 observer binding
                    |
                    v
       SearchCandidateRef / SearchResultRef
```

R8 does **not** execute an attack engine, grant effect authority, interpret provider-positive as verified world
truth, or mint Security standing. It normalizes identity, controls, and evidence references only.

## Core invariants

- provider/version/run/target identity must match exactly;
- search budget, random seed, adaptivity mode, and feedback owner are committed before normalization;
- the R4 environment must be admitted for its declared threat class;
- the R7 observer binding must be applicable and its digest must match the R4 environment contract;
- candidate identity is derived from provider-native case identity plus the immutable provider artifact/projection digest;
- provider artifacts stay provider-native and retain the R1 `ProviderArtifactRef` projection to Security `EvidenceRef`;
- optional R7 observations are references to independently captured world evidence, never derived from provider outcome;
- no `SearchResultRef` field represents production Security standing;
- hostile-code search fails closed with the current process-local R7 observer and requires a stronger observer provider.

## Adaptivity modes

- `fixed_sequence`: no feedback changes later candidates;
- `provider_adaptive`: provider-native feedback may influence later candidates;
- `observer_adaptive`: an explicitly observer-owned feedback channel may influence later candidates.

These labels describe search mechanics only. They do not enlarge effect authority.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r8/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r8/scripts/run_search_adapter_fixture.py
python3 -m compileall -q studies/security/ai-redteam-foundry-r8
```
