# AI Red-Team Foundry R7 — Independent Consequence Observation

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R6 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-27

## Objective

R7 gives the red-team stack an observer path that does not trust the R6 executor receipt as world truth.
It reuses Security v2's existing consequence-verification semantics rather than inventing a second standing
machine.

```text
R6 executor receipt -----\
                          +--> consistency evidence --> Security v2 consequence policy
R7 world observation ----/
```

The reference provider observes the R5 synthetic world directly. It is authoritative for the closed synthetic
world used by `synthetic_agent` evaluation, but it is only `process_local_independent_code_path`: it is NOT a
hostile-code, independent-process, or independent-kernel observer. R7 fails closed if that reference provider
is asked to claim applicability to `hostile_code`.

## Core invariants

- observer input is the world provider, never an R6 receipt;
- observation captures its own before and after anchors;
- exact world-spec and environment digests are bound;
- outbound state, synthetic-secret crossings, state digest and trace digest are independently read;
- forged or changed executor receipts cannot alter an already captured observation;
- receipt/observation reconciliation reports consistency only; it does not mint Security standing;
- the Security v2 `world-truth` plane adapter is available only for threat classes supported by the observer binding;
- hostile-code experiments require a stronger observer provider with real process/kernel separation.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r7/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r7/scripts/run_observer_fixture.py
python3 studies/security/ai-redteam-foundry-r7/scripts/run_security_v2_policy_compat.py
python3 -m compileall -q studies/security/ai-redteam-foundry-r7
```
