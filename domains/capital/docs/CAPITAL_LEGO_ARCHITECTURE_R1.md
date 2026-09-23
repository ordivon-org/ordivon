# Ordivon Capital LEGO Architecture R1 — Acceptance

Date: 2026-09-23
Standing: **PASS_R1_ACTIVE_SCOPE**
Implementation commit: `847099db22b0f21b2f36b5776133b8c8f748418e`

This acceptance closes the active R1 scope of the Capital LEGO architecture. It is an implementation/verification receipt, not provider, account, investment, settlement, or production-write truth.

## What R1 now is

```text
Current authority/config truth
        ↓
12 functional LEGO roles
        ↓
39-entry machine registry
        ↓
typed authority/effect/evidence/composition contracts
        ↓
┌────────────────────────────┬──────────────────────────────────┐
│ read-only circuits         │ non-live simulated effect circuit│
│ 3 explicit families       │ 5 bounded scenarios              │
└────────────────────────────┴──────────────────────────────────┘
        ↓                                ↓
standard Agent Skills             reconciliation → accounting
        └──────────────┬─────────────────┘
                       ↓
         architecture / information-flow /
                  FMEA-FTA gates
```

The seven business/source owners remain **Markets, Trading, Portfolio, Risk, Research, Governance, Accounting**. Functional LEGO are composition roles, not replacement source packages.

## Verified inventory

| Surface | R1 standing |
| --- | --- |
| Functional LEGO roles | 12 |
| LEGO Registry entries | 39 |
| Canonical registry entries/modules | 34 |
| Read-only circuit families | 3 |
| Standard project Agent Skills | 3 |
| Non-live effect scenarios | 5 |
| Production/live wave | DEFERRED_BY_DESIGN |

Read-only families:

- `PUBLIC_MARKET_OBSERVATION_R1`
- `PORTFOLIO_RISK_R1`
- `COUNTERFACTUAL_ANALYSIS_R1`

Standard Skills are canonical at:

- `meta/next/.agents/skills/capital-observe/SKILL.md`
- `meta/next/.agents/skills/capital-risk/SKILL.md`
- `meta/next/.agents/skills/capital-reconcile/SKILL.md`

They are advisory routing/procedure only. Removing a Skill does not remove executable Capital semantics, and a Skill cannot grant provider, credential, Runtime, owner, or financial-write authority.

## Read circuit boundary

A read circuit can mechanically compile, run current owner-native primitives, and produce a digest-bound receipt. Its receipt is explicitly:

```text
MECHANICAL_COMPLETION_ONLY
```

It does not infer risk appetite, rank scenarios, select investments, approve trades, or claim semantic completion. An `UNSET` owner risk budget remains `UNSET`.

## Non-live effect boundary

The admitted R1 effect class remains only:

```text
SIMULATED_EXCHANGE_ORDER_EFFECT
```

The circuit composes the existing owners rather than recreating an OMS:

```text
current non-live admission
        ↓
durable reservation
        ↓
bounded simulated provider episode
        ↓
Trading reconciliation
        ↓
accounting resolution
        ↓
durable SQLite reconciliation
```

Dogfood results:

| Scenario | Reconciliation/accounting disposition |
| --- | --- |
| FILL | POST_PENDING_TRANSFER |
| PARTIAL_FILL_SLICES | POST_PENDING_TRANSFER |
| CANCEL | VOID_PENDING_TRANSFER |
| DENY | VOID_PENDING_TRANSFER |
| UNKNOWN_AFTER_SUBMISSION | NO_MUTATION |

All five scenarios ended with durable-ledger reconciliation `MATCH`. UNKNOWN remained pending/no-mutation. No real-money or external financial write was attempted.

## Historical/current evidence split

Protocol-v2 migration evidence and fixtures remain frozen byte-for-byte. New current R1 receipts are written to the separate `acceptance/` root rather than mutating historical `evidence/`.

Frozen migration baseline:

- evidence: 54 files, `sha256:c6a4f1293de042a5df2797afc8e49b90b736d704135ea4aad20914d7cb2e82be`
- fixtures: 4 files, `sha256:69ca14c2747c05f4adbe08f178ebc4351d381283da0ef71ea5507af4819d5159`

## Cross-cutting gates

W7 now mechanically checks:

- Markets has no upward imports into Trading/Portfolio/Risk/Research/Governance/Accounting.
- Gateway, Runtime and Host do not import Capital domain semantics.
- Nautilus/QuickFIX-n/OPA/TigerBeetle candidate tool paths do not become canonical source dependencies.
- Capital Skills exist only in the standard Agent Skills source, not a private Capital Skill format.
- observer/private information visibility does not transfer effect authority.
- secret credential bytes cannot flow into repository Skills/current acceptance/registry.
- blind resend after UNKNOWN is forbidden by reconciliation/accounting behavior.
- terminal accounting state cannot be resurrected by stale/contradictory provider observations.
- candidate frameworks cannot silently become source owners.

## Exact verification

The implementation commit above was verified from a clean detached workspace by Runtime Job:

`job-01a0cd27-d7d6-73b1-b1b7-bfe084bc5555`

Result:

```text
Ruff              PASS
pytest             369 passed
provider-bound     11 deselected
failed             0
```

W7 targeted architecture/information-flow/FMEA gates independently passed 8/8 in Runtime Job `job-01a0cd25-bb18-7f83-92dc-d08bd6897ec7`.

## Authority standing after R1

Nothing in this acceptance widens financial authority:

```text
execution lane                 NON_LIVE
production authorization       BLOCK_NOT_GRANTED
external financial write       false
private account data           NOT_ADMITTED
portfolio risk budget          UNSET
```

Therefore W6 remains intentionally deferred. Production adapter qualification and production admission require a separate future owner/provider authority event and are not prerequisites for R1 closure.
