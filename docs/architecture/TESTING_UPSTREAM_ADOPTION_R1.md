# Upstream-first testing — Agent operating guide (2026-10-16)

This is **navigation**, not a new test framework, a new Skill, or a second CI authority. Follow `AGENTS.md`: work in natural Owner directories; do not replace Owner verification with a generic green signal.

## Default Spec → SOP → Plan → Tool → Acceptance

1. **Spec**: state the observable behavior, failing counterexample, legitimate-equivalent control and pass/fail condition.
2. **Established SOP**: choose an upstream-native unit, property, integration, contract, browser E2E, or Godot visual/input testing practice; never create a per-Bug Skill.
3. **Execution Plan**: bind existing mature Skills (`user-agents/tdd`, `user-agents/diagnosing-bugs`, `obra-superpowers/verification-before-completion`) and actual Owner Tools.
4. **Execute** focused native test, then the Owner's `mise run verify` or documented queue qualification.
5. **Acceptance** reports exact source SHA, tool/runtime, test count, positive/negative/equivalent cases and separate **PASS / FAIL / SKIP / NOT_RUN / ENV_BLOCKED** status. Local green does not equal protected GitHub green.

## Verification by property and consumer (select on demand)

Formal-first specifies *what must hold*, not a universal demand that every Owner run every formal tool. Before selecting verification, record the exact property, environment/SourceCut, implementation, affected consumers, permitted effects and falsifying result. For a routine local edit, use focused native checks; for a high-consequence boundary, strengthen the proof/test chain as the actual failure mode requires.

| Claim / failure mode | Suitable established verification | What a PASS does **not** establish |
| --- | --- | --- |
| Types, input and output shape | Owner compiler, schema checker, static analysis and unit tests | Temporal behavior, real consumer correctness |
| Invariants over many inputs or action sequences | Property-based and model-based/state-machine testing, with shrinking and replay | An exhaustive mathematical theorem |
| Abstract safety/liveness/contract obligations | Lean, TLA+/TLC, Z3/SMT or the Owner's current formal model, each with explicit bounds and assumptions | Implemented code refinement or deployed effects |
| Model-to-code or cross-language compatibility | Kani/Verus/CrossHair only on supported code; independent reference, differential and consumer-driven contract (CDC) tests | Correctness outside the model/tool scope |
| Persistent effects and recovery | Real Owner integration, PostgreSQL read-back, concurrency, fault injection and replay | External or domain acceptance without its own oracle |
| Agent choices and probabilistic predictions | Trace/trajectory eval, independent outcomes, held-out cases, calibration and cost/error comparisons against a simple baseline | Authority, causal effect or universal generalization |

Prefer the Owner's *already installed* runner, not the example tool by name: Rust Cargo / cargo-nextest, proptest, cargo-fuzz, Kani or Verus where supported; Python pytest, Hypothesis, CrossHair or Z3 where relevant; TypeScript's existing Node runner, fast-check and Playwright, rather than requiring Vitest. Specialized proof languages do not expand the Rust/Python/TypeScript implementation policy. Preserve the Owner's lockfiles; keep upgraded dependencies and affected tests consistent.

Keep three evidence claims separate: **specification/model property**, **implementation refinement**, and **current consumer/deployed outcome**. A checked finite trace or toy model is not a universal liveness theorem. CDC and replay require the actual old/new observation boundary; static imports alone are not observed consumers. Binding evidence to SourceCut, tool/version, environment assumptions, readsets and consumers makes invalidation precise; when a required dependency changes or cannot be observed, retain UNKNOWN. A successful process exit, model conclusion, test-only loop or untrusted tool text never grants permission or establishes semantic acceptance.

Stop once the scoped acceptance predicate has owner-native execution evidence and the remaining uncertainty is explicit. Do not add a generic testing service, verifier registry, redundant Skill or mandatory global preflight to implement this guidance.

## Formal-first proof-to-consumer retirement decision (native Owner method)

This section **reuses** the natural Owner's formal toolchain, contract, code review,
existing GitHub CI, and observed consumer. It creates no second registry, proof
engine, orchestration service, or mandatory global gate. The claim is
**property-scoped**, never file-count-scoped:

1. **Specification** — identify a precise contract, environment assumptions,
   allowed effects, state projection, source revision, and counterexample.
   For a declared Recursive LEGO R2.1 responsibility use all eleven existing
   typed coordinates: I/O/S/pre/post/inv/eff/c/epsilon/prov/unfold.
2. **Model** — choose the smallest faithful state machine, relation, refinement
   type or assume-guarantee contract. State finite bounds, fairness and
   abstraction explicitly; UNKNOWN is not FALSE.
3. **Proof or model checking** — run the existing Owner's Lean/SMT/TLC/Quint/
   Alloy/Kani/Verus/CrossHair procedure; record actual executable/toolchain
   versions, assumptions, source readset and negative controls. A bounded
   check is never an unbounded theorem.
4. **Implementation refinement** — prove, or independently falsify, the map
   from the actual Rust/Python/TypeScript operation and observed effects to
   the model. A valid Lean theorem alone does not discharge this obligation.
5. **Real consumer** — retain the smallest indispensable native integration
   check for database transactions, recovery, filesystem identity, process
   lifecycle, network, credential authority, OS, hardware or deployed user
   behavior not represented by the refinement.
6. **Subtraction** — for each old test, identify the exact property it checks,
   its consumer, whether the same failure is already excluded by the *current*
   proof+refinement, and whether it has a distinct failure oracle. Delete or
   merge only the strictly dominated test; keep an independent consumer
   observation where the abstract-to-physical seam is not proved.

A test is **retirement-qualified** only if its property and fault model are
subsumed by a valid, current formal claim **and** its real implementation
refinement (or the test is demonstrably unused with no distinct consuming
requirement). Cross-check actual imports, native jobs, installed versions,
Host Work/Message references and source branches for lifecycle deletion.
The original test's own success is not evidence that the test is redundant.
A contract that is merely *written*, a model that is merely *simulated*,
and a job whose exit code is zero each leave a different evidence gap.
Keep test statuses PASS / FAIL / SKIP / NOT_RUN / ENV_BLOCKED distinct.

### Owner-specific formal targets and retained physical consumers

| Natural Owner | First high-value obligation | Native proof / implementation candidate | Irreducible real consumer |
| --- | --- | --- | --- |
| Runtime | Job/Attempt/Workspace transitions, exactly one committed lease, recovery monotonicity | TLC/Quint transition model + Verus/Kani on Rust state effects | Actual Registry PG readback, process crash/restart and replay |
| Host | Atomic Work revisions, Topic/Message reference integrity, idempotency | SQL constraints + transaction serializability model + Python contracts | Real PostgreSQL concurrent writers, MCP pagination and readback |
| Harness | Agent/tool state trace, cancellation, observation ordering | LTS and assume-guarantee contracts, CrossHair on pure Python paths | Actual tool adapter, Agent trajectories, timeout/cancel effects |
| Gateway | Routing determinism, authorization delegation, response provenance | Contracts + SMT/Quint route/deny semantics | Real northbound traffic, headers and rejection at provider seam |
| Network | DNS/VPN/egress policy under failure and reconnect | TLA+/fault state model + route constraints | Actual OS route, DNS, tunnel and physical egress observation |
| Security | Principal/policy separation, no unauthorized effect | Information-flow/noninterference, SMT and policy model | Native credential provider, OS principal and deny outcomes |
| Skills | Deterministic current binding, stale reference rejection | Typed binding contract, finite state model, pure resolver properties | Installed Skill source, consumer read, revision fences |
| Workstation | Installation/rollback preservation, restart currentness | State/refinement of deployment transitions | Real Windows/WSL/systemd/Chrome restart and installed SHA |
| Artifact | Content digest/identity, transformation provenance | Functional contract and byte-level Kani/CrossHair | Actual parse, conversion and durable Artifact readback |
| Distribution | Release receipt/order/idempotency | Refinement types, state model and effect contract | Actual destination acknowledgement and delivery outcome |
| Media | Asset/source identity, provider and export output contract | Typed provenance, compositional contracts, pure metadata properties | Real codec/render/export bytes and native consumer |
| Preservation | Retention obligations, recoverability before deletion | Temporal state model and integrity contracts | Restore from retained original bits with fresh consumer |
| Game | ECS state invariants, replay determinism | State-machine property checking, Rust model/refinement | Bevy or Godot native input, frame, save and real play |
| Capital | No future-data leakage, allocation/cash invariants | Refinement types + Kani/CrossHair/SMT | Historical market point-in-time replay and paper ledger settlement |
| Web | API schema/route and client state invariants | TypeScript types, pure state-property checks | Actual browser, accessibility and deployed API |
| Control Plugin | Manifest/tool binding and no authority amplification | Interface contract and effect/refinement check | Actual plugin install, tool invocation and consent projection |
| Composition | LEGO assume-guarantee compatibility and substitutability | Existing compositional-contracts Skill, Pacti/SMT/Lean | At least one real consumer of the composed capability |
| Authority Catalog | Source currentness and stable identity | Provenance rules / constrained type checks | Exact real authority resolution and latest source readback |
| Capability Catalog | Provider discovery and binding validity | Set/graph invariants and type checks | Actual chosen provider callable and observed result |
| Chaoxing | Session/action idempotency and outcome integrity | State machine and effect pre/post contracts | Real Chrome and remote session acknowledgement |

The table is a **selection map**, not a claim that all listed tools are already
installed, used or proved for every Owner. In particular, LTS/Lean/R2.1
theorems do not establish the Rust production migration, PostgreSQL
writer fencing, an external issuer's authority or real network behavior.

### Human guidance — acceptance and deletion choices

Start from one concrete user-facing outcome. Ask which Owner owns the
domain fact or effect, which property is valuable, and what observation
would distinguish correctness from an implementation that only passes
its own tests. Prefer a proven native capability over a custom wrapper.
Approve test deletion after the specific property has been discharged,
but keep recovery and real-device checks whenever the remaining effect
crosses a model boundary. Read merged source, installed binary and
executed consumer as separate statuses. For data cleanup, verify every
final consumer and preserve the last independent recoverable bytes before
using native lifecycle deletion.

### Agent guidance — minimal executable sequence

Resolve the actual consumer and natural Owner through the existing
tools/repo/owners.toml and current Host Work; inspect current SourceCut
and exact installed/readset dependencies. Reuse method-router,
recursive-lego-calculus and compositional-contracts only if relevant;
read the current Skill, do not create a per-property Skill. Select one
formal technique suited to the property, run a real positive and
falsifying negative, and trace its assumptions to the implementation.
Execute only the Owner's focused native verification and the smallest
real physical consumer that remains outside the model. For every
removed test/file/Workspace, record a witnessed consumer substitution,
source/artifact digest, provenance, native deletion receipt, and
post-delete readback in the existing Host Work/Topic. Report
SPECIFIED / MODEL_VERIFIED / IMPLEMENTATION_REFINED / CONSUMER_OBSERVED
separately; mark anything not established UNKNOWN. Do not create a
fourth verifier or a second Host/Runtime cleanup authority.

## Executable Agent Tool binding — upstream Skills + native Owner commands

This is task **Spec → established third-party testing SOP/Skill → task Plan →
native Owner Tool → observed acceptance**. Never copy SKILL.md or invent a
parallel Agent test framework. The installed Ordivon Skill MCP returns these
approved exact IDs via `skills.search` / `skills.read`:

- `obra-superpowers/test-driven-development` or `user-agents/tdd`: Red → Green
  and behavior seams; choose one lead rather than duplicate two workflows.
- `obra-superpowers/systematic-debugging`: diagnose reproducible test failures.
- `obra-superpowers/verification-before-completion`: real execution before
  claiming completion.

Skill lookup is dynamic. If a binding is not visible to the requesting Agent,
do not pretend it was activated. Execution uses the existing `mise` and
framework-native test runners, **not a new Ordivon test dispatcher**.

| Task | Direct native Tool | Evidence boundary |
| --- | --- | --- |
| Host Python property/contract example | `cd services/host && mise run test:focused` | Hypothesis `@given` on real RFC 8785 canonicalization, plus independent literal example |
| Host another exact test node | `cd services/host && HOST_PYTEST_NODE=tests/test_contract_policy.py mise run test:focused` | Scoped pytest test, *not* whole Host DB verification |
| Rust selected core test | `cd services/runtime && mise run test:focused` | Installed cargo-nextest optional runner, JUnit `target/nextest/ci/junit.xml` |
| Rust another exact filter | `cd services/runtime && RUNTIME_TEST_EXPR='test(explicit_root_workspace_identity_is_not_forbidden_by_policy)' mise run test:focused` | That native test, not the entire Runtime suite |
| Source Owner qualification | `cd services/host && mise run verify`, or `cd services/runtime && mise run verify` | The existing Owner full gate |
| Find the actual executable surface | `cd services/host && mise tasks ls`, or `cd services/runtime && mise tasks ls` | Official mise task discovery; no custom registry |

Host's `test_canonical_property.py` is an executable, reusable upstream
Hypothesis idiom. An intentionally inverted equality produced a real failing
two-key counterexample (RED); restoring the real contract passed (GREEN).
The separate reference example has fixed RFC 8785 output bytes and does not
derive its expectation from the implementation.

## Use these existing mature sources, not another Ordivon framework

| Natural task | Preferred upstream / official docs | Ordivon native entry / decision |
| --- | --- | --- |
| Python behavior, fixtures, parameter tables | [pytest](https://github.com/pytest-dev/pytest), [fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) | `cd services/host && uv run python -m pytest -q tests/FILE.py`; also Harness/Gateway owner |
| Python generated invariants | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | Already in Host; actual `test_canonical_property.py` runs with upstream Hypothesis via `mise run test:focused` |
| Disposable PostgreSQL | [testcontainers-python](https://github.com/testcontainers/testcontainers-python) | Already in Host dev dependencies; qualified small real PG18 trial, **not** approved to replace Host queue (see binding caveat) |
| Rust focused unit tests | [cargo-nextest](https://github.com/nextest-rs/nextest), [JUnit reference](https://nexte.st/docs/machine-readable/junit/) | `cd services/runtime && cargo nextest run --locked --lib -p ordivon-runtime-core --no-default-features --features transactional-runtime -E 'test(public_requests_reject_unknown_fields_and_path_escape)' -P ci`; native optional fast feedback |
| Rust complete source gate | [Cargo](https://github.com/rust-lang/cargo) | Keep `cd services/runtime && mise run verify` (Cargo + clippy + environment + docs). Nextest does not replace it |
| Browser end-to-end | [Playwright](https://github.com/microsoft/playwright) | Already pinned in Web, Game TS and Harness. Invoke existing Owner E2E tasks |
| TypeScript unit | [Node test runner](https://nodejs.org/api/test.html) | `cd apps/web && pnpm test`; `cd domains/game && pnpm test`. No new Vitest requirement |
| Native Godot 4 | [GUT](https://github.com/bitwes/Gut), [gdUnit4](https://github.com/godot-gdunit-labs/gdUnit4) | Candidate only. Verify actual project/engine/Godot headless input & video before installing either |
| Only if repeatable scaffold gap appears | [Cookiecutter](https://github.com/cookiecutter/cookiecutter), [Copier](https://github.com/copier-org/copier) | Do not install another generator globally until official Owner tools prove insufficient |
| Owner and CI tasks | [mise](https://github.com/jdx/mise), [GitHub Actions](https://github.com/actions/runner) | Owner `verify_task`, `queue_verify_task`, `tools/repo/affected_owners.py`; no parallel scheduler |

These repositories were checked against GitHub stars, recent activity and license metadata on 2026-10-16. A high star count is a **discovery filter**, not evidence of an installed tool or a reason to duplicate Node / Cargo / Python runners.

## Upstream-native test templates, not custom scaffolding

- Python: use pytest's **parametrize** for valid, invalid and equivalent cases; use **fixtures** to scope external dependencies; Hypothesis to generate inputs and shrink real failures. Source: official pytest/Hypothesis links above.
- PostgreSQL: `from testcontainers.community.postgres import PostgresContainer` with `with PostgresContainer("postgres:18", driver=None) as db: ...` is a working upstream context manager. A 2026-10-16 real local trial showed PG server version **180006** and successful teardown. **Safety caveat:** testcontainers-python 4.15.0 by default binds port to `0.0.0.0` and `::`, whereas Host's existing queue script binds `127.0.0.1`. Do not silently substitute it on shared/production host; a safe upstream-supported loopback bind must be demonstrated first. For disposable hosted CI, evaluate runner isolation separately.
- Rust: the previously installed system binary was 0.9.143. The updated **Runtime-local** `mise install` now installs upstream `cargo-nextest 0.9.148` via the official [mise HTTP backend](https://mise.jdx.dev/dev-tools/backends/http.html), using a GitHub Release mirror solely for transport. The artifact's published GitHub API SHA-256 is pinned in `services/runtime/mise.toml` together with exact byte size; the 12,127,365-byte mirror download independently passed SHA-256 and the native mise installation successfully produced version 0.9.148. Only `linux-x64` is qualified; on other platforms do not assert an install. The optional native `services/runtime/.config/nextest.toml` CI profile writes JUnit. A selected test ran **1 PASS / 389 filtered** under 0.9.148, not full Runtime-suite qualification. Keep the existing full Owner `mise run verify`.
- Godot: **no default GUT/gdUnit4 installation**; browser tests do not imply real Godot input or frame-based qualification.
- CI: use established Owner selection and real dependencies. A root `mise.toml` or `owners.toml` change may select all Owners, even if intended for one. Do not equate SKIP with PASS.

## Explicitly deferred, not silently constructed

Do **not** build `.agents/skills/ordivon-test-*` phases, a global test-results database, another test dispatcher, or new approval gates. Do not add Nx, Vitest, Cypress, Act, Playwright MCP or custom test-generation services without a specific unmet native consumer. Favor upstream instructions/templates over copying their internal code.

**Historical example only:** GitHub PR #129 (U4/Host PostgreSQL CI) currently has a separate required GitHub CI failure at Runtime supply-chain policy due to rustls 0.23.45 advisories. Its local Host PASS is not protected-main acceptance. This guide deliberately does not modify Runtime security dependencies or disguise that failure.
