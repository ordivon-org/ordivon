# M1 Canary Source Acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

Scope: `meta/next`, `platform/security`, `platform/network`.

This acceptance covers Git source/history relocation, deterministic replay, owner-local environment behavior, and owner-native verification. It does **not** authorize deployment, service cutover, state migration, release unification, old-repository retirement, or domain/scientific standing changes.

## History and tree evidence

| Owner | Frozen source | Rewritten source | Import merge | Bundle SHA-256 |
| --- | --- | --- | --- | --- |
| Next | `a119ccb11d32edebe08f197a4af8f8a67f8c086f` | `606526ebd6d9a6e7031906ebf69f01f940e65713` | `97fcbd5c1d0a5c8a166e175cf35f5b4b484e3bbe` | `3acf7b5b325b04ca3342b6817334db2031d8770c7355839a3ccf73867e662e80` |
| Security | `f5db8508857ee844323f145891fb9cb832b12785` | `fd72f6a175c9180606ae0c4638665d5aee91ec77` | `0f3fd80c12d600c32e796eb4d32636e692abe65d` | `91d92ba84c5c43e970ce86555f6d81b444561e9033e044d023ae45702f2cd329` |
| Network | `9aec70bbfa3c8847dbd52c03a939c61f45e2f338` | `ffd138649e1c9719c26238cf940fc7f2c03b56ff` | `a6d52c63df7a93a02e043b8372a568d8b3b7d9e4` | `4033ac574b7d9bc0215014bb6a2879dbcef49675977160900ec16df690bdaa06` |

For every owner, an independent replay using the preserved Git bundle as source transport reproduced the committed rewritten revision exactly. The replayed git-filter-repo commit map was byte-identical to the tracked map, and the source tree equaled the imported subtree tree at the import merge.

## Owner-native verification

- Next: 102 tests passed; Ruff check/format, authority catalog, standard-native enterprise integration, reasoning-waist, governance-persistence and Gitleaks gates passed.
- Security: 57 tests passed; Ruff passed.
- Network: `task all:validate` passed, including sing-box, blackbox exporter, Prometheus, systemd static verification, provider configuration and Finance consumer-policy validation.

At M1 acceptance, systemd unit files and running processes had zero references to `/root/projects/ordivon/`. Known live consumers still referenced pre-monorepo paths.

Therefore: `source accepted != production cut over`.
