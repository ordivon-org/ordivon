# Incremental Evidence Validity R1 — Exact-Check Consumer

Status: SOURCE IMPLEMENTED, LIVE GITHUB CHECK READBACK OBSERVED, cross-SHA proof
reuse NOT implemented. Source date: 2026-11-14. Natural facts remain owned
by Git, GitHub Actions, the existing repository SourceCut selector and native
verification owners. No new database, Registry, Gateway MCP, Runner, Scheduler,
or agent was created.

## Actual business consumer

An Agent often launches Gateway/Runtime replay or TLA+ checks on its next turn
even though an accepted GitHub Actions Check Run already finished for the
unchanged exact source SHA. Do not repeat a successful exact-SHA check simply
because a new conversation/Agent turn started.

Minimal read-only interface:

    python3 tools/repo/evidence_validity.py --current-sha FULL_GIT_SHA --check-name root-verification

For historical comparison add --prior-sha FULL_ANCESTOR_SHA. The entrypoint
reuses ci_telemetry.Gh for original GitHub Check Run transport,
convergence_plan.build_plan for existing Owner verification selection, and
source_history_legos.require_ancestral_source_cuts for native Git ancestry.
It does not initiate verification, dispatch CI, or mutate Host Work/Runtime.

## Distinct evidence and truth scopes

- A GitHub Actions Check Run at an exact SHA, with its original Check Run ID,
  app, name and completed/success result, may be reused as evidence that
  THAT CHECK finished successfully. It is NOT a theorem about every
  consumer, a production installation, an actual Agent task, or a
  different SHA.
- A missing, failed, skipped or still-running current Check Run cannot be
  replaced with an older successful Check Run. Query the current existing
  provider result first; do not dispatch a duplicate.
- When the requested exact SHA has no accepted check, optional prior
  ancestor evidence may be read. The existing native convergence plan
  reports changed paths and affected verification Owner tasks, but does
  not grant formal proof reuse or close dynamic/non-Git assumptions.
- A changed SourceCut with no known affected Owner remains
  UNKNOWN_CROSS_CUT_READSET; a sibling-tip comparison or unavailable
  provider is UNKNOWN, not a PASS or a failure.
- The source consumer intentionally separates
  existingCheckReceiptReusable=true from proofReuseAdmissible=false.
  Existing LEGO graph impact projections also keep
  proofReuseAdmissible=false until real proof readset closure is
  independently established.

## Status contract

| Disposition | Consequence |
| --- | --- |
| REUSE_CURRENT_RECEIPT | Reuse same-SHA named GitHub Check Run outcome; no repeat run |
| OBSERVE_EXISTING_RUN | Current check is already in flight; do not start another |
| INVESTIGATE_EXISTING_RESULT | Current check completed without PASS; read that result |
| SOURCE_AFFECTED | Native Owner selector identifies affected tasks; inspect real new obligations |
| UNKNOWN_CROSS_CUT_READSET | No affected native task, but no cross-SHA proof-readset closure |
| UNKNOWN_SOURCE_RELATION | Git ancestry / source delta cannot be qualified |
| UNKNOWN_NO_ACCEPTED_EVIDENCE | No qualified current or prior successful result |
| UNKNOWN_PROVIDER_OR_SOURCE | GitHub provider or exact native Git identity unavailable |

## Nonfictional consumer evidence

On actual GitHub source commit
9df78f24899eac718d563e5686d973a9bbb398c6,
the read-only CLI observed GitHub Check Run 132064192546:
root-verification, app github-actions, completed/success.
Disposition was REUSE_CURRENT_RECEIPT. No CI or test replay occurred.

The new bounded tests exercise provider paging, exact SHA/app identity,
pending and failed Check Runs overriding earlier PASS, unrelated commits,
unknown/empty readsets, immutable ancestor ordering, malformed provider
output, and finite decision-state combinations. These are part of the
existing repository CI pytest collection, not a new test framework.

## Remaining P0 / P1 capabilities

P0: Produce exact proof readset + verifier config + dependency/consumer
closure + external assumption receipts at the natural verifier Owner.
GitHub metadata alone cannot authorize reuse across commits.

P0: Harness Agent verification-task selector must consume this existing
read-only decision before scheduling a replay. The CLI and Agent guidance
do not yet enforce remote Harness/Runtime scheduling.

P1: Mature red-green incremental calculation with scoped dependency
closure and a proof-evidence argument (GSN/Assume-Guarantee) on only
those new source/business consumers that need cross-SHA reuse.

P1: Strict source/model/implementation/consumer refinement when changing
the actual semantics, using existing formal tools. Unchanged formal
models should not be rechecked every Agent turn.

P2: Empirically measure duplicate checks avoided and false positive
reuse as real Agent consumer metrics. Do not invent a percentage from
synthetic test counts.
