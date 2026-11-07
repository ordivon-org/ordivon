# General formal-thinking LEGOs — separate Human and Agent guides

**Scope:** Optional, on-demand reference of the existing
`recursive-lego-calculus` Skill, not an Owner, standalone Skill, central
registry, new verifier or parallel release process. Use the natural Owner and
existing `method-router`, `compositional-contracts` and
`references/formal-model.md`. A *thinking LEGO* is an independently
replaceable **method responsibility** only once it has a real consumer and
an admitted full R2.1 contract; the families below are **selection patterns**,
not a predeclared population of LEGOs.

## First principles: what a formal thinking LEGO must accomplish

The scarce output is a **decision that remains defensible when the implementation
or provider changes**, not more math notation or more test files. Start with:
(1) one consumer and normative property `phi`; (2) the relevant state/effects
and environment assumptions; (3) a cheaper/more trustworthy method than the
existing alternative; (4) a falsifiable completion or rejection condition.

For a genuinely declared/admitted method responsibility retain the full typed
`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`. Interpret
`I` as problem/source/consumer/evidence, `O` as a *scoped* choice,
obligation or witness, `S` as method/decision state (or justified Unit),
`pre` as validity and currentness assumptions, `post` as its promised
*reasoning* result, `inv` as properties preserved during refinement,
`eff` as real side effects or empty effects, `c` as qualified cost,
`epsilon` as scoped approximation or genuine zero (not fabricated),
`prov` as exact theory/tool/version/source/evidence, and `unfold` as
optional deeper model, proof or implementation. Record typed
`UNKNOWN(reason, scope, obligation)` for unsupported facts.

Do not claim a theorem about the world from an encoding without a bridge:
`Spec -> Model -> Check/Proof -> Source refinement -> Installed consumer`
contains **distinct obligations**. A verified finite abstraction is not an
automatically verified PostgreSQL transaction or distributed service.

## Industrial core modes: choose by the missing evidence, not by tool popularity

The following six **reusable reasoning patterns** are derived from documented
engineering practices. They are *not* a newly mandatory lifecycle, separate
prover, Owner, Agent role or six automatically admitted R2.1 LEGOs.
A method choice is useful only when it changes the next real consumer decision.

| Core mode | Grounded industrial practice | What Human decides / what Agent actually delivers |
| --- | --- | --- |
| **Contract-first specification** | AWS TLA+ distributed design; Microsoft P/P# event-machine specifications in Azure engineering | Human states an unacceptable outcome; Agent makes safety/liveness assumptions and legal transitions explicit *before* implementation |
| **Model checking with real failure replay** | Google's CAV 2026 network protocol work used seven TLA+ models, recreated prior bugs and checked fixes; state projection helped assess model coverage | Human asks whether known failures are reproducible; Agent provides model trace, concrete feasibility and explicit model scope |
| **Verification-guided development with implementation bridge** | AWS Cedar proves Dafny-model properties and uses differential randomized comparisons against its Rust engine; AWS authorization engine also used shadow/differential production comparison for a legacy replacement | Human demands behavioral compatibility; Agent binds exact model/source versions, known equivalence limits, difference findings and real production comparison |
| **Composable, incremental source summaries** | Meta Infer uses Separation Logic and procedure pre/post summaries, reusing analyses across changed code; the analyzer supports review-time feedback | Human cares about time-to-action and useful bugs; Agent records proof dependence and rechecks only affected callers/assumptions, *unless* coverage is unknown |
| **Independent proof checking / small trusted base** | Anthropic + Theorem generated executable-level proofs checked by Rocq; the claimed no-crash properties are conditional on RISC-V, modeled Linux and single-thread execution assumptions | Human sees exact theorem and trust assumptions; Agent may propose proof but the native independent kernel determines acceptance |
| **Trace-to-evaluation improvement and subtraction** | OpenAI advocates trace grading, real task evals and iteration; Anthropic recommends simple composable agent patterns and increasing complexity only for measured value | Human evaluates actual outcome and maintenance cost; Agent records failures, adds only value-earning checks, repairs and retires obsolete custom paths |

### Soundness and economic decision rules

1. A proof about an abstract model does **not** prove source behavior unless
   a concrete simulation, refinement relation, translation argument, or
   other qualified bridge exists. AWS Cedar's differential randomized testing
   is useful corroboration of model/production equivalence across generated
   inputs, **not** a universal deductive proof of that equivalence.
2. A model-checking counterexample may be a real spec/design error or an
   abstraction artifact. The agent must replay or check feasibility before
   eliminating the offending transition. Reconstructing a *known* production
   failure is strong model-relevance evidence, not total state-space coverage.
3. A procedure summary applies only while the source cut, relevant callees,
   environment assumptions, and effect readset are current. An incremental
   proof-cache HIT without these preconditions is stale evidence. Meta's
   industrial approach argues for **local summary reuse**, not global
   verification of arbitrary future changes.
4. Independent checker PASS must be scoped by the trusted base, theorem
   statement, exact build and environment assumptions. Anthropic's 2026
   assembly-level no-crash results cover selected single-threaded static
   RISC-V Linux binaries with stated resource limits; they do not certify
   arbitrary deployed architectures, networks or all bug classes.
5. Agent task evaluation/trace grading measures behavior on selected tasks.
   It is **not** a proof of an invariant. Conversely, a valid theorem is not
   evidence that the human's problem framing or domain objective was right.
6. **Stop or subtract** when a simpler native method satisfies the actual
   consumer. A generic code analysis dashboard, second registry, new
   proof-file format, mandatory six-stage Agent workflow or an added
   sample test needs its own earned consumer; method popularity is not one.

### Two views of the same mode

**Human-facing question:** "What important failure must never occur,
under which conditions, and what live outcome would convince me that the
change worked?" The reply should identify the required guarantee, the
best industrial precedent, which of model/proof/code/live standing is
known, at least one plausible falsifier, and the affected consumer.
No solver commands are necessary for an ordinary acceptance decision.

**Agent-facing decision:** The method operator takes the current property,
Owner/consumer, exact SourceCut, evidence readset, assumptions and budget;
it returns a chosen existing method/provider, one scoped obligation,
negative witness or counterexample, a source-to-consumer bridge if needed,
and a stop/retire decision. First check whether a weaker existing method
already meets the consumer contract. If not, choose one dominant mode;
combine modes only for separate obligations. Invalidate proof evidence on
changes to dependent source, assumptions, checker or installation.
Publish through the existing Owner and protected Git path. Never establish
a shared reasoning ledger or a second execution authority.

**Ordivon example:** Runtime's Job/Attempt recovery behavior primarily
needs state-machine exploration (AWS/Google/Microsoft modes), followed by
source/receipt replay on native Runtime. Host Work revision arithmetic
primarily needs code contracts and source checking, but PostgreSQL CAS,
MCP ingress and installed source still need targeted real checks.
Harness Agent/Tool trajectories benefit from task-specific trace evaluation,
while its tool-dispatch invariants require independent state-model/source
evidence. These are different claims and must not be merged into a
single vague "verified" label.

### Industrial primary sources

- AWS, *How Amazon Web Services uses formal methods* (2015):
  https://www.amazon.science/publications/how-amazon-web-services-uses-formal-methods
- AWS, *How we built Cedar with automated reasoning and differential testing*:
  https://www.amazon.science/blog/how-we-built-cedar-with-automated-reasoning-and-differential-testing
- Microsoft, *Building Reliable Cloud Services Using P#*:
  https://www.microsoft.com/en-us/research/publication/building-reliable-cloud-services-using-p-experience-report/
- Google, *Model Checking for Flexible Networking Protocols* (CAV 2026):
  https://research.google/pubs/model-checking-for-flexible-networking-protocols/
- Meta, *Finding inter-procedural bugs at scale with Infer*:
  https://engineering.fb.com/2017/09/06/android/finding-inter-procedural-bugs-at-scale-with-infer-static-analyzer/
- Anthropic, *LLMs are making formal software verification feasible
  at a much larger scale* (Oct. 2026):
  https://www.anthropic.com/research/formal-verification
- Anthropic, *Building effective agents*:
  https://www.anthropic.com/research/building-effective-agents
- OpenAI, *Evaluate agent workflows*:
  https://developers.openai.com/api/docs/guides/agent-evals

## Select one method family that changes the decision

| Decision-changing question | Mature *thinking* LEGO pattern | Existing capability/provider and appropriate evidence |
| --- | --- | --- |
| Where should responsibility be split? | **Information hiding / bounded context** (Parnas); hide independent design decisions, not every function | Owner public APIs + `design-structure-matrix`; observed dependencies, consumers and replacement seam |
| Can two providers compose or replace each other? | **Assume–guarantee algebra**, compatibility, refinement and quotient | `compositional-contracts`; Pacti for supported contract classes; explicit assumption discharge and non-circular guarantee |
| Can Job/Attempt/Workspace or Agent/Tool reach an illegal state? | **Transition relation + inductive invariant** | Current Owner TLA+/TLC or Quint; actual initial-state set, enabled actions, finite model scope and counterexample trace |
| Do ordering, retries or recovery break liveness? | **Temporal reasoning, fairness and recovery semantics** | TLA+/TLC/Quint where supported; fairness assumptions and checked temporal scope; simulation cannot prove universal liveness |
| Can two relational facts violate identity or reference consistency? | **Relational constraints / bounded counterexamples** | Alloy or native PostgreSQL constraints; exact relational scope and real transaction consumer |
| Is a pure expression, boundary or type obligation satisfiable? | **Hoare / design-by-contract + SMT** | Z3/cvc5, Python CrossHair; executable source path, premises, solver result and unsupported paths recorded |
| Does Rust code satisfy its own assertions or mathematical spec? | **Implementation-directed deductive or bounded verification** | Kani for covered Rust harnesses; Verus for supported Rust specifications; exact build/toolchain and limitations |
| Must a statement hold for all admitted mathematical structures? | **Proof as terms, induction, substitution law** | Lean kernel-checked theorem; exact axioms, theorem, imports and relation to implementation |
| Did the abstract checker find a real defect? | **CEGAR with concrete-feasibility check** | Current Owner model checker + actual source/trace replay; do not erase feasible counterexamples as “spurious” |
| Can old code, tests, Work or Workspace be retired? | **Consumer-reachability / evidence currentness** | Existing `consumer-rooted-retirement.md`, conditional Lean law and native Git/Runtime/Host owner evidence; UNKNOWN blocks a deletion claim dependent on missing consumers |

These patterns overlap. Do **not** mint one declared LEGO per row, impose every
method, or add universal proof plumbing. Prefer DELETE unsupported claims,
REUSE admitted local or mature upstream proof, then COMPOSE a thin bridge.
Only implement a novel method when a concrete unmet consumer obligation
survives comparison.

### Apply methods to Ordivon's actual Owner abilities

The *current* Owner roots are documented in tools/repo/owners.toml;
the following are **recommended proof targets**, not claims
that each theorem is already proved. The final column is deliberately
non-substitutable physical/consumer evidence.

| Existing Owner(s) | Formal-thinking question and chosen model | Indispensable real acceptance |
| --- | --- | --- |
| Runtime | Job/Attempt/Workspace transitions; admission witness and recovery invariants (TLA+/TLC, Rust/Kani on actual covered functions) | Native durable Job/Attempt recovery, Workspace close and Linux/Windows readback |
| Host | Work CAS and snapshot revision, message/reply reachability, transactional identity and references (contract/SMT/CrossHair; relational model) | PostgreSQL transaction, MCP Work/Topic/Message consumers and live Host doctor |
| Harness | Agent/Tool proposal, binding, execution, timeout, cancellation and replay (TLA+/Quint and source refinement) | Actual Tool trace, Runtime receipts and real Agent consumer |
| Gateway | Provider/Owner route selection, identity forwarding, request/error contract (assume–guarantee) | Gateway-to-Host/Runtime actual routed request and negative route |
| Network | DNS/proxy/VPN path and policy-dependent egress, recovery under failures (transition system, fault model) | Native DNS/tunnel/egress and connection reset experiments |
| Security | Explicit principal/capability authorization and no privilege amplification (relational invariant / SMT) | Actual current principal and rejected unauthorized effect |
| Skills | Source priority, exact binding, package digest and currentness (deterministic resolution relation) | Live skills.resolve/read from the natural Skills service |
| Workstation | Installed Git SourceCut, immutable release, atomic switch/rollback (state machine) | systemd, actual executable/interpreter, installed-source readback |
| Artifact / Preservation | Digest integrity, lineage and retention/restoration preconditions (algebraic relations) | Open/recover actual bytes and target consumer |
| Distribution | Destination receipt and retry/idempotency contract (state machine) | Remote destination readback; local packaging PASS is not delivery |
| Media | Source-to-export identity, transformations, loss/quality bounds (typed contract, SMT where decidable) | Actual rendered/encoded media inspection and target platform |
| Capital | Accounting conservation, no look-ahead, position/risk bounds and simulation/live separation (Lean/Z3 and source tests) | Real feed provenance, historical replay and simulation consumer |
| Game | ECS state invariants, inventory/resource bounds, replay determinism (model + Kani where applicable) | Playable Bevy/Godot run and real Agent-controlled session |
| Composition / authority & capability catalogs | Assumption discharge, provider refinement, evidence currentness (Pacti/Lean/TLC) | One actual provider resolution and composed Owner consumer |
| Web / Control Plugin / Chaoxing | User-visible request/action, permission and result semantics (interface contract) | Native browser/plugin action and external readback |

Do not mark any row complete from the method choice alone. Some capabilities
are intentionally outside the presently installed prover's sound fragment;
prefer an honest UNKNOWN plus a focused real consumer to an elaborate
unconnected model.

### Verification and composition laws

- **Validity:** `pre` must be satisfiable *and reachable* under the stated
  initial states; exercise deliberately false properties to rule out vacuity.
- **Induction:** `Init => Inv` and `Inv /\ Next => Inv'` (with the
  correct state/transition definitions) establishes invariant preservation
  for admitted executions, not an unrelated source program.
- **Contract composition:** each consumer assumption is discharged by a
  producer guarantee or stated environmental assumption; a local PASS is
  insufficient if the wiring, effects, identity, timing or authorization differ.
- **Replacement:** the new component must not demand a stricter environment
  or offer weaker required behavior in the relevant contract order; prove
  refinement including failures and effects, not merely matching types.
- **Model refinement:** name the abstraction/simulation/refinement mapping
  and show the direction needed for the property. Bounded TLC/Alloy success
  cannot by itself establish the real source relation.
- **Transfer example for safety:** if `Traces(Impl)` is contained in
  `gamma(Traces(Model))` under identical environment assumptions,
  `Model |= Safe_model`, and the concretization mapping preserves
  `Safe_model -> Safe_real`, then the safety claim transfers to the
  admitted implementation traces. Each inclusion and property-preservation
  premise needs its own evidence; merely naming a refinement mapping
  is not proof of its validity.
- **Evidence:** distinguish `DECLARED`, `MODEL_CHECKED`,
  `SOURCE_REFINED`, `INSTALLED_CURRENT`, `CONSUMER_ACCEPTED`,
  `FALSIFIED` and `UNKNOWN`, with source cut, config, assumptions,
  checker version, actual exit status, and affected consumers. Terms are
  evidence descriptions, **not** a new state machine or database enum.
- **Test substitution:** delete duplicate sample assertions only after the
  original behavioral obligation and the implementation-to-model bridge
  are covered *at current source*. Preserve the smallest necessary real
  PG/network/systemd/hardware/end-to-end acceptance for external effects.
  Count removed redundant maintenance, coverage of required properties
  and actual bugs found, not number of proof files.

## Human: outcome-first decision guide

You need not learn Lean or SMT to request or accept a formal LEGO.

1. **State one desired outcome and final consumer:** “A recovered Runtime Job
   cannot be committed twice,” “Host Work revision never overflows,” or
   “Gateway routes to the authorized current target.” Say which failure would
   matter, not how many tests should exist.
2. **Ask for an explicit claim:** Is it a mathematical identity, a finite
   state-machine property, a specific Python/Rust source guarantee, or a
   deployed behavior? Require the claim to state its assumptions and
   what's outside its scope.
3. **Prefer the lightest qualified method:** Type/contract/SMT for arithmetic
   and pure invariants; TLA+/Quint for concurrency and recovery; Lean for a
   general mathematical law; existing direct consumer integration for real
   effects. Ask what would disprove the claim.
4. **Compare replacements by consumer value:** Does an external library or
   existing Owner implementation discharge the same assumptions and
   guarantees? Avoid converting a useful abstraction into ten tiny services.
5. **Accept a traceable result:** named obligation, source/version, proof or
   counterexample, installed readback where relevant, remaining UNKNOWN,
   and concrete obsolete artifacts actually retired. Do not accept a model
   screenshot as proof that a live service has changed.

**Human example:** “Ensure Host Work revisions never exceed PostgreSQL
BIGINT.” The useful acceptance is **two separate answers**: (a) the
arithmetic and typed API bound are checked; (b) the installed Host can still
read and commit a Work through PostgreSQL. The first cannot replace the
second. The normal user need not reproduce every solver invocation.

## Agent: repeatable source-bound procedure

1. **Locate the real authority:** read `AGENTS.md`, current SourceCut,
   `tools/repo/owners.toml`, the natural Owner's `mise tasks ls`,
   actual MCP/CLI entrypoint, installed SHA, and named consumer. Do not
   reuse stale reports as observations. Discover existing Skills first.
2. **Represent the obligation:** freeze `phi`, state `S`, legal inputs,
   environment `Gamma`, transition/effect boundary and the smallest
   relevant R2.1 projection. For an independent declared LEGO, bind all
   eleven typed coordinates; for a candidate keep `INCOMPLETE`/
   `UNKNOWN`, not fabricated formal standing.
3. **Select via the table:** classify proof as algebraic, state, temporal,
   relational, implementation or cross-provider. Use only the provider
   with a real matching contract. Check scope, type widths, fairness,
   solver timeout, external effects and dependency currentness.
4. **Challenge the property:** seek a non-vacuity witness (reachable
   successful path and deliberately violated negative oracle), counterexample
   or adverse interleaving. A timeout, unsupported operation or unknown
   refinement relation remains `UNKNOWN`.
5. **Check composition:** prove assumptions discharged, or state missing
   obligations; bind identity, timing, failure, state and effect contracts.
   For source claims verify actual called functions, not a prettier
   disconnected model. Avoid CrossHair on side-effectful code.
6. **Verify with the Owner's existing tools, not a new runner:**
   - `cd tools/formal && mise run verify` — current shared Lean/SMT/
     Quint/Kani/Verus/Alloy selection; inspect `verify.py` for exact coverage.
   - `cd services/runtime && mise run formal:verify` — Runtime TLA+
     model checks with locked upstream JAR.
   - `cd packages/composition && mise run formal:verify` — R2.1
     Owner-boundary model and negative oracles.
   - `cd services/harness && mise run formal:source-refinement` and
     `mise run formal:verify` — use the actual versioned Owner targets.
   - `cd services/host && mise run formal:reply-source` — CrossHair
     on real pure Host code; add actual PostgreSQL acceptance when needed.
   - `mise run gateway:formal:verify` from repo root for the existing
     Gateway proof target. Inspect current tasks before running.
7. **Refine then observe:** compare exact abstraction relation to source,
   run the smallest real consumer sequence through native Owner authority,
   check live release/readback and negative path where material. Do not
   replace implementation evidence with a model PASS.
8. **Subtract:** only with current dependency/consumer closure and qualified
   proof + source refinement, remove duplicative examples/adapter carriers.
   Retire Workspaces using native Runtime `workspace.close` with verified
   release and exact digest, not manual path deletion.
9. **Handoff in the existing Owner/Host Space:** `property | scope |
   assumptions | source/proof digests | checker result | implementation
   bridge | real consumer | retained tests | removed artifact | UNKNOWN`.
   This is a response format, not a new evidence registry.

**Agent example — Work CAS revision.** Let `M=2^63-1` and
`S={r in Z | 1<=r<=M}`. For a committed increment:
`pre: 1<=r<M`, `post: r'=r+1`, `inv: r' in S`.
CrossHair can analyze the real pure increment function and Pydantic can
reject an `expectedRevision=M` at the MCP ingress. That evidence **does
not** prove the psycopg compare-and-swap is atomic, that retry receipts
are idempotent, or that the installed service uses the checked SHA. Those
separate duties stay with native PostgreSQL tests and Host/Gateway live
readback. When the implementation or SourceCut changes, recheck the
relevant evidence; do not keep claiming a proof about old bytes.

## Mature upstream foundations (consult for the matched obligation)

- Parnas, *On the Criteria to Be Used in Decomposing Systems into Modules*,
  CACM 1972, DOI https://doi.org/10.1145/361598.361623
- Lamport, TLA+ and its TLC/TLAPS tools: https://lamport.org/tla/tla.html
- Quint executable state specifications: https://quint.sh/docs/what-does-quint-do
- Pacti contract composition/refinement/quotient:
  https://www.pacti.org/docs/getting_started/
- Lean kernel-checked proofs: https://lean-lang.org/doc/reference/latest/
- Z3 SMT and quantifier limitations:
  https://microsoft.github.io/z3guide/docs/logic/Quantifiers/
- Kani Rust verification: https://model-checking.github.io/kani/
- Verus source specifications: https://verus-lang.github.io/verus/guide/
- CrossHair side-effect and proof limitations:
  https://crosshair.readthedocs.io/en/latest/contracts.html
- Agent Skills on-demand references, not a second agent system:
  https://agentskills.io/specification

**Stopping condition:** the one decision is grounded in an admitted
consumer, the smallest method gives either a scoped proof, concrete
counterexample or explicit UNKNOWN, a real implementation claim has its
necessary source/installed bridge, and no unconsumed duplicate remains.
