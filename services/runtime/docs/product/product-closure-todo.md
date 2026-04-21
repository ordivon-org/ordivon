# Product Closure Master TODO

## Purpose

Use this document as the single active mother list for the remaining product closure work.

- This is a product-facing execution backlog, not an ADR.
- The list is ordered by delivery and trust risk, not by architectural purity.
- Capability remediation is included only where it directly supports product truthfulness, semantics, and stability.
- Existing ADRs in [docs/decisions](../decisions/) remain the source of permanent architectural policy.

## Closure Principles

- [ ] Principle: Product truth beats smooth illusion.
  - Intent: Never let UI or API wording imply more business completion than the system can prove.
  - Owner: `web` `api` `docs`
  - Proof: `manual screenshot/route check`
- [ ] Principle: Empty / unavailable / error are safer than fake completeness.
  - Intent: No placeholder business rows, fake success states, or silent null fallbacks in product-facing flows.
  - Owner: `web` `api`
  - Proof: `UI state`
- [ ] Principle: Capability work is subordinate to product closure.
  - Intent: Do not expand capability restructuring beyond what is needed to protect product semantics and trust.
  - Owner: `capability` `docs`
  - Proof: `manual review`
- [ ] Principle: New work must follow the fixed phase order in this document.
  - Intent: Prevent parallel cleanup from re-opening already-closed layers or reintroducing mixed abstractions.
  - Owner: `docs`
  - Proof: `manual review`

## Phase Order

- [ ] Phase 1: Experience Truthfulness Stop-Gap
  - Intent: Remove the remaining user-visible truth violations before deeper structural cleanup.
  - Owner: `web` `tests`
  - Proof: `UI state` `build` `pytest`
- [ ] Phase 2: Capability Boundary Freeze For Product Work
  - Intent: Freeze second-layer drift so Experience fixes do not keep landing on unstable contracts.
  - Owner: `capability` `docs` `api` `tests`
  - Proof: `manual review` `pytest`
- [ ] Phase 3: Experience Semantic Clarity
  - Intent: Make object type, action meaning, and time semantics explicit to the user.
  - Owner: `web` `api` `tests`
  - Proof: `UI state` `manual screenshot/route check`
- [ ] Phase 4: Capability Reclassification And Contract Cleanup
  - Intent: Reclassify mixed capability modules without turning the closure effort into a new migration.
  - Owner: `capability` `api` `docs` `tests`
  - Proof: `pytest` `manual review`
- [ ] Phase 5: Long-Tail Closure
  - Intent: Finish trust-tier, lineage, and lifecycle work after all higher-priority closure items are stable.
  - Owner: `web` `capability` `docs`
  - Proof: `manual screenshot/route check` `pytest`

## Dependency Rules

- [ ] Rule: Experience tasks may proceed first if they do not require capability reclassification.
  - Intent: Unblock user-facing truth fixes without waiting on deep internal cleanup.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] Rule: Product wording and state handling changes come before deep contract restructuring.
  - Intent: Fix user-visible harm before internal elegance work.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] Rule: Purely structural capability work waits until Experience P1 is complete unless it blocks product truthfulness.
  - Intent: Keep scope tight and closure-oriented.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] Rule: No P2 task starts until all P0 and P1 tasks in both tracks are complete.
  - Intent: Prevent trust-tier and IA polish from hiding unresolved semantic defects.
  - Owner: `docs`
  - Proof: `manual review`

## Phase 1 — Experience Truthfulness Stop-Gap

- [ ] Remove unconditional “All systems operational” style messaging from homepage.
  - Intent: Homepage summary text must not overstate system health beyond live reachable evidence.
  - Owner: `web`
  - Proof: `UI state` `manual screenshot/route check`
- [ ] Make homepage summary status strictly reflect live reachable state.
  - Intent: Homepage-level status copy must derive from real status checks, not unconditional prose.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Add explicit error state to `RecentRecommendations`.
  - Intent: Recommendations API failures must render as error/unavailable, not empty state.
  - Owner: `web`
  - Proof: `UI state` `pytest`
- [ ] Add explicit error state to dashboard `LatestReportsList`.
  - Intent: Reports API failures must render as error/unavailable, not “no reports yet”.
  - Owner: `web`
  - Proof: `UI state` `pytest`
- [ ] Replace `error -> empty` fallback in dashboard modules.
  - Intent: Dashboard cards must stop collapsing transport/runtime failure into no-data semantics.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Replace `error -> loading` fallback in dashboard modules.
  - Intent: Failed requests must not leave widgets in infinite loading state.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Replace `ValidationHub` silent null with visible unavailable/error state.
  - Intent: Validation module absence must be explicit to the user.
  - Owner: `web`
  - Proof: `UI state` `pytest`
- [ ] Replace `EvalStatus` infinite loading-on-failure with explicit error state.
  - Intent: Eval fetch failure must stop masquerading as “still loading”.
  - Owner: `web`
  - Proof: `UI state` `pytest`
- [ ] Create a shared Experience state spec: `loading / ready / empty / unavailable / error`.
  - Intent: All user-facing cards should use the same small state vocabulary.
  - Owner: `docs` `web`
  - Proof: `manual review`

## Phase 1 Verification

- [ ] Manual route check for homepage, dashboard widgets, and analyze page after P1 changes.
  - Intent: Confirm no homepage/dashboard state silently lies about health or availability.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Confirm no component collapses error into `empty`, `loading`, or `null`.
  - Intent: Lock the truthful state model in product-facing cards.
  - Owner: `web` `tests`
  - Proof: `pytest`
- [ ] Confirm frontend build passes after Experience P0 changes.
  - Intent: Keep closure work shippable at every stop.
  - Owner: `web`
  - Proof: `build`

## Phase 2 — Capability Boundary Freeze For Product Work

- [ ] Write a hard boundary spec for the Capability layer.
  - Intent: State what capability is allowed to represent and what it must not absorb.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Define the primary slicing rule: domain object + domain action first.
  - Intent: Freeze one primary classification axis before new capability work lands.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Explicitly classify all existing contracts as `domain / workflow / view / diagnostic`.
  - Intent: Make mixed contract types visible instead of pretending they are all the same abstraction.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Mark `AnalyzeResult`, `DashboardResult`, and `ValidationSummaryResult` as non-domain composite contracts.
  - Intent: Stop composite workflow/view payloads from masquerading as stable domain objects.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Freeze creation of new page-driven capabilities.
  - Intent: Prevent further slide into page/BFF capability naming.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Add minimal defensive boundary to side-effecting capability methods.
  - Intent: Side-effecting methods must declare minimum call context rather than assume trusted callers forever.
  - Owner: `capability` `api`
  - Proof: `pytest`
- [ ] Require `actor / context / reason / idempotency` fields where applicable.
  - Intent: Side-effecting methods must carry enough context to support future governance hardening.
  - Owner: `capability` `api`
  - Proof: `pytest` `manual review`
- [ ] Audit API routes that bypass capability and list all direct `repo -> response` paths.
  - Intent: Make current second-layer bypasses explicit.
  - Owner: `api` `docs`
  - Proof: `manual review`
- [ ] Prioritize moving core business API reads through capability.
  - Intent: Keep direct bypass cleanup focused on business-facing reads, not every utility endpoint.
  - Owner: `api` `capability`
  - Proof: `manual review`

## Phase 2 Verification

- [ ] Boundary doc exists and is referenced from this TODO.
  - Intent: The freezing rule must become explicit, not tribal.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] Every current capability file is labeled by abstraction type.
  - Intent: No capability remains “generic” by default.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] List of API bypasses exists and is up to date.
  - Intent: Direct router/repo shortcuts must be visible before cleanup work starts.
  - Owner: `docs` `api`
  - Proof: `manual review`
- [ ] Side-effecting capability methods either enforce a minimal boundary or are listed as follow-up blockers.
  - Intent: Avoid silent governance drift.
  - Owner: `capability` `api`
  - Proof: `pytest` `manual review`

## Phase 3 — Experience Semantic Clarity

- [ ] Refactor `RiskSnapshot` to stop inventing frontend business semantics.
  - Intent: Homepage snapshot should render real backend semantics, not frontend-renamed business truth.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Make homepage object types explicit: `Recommendation / Review / Audit / Report / Decision`.
  - Intent: Users must know what kind of object they are looking at without inferring from layout.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Clarify what `Latest Decisions` actually represents.
  - Intent: That card must say whether it is showing audit decisions, governance events, or another object type.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Add consequence messaging to recommendation action buttons.
  - Intent: Buttons must communicate what object changes when clicked.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Clearly distinguish “update recommendation status” from “execute external action”.
  - Intent: Recommendation lifecycle actions must not read like exchange execution controls.
  - Owner: `web`
  - Proof: `UI state`
- [ ] Promote time semantics: `generated_at / updated_at / stale / current`.
  - Intent: Time must affect interpretation, not sit as a decorative timestamp only.
  - Owner: `web` `api`
  - Proof: `UI state`
- [ ] Introduce shared `EmptyState / UnavailableState / ErrorState / LoadingState` components.
  - Intent: Reuse a truthful product vocabulary instead of ad hoc fallback prose.
  - Owner: `web`
  - Proof: `build` `pytest`

## Phase 3 Verification

- [ ] Object labels are visible in key homepage cards.
  - Intent: Homepage must stop relying on user inference for object identity.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Action consequence text is visible before state-changing clicks.
  - Intent: Reduce low-friction semantic misclicks.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Time semantics materially affect interpretation of at least one homepage and one detail view.
  - Intent: Confirm timestamps are not decorative only.
  - Owner: `web`
  - Proof: `manual screenshot/route check`

## Phase 4 — Capability Reclassification And Contract Cleanup

- [ ] Split `contracts.py` into `domain / workflow / view / diagnostic` contract files.
  - Intent: Make contract type explicit instead of letting one file imply false uniformity.
  - Owner: `capability`
  - Proof: `pytest`
- [ ] Define a stable object model for `Recommendation`.
  - Intent: Recommendation contract should stand on object semantics, not mixed presentation fields.
  - Owner: `capability` `api`
  - Proof: `pytest`
- [ ] Define a stable object model for `Review`.
  - Intent: Review contract should clearly separate review fact fields from workflow/view conveniences.
  - Owner: `capability` `api`
  - Proof: `pytest`
- [ ] Separate core fact fields from presentation-friendly fields.
  - Intent: Stop freezing mixed fact/view payloads as “stable objects”.
  - Owner: `capability` `api`
  - Proof: `pytest`
- [ ] Reclassify `dashboard.py` as a view aggregate, not a standard domain capability.
  - Intent: Homepage aggregate must stop pretending to be a domain object capability.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Reclassify `evals.py` as a diagnostic read adapter.
  - Intent: Eval run reading is not a domain object capability.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Reclassify `validation.py` based on its actual role.
  - Intent: Make clear whether validation is a workflow aggregate, governance summary, or mixed product view.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Add capability naming rules to block multi-stage `*And*` methods.
  - Intent: Prevent capability from swallowing orchestration by naming convention drift.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Create a minimal capability test matrix.
  - Intent: Each abstraction type should have at least one contract or behavior test.
  - Owner: `tests` `capability`
  - Proof: `pytest`

## Phase 4 Verification

- [ ] Contract files are classified and routed by abstraction type.
  - Intent: No single contracts file implies fake uniformity anymore.
  - Owner: `capability`
  - Proof: `pytest`
- [ ] Reclassification of mixed modules is documented.
  - Intent: Prevent future contributors from re-growing hidden view/diagnostic capabilities.
  - Owner: `docs`
  - Proof: `manual review`
- [ ] Capability tests cover category expectations.
  - Intent: Stop silent regression into page-driven or mixed abstractions.
  - Owner: `tests`
  - Proof: `pytest`

## Phase 5 — Long-Tail Closure

- [ ] Create visual trust tiers for `fact / system artifact / inference`.
  - Intent: Users must be able to distinguish record truth from model interpretation.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Reorganize homepage information architecture by object type.
  - Intent: Homepage should group information by what the object is, not only by visual convenience.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Add traceability links across `recommendation -> review -> audit -> report`.
  - Intent: Product truth should be navigable.
  - Owner: `web` `api`
  - Proof: `UI state`
- [ ] Make object lineage visible from key cards and pages.
  - Intent: Users should be able to tell where an object came from and what followed it.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Introduce capability subdirectories: `domain / workflow / view / diagnostic`.
  - Intent: Make the reclassification legible in the filesystem only after semantics are already stable.
  - Owner: `capability`
  - Proof: `manual review`
- [ ] Define contract lifecycle policy: `stable / workflow / view / experimental`.
  - Intent: Prevent every contract from carrying the same implied stability guarantee.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Tag every existing capability file with `keep / reclassify / split / deprecate`.
  - Intent: Finish the mixed-module cleanup with an explicit disposition table.
  - Owner: `docs` `capability`
  - Proof: `manual review`
- [ ] Build a migration plan for mixed modules like `reports.py` and `audits.py`.
  - Intent: Close remaining ambiguity without reopening the full migration.
  - Owner: `docs` `capability`
  - Proof: `manual review`

## Definition Of Done

- [ ] No fake reality in UI.
  - Intent: No placeholder business truth, fake success, or over-strong operational copy remains.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] No error collapsed into empty, loading, or null.
  - Intent: All failure modes must be explicit to the user.
  - Owner: `web` `tests`
  - Proof: `pytest`
- [ ] No over-strong success or operational wording without business definition.
  - Intent: Product copy must never out-run actual state semantics.
  - Owner: `web` `docs`
  - Proof: `manual review`
- [ ] No frontend-defined core business truth.
  - Intent: Frontend may format and compose, but not invent core object state.
  - Owner: `web` `api`
  - Proof: `manual review`
- [ ] Object type is always explicit.
  - Intent: Users should know what kind of object they are viewing without guessing.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Action consequences are visible.
  - Intent: State-changing controls must say what object and effect they apply to.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Time semantics affect interpretation, not just display.
  - Intent: Staleness and recency must matter to the user-facing meaning of objects.
  - Owner: `web` `api`
  - Proof: `manual screenshot/route check`
- [ ] Trust boundaries are visible.
  - Intent: Fact records, system artifacts, and inferred content must not be visually indistinguishable.
  - Owner: `web`
  - Proof: `manual screenshot/route check`
- [ ] Every capability has a clear abstraction type.
  - Intent: No capability remains “generic” or undefined.
  - Owner: `capability` `docs`
  - Proof: `manual review`
- [ ] No page aggregate disguised as a domain capability.
  - Intent: View aggregates must be called what they are.
  - Owner: `capability` `docs`
  - Proof: `manual review`
- [ ] No technical read disguised as a domain object.
  - Intent: Diagnostic adapters must not masquerade as stable business capabilities.
  - Owner: `capability` `docs`
  - Proof: `manual review`
- [ ] Side-effecting methods have a minimal defensive boundary.
  - Intent: Capability must not stay indefinitely callable as a blind trusted middle layer.
  - Owner: `capability` `api`
  - Proof: `pytest`
- [ ] API and Experience cannot casually bypass capability.
  - Intent: Core business-facing routes should flow through the declared semantic boundary.
  - Owner: `api` `capability`
  - Proof: `manual review`
- [ ] Capability does not absorb orchestration.
  - Intent: Workflow composition must remain outside capability methods.
  - Owner: `capability`
  - Proof: `manual review`
- [ ] Capability is not a mapper/fallback dumping ground.
  - Intent: Contract cleanup must reduce, not expand, adapter sprawl.
  - Owner: `capability`
  - Proof: `manual review`
- [ ] New modules follow naming and classification rules.
  - Intent: Prevent immediate regression after closure.
  - Owner: `capability` `docs`
  - Proof: `manual review`

## Operating Notes

- [ ] Use `pytest -q` as the default backend regression gate.
  - Intent: Keep closure verification lightweight and consistent with current repo practice.
  - Owner: `tests`
  - Proof: `pytest`
- [ ] Use `pnpm build:web` or `pnpm --dir apps/web build` as the default frontend stability gate.
  - Intent: Ensure Experience changes stay shippable while keeping `pnpm` as the only supported package manager.
  - Owner: `web`
  - Proof: `build`
- [ ] Extend tests only when a task changes user-visible state semantics or contract boundaries.
  - Intent: Avoid building a heavyweight framework just to carry this closure list.
  - Owner: `tests`
  - Proof: `manual review`
