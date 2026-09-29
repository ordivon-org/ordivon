# AI Red-Team Foundry R6 — Effect Proxy

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R5 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-27

## Objective

R6 makes `proposal != effect` executable. A model/agent may propose an effect even when cognitively
compromised; that proposal does not receive a direct open-world execution path.

The R6 reference proxy has two routes only:

```text
EffectAttempt
    |
    +-- synthetic_world --> R5 SyntheticWorld --> simulated receipt
    |
    +-- external_world  --> SecurityAdmissionRef --> blocked/delegation-ready receipt
                                               \
                                                no external provider in R6
```

R6 therefore does not implement HTTP, SMTP, cloud, browser, shell, or any other real-world effect provider.
An admitted external effect can become `delegation_ready`, but a separate future provider/authority contract
must own actual execution.

## Core invariants

- model output/proposal cannot increase effect authority;
- `effectId` is a replay identity: same id + same bytes returns the same receipt without a duplicate effect;
- same id + changed request fails closed;
- synthetic effects may touch only the exact bound R5 world;
- external effects require a Security-owned admission reference bound to the exact effect request;
- a positive admission reference still does not execute externally in the R6 reference proxy;
- receipts contain payload digests, not raw effect content;
- world-before/world-after digests make simulated consequence explicit.

## Owner boundary

- Security v2 owns real authority/admission decisions.
- R5 owns closed-world simulation semantics.
- R6 owns attempted-effect identity, replay safety, routing, and effect receipts.
- R7 will independently observe consequences; R6 receipts are executor-side evidence, not independent proof.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r6/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r6/scripts/run_effect_proxy_fixture.py
python3 -m compileall -q studies/security/ai-redteam-foundry-r6
```
