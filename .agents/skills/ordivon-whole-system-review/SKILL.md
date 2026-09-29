---
name: ordivon-whole-system-review
description: "Run an evidence-bounded whole-system review of Ordivon: reconstruct current truth, compare against a prior review or Git boundary, analyze architecture tradeoffs and production continuity, classify the capability frontier, route specialist reviews, and convert repeated findings into fitness functions or controls. Use for weekly/deep Ordivon system reviews, architecture re-anchoring, or questions about what Ordivon can reliably do now and what constrains future reachability. Do not use for ordinary changelogs, narrow component debugging, or project management status summaries."
compatibility: "Ordivon project Skill. Requires read access to current repository truth; live owner projections materially improve run-state claims. The Skill is advisory and never becomes Git, Runtime, Host, effect, security, or domain authority."
metadata:
  source-authority: "Ordivon LEGO/owner-authority-evidence model with SEI ATAM/QAW, NASA systems engineering V&V, Google SRE production readiness, DORA evolution metrics, C4-style multiscale representation, and evolutionary architecture fitness functions"
---

# Ordivon Whole-System Review

This Skill does not produce a weekly changelog. It rebuilds a defensible model of the **current whole Ordivon system**, compares it with the previous review boundary, and identifies the few changes that materially alter capability pressure, future reachability, owner/authority boundaries, continuity, external capability realization, or high-leverage architectural tradeoffs.

## Non-negotiable invariants

1. **Current truth before narrative.** Re-establish current Git/code truth and available live owner truth before using historical reviews, plans, or chats.
2. **Co-location does not merge authority.** Repository, Runtime, Host, Harness, Gateway, Workstation, domain owners, and external providers keep their natural truth boundaries.
3. **Observation != Evidence != Inference != Diagnosis != Decision.** Label the transition explicitly for material conclusions.
4. **Mechanical completion != semantic completion.** Process exit, Job terminal state, MCP success, or CI green cannot by itself prove domain completion.
5. **Full surface, adaptive depth.** Census every current macro LEGO; deeply inspect only changed, high-churn, evidence-stale, incident-linked, boundary-changing, capability-pressured, or unresolved-risk areas.
6. **No invented currentness.** If a live owner or receipt cannot be reached, record UNKNOWN and lower census confidence.
7. **DELETE-CUSTOM-BY-DEFAULT.** Ask whether mature external standards/providers now make a custom LEGO removable or thinner; preserve sovereign local ownership only where continuity, authority, evidence, or irreducible composition justify it.
8. **Review must converge.** Repeated important findings must become a fitness function, operational control, explicit architecture decision, or redesign item; do not rediscover the same risk forever.

## Phase 0 — Freeze the review boundary

Record:

- review timestamp and timezone;
- canonical repo and current source revision;
- working-tree/workspace state;
- available owner surfaces and their observation times;
- previous ReviewRecord revision if available, otherwise a defensible Git baseline near the requested period start;
- current census-confidence limitations.

Bind every present-tense claim to this boundary. See `references/evidence-contract.md`.

## Phase 1 — Reconstruct the current macro-LEGO landscape

Start from repository and deployed architecture evidence, not from a fixed historical list. At minimum look for currently existing responsibilities around:

- public ingress / Gateway / capability routing;
- Linux and Windows execution Runtime;
- Host semantic continuity / social work fabric;
- Harness / Agent Run ownership;
- Agent Birth / lifecycle surfaces;
- Skills, plugins, capability packages, external providers;
- Artifact / evidence / provenance;
- security / identity / authority / network;
- CI / verification / release / delivery;
- Workstation/platform realization;
- current domain/capability packages actually present in the repo.

For each macro LEGO capture owner, authoritative state, key interfaces, durable boundary, failure/recovery semantics, verification evidence, and whether it is intrinsic, replaceable, or externally substitutable.

Use `systems-engineering` when the system boundary itself is unclear. Use `project-kernel-decomposition` only when a changed subsystem must be decomposed below the macro-LEGO level.

## Phase 2 — Reconstruct material delta

Compare baseline to current truth using Git history/diff, contracts, manifests, tests, owner receipts, incidents, workspaces, and release evidence.

Do **not** report commit counts. Translate changes into one or more of:

- capability boundary changed;
- owner/authority moved or split;
- interface/contract changed;
- persistence/recovery/replay semantics changed;
- external dependency/provider changed;
- verification or semantic-completion boundary changed;
- delivery/recovery constraint changed;
- custom LEGO added, removed, thinned, or retired.

Routine refactors/docs/cleanup remain background unless they change one of those system properties.

## Phase 3 — Allocate analysis depth

Every macro LEGO gets a currentness census. Deep analysis is triggered by any material signal:

- changed contract or owner boundary;
- high recent churn around a shared seam;
- evidence older than the claim it is being used to support;
- recent incident, orphan, recovery, rollback, stale effect, or response-loss event;
- latent capability waiting on this LEGO;
- multiple open findings sharing the same dependency;
- new external mature substitute;
- disagreement between intent docs, current source, deployed configuration, and live behavior.

Do not use a universal numeric score. Explain why a LEGO received deep review.

## Phase 4 — Architecture analysis

Apply the ATAM/QAW lens in `references/framework-stack.md`:

1. build/update a quality-attribute utility tree for the current system;
2. choose a small number of highest-leverage use, growth, and exploratory/stress scenarios;
3. trace scenarios through concrete owners/components/contracts;
4. identify sensitivity points, tradeoff points, architectural risks, and confirmed non-risks;
5. aggregate related risks into 3–5 systemic risk themes.

Core quality attributes include continuity, recovery/reconciliation, correctness/evidence, evolvability, replaceability, interoperability, authority isolation, observability, resource efficiency, delivery velocity, and external capability realization.

## Phase 5 — Production and continuity readiness

Apply the SRE production-readiness lens in `references/framework-stack.md` to architecture/dependencies, instrumentation, emergency response, capacity, change management, availability/latency/efficiency, incidents/postmortems, and toil.

Always probe Ordivon-specific seams when relevant:

- long-running Job and worker lifecycle;
- response-loss reconciliation;
- orphan / reconciliation_required handling;
- duplicate admission and replay identity;
- stale external-effect suppression;
- offline/resume and checkpoint continuity;
- retry/rollback safety;
- semantic-completion receipts;
- Linux/Windows authority handoff;
- Host continuity after client/session loss.

A positive production claim requires live owner/receipt or executed evidence, not source intent alone.

## Phase 6 — Systems engineering traceability and V&V

Trace important capabilities through:

`mission/user need -> capability -> macro LEGO -> owner -> authority -> contract -> implementation -> verification -> intended-use validation -> evidence`

Distinguish verification (the implementation satisfies its contract/requirement) from validation (the resulting system actually satisfies the intended use). Milestones must have explicit entrance and success criteria.

## Phase 7 — Evolution and delivery health

When evidence exists, compare Ordivon against its own prior trend using DORA-style delivery signals:

- change lead time;
- deployment frequency;
- failed deployment recovery time;
- change fail rate;
- deployment rework rate.

Also consider Ordivon-specific root-verification latency, integration wait, manual recovery burden, batch size, and repeated rework. Missing numbers remain UNKNOWN; do not invent targets or benchmark theatre.

## Phase 8 — Capability frontier and future reachability

Classify material capabilities as:

- `REALIZED` — current behavior is supported by adequate executed/live evidence;
- `LATENT` — required LEGO exists but integration/exposure/real-use validation is missing;
- `BLOCKED` — a named dependency, authority, contract, or external constraint prevents realization;
- `DEGRADED` — previously supported capability lost current evidence or suffered a material regression;
- `RETIRED` — explicitly removed/superseded and must not be resurrected from stale plans.

For each material frontier transition, state what changed, the bottleneck, and whether the architectural change expands, preserves, or constrains future option space.

## Phase 9 — Route specialist reviews

Do not absorb every analytical method into this Skill. Route only when the current evidence warrants it. Use `references/specialist-routing.md`.

Typical examples:

- changed trust/security boundary -> repository-grounded threat model / information-flow analysis;
- unclear whole-system boundary -> systems-engineering;
- suspicious decomposition/cycles -> design-structure-matrix;
- substitution/assumption-guarantee seam -> compositional-contracts;
- concrete failure propagation -> fmea-fta;
- unsafe interaction/control loss -> stpa;
- major project/release diff -> SHA-bounded independent code review;
- incident/reconciliation fracture -> incident/postmortem/root-cause workflow;
- custom-vs-external decision -> bounded external primary-source research.

The Whole-System Review owns synthesis only; specialist methods retain their own non-claims and stop conditions.

## Phase 10 — Adversarial validation

Before promoting a major conclusion ask:

- What evidence would falsify it?
- Could this be documentation or deployment drift rather than a true architectural change?
- Does code truth conflict with live truth?
- Did we mistake an observation for a diagnosis?
- Did we mistake process completion for semantic completion?
- Is there a plausible alternative failure mechanism?
- What second-order cross-LEGO effect was omitted?
- Is the review toolchain itself unable to establish current truth?

If the review path itself fails currentness/reconciliation, record a **census-confidence risk** rather than silently shrinking scope.

## Phase 11 — Convert recurring findings into controls

Classify every repeated important finding as exactly one primary disposition:

- `ARCHITECTURE_DECISION` — a one-time explicit decision/tradeoff is required;
- `FITNESS_FUNCTION` — an architectural invariant can be continuously verified;
- `OPERATIONAL_CONTROL` — alert/read-back/recovery control is missing;
- `REDESIGN` — the structure itself must change.

A fitness function must protect an architectural characteristic, not create vanity metrics.

## Phase 12 — Persist and render

Create a ReviewRecord conforming to `assets/review-record.schema.json` and `references/review-record-contract.md`.

Persist semantic continuity through the current Host Work/Social Work Fabric owner when available, following `references/ledger-contract.md`. The ledger is **not** Git, Runtime, release, external-effect, or domain truth. Every subsequent review must revalidate current owner facts before using the prior record.

Render the human report using `references/output-contract.md`.

## Completion gate

Do not call the review complete unless:

- all current macro LEGOs were censused or explicitly marked unavailable;
- every `REALIZED` capability has adequate live/executed evidence;
- risk themes are systemic causes, not task lists;
- milestones include dependencies plus entrance and success criteria;
- user decisions are genuine tradeoffs, not questions engineering evidence can answer;
- retired/completed LEGOs were not recreated from stale docs;
- repeated findings have a control/fitness/redesign disposition;
- the report can answer: **what is Ordivon now, what can it reliably do, what can it not do, why, which decisions expand or constrain future reachability, and which constraint is now highest leverage?**

## Stop condition

Stop when the current whole-system model is evidence-bounded, material capability/frontier changes are explained, systemic risk themes and tradeoffs are explicit, the next milestone chain is testable, and no additional broad investigation would change those conclusions. Do not continue merely to make the report exhaustive.
