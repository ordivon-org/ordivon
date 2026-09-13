# Migration Strategy

## 1. Migration is gradual and evidence-driven

The current Ordivon estate remains operational while Ordivon Next is built in parallel. Historical repositories are not bulk-copied into this repository.

For every historical component:

```text
observe current responsibility
        -> classify using the new model
        -> find mature external owner
        -> identify residual Ordivon value
        -> map or adapt
        -> run a real workload
        -> verify
        -> cut over only when proven
        -> archive/retire old ownership
```

## 2. No big-bang rewrite

The new architecture becomes authoritative by successfully solving real problems, not by declaration. Existing working paths remain until an independently verified replacement exists.

## 3. Historical repositories are sources, not dependencies by default

A historical repo may become:

- a retained external capability provider;
- a domain profile source;
- a thin adapter source;
- a migration/evidence source;
- a read-only archive;
- fully retired.

No repo is automatically merged into Ordivon Next.

## 4. First-pass estate mapping

| Historical area | New classification hypothesis | Initial action |
| --- | --- | --- |
| `ordivon-game` | Domain Life-Cycle Profile source | read-only mapping; first vertical slice |
| `ordivon-research-v2` | Domain Life-Cycle Profile source | retain working external stack; later second slice |
| Engineering/software workflows | Domain Life-Cycle Profile | reconstruct from mature SE/software standards when needed |
| `ordivon-operations-v2` | Enabling capabilities/integration substrate | reuse rather than absorb |
| `ordivon-runtime` | Physical execution provider | keep external and replaceable |
| `ordivon-network-v2` | Enabling network capability | keep external; consume as capability |
| `ordivon-artifact-v2` | Enabling artifact capability | keep external; expose capability contracts |
| `ordivon-distribution-v2` | Enabling distribution capability | keep external; expose capability contracts |
| `ordivon-security-v2` | Cross-cutting discipline/tooling source | map controls/validators; avoid a universal security platform |
| `ordivon-workstation-v2` | Enabling system | consume substrate facts/capabilities |
| `ordivon-host*` | retired historical mixed responsibilities | preserve retirement/provenance only; use domain owners, mature providers and projection-only views |
| `ordivon-harness` / Agent Birth | agent execution/provisioning history | use only where mature agent interfaces do not cover real needs |

## 5. Promotion rule

A migrated concept enters Ordivon Next only if it has at least one of:

- a necessary domain mapping not supplied by upstream knowledge;
- a necessary adapter between mature capabilities;
- a reusable composition proven on a real task;
- a verification/evidence mapping necessary to establish semantic success;
- a cross-domain contract proven by multiple materially different domains.

## 6. Retirement rule

Historical ownership can be retired after:

- replacement capability is identified;
- interfaces/semantics are mapped;
- at least one relevant real workload passes;
- domain V&V confirms equivalent or better outcome;
- recovery/rollback path is understood;
- authoritative source and migration evidence are recorded.
