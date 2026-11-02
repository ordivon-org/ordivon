# Agent Service Regime Card R1

Date: 2026-09-18
Status: CANARY_A_COMPLETE / ANALYSIS EVIDENCE
Lens: LEGO Regime Shift & Deep-Uncertainty Decision R1
Baseline: LEGO Theory Wave 1 (Systems Engineering / DSM / Feedback Control / STPA)

## Decision question

Is Agent Service still mainly constrained by raw Agent/model/tool capability, or has the dominant constraint migrated toward integration/deployment, provider admission/trust, observation validity, recovery, and semantic acceptance?

## Evidence cuts

### Current Ordivon main

Observed main at analysis start:
- `2b6386968ec188f59b117cb8a0b5a437ff92c012`
- `agent_service/` directory absent.
- Relation to frozen R14: current main has 26 unique commits; R14 has 14 unique commits.
- Merge base: `bd2dee7accd50482ccb16f2c03a5e8c4bc9eb9a3`.

A Git `merge-tree --write-tree` between current main and R14 returned RC=0 and a merged tree without conflict output. There were no same-path changes between the two sides relative to the common base in the collision check.

Interpretation:
- the implementation-to-main delay is real;
- the observed delay is not currently explained by a file-level merge conflict.

### Frozen Agent Service R14 implementation

R14:
- `0721009237365ea61cd975bd187be5171f1dcd52`
- clean detached Workspace;
- acceptance receipt reports:
  - 214 repository tests PASS;
  - 15 interface/credential tests;
  - 5 Browserless effect-reader tests;
  - 1 public API test;
  - zero repository test failures.

R14 already implements identity/session/delegation, evidence verification, single execution ownership, governed A2A/MCP delivery, failover safety, provider/effect adapters, credential binding and one real Browserless effect-ledger reader.

This is implementation maturity evidence, not deployment evidence.

### Live production surface

Current systemd observation:
- Ordivon Runtime: active;
- Host v2: active;
- Agent Automation MCP: active;
- Agent Temporal worker: active;
- Browserless carrier 11: active;
- Browserless operator proxy 11: active.

The live Agent-facing automation surface remains the legacy Agent Automation MCP, exposing 11 tools. No dedicated Agent Service systemd unit/process was observed.

Current read-only provider preflight on `chatgpt-carrier-11`:
- Browserless substrate health: healthy;
- HTTP substrate status: 204;
- provider standing: `CHALLENGE_GATED`;
- providerEffectAttempted: false;
- composerFilled: false;
- sendAttempted: false;
- assistantOutputRead: false.

Therefore:
`carrier/service health != provider admission readiness`.

### Historical Agent Automation effect ledger

Birth ledger total: 313 requests.

Standing counts:
- bound: 150 (47.9%);
- pre-effect-failed: 129 (41.2%);
- submit-observed: 6 (1.9%);
- unknown: 27 (8.6%);
- human-required: 1 (0.3%).

Effect-outcome ambiguous:
- 33 / 313 (10.5%).

Unresolved compatibility count:
- 34 / 313 (10.9%).

The 129 pre-effect failures were dominated by:
- 80 human-handoff-unavailable (62.0%);
- 32 conversation-history-rate-limit-modal (24.8%);
- 15 composer-not-empty (11.6%);
- 2 composer-unavailable timeout (1.6%).

Critical freshness correction:
- all 313 rows were last updated during 2026-09-13 through 2026-09-16;
- no ledger rows were updated in the most recent 24 hours at observation time.

Therefore these counts characterize historical friction, not current throughput.

### Host continuity

Host integrity Doctor was healthy:
- 2,100 tasks total;
- 1,835 terminal;
- 265 open;
- Journal/task/Board integrity checks PASS.

The 265 open continuity rows are not interpreted as 265 active jobs or a backlog metric because Host explicitly defines them as continuity inventory, not current work/priority truth.

## Stock / flow / derivative

| Variable | Observed level | Current flow / derivative | Interpretation |
|---|---|---|---|
| Agent Service implementation maturity | R14 with 214 repository tests PASS | R14 not present on current main | high implementation stock, zero observed integration realization |
| Main-line Agent Service capability | no `agent_service/` tree | no integrated R14 flow yet | capability stock is buffered outside production lineage |
| Live automation availability | Runtime/Host/Automation/Browserless healthy | current provider preflight challenge-gated | infrastructure up, provider admission not ready |
| Historical birth materialization | 150/313 bound | no rows updated in last 24h | historical success/failure distribution is stale for current-rate inference |
| Semantic accepted E2E throughput | not directly measured by live Automation ledger | unknown | primary observability gap |

No first- or second-derivative claim is made for accepted E2E throughput because the required recent series does not exist.

## Buffers

### B1 — Detached implementation buffer

R14 stores substantial validated capability outside current main. It can make project capability look advanced without changing live system behavior.

### B2 — Legacy production buffer

The old Agent Automation + Temporal + Browserless stack remains live and mechanically healthy. It masks the absence of a deployed Agent Service by preserving current automation functionality.

### B3 — Durable effect-evidence buffer

SQLite materialization/effect fences preserve UNKNOWN, SUBMIT_OBSERVED and related states instead of allowing blind resend. This protects correctness but also means unresolved external-effect uncertainty can remain durable until stronger observation arrives.

### B4 — Host continuity buffer

Host preserves semantic re-entry even while current physical execution is elsewhere or absent. This is useful continuity state, but must not be misread as active-work throughput.

## Delays

1. implementation -> main integration:
   - observed;
   - currently not explained by merge conflict;
   - exact elapsed time is not claimed.

2. integration -> deployment:
   - not yet observed for R14;
   - current live surface remains legacy Automation.

3. provider challenge -> provider-ready admission:
   - currently blocking carrier 11 at preflight;
   - historical handoff failures show this boundary has mattered before;
   - present recovery latency is not quantified.

4. provider/effect observation -> semantic acceptance:
   - architecturally explicit in R14;
   - current live stage-to-stage latency and acceptance rate are not instrumented as one E2E funnel.

## Constraint migration

### Historical constraint family

Earlier Agent Service slices progressively solved:
- Agent identity / revision / instance;
- placement and Runtime execution;
- semantic evidence verification;
- Goal/Task graph;
- delegation and governed delivery;
- remote evidence and single-owner execution;
- failover;
- provider/effect adapters;
- credential/interface binding.

This means "missing raw Agent Service mechanics" has been substantially reduced in the R14 implementation lineage.

### Current candidate constraints

C1. **Integration/deployment propagation**
- strong evidence;
- R14 is validated but detached;
- current main lacks Agent Service;
- clean mergeability check indicates this is not presently a merge-conflict blocker.

C2. **Provider admission / trust boundary**
- strong current evidence;
- carrier is healthy while current provider preflight is CHALLENGE_GATED before SEND.

C3. **Outcome observability / semantic acceptance funnel**
- strong evidence of measurement gap;
- live ledger records effect-materialization standing, but does not provide a current end-to-end series from task intent through semantic acceptance.

C4. **Controller stability / shared failure domains**
- plausible, already surfaced by Wave-1/STPA and destructive contraction;
- a separate control-stability workspace contains only an untracked RED test at this evidence cut and no experiment runner, so no new pass/fail claim is made here.

C5. **Raw model/tool capability**
- not falsified;
- no current evidence shows it is the binding constraint before the above gates are cleared.

## Competing hypotheses

### H0 — ordinary implementation noise / no migration

Evidence against:
- R14 implementation stock is large and verified while current main/live production remain on another lineage/surface;
- current provider gate blocks before any model prompt effect.

Falsifier for migration claim:
- integrate/deploy R14, clear provider admission, measure accepted E2E work, and show raw reasoning/tool failures dominate accepted-throughput loss.

Standing: weakened, not eliminated.

### H1 — raw capability is still dominant

Evidence for:
- not directly measured.

Evidence against:
- current observed gate occurs before SEND;
- live system does not yet expose R14 semantics.

Standing: UNKNOWN / currently downstream of stronger observed gates.

### H2 — bottleneck migrated to orchestration/integration

Evidence:
- validated R14 is detached from main;
- current main lacks the Agent Service tree;
- mergeability is clean;
- live production still uses legacy Automation.

Standing: SUPPORTED AS CURRENT CANDIDATE.

### H3 — bottleneck migrated to trust/observation boundaries

Evidence:
- current provider preflight = CHALLENGE_GATED with healthy carrier/substrate;
- historical failures are dominated by pre-effect provider/handoff states;
- R14 architecture complexity is concentrated in delegation/trust and evidence/verification.

Freshness caution:
- historical ledger is stale; current challenge observation is the current evidence.

Standing: SUPPORTED AS CURRENT CANDIDATE.

### H4 — resource limits dominate

Evidence for:
- none in this cut.

Evidence against:
- relevant services were active with zero observed restart count in the inspected units;
- carrier health returned healthy.

This is not a capacity benchmark.

Standing: NOT SUPPORTED BY CURRENT CUT / NOT FALSIFIED.

## Feedback / adaptation

Important loops:
- provider admission -> human handoff/revalidation -> provider admission;
- effect attempt -> durable ambiguity fence -> reconciliation -> replay decision;
- execution -> evidence -> semantic acceptance -> next Task/Goal action;
- placement/failover -> provider/carrier state -> observation -> reassignment.

The main stability risk remains multiple control layers reacting to one transient. Retry/failover ownership therefore stays explicit; no new generic RetryManager is justified.

## Threshold / early-warning decision

Critical-transition statistics, critical slowing down, variance/autocorrelation alarms, and tipping-point thresholds are **not activated** for Canary A.

Reason:
- there is no justified continuous-state tipping-point model;
- current problem is better explained as staged constraint migration and propagation delay.

This is a deliberate local rejection/simplification of the lens rather than forcing every operator into every case.

## Decision change caused by Regime Lens

Before this canary, a reasonable next move was continued Agent Service feature expansion or control-theory hardening.

After the canary, the higher-information next sequence is:

1. stop adding broad R15 capability until the R14 integration gap is closed or explicitly rejected;
2. integrate R14 into an isolated current-main candidate first;
3. preserve Wave-1's unresolved authority-lifetime/revocation question as an explicit semantic gate;
4. fix known R14 architecture-evidence metadata collisions during integration;
5. run full repository verification on the integrated cut;
6. build an E2E stage funnel that distinguishes:
   - task intent;
   - provider preflight/admission;
   - effect attempt;
   - provider-bound/effect evidence;
   - semantic acceptance;
7. only after that decide whether the next bottleneck is model capability, provider trust, recovery, verification, or coordination.

This changes resource allocation away from adding raw capability and toward integration + observation + current-provider admission.

## Robust action

The robust action is staged:

- **Stage 0: no production deployment change.**
- **Stage 1: isolated R14 + current-main integration candidate.**
- **Stage 2: full tests + graph identity/status consistency + authority-lifetime decision.**
- **Stage 3: deployment/canary only after acceptance.**
- **Stage 4: measure E2E accepted-throughput funnel before expanding capability.**

This preserves rollback and information gain.

## Signposts

| Signpost | Interpretation | Action |
|---|---|---|
| R14 integrates cleanly and full tests pass | integration delay was organizational/process, not technical incompatibility | proceed to bounded deployment preparation |
| merge/integration exposes semantic conflicts | integration itself is a real constraint | repair contract before feature expansion |
| provider preflight repeatedly becomes READY | challenge gate may be transient rather than dominant | move measurement downstream |
| provider remains challenge-gated while substrate stays healthy | provider trust/admission remains binding | work provider admission/control-transfer path, not raw capability |
| deployed Agent Service produces stage funnel | observability gap closed | identify largest measured stage loss |
| semantic acceptance loss dominates after provider readiness | verification/question/task quality may be next constraint | shift work there |
| raw model/tool failure dominates after all upstream gates clear | H1 regains support | resume capability expansion |

## Canary A verdict

**PASS — DECISION-RELEVANT BUFFER / DELAY / CONSTRAINT-MIGRATION DISCOVERY.**

Incremental value over Wave-1 baseline:
- Wave-1 already found the authority-lifetime/STPA hazard.
- Regime Lens added:
  - implementation-stock vs integration-flow separation;
  - legacy-live-system buffer;
  - stale historical ledger vs current-state separation;
  - current healthy-substrate / challenge-gated-provider divergence;
  - clean-mergeability evidence that changes the integration diagnosis;
  - a staged decision rule tied to measurable signposts.

This is one of three required prospective canaries. It does not promote the lens to R2 by itself.
