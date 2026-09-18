# LEGO Question Compiler — Cross-Domain Prospective Canaries R1

Date: 2026-09-18
Status: CROSS_DOMAIN_FRAMING_PASS / OUTCOME_VALIDATION_PENDING
Method package:
- skill: project-ordivon-next/lego-question-compiler
- instruction digest: sha256:c965eb10bd5f2cfcab3f06c8158abc016b5568932f2955ac5dd7a2413d04edab
- package revision: sha256:860e1a047777774483f64e1d942262430665fb02940a1a22339da72784cb7b3b

## Purpose

Prospectively test whether LEGO Question Compiler changes the investigation surface in two non-poker Ordivon domains without creating a new ontology.

This is a framing canary. It does not yet test whether downstream execution produces better final outcomes.

## Canary A — Agent Service / Agent Birth

### Evidence boundary

Current Ordivon-next source revision:
- 13c107efce5b721112c804285408196ea944a162

Relevant evidence:
- knowledge/lessons/ordivon-agent-birth-lego-r1.md
- knowledge/graphs/ordivon-agent-birth-r1.json
- planning/lego-regime-shift-validation-r1.md
- evidence/browser-security/cloudflare-provider-security-exp-r4-cf07-analysis-20260918.json
- evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run1-20260918.json
- evidence/browser-security/cloudflare-provider-security-exp-r5-controlled-run2-20260918.json
- evidence/browser-security/cloudflare-provider-security-exp-r5-repeatability-20260918.json

### Target

Decide whether the next Agent Service/Birth slice should add raw capability, redesign ownership, or first measure/repair lifecycle, observation, provider-boundary and recovery behavior.

### Epistemic split

**OBSERVED**
- Agent Birth already separates semantic lifecycle authority from provider-specific effect authority.
- Raw provider SEND and strongest evidence about whether SEND was crossed remain provider-adapter responsibilities; Agent Service consumes references/receipts and derives lifecycle state.
- UNKNOWN/SUBMIT_OBSERVED do not authorize blind resend; human verification is a recovery branch under the same effect identity.
- Current browser-security R4/R5 evidence does not establish a single Cloudflare root cause. R5 remains NEUTRAL_ATTRIBUTION_ONLY_ROOT_CAUSE_OPEN.
- The examined Ordivon-next evidence contains provider-boundary experiments and a detailed state machine, but no population-level summary of Birth state frequencies, end-to-end completion loss by state, or recovery latency by state.

**INFERRED**
- "The bottleneck is Cloudflare", "the bottleneck is coordination", and "we need more raw capability" are all premature without a common accepted-completion denominator and state-transition census.

**UNKNOWN**
- distribution of Birth outcomes by lifecycle/effect state;
- conditional recovery probability and latency from HUMAN_REQUIRED, UNKNOWN and SUBMIT_OBSERVED to BOUND;
- fraction of accepted-completion loss attributable to pre-SEND provider boundary, orchestration/admission, ambiguous-effect recovery, and post-BOUND continuation.

### Primary compiled questions

#### AQ1 — STATE / OBSERVABILITY

**Question:** What is the exact accepted end-to-end Birth completion denominator, and what fraction of occurrences terminate or dwell in each material state?

Decision relevance:
Without this denominator, local browser experiments cannot identify the dominant system bottleneck.

Evidence route:
Aggregate existing Birth/effect receipts over a frozen observation window. Preserve semantic identity and do not infer missing states from absence of logs.

Discriminating outcomes:
- provider-boundary states dominate accepted-completion loss -> prioritize provider-boundary/recovery work;
- orchestration/admission states dominate -> prioritize Agent Service/Temporal integration;
- post-BOUND continuation dominates -> Birth is not the current bottleneck.

#### AQ2 — FEEDBACK / RECOVERY

**Question:** For HUMAN_REQUIRED, UNKNOWN and SUBMIT_OBSERVED, what are conditional recovery probability, time-to-BOUND, and unrecovered tail?

Decision relevance:
Frequency alone can overstate a frequently encountered but cheaply recoverable state; latency/tail can reveal the true constraint.

Evidence route:
Bind state transition timestamps from existing durable receipts/workflow history where available.

Discriminating outcomes:
- high frequency + fast recovery -> likely nuisance, not dominant throughput constraint;
- low frequency + very long/irrecoverable tail -> high-leverage recovery target;
- high frequency + long tail -> dominant recovery candidate.

#### AQ3 — AUTHORITY / FAILURE OWNERSHIP

**Question:** Among failed or delayed accepted Births, what share is first attributable to provider-effect boundary, lifecycle/orchestration, observation/reconciliation, or post-Birth session continuation?

Decision relevance:
The existing architecture already states natural owners. The unresolved problem is attribution, not another ownership diagram.

Evidence route:
Classify the first action-changing failure boundary from frozen receipts; do not relocate raw SEND into Agent Service merely to simplify accounting.

Discriminating outcomes:
Each dominant class routes work to a different natural owner.

#### AQ4 — FALSIFICATION

**Question:** What observation would falsify the hypothesis that provider trust/verification is the dominant current bottleneck?

Decision relevance:
Current Cloudflare experiments leave root cause open; the architecture should not be rebuilt around an unfalsified narrative.

Evidence route:
Pre-register a threshold/comparison over accepted-completion loss and recovery latency by failure owner before the next controlled campaign.

Discriminating outcomes:
If provider-boundary-normalized runs still lose most accepted completion elsewhere, demote the provider-boundary bottleneck hypothesis.

### Pruned questions

- "Should raw SEND move into Agent Service?" — already answered by current architecture evidence: no; provider-specific effect safety stays near the provider.
- "Is current request burst the Cloudflare root cause?" — R4 weakened sufficiency and R5 keeps root cause open; this is a narrower provider experiment, not the system-level canary.
- "Should we add another browser provider?" — solution-shaped before the dominant failure boundary is measured.

### Handoff

**INVESTIGATE -> EXPERIMENT**

First bounded experiment:
Create a frozen Birth transition/recovery census over existing receipts before adding raw capability.

### Canary A result

**FRAMING_PASS**

The compiler changed the next question from a broad capability/bottleneck debate to a measurable lifecycle/recovery attribution problem. No outcome benefit is claimed until the census is executed and changes a real work allocation.

---

## Canary B — Research v2 / Paper2

### Evidence boundary

Research v2 source revision:
- 5b1d81e3fbb418a713d1a72d339e058fec55b2bb

Paper2 source revision:
- 4692609a75caa016134e8686ebfa4da49a4ae20f

Relevant evidence:
- /root/projects/ordivon-research-v2/README.md
- /root/projects/ordivon-research-v2/docs/ARCHITECTURE.md
- /root/projects/ordivon-research-v2/docs/FIRST_PAPER_V2_DOGFOOD_STATUS.md
- /root/projects/ordivon-research-v2/planning/lego-plan-r1.json
- /root/projects/ordivon-paper2/screening/waves/FINAL_TITLE_ABSTRACT_SCREENING_R1.json
- /root/projects/ordivon-paper2/screening/adjudication/FIRST_PASS_FREEZE_R1.json
- /root/projects/ordivon-paper2/screening/fulltext/FULLTEXT_ELIGIBILITY_READINESS_R1.json
- /root/projects/ordivon-paper2/screening/fulltext/FULLTEXT_ACQUISITION_CLOSURE_R1.json

### Target

Decide where the next Research-v2/Paper2 pressure-test effort should go: more candidate generation, title/abstract screening, disagreement adjudication, full-text accessibility resolution, or full-text scientific eligibility.

### Epistemic split

**OBSERVED**
- Research v2's persistent core is CLASSIFY -> BIND -> COMPOSE -> VERIFY -> RECORD and explicitly refuses a universal local scientific ontology.
- Its LEGO plan RS1 is still PROPOSED and calls for pressure-testing the five-node waist on the next active Paper workload.
- Paper2 first-pass title/abstract screening is mechanically frozen for 4,142 paired records across 87 formal batches.
- 3,569/4,142 decision pairs agree; 573 disagree and remain unadjudicated in the first-pass freeze.
- The freeze explicitly states same-model-family correlated error remains and the counts are not independent-human inter-rater reliability.
- Full-text escalation contains 1,396 records.
- 793 have locally verified PDFs; 603 are in RETRIEVAL_BOUNDARY_REVIEW_REQUIRED.
- All current retrieval routes are mechanically closed; acquisition closure is explicitly not eligibility closure.

**INFERRED**
- Candidate generation and first-pass execution are not the immediate mechanical bottleneck represented by the current Paper2 state.
- "603 not ready" must not be collapsed into "603 inaccessible"; the source explicitly keeps those semantics separate.
- The next useful Research-v2 pressure test should distinguish scientific adjudication/eligibility throughput from access-boundary work rather than add a generic workflow layer.

**UNKNOWN**
- time/cost distribution for adjudicating the 573 first-pass disagreements;
- resolvable fraction and effort distribution within the 603 retrieval-boundary records;
- full-text screening throughput for the 793 ready PDFs;
- which of those three queues dominates time to an accepted study set.

### Primary compiled questions

#### RQ1 — STATE / OBSERVABILITY

**Question:** What state transition counts as scientific progress now: mechanical first-pass completion, adjudicated eligibility, locally ready full text, or accepted full-text inclusion/exclusion?

Decision relevance:
Mechanical closure cannot be used as a proxy for scientific closure.

Evidence route:
Define stage-native denominators and transition receipts without inventing a universal Research state ontology.

Discriminating outcomes:
Whichever transition has the largest unresolved queue/time contribution becomes the next pressure-test focus.

#### RQ2 — OBJECTIVE / BOTTLENECK

**Question:** Among the 573 disagreements, 603 retrieval-boundary records, and 793 ready PDFs awaiting downstream scientific use, which queue currently dominates time to an accepted study set?

Decision relevance:
These are different constraints with different owners; combining them into "review workload" hides the actionable bottleneck.

Evidence route:
Measure queue size, age, service time and completion rate per stage over a frozen window.

Discriminating outcomes:
- adjudication dominates -> invest in adjudication protocol/reviewer capacity;
- retrieval-boundary resolution dominates -> improve authorized access/routing evidence;
- full-text eligibility dominates -> improve full-text screening capacity/protocol execution.

#### RQ3 — COUNTERFACTUAL

**Question:** If candidate generation throughput doubled tomorrow while the current downstream queues stayed fixed, would accepted-study throughput materially increase?

Decision relevance:
This directly tests whether more search/generation is a useful current lever.

Evidence route:
Simple capacity/queue counterfactual grounded in current stage counts and measured service rates.

Discriminating outcomes:
- negligible accepted-throughput change -> stop allocating marginal capacity to candidate generation;
- substantial change after downstream slack is shown -> generation remains material.

#### RQ4 — INFORMATION / CLAIM BOUNDARY

**Question:** Which current stage labels are evidence about logistics only, and which are scientific eligibility decisions?

Decision relevance:
The current full-text files explicitly warn that acquisition closure != eligibility closure. Losing this distinction would turn infrastructure success into scientific acceptance.

Evidence route:
Audit current receipts against their declared semantics.

Discriminating outcomes:
Any label that mixes logistics with scientific acceptance requires split ownership/evidence, not a larger universal schema.

#### RQ5 — FALSIFICATION / PRESSURE TEST

**Question:** What Paper2 observation would falsify the claim that Research-v2's five-node waist is sufficient for a real active workload?

Decision relevance:
RS1 should test the architecture rather than merely demonstrate that Paper2 can be described with its vocabulary.

Evidence route:
Run the next Paper2 stage through CLASSIFY/BIND/COMPOSE/VERIFY/RECORD and record only residuals that change action and lack a mature owner.

Discriminating outcomes:
- no action-changing residual -> keep the waist thin;
- concrete repeated residual -> candidate local responsibility, still requiring owner/substitution review.

### Pruned questions

- "Should Research generate more papers/search hits?" — solution-shaped; current Paper2 evidence already has closed first-pass execution and large downstream queues.
- "Should Research create one universal screening state machine?" — conflicts with current semantic ownership law and is not required by the observed queues.
- "Are the 603 retrieval-boundary records inaccessible?" — contradicted by the source semantics; they require separate boundary review.

### Handoff

**INVESTIGATE -> EXPERIMENT**

First bounded experiment:
Use Paper2 as Research-v2 RS1 and measure stage-native queue/service-time transitions for disagreement adjudication, retrieval-boundary resolution and full-text eligibility.

### Canary B result

**FRAMING_PASS**

The compiler changes resource-allocation framing from generic generation/review capacity to three separately owned downstream queues with explicit claim boundaries.

---

## Cross-domain result

### Standing

**CROSS_DOMAIN_FRAMING_PASS / OUTCOME_VALIDATION_PENDING**

Both non-poker canaries satisfy the R1 framing criterion:
- a broad question was narrowed to decision-relevant uncertainty;
- at least one already-answered or malformed question was pruned;
- surviving questions bind to evidence/experiments;
- the output changes the next bounded investigation.

This is stronger than the original single poker pilot, but it is not evidence that Question Compiler improves final project outcomes.

### No promotion

Do not add STATE, OBSERVABILITY, EXPLOITABILITY, INFORMATION FLOW, or other Question Compiler vocabulary to the common LEGO project schema from these canaries.

### Next evidence

1. Execute Agent Birth transition/recovery census and compare work allocation before/after.
2. Execute Paper2 stage-native queue/service-time pressure test under Research-v2 RS1.
3. Record whether either experiment changes an architecture boundary, owner, experiment, or resource allocation.
4. Reject or simplify question families that repeatedly fail to change decisions.
