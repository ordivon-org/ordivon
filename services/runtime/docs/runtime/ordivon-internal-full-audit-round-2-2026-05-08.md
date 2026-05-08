# Ordivon Internal Full Audit Round 2 — 2026-05-08

> Status: current internal audit / supporting evidence  
> Phase: Internal-Full-Audit-R2  
> Observed at audit: 2026-05-08  
> Authority impact: evidence and backlog only; no action authorization

This Round 2 audit deepens the internal full audit from
`docs/runtime/ordivon-internal-full-audit-2026-05-08.md`. It does not extend
Ordivon Verify, does not modify behavior code, does not promote checkers, and
does not authorize merge, release, deploy, publication, trading, tool use, skill
activation, policy activation, or any external action.

## Executive Verdict

The self-governed Ordivon substrate is stable enough for continued work:
document registry, artifact registry, current truth, read-only baseline, and
pr-fast all pass. The deeper issue is no longer "can Ordivon govern its own
governance objects?" The deeper issue is whether Ordivon's application, pack,
adapter, execution, knowledge, trace, and capability layers are truly connected
to owner-confirmed gates and receipts.

Round 2 verdict:

- **Stable**: registry-controlled governance substrate, checker baseline, OV
  public wedge boundary, CTTS/CTA closure state.
- **Partially connected**: execution catalog, governance decisions, finance
  plan-only receipts, knowledge/state boundary docs.
- **Still weak**: ownership manifest coverage for governed target directories,
  application-level gate authority, app UI wording around execute/approved,
  pack-local governance skeletons, and target-layer receipt discipline.
- **Not a bug by itself**: application-layer files are not in
  `artifact-registry.jsonl`; this is the current architecture boundary.
- **Mainline need**: advisory owner/gate/receipt integration for governed
  target directories, without turning all application files into hard registry
  objects.

## Observed Baseline

Observed before adding this Round 2 report:

| Surface | Observed state |
| --- | --- |
| Base commit | `00b72d4 Add Ordivon internal full audit` |
| Document registry | 242 docs, 0 completeness violations |
| Artifact registry | 705 artifacts, 0 ungoverned, 0 class errors |
| Current truth | PASS |
| Diagnostic metrics | `blocked_count=523`, `degraded_count=119`, `missing_evidence_count=35`, `open_debt_count=3`, `checker_shadow_count=5`, `registry_drift_count=0`, `stale_source_count=0` |

Tracked file inventory, excluding generated/cached files:

| Layer | Directories | Tracked files |
| --- | --- | ---: |
| Self-governed | `docs`, `tests`, `scripts`, `domains`, `src`, `checkers` | 1259 |
| Governed target | `apps`, `packs`, `adapters`, `governance_engine`, `execution`, `knowledge`, `skills`, `capabilities`, `state`, `orchestrator`, `intelligence` | 389 |
| Deferred/support | `data`, `infra`, `shared`, `services`, `tools`, `policies`, `workflows`, `prompts` | 70 |

Generated artifact check:

- No tracked `.next/`, `__pycache__/`, `.pyc`, or `.tsbuildinfo` files were
  found by the tracked-file inventory.
- Generated outputs seen in the working tree are not treated as registry drift
  unless they are promoted into evidence artifacts or governance authority.

## Directory Inventory

Tracked governed-target files, excluding generated/cached files:

| Directory | Files | Current classification | Round 2 judgment |
| --- | ---: | --- | --- |
| `apps/` | 149 | governed target | Needs owner-confirmed app gates and UI wording review. |
| `packs/` | 18 | governed target | Needs pack-local skeletons before new profiles. |
| `adapters/` | 11 | governed target | Finance read-only/paper boundaries are visible; adapter authority still needs advisory ownership. |
| `governance_engine/` | 26 | governed target | Core runtime governance exists, but `execute` language must stay internally scoped. |
| `execution/` | 10 | governed target | Execution catalog is strong; partially covered action families need follow-up. |
| `knowledge/` | 64 | governed target | Boundary docs correctly say derived/non-authoritative; needs evidence hygiene continuation. |
| `skills/` | 1 | governed target | Existing skill states READY is not authorization; keep under agent-native evidence review. |
| `capabilities/` | 35 | governed target | Capability declarations need can/may boundary mapping. |
| `state/` | 26 | governed target | Correctly claims state truth authority; trace subarea still has deferred placeholders. |
| `orchestrator/` | 24 | governed target | Workflow execution language needs receipt/gate connection. |
| `intelligence/` | 25 | governed target | Agent evidence and token/trace language need advisory audit. |

Ownership manifest coverage:

| Group | Files checked | Covered | Uncovered | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Self-governed layer | 1259 | 1062 | 197 | Mostly healthy, but `domains/` and some doc families are not in ownership manifest coverage. |
| Governed target layer | 389 | 0 | 389 | Expected under current design, but now the biggest reconnect gap. |

This confirms the internal audit Round 1 diagnosis: target-layer files are not
artifact registry drift, but they are also not yet owner/gate integrated.

## Authority Language Findings

Round 2 scanned governed target directories for high-risk terms around
authorization, execution, finance, policy, agent evidence, and secrets. Counts
are text indicators only; they are not failures by themselves.

| Directory | Main concentration |
| --- | --- |
| `adapters/` | Finance/broker/read-only/paper boundary language; secret redaction terms. |
| `apps/` | UI language around execution, policy shadow, approval, trace, finance. |
| `capabilities/` | Execution and policy bridge language. |
| `execution/` | Action catalog, side-effect levels, receipt candidates, approval requirements. |
| `governance_engine/` | Governance decision, approval, active policy, execute/escalate/reject. |
| `knowledge/` | Memory/feedback/retrieval language and explicit non-authority disclaimers. |
| `packs/` | Coding/Finance discipline policy language. |
| `skills/` | READY/BLOCKED/DEGRADED and non-authorization skill instructions. |
| `state/` | State truth, trace, and execution reference language. |

Notable findings:

1. `governance_engine/decision.py` defines `execute`, `escalate`, and `reject`,
   and exposes `allowed` / `allows_execution()`. This is internally coherent,
   but it is a laundering risk if downstream UI or docs treat governance
   `execute` as external action permission.
2. `governance_engine/approval.py` has explicit approval records and
   `ensure_approved()`. This is a real application concept, not an OV trust
   signal. Future audits must keep "human approval gate" separate from
   `READY_WITHOUT_AUTHORIZATION`.
3. `execution/catalog.py` is one of the strongest target-layer controls. It
   classifies side-effect level, owner path, boundary status, and receipt
   candidacy. Two entries remain `partially_covered`: `intelligence_run_write`
   and `agent_action_write`.
4. `execution/adapters/finance.py` and `capabilities/domain/finance_decisions.py`
   repeatedly state plan-only / no broker / no trade boundaries. The language is
   good, but the `governance_status == "execute"` condition remains a place
   where non-external execution wording must be preserved.
5. `apps/web/src/app/analyze/page.tsx` uses "Execution Workspace" and "Use
   execution here" wording. This may be acceptable as product UI, but it is
   higher-risk than the backend wording because users see it without code
   context.
6. `apps/web/src/app/policy-shadow/page.tsx` uses preview/sample data and
   boundary banners, but sample owner names (`alice`, `bob`) and phrases such as
   "would recommend merge" deserve a future UI wording audit.
7. `knowledge/README.md`, `knowledge/memory/README.md`, `state/README.md`, and
   `state/trace/README.md` correctly distinguish derived knowledge, memory, and
   trace from current state truth.

Round 2 conclusion: the high-risk language is mostly bounded in code comments
and docs, but the UI/product surfaces need an advisory wording review before
they become external-facing or user-trusted.

## Boundary Gap Matrix

| Boundary | Current state | Gap | Round 2 decision |
| --- | --- | --- | --- |
| Self-governed registry boundary | Strong | Some ownership gaps outside current manifest patterns. | Keep hard registry gates; add advisory owner coverage later. |
| Application target boundary | Conceptually clear | No owner manifest coverage for `apps/`. | Add advisory app owner/gate map next. |
| Pack boundary | Coding/Finance packs exist | No shared minimal pack skeleton across future packs. | Define pack-local governance skeleton before Trade/Health expansion. |
| Adapter boundary | Finance adapter has read-only/paper guards | Adapter authority not connected to owner manifest. | Add adapter owner/gate coverage as advisory. |
| Execution boundary | Catalog has side-effect levels and receipt candidates | Partially covered intelligence/agent actions. | Create execution action backlog, not new hard gate. |
| Knowledge/memory boundary | Docs say derived/non-authoritative | Needs recurring hygiene check for memory/content. | Keep agent-native evidence checker shadow-first. |
| App UI boundary | Banners and disabled actions exist | "Execution", "approved", and sample owner terms can confuse users. | Add UI trust-language audit as P1. |
| Generated artifacts | No tracked generated/cached files observed | Build outputs may still appear locally. | Keep generated excluded unless promoted to evidence. |

## Risk Register

| Priority | Risk | Evidence | Mitigation |
| --- | --- | --- | --- |
| P0 | Governance `execute` is mistaken for external execution permission | `GovernanceDecision.allowed` and `allows_execution()` are valid internal APIs but high-risk language. | Require downstream docs/UI to state execute is scoped to internal governance decision only. |
| P0 | App UI overstates authority | Analyze page and policy shadow page use execution/approved/merge language. | Add UI trust-language audit before external user exposure. |
| P0 | Governed target layer stays ownerless | 389/389 target files uncovered by current ownership manifest. | Add advisory owner manifest expansion; do not make hard gate yet. |
| P1 | `domains/` lacks ownership coverage | 107/107 domain files uncovered by ownership manifest despite artifact registry coverage. | Add domains owner pattern in next owner expansion round. |
| P1 | Execution catalog partial coverage remains unresolved | `intelligence_run_write` and `agent_action_write` are partially covered. | Create execution receipt alignment backlog. |
| P1 | Pack expansion imports coding assumptions | Coding Trust is mature; non-coding packs are not. | Define minimal pack skeletons independent of coding gates. |
| P1 | Knowledge feedback becomes policy truth | Knowledge docs are clear today, but app/runtime integration can drift. | Keep CandidateRule/lesson/policy boundaries explicit in receipts and UI. |
| P1 | Finance plan receipt language implies trading permission | Finance code says no broker/order/trade, but uses `execute` for governance status. | Rename in future UX or wrap with explicit "plan-only" wording. |
| P2 | Generated artifacts cause false drift alarms | `.next` and caches exist locally in some worktrees. | Use tracked-file inventory for registry decisions. |
| P2 | Sample data looks real | UI sample owners and policy IDs can be overread. | Replace personal-looking sample owners with role placeholders in a later UI polish round. |

## Mainline Reconnect Backlog

| id | surface | risk | recommended action | owner candidate | gate candidate | priority | promotion boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MLR-001 | `apps/` | UI authority language and no owner coverage | Create advisory app trust-language + gate map for web/API. | app-surface-owner | app-ui-trust-language-advisory | P0 | Advisory only; no hard baseline until fixtures exist. |
| MLR-002 | `governance_engine/` | `execute` can be misread as permission | Document scope of `execute/escalate/reject` and where it may be displayed. | governance-runtime-owner | governance-decision-language-check | P0 | Docs/tests first; no API rename in audit phase. |
| MLR-003 | `execution/` | Partially covered intelligence/agent action writes | Create execution receipt alignment backlog for partial catalog entries. | execution-owner | execution-catalog-coverage-report | P1 | Report only until receipt fixtures exist. |
| MLR-004 | `domains/` | Artifact-registered but owner-manifest uncovered | Add advisory ownership pattern for domain semantics. | domain-model-owner | owner-manifest-advisory | P1 | Shadow/advisory; no hard owner gate. |
| MLR-005 | `packs/` | Future packs may inherit coding assumptions | Define minimal pack governance skeleton for Coding/Finance/Body/Learning. | pack-governance-owner | pack-boundary-review | P1 | No Trade/Health activation. |
| MLR-006 | `adapters/` | Adapter capabilities can be mistaken for action permission | Add adapter capability/permission boundary table. | adapter-owner | adapter-boundary-advisory | P1 | Read-only/advisory; no external calls. |
| MLR-007 | `knowledge/` / `state/trace` | Derived knowledge/trace may be treated as truth | Extend memory/content/trace hygiene backlog from agent-native evidence checker. | knowledge-state-owner | evidence-hygiene-shadow | P1 | Shadow-first only. |
| MLR-008 | `capabilities/` | Capability declarations blur can/may | Create can/may capability manifest review. | capability-owner | capability-boundary-advisory | P1 | No permission semantics. |
| MLR-009 | `apps/web` | Sample owners and approved labels look real | Replace sample actors with role placeholders and improve preview banners in future UI round. | app-surface-owner | ui-preview-data-check | P2 | UI copy only; no policy change. |
| MLR-010 | generated outputs | Local build artifacts can confuse audits | Codify tracked-file-only inventory rule in audit runbook. | tooling-owner | generated-artifact-inventory | P2 | Documentation/checklist only. |

## NO-GO Confirmation

This Round 2 audit does not authorize:

- merge
- release
- deploy
- publish
- trade
- broker write
- order placement
- live execution
- skill activation
- tool permission
- policy activation
- CandidateRule promotion
- checker promotion
- public schema standardization
- compliance/certification/production-ready claims
- SaaS, GitHub bot, MCP server, or agent runner launch

All recommendations are backlog candidates. They require separate owner review
before any implementation or gate promotion.

## Verification Results

Final verification commands were run after this report and registry updates.
Results are audit evidence only.

| Command | Result |
| --- | --- |
| `git status --short` | Working tree contained only this Round 2 audit/report registry change set before commit |
| `git log --oneline -5` | Base observed before Round 2 change set: `00b72d4 Add Ordivon internal full audit` |
| `uv run python scripts/check_document_registry.py` | Final PASS: 243 docs, 0 completeness violations |
| `python scripts/check_artifact_registry.py` | PASS: 705 artifacts, 0 ungoverned, 0 class errors |
| `python checkers/current-truth/run.py` | PASS after auto-fixing document count drift from 242 to 243 |
| `python scripts/report_governance_delivery_metrics.py --json` | PASS: `blocked_count=524`, `degraded_count=120`, `missing_evidence_count=35`, `registry_drift_count=0`, `stale_source_count=0` |
| Directory inventory probe | PASS: target layer 389 tracked non-generated files; no tracked generated/cached files observed |
| Authority language probe | PASS as audit probe; high-risk terms categorized, not treated as failures |
| Ownership coverage probe | PASS as audit probe; target layer 0/389 covered, recorded as reconnect backlog |
| `uv run python scripts/run_baseline.py --read-only` | READY: 26/26 hard gates PASS |
| `uv run python scripts/run_baseline.py --pr-fast` | READY: 12/12 hard gates PASS |
| `uv run python scripts/audit_ordivon_verify_public_wedge.py` | PASS: 0 blocking findings |
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS: 367 files already formatted |
| `python -m compileall -q src/ordivon_verify scripts tests/unit/product checkers governance_engine packs adapters execution capabilities knowledge state` | PASS |
| `git diff --check` | PASS |
