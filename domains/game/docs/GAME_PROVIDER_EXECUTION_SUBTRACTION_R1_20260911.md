---
schema_version: 1
id: game.provider-execution-subtraction-r1-20260911
title: Ordivon Game — Provider Execution Subtraction R1
profile: engineering
lifecycle: candidate
source_role: migration-evidence
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-11
base_candidate: c89c8c9d599b587807faa7b60410c3955477b365
---
# Provider Execution Subtraction R1

## Result

The current main Mission Control path no longer owns generic cognition-process execution, executable/credential preflight, Codex/Hermes CLI transport, or generic fallback chaining.

Physically retired from the candidate:

```text
src/team/provider-runtime.ts    118 LOC
src/team/codex-cli.ts           113 LOC
src/team/hermes-cli.ts          148 LOC
src/team/provider-preflight.ts  112 LOC
src/team/provider-chain.ts       36 LOC
---------------------------------------
TOTAL                           527 LOC
```

A 16-line `provider-contract.ts` remains only for the Game-facing technical-failure vocabulary used by decision parsing/admission and existing research apparatus.

## New boundary

```text
Game Context / allowed actions
          ↓
TeamDecisionProvider interface
          ↓
external providerFactory implementation
          ↓
structured TeamProviderDecision
          ↓
Game parser + stale-world/action admission
          ↓
Game consequence
```

Game no longer decides how an external provider is launched, where its executable lives, how credentials are discovered, how stdout/stderr are bounded, or whether one provider should fall back to another.

The default product catalog now exposes only:

```text
fixture — deterministic Game-owned baseline
```

An external cognition owner may be exposed to the product only by supplying both:

```text
providerOptions   — explicit user/product-visible provider identity
providerFactory   — externally implemented cognition adapter
```

This keeps provider identity and evaluation condition visible to Game without granting Game execution ownership.

## Removed false authority

The following former endpoint is removed:

```text
GET /api/providers/preflight
```

It previously caused Game to probe executable paths and credential material and then present that local probe as provider readiness. Readiness/currentness belongs to Workstation/Provider/Runtime/cognition owners, not Game.

The browser now renders only providers explicitly present in the Game server's configured provider catalog. It does not disable/enable options based on Game-local executable or credential inspection.

## Fallback

`codex-hermes` and `hermes-codex` are no longer special Game provider identities. Generic provider retry/fallback belongs to the cognition executor/provider layer.

If provider ordering itself becomes an experimental condition, Game may record that condition as an opaque externally supplied provider identity; it still does not own the retry engine.

## Preserved Game authority

The subtraction intentionally retains:

- `TeamDecisionProvider` as the Game-facing cognition port;
- exact `CompiledTeamContext` and allowed-action frontier;
- structured decision parsing;
- context identity validation;
- stale World rejection;
- invented-action rejection;
- provider identity in retained evidence/evaluation conditions;
- deterministic `FixtureTeamProvider` as a Game-owned baseline/test policy.

## Explicit non-scope

Station Zero v3's direct DeepSeek HTTP/credential pool remains under the opt-in `researchSurfaces` apparatus in this round. It is not part of the default Mission Control provider catalog and is recorded as the next provider-transport subtraction frontier rather than silently treated as clean production architecture.

`storage.ts`, `replay/*`, and `deployment/*` are also unchanged in this round.

## Verification

Focused provider/product/replay/web/DeepSeek suite after subtraction:

```text
57 / 57 PASS
```

Full repository verification after subtraction: `427 / 427 PASS`, `0 FAIL`. This closes the bounded Mission Control provider-execution subtraction but does not promote the candidate to `main` or claim the opt-in Station Zero v3 DeepSeek research transport is externalized.
