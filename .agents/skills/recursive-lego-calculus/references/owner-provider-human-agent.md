# Owner / mature LEGO adoption — Human and Agent

This is an **optional reference under the existing recursive-lego-calculus Skill**.
It adds no Owner, execution service, registry or mandatory gate. For Ordivon
source maps see `tools/repo/owners.toml`, and for current orchestration see
`docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`.
These repository paths are informative; they are not portable Skill dependencies.

## Shared representation

A LEGO is a goal-conditioned, independently replaceable responsibility with
identity, inputs, outputs, behavioral contract and real consumer acceptance.
The method/capability distinction describes responsibilities, **not** an
automatic Skill/Tool type system. A discovered file, paper or provider is only
a candidate. A separately DECLARED/ADMITTED LEGO uses the complete typed
`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` contract; state and
effect may be genuinely empty and unknown fields remain typed UNKNOWN.
Never infer production adoption from a test-only consumer or a source commit.

## Human guide — outcomes instead of infrastructure

1. **Describe the result and consumer.** Examples: “Close old Host discussions
   but keep their evidence readable”; “Use mature quantitative research
   capability in Capital without creating another engine.”
2. **Choose your success predicate.** Can the intended person or product consume
   the new output? Does the service work now, not merely build?
3. **Use the existing Package and Owner.** Open
   `catalogs/capabilities/packages/INDEX.md` and the relevant package;
   check the Owner at `tools/repo/owners.toml`.
4. **Compare DELETE / REUSE / mature provider / thin composition** against
   the same outcome and ongoing maintenance burden. Ask only for the options
   that materially change the decision.
5. **Accept real before/after evidence:** observable state, original source PR,
   installed readback, consumer success and any unresolved gap. Technical
   proof detail is available on request, not mandatory for ordinary use.

*Example:* A completed Host Topic is not the same as a meaningless message.
The installed Host `topic.state.set` can change `open→closed`
using expected state and message high-sequence while retaining all messages.
The Human should receive the closed state and a successful old-message read,
rather than a raw database deletion or a new custom lifecycle service.

## Agent guide — contracts, currentness and effects

1. **Freeze the real SourceCut.** Read `AGENTS.md`, current
   `origin/main`, natural Owner and package entrypoint, public API,
   installed release and observed consumer. Dated docs are not current truth.
2. **Choose the smallest theory.** Use existing `method-router` for
   uncertain method selection. Bounded Context determines authority;
   `design-structure-matrix` checks observed edges and cycles;
   `compositional-contracts` checks assumptions and substitutability.
3. **Bind one responsibility.** For independent LEGO declarations instantiate
   all eleven typed R2.1 coordinates; candidate/UNKNOWN is not PROVED.
   Do not create per-file LEGO cards or a new central index.
4. **Qualify external providers using existing evidence.** Check version/commit,
   license, maintenance, interface, authority, effect, negative control and
   consumer-specific compatibility. OpenSSF Scorecard supplies risk signals,
   not security certification. SLSA provenance describes builds, not algorithm
   correctness. Agent Skills delivers instructions, not execution authority.
5. **Perform effects through the natural Owner.** Reuse Git/Host/Runtime
   native operations, source/type/concurrency contracts and existing releases.
   Do not directly delete live Postgres rows to simulate a native lifecycle
   effect. Verify current readbacks and preserve the actual consumer.
6. **Publish, then subtract.** Run the affected native tests and appropriate
   independent check, merge via protected GitHub queue, verify installed
   SourceCut and live consumer, then retire obsolete adapters/build artifacts
   and Workspace through Owner-native close. No second management system.
7. **Return a compact handoff:**
   `goal | owner | consumer | decision | external provider/skill |
   exact source | executed effect | acceptance | retired carrier | UNKNOWN`.
   Skip fields that do not affect the decision.

*Runtime example:* A clean Workspace whose HEAD is in `origin/main`
is not automatically released. Check current Job/Host consumers and exact
`sourceStateDigest`; invoke the native `workspace.close` with
its real consumer-released standing, then read back absence and preserved
Git/consumer state. No `rm -rf` bypass.

*Worktrunk example:* The existing
`catalogs/capabilities/providers/worktrunk.md` has scoped source-locked
read-only Git-worktree parity evidence. It does not prove Runtime Workspace
identity, lifecycle, recovery or authorization equivalence. Treat it as an
optional Workstation UX provider pending a real user.

## Mature upstream references (only as needed)

- Bounded Context: https://martinfowler.com/bliki/BoundedContext.html
- Team Topologies: https://teamtopologies.com/key-concepts-content/team-interaction-modeling-with-team-topologies
- Agent Skills specification: https://agentskills.io/specification
- Worktrunk: https://worktrunk.dev/faq/
- OpenSSF Scorecard: https://openssf.org/projects/scorecard/
- SLSA provenance: https://slsa.dev/spec/v1.2/provenance
- OpenTelemetry semantic naming: https://opentelemetry.io/docs/specs/semconv/

Stop once the Human can see a real outcome and the Agent can identify the
current source, owner, consumer, effect, acceptance and justified retirement.
