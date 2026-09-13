# Migration Candidates R1 — 2026-09-12

This is a migration inventory, not a fixed Ordivon topology. Entries record what can be reused from the current estate without importing historical subsystem identity into Core.

## Decision classes

- **REGISTER_PROVIDER** — keep the existing repository/service external; migrate only capability metadata, boundaries and evidence references.
- **MIGRATE_KNOWLEDGE** — migrate reusable rules/mappings/lessons, not implementation ownership.
- **MIGRATE_RETIREMENT_RECORD** — preserve disposition/provenance only.
- **HOLD** — current state is active/dirty/semantically unsettled; do not migrate yet.
- **ARCHIVE_CANDIDATE** — no forward ownership justified; preserve Git history until explicit retirement.

## R1 inventory

| Source | Observed state | New-model treatment | R1 decision | Why |
| --- | --- | --- | --- | --- |
| `ordivon-operations-v2@047ca7f2a943` | mature external-first shared substrate; only untracked pytest cache observed | task-local execution/integration capability provider | **REGISTER_PROVIDER** | already separates n8n, Temporal, Runtime, OTel, OpenTofu, systemd/Ansible responsibilities and avoids domain semantic ownership |
| `ordivon-runtime@e2c25e03dde1` | clean current runtime | physical/local execution capability provider | **REGISTER_PROVIDER** | valuable operational surface; should remain replaceable and outside Core ontology |
| `ordivon-network-v2@10cc82bf2c0c` | clean; `LOCAL_WSL_GRADUATED`; independent Linux reference acceptance | network capability provider + verification evidence | **REGISTER_PROVIDER** | already describes itself as composition/verification rather than custom stack |
| `ordivon-artifact-v2@39b6281b9b59` | clean; accepted forward source authority | artifact build/validation/delivery capability provider | **REGISTER_PROVIDER** | standards-first, external validators, OCI/OPA, explicit fail-closed release gates |
| `ordivon-distribution-v2@03ccc562160b` | clean; provider read/readback paths proven, real writes authority-gated | distribution/effect execution capability provider | **REGISTER_PROVIDER + MIGRATE_KNOWLEDGE** | strong reusable rules for exact effect binding, external acceptance and ambiguous retry |
| `ordivon-security-v2@17ebfb63f710` | clean; external-first security verification substrate | security verification capability family | **REGISTER_PROVIDER + MIGRATE_KNOWLEDGE** | provider-native SARIF/CycloneDX/OPA etc.; thin residual evidence/authority semantics |
| `ordivon-workstation-v2@88c05d922d43` | formally retired 2026-09-12 | historical migration/retirement evidence | **MIGRATE_RETIREMENT_RECORD** | active responsibilities already transferred to Operations/upstream tools |
| `ordivon-research-v2@9d767a028719` | working tree currently has modified/deleted migration/cutover files | research domain knowledge/profile source | **HOLD implementation; MIGRATE_KNOWLEDGE selectively** | direction is compatible, but current source state is not a clean authority snapshot |
| `ordivon-host-v2@35b9defb1d2e` | clean; responsibility closure completed 2026-09-13 | historical migration/retirement evidence; no successor Host/Board | **MIGRATE_RETIREMENT_RECORD** | `host.*`, `task.*`, `board.*`, `news.*` and `attention.*` responsibilities are assigned to domain owners, mature external providers, disposable projections, or deletion; see `migrations/records/host-board-retirement.md` |
| `ordivon-market-capital-next@0483e58017a5` | clean clean-room domain reconstruction | market/capital domain working-set source | **HOLD provider registration; keep domain-local** | already follows mature-external-first rule; domain is active and should not become Core structure |
| `ordivon-market-capital-v2@fd0a15db0152` | clean older external-first semantic skeleton | historical/domain comparison source | **ARCHIVE_CANDIDATE** | successor `market-capital-next` is cleaner and more aligned with current direction |

## Wave-1 migration rule

Wave 1 copies no implementation code from these repositories. It records:

1. capability offered;
2. provider/source repository and revision;
3. what the provider explicitly owns and does not own;
4. current acceptance/standing;
5. activation conditions;
6. evidence pointers;
7. known reusable lessons.

The original repository remains the source authority for implementation until a later explicit cutover says otherwise.
