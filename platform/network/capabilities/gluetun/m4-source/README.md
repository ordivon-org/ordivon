# M4 — Gluetun owned lifecycle (production default)

This directory is the current source for the admitted Gluetun physical provider
lifecycle. It began as a nonproduction M4 candidate, but the supervised
2026-10-15 cold replacement has now made Gluetun the default production
realization.

## Current composition

- network-v2-gluetun-owned.network: private Podman /30.
- network-v2-gluetun-owned.container: exact pinned Gluetun v3.41.3 image,
  service-level provider-identity guard and Restart=on-failure.
- network-v2-gluetun-owned-adapter.service: compatibility adapter preserving
  the 10.252.246.2:19680 consumer seam.
- network-v2-gluetun-owned.target: durable boot owner for provider + adapter.
- network-v2-browserless-legacy-provider.target and legacy WireGuard/DNS/
  carrier source: disabled rollback realization retained during soak.
- m4-owned-restore-legacy and its service: retained recovery tooling from the
  pre-adoption design; current Gluetun failure recovery is restart-in-place,
  not automatic physical failover to Legacy.

## Provider-mode safety

The durable selector is:

    /etc/network-v2/gluetun/m4-owned-mode.selected

Gluetun physical startup requires the selector, Legacy WireGuard physical
startup requires its absence, and provider-identity-exclusive additionally
checks the opposite physical realization is absent before starting. This is the
mechanical single-Surfshark-ClientIdentity fence.

The selector is a mode input, not an authorization system. A privileged
administrator can still defeat local service isolation.

## Cold-replacement transaction

The acceptance/cold-replacement.sh transaction is the supervised
adoption/rollback path. It:

1. requires the Browserless owner contract to already expose the stable
   10.252.246.2:19680 seam;
2. snapshots Network-owned installed bytes and records active Network consumer
   services;
3. stops Legacy carrier/DNS/WireGuard;
4. proves the Legacy physical interface is absent;
5. creates the durable owned selector and starts Gluetun;
6. waits for a real HTTPS consequence through the Gluetun tunnel rather than a
   listening port;
7. runs mechanism-neutral provider consequences and selected live-consumer
   consequences;
8. restores the preimage and Legacy realization if adoption fails.

Network does not invoke or mutate Harness implementation internals. Harness /
Browserless materialization is owned by Harness; Network only reads the
installed owner contract and fails before provider interruption if that
contract is stale.

## Accepted runtime evidence

The successful adoption receipt is under:

    /var/lib/network-v2/m4-cold-replacement/20261014T161339Z-1322564/

The successful transaction established real provider consequences for OpenAI,
Anthropic, Docker Registry, DeepSeek, X, OKX and Binance, with the private
destination witness rejected. Model Provider, Supply-Chain and Windows Chrome
selected consumer consequences also passed.

A later real network-v2-gluetun-owned.target restart recreated the Gluetun
container and re-passed provider readiness. A fresh post-adoption Browserless
carrier check reached https://chatgpt.com/ through its installed proxy launch
contract and returned CHALLENGE_GATED; this establishes the live Browserless
network path without treating provider challenge state as Network success.

## Validation and remaining retirement gate

Ordinary source validation must never touch the live mode selector. Tests use a
temporary M4_PROVIDER_MODE_MARKER when exercising fallback helpers.

Still pending before deleting Legacy rollback assets:

- deliberate host/WSL cold-boot acceptance;
- ordinary workload soak;
- final retirement cleanup of Legacy WireGuard/DNS/carrier and historical
  recovery-only source where no longer referenced.

Legacy retention is rollback policy, not the current provider mode.
