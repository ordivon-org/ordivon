# AI Red-Team Foundry R5 — Deterministic Synthetic World

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R4 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-27

## Objective

R5 provides the smallest deterministic closed-world substrate needed to test tool-bearing model/agent behavior
without granting real-world effects. It is intentionally **not** a second AgentDojo, browser platform, mail
server, database, or authorization engine.

The stable Ordivon-owned waist is:

```text
SyntheticWorldSpec
        |
        v
WorldAction
        |
        v
SyntheticWorldProvider
        |
        +--> WorldActionResult
        +--> WorldStateReceipt
        +--> provider-native trace/evidence
```

External environments such as AgentDojo/Inspect-style worlds should later adapt into this waist rather than
being reimplemented inside Ordivon.

## Core invariants

- the world has no network client and performs no host/external effect;
- synthetic secrets must use the explicit `ORDIVON_SYNTH_CANARY_` namespace;
- simulated mail destinations must end in `.test` / `example.test`;
- simulated HTTP destinations must use `http(s)` and a `.test` hostname;
- instruction-like content is always data; world state never interprets content as authority;
- identities/roles are immutable experiment fixtures, not Security authority;
- same spec + same ordered action sequence => same state/trace digests;
- reset returns exactly to the initial world state and empty trace;
- outbound synthetic-secret crossings are exactly detectable without an LLM judge.

## Owner boundary

- Security v2 owns real authority/admission/standing.
- R4 owns environment/isolation contract.
- R5 owns deterministic synthetic world semantics only.
- R6 will own attempted-effect mediation; R5 does not authorize open-world effects.
- R7 will own independent observation; R5's exact canary helper is a reference predicate, not an independent observer.

## Reference services

R5 includes only generic in-memory service kinds sufficient for contract testing:

- `files` — read/write named synthetic resources;
- `mail` — simulated send into a `.test` address;
- `http` — simulated request to a `.test` hostname;
- `database` — read/write/query named synthetic resources.

These are reference semantics. Real benchmark environments remain provider-owned.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r5/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r5/scripts/run_world_fixture.py
python3 -m compileall -q studies/security/ai-redteam-foundry-r5
```
