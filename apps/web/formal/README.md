# Agent effect response consistency R1

The browser or Agent must never mistake an earlier asynchronous admission
decision for the current effect outcome. Web owns the canary effect receipt;
Security owns evaluation of the request; the store retains its transaction
fence. Neither UI nor an AG-UI adapter is an authority.

## Finite model

`AgentEffectResponseR1.tla` models one authenticated Agent, one exact effect,
one in-flight asynchronous decision (ALLOW or STEP_UP), and one interfering
authority change or other legal exact commit. The current policy checks exact
committed replay before re-resolving the current unique grant. The legacy
policy abstracts the former routes: STEP_UP wrote a pending approval without
reconciliation; ALLOW relied on the selected grant's commit fence, which did
not detect a new overlapping grant.

| Obligation | Concrete source / behavior |
|---|---|
| NoStaleApproval | Re-resolve grant identity, digest, revision after await, before registering a pending approval. Revocation/expiry/ambiguity cannot create a new pending approval through this request. |
| ExactCommitWins | An exact committed receipt supersedes a late decision, before a new pending approval or write. Actor/digest/action/resource equality remains checked by WebStore. |
| NoAmbiguousCommit | A newly overlapping matching grant fails closed after ALLOW, before calling the existing transaction. |
| Reachability | Both ordinary step-up and replay remain reachable; a policy that always denies does not satisfy acceptance. |

The implementation boundary is `../src/agent-canary-routes.ts`.
The concrete refinement witnesses are the three deterministic asynchronous
interleaving tests in `../test/agent-authority.test.ts` using the real
Security evaluator and Fastify route. They failed on the earlier route
behavior and passed on the candidate; model checking does not replace these
implementation witnesses.

Scope: single Web canary process with synchronous SQLite operations between
await boundaries; the model does not establish multi-process DB
linearizability, a complete grant/approval lifecycle, WebAuthn physical
presence, runtime implementation refinement, or UI/product acceptance.
Previously issued pending approvals are outside this model; any subsequent
effect must still satisfy the owner commit fence. Do not infer production
installation or authorization from this proof.

## Execute

Reuse the existing Runtime TLC pin
(`services/runtime/formal/toolchain.lock.json`). From the repository root:

```sh
mise run web:formal:effect-response
# Or, if the pinned JAR is elsewhere:
ORDIVON_TLA_TOOLS_JAR=/absolute/path/tla2tools-v1.7.4.jar \
  mise run web:formal:effect-response
```

Expected: the current configuration passes; each of the three legacy
configurations violates its named invariant, and both reachability controls
violate their deliberate "never" invariants. Temporary TLC state is removed.
This task is explicit rather than an unconditional dependency install or
new default gate.
