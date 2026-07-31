# P0 Core A constraint audit

Audit basis: Ordivon Computer `be5fe779267f0225dd37c570932c7d71ee5223a7`,
`core/foundations.md` SHA-256
`7ac5eb7a158d169277a53f59c6655a4201bacc58e9a00d1fef86ab874560698f`.

This audit applies A0–A16 to the active Game path. It is not a new policy
engine. Its purpose is to make every durable constraint state what capability
it buys, who consumes it, what it costs, and when it should be deleted.

## Ownership path

```text
Player / Mission Control
→ Station Zero domain coordination
→ specialist Action Proposals
→ domain authority and compatibility admission
→ Embedded Host Task/Effect/Dispatch authority
→ deterministic Game World
→ World Event and per-Intent evidence
→ VerificationReceipt and TaskOutcome
```

`TeamHost` is therefore a Station Zero domain coordinator despite its historical
class name. It is not the generic Ordivon Host or Harness. New generic Session,
Task, provider-loop, or recovery responsibilities must not be added here.

## Constraint ledger

| Constraint | Core A basis | Unrecoverable loss prevented / capability purchased | Recurring cost | Current consumer | Disposition and deletion trigger |
|---|---|---|---|---|---|
| one authoritative World reducer | A1, A2 | prevents split World truth and partial mutation | reducer/version maintenance | every Run and replay | **keep**; delete only if another owner becomes the sole World authority |
| command identity and retained receipt | A5, A9 | prevents duplicate Effects after response loss | identity and receipt bytes | recovery and replay | **keep-local** while duplicate delivery is possible |
| expected World revision/digest | A2, A6, A10 | prevents stale Context or Proposal commitment | one comparison per admission | World and Host adapter | **keep-local**; narrow only if backend offers an equivalent atomic precondition |
| atomic Team Tick | A1, A2 | prevents partial simultaneous-action commitment | conflict evaluation | Station Zero multi-Actor Runs | **keep** while simultaneous actions exist |
| three-specialist legal-subset enumeration | A11, A13 | purchases deterministic conflict resolution for the fixed Station Zero team | exponential enumeration, currently bounded to 3 | Station Zero only | **keep-bounded**; reject promotion beyond 3 until another workload proves a general solver is needed |
| exact authority Decision/Grant binding | A3, A7, A8, A12 | prevents one approval authorizing another Actor/action/world | binding records and occasional interruption | supervised Mission Control | **keep-local**; remove generic approval concepts not bound to a concrete consequence |
| accepted Verification before completed Outcome | A2, A10 | prevents Tool/Dispatch success from becoming false Task completion | one verification record | Host completion authority | **keep** |
| hash-chained World and Host journals | A1, A5, A10 | detects history mutation and supports reconstruction | storage and full-audit time | replay/evidence | **keep**, but do not add per-step global scans |
| snapshots | A1, A11 | reduces replay latency without becoming truth | cache invalidation and storage | point-in-time replay | **keep as cache**; delete if measured replay remains cheaper without them |
| single-Agent M1/M2 Host path | A11, A14 | preserves frozen historical and equal-budget comparison evidence | roughly 2.5k LOC plus debug APIs | compatibility fixtures and future #40 ablation | **freeze**; move/delete after the equal-budget study and Harness replacement retain the needed evidence |
| raw `/api/agent/*`, `/api/team/*`, `/api/actions` | A8, A11 | supports reversible engineering and old Runs | route/test surface | developers only | **debug compatibility**; remove from default product after consumers migrate |
| Game-private generic Host growth | A13 | none demonstrated beyond the embedded contract adapter | duplicate semantics and drift | no valid consumer | **forbid** until a second non-Game workload proves an unowned responsibility |

## P0 changes

1. The three-Actor subset selector is now a named, versioned Station Zero policy
   with an enforced limit; it cannot silently grow into a generic scheduler.
2. Team and Host table queries are localized in `TeamStore` and `HostStore`;
   product/replay/comparison layers no longer know their SQL schemas.
3. Product and debug/compatibility API surfaces are documented separately.
4. Existing World, Effect, authority, verification, journal, and replay
   invariants remain unchanged.

## Deferred deletion

The single-Agent compatibility stack and Game-private Effect/Dispatch projection
wrappers are not deleted in P0 because Harness v0 and the equal-budget single
versus multi-Agent experiment are active dependencies. They receive no new
features. Physical deletion is gated on evidence, not on architectural taste.
