---
schema_version: 1
id: game.v3-provider-transport-subtraction-r1-20260911
title: Ordivon Game — Station Zero v3 Provider Transport Subtraction R1
profile: engineering
lifecycle: candidate
source_role: migration-evidence
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-11
base_candidate: 3aa753ed695f9219362130a2519fb5843a3b1044
---
# Station Zero v3 Provider Transport Subtraction R1

## Result

The opt-in Station Zero v3 research surface no longer owns a DeepSeek HTTP client, credential discovery/pool, rate-limit cooldown, retry, quarantine, weighted scheduling, per-credential semaphore, or model-specific server configuration.

Physically retired from the Game source graph:

```text
src/station-zero-v3/deepseek-provider.ts      553 LOC
src/station-zero-v3/deepseek-credentials.ts   580 LOC
-----------------------------------------------------
TOTAL                                         1133 LOC
```

The former DeepSeek-specific test apparatus and operating guide were also retired/replaced.

## Retained Game authority

Game retains only provider-neutral semantics:

```text
StationZeroV3AgentContext
       ↓
StationZeroV3AgentProviderFactory
       ↓
StationZeroV3AgentDecision
       ↓
assertStationZeroV3AgentDecision
       ↓
Plan Preview / World consequence / replay / evaluation
```

Game continues to own the bounded context, exact Candidate frontier, directive authority, decision validation, retained decision identity, World consequence, and evaluation meaning.

## External provider boundary

A standalone research server may now load an external module only through:

```text
ORDIVON_GAME_RESEARCH_SURFACES=1
ORDIVON_GAME_V3_PROVIDER_MODULE=/absolute/path/to/provider-module.ts
```

The external module supplies `providerFactory` and optionally bounded provider-neutral call evidence. It owns all provider/model configuration, credentials, endpoints, SDK/HTTP mechanics, retries, concurrency, failover, cooldown, cost accounting, and provider currentness.

Historical `ORDIVON_GAME_V3_PROVIDER=deepseek` and `ORDIVON_GAME_V3_DEEPSEEK_*` configuration is explicitly rejected rather than silently translated.

## Research runners

Historical fresh-agent evaluation runners were preserved without retaining transport debt:

- Casefile and Concept Lab now load `ORDIVON_GAME_EXTERNAL_JSON_MODEL_MODULE`;
- Station Zero v3 evaluation is now `scripts/eval-station-zero-v3-external-provider.ts`;
- no research runner in this candidate opens model credential files or calls `/chat/completions` directly.

These are experiment/evaluation adapters, not provider owners.

## Regression boundary

`test/game-provider-execution-subtraction.test.ts` now asserts that both retired v3 files remain absent and that neither the server nor generic provider module contains model HTTP/credential/retry machinery.

Focused affected verification after subtraction: `12 / 12 PASS`.

Full repository verification after subtraction: `414 / 414 PASS`, `0 FAIL`. The lower total versus the previous 427-test candidate is intentional: 13 tests of the retired DeepSeek credential/retry/pool implementation were removed and replaced by 3 provider-neutral external-boundary tests. No Game domain test failed.
