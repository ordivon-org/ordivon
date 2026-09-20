---
schema_version: 1
id: game.station-zero-v3.external-provider
title: Station Zero v3 — External Provider Boundary
profile: research
lifecycle: current
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-11
---
# Station Zero v3 — External Provider Boundary

Station Zero v3 owns bounded context, legal Candidate identities, decision admission, World consequence, replay and evaluation meaning. It does **not** own model HTTP transport, credentials, provider retry, credential pools, rate-limit handling or model-specific SDK configuration.

The Game-facing extension point is `StationZeroV3AgentProviderFactory`. A standalone research server may import one external module via:

```text
ORDIVON_GAME_RESEARCH_SURFACES=1
ORDIVON_GAME_V3_PROVIDER_MODULE=/absolute/path/to/provider-module.ts
```

The module must export `providerModule` or a default object matching:

```text
schemaVersion: 1
kind: ordivon.game.station-zero-v3-external-provider-module
providerId: stable external identity
providerFactory: StationZeroV3AgentProviderFactory
evidenceSnapshot?: provider-neutral bounded call evidence
```

The external module owns credentials, endpoint/model choice, retries, concurrency, cooldown, failover, cost accounting and transport evidence. Game revalidates every returned decision against the exact current context and legal Candidate frontier.

Historical `ORDIVON_GAME_V3_DEEPSEEK_*` and `ORDIVON_GAME_V3_PROVIDER=deepseek` configuration is retired and fails closed.
