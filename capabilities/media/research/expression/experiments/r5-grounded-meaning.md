# R5 Grounded Meaning acceptance — 2026-08-11

## Research question

R4 established that richer mechanical perception can reveal real structure without necessarily increasing explanatory power. R5 therefore did **not** ask for another larger feature vector. It asked:

> Can Studio turn meaning into a bounded experimental object whose claims are evidence-addressed, perturbable, independently scored, and separable from downstream consequence?

The target was not a universal semantic ontology. The target was an apparatus that can distinguish:

```text
artifact evidence
→ candidate semantic observation
→ grounded relation / event / proposition
→ controlled falsifier
→ observer consequence
```

The five branches were:

- **R5-0** — apparatus acceptance law;
- **R5-A** — controlled writing/discourse relations;
- **R5-B** — time-grounded video event/narrative checks;
- **R5-C** — speech meaning over exact transcript/timing;
- **R5-D** — crossmodal relation probes;
- **R5-E** — controlled Agent-observer knowledge transfer.

Source revision at admission: Studio `346ec9fb0dcbf541062adec890ada5200910e18a`.

## R5-0 — acceptance law

A semantic apparatus earns reuse only if the experiment can attack the following properties independently.

### Grounding

A semantic observation should point back to supplied evidence IDs, text segments, time ranges, or another exact locator. A plausible statement with the wrong evidence is not a grounded success.

### Sensitivity

A known meaning-changing intervention should change the targeted semantic result.

### Invariance

A meaning-preserving paraphrase or representation change should not cause arbitrary semantic drift.

### Counterexample resistance

Explicit contradiction, evidence omission, or another falsifier must not be smoothed back into the baseline interpretation merely because the baseline story is plausible.

### Disagreement visibility

Replicate disagreement remains evidence. R5 does not majority-vote two unstable labels into a fictional stable truth.

### Consequence separation

Semantic annotation and knowledge transfer are different measurements. R5-E is explicitly **Agent-observer consequence**, not human comprehension, memory, trust, or preference.

These principles were informed by current primary research that separately emphasizes discourse structure in long documents, timestamp-aware multi-segment video grounding, perception/comprehension/adaptation separation in video knowledge acquisition, and strict multimedia-event evaluation. The source ledger records the exact papers and DOI identities.

## Provider authority boundary

R5 pressure-tested the existing Ordivon boundary instead of giving Studio a hidden model path.

```text
Studio
  owns experiment bundle + oracle + independent scoring
        ↓
Harness
  owns Provider settings + credential authority + structured completion
        ↓
DeepSeek Provider
  returns candidate semantic observations
        ↓
Studio
  independently scores against preregistered oracle/evidence rules
```

A harmless authority probe confirmed Harness could resolve its existing `deepseek-v4-flash` credential scope. Studio never loaded or serialized the Provider secret.

The final official run used Harness adapter:

`deepseek.chat-completions.non-thinking.v1`

The Provider saw only:

- task-specific system instruction;
- evidence-bearing user payload;
- structured result schema.

The Provider did **not** see Studio's oracle.

## Protocol faults found before the official run

R5 deliberately records its own experimental failures.

The first generated bundle was rejected before full execution because some task-local oracle hints had leaked into Provider-facing structures (`expectedRelation`, `expectedPresent`, and required-evidence hints), and the first consequence metric incorrectly allowed correct no-evidence abstention to cancel true knowledge acquisition.

Both were fixed before the official experiment:

- Provider payload became oracle-free;
- no-artifact epistemic discipline became a separate metric from substantive knowledge acquisition;
- grounding legality became independently scored;
- the recovery-omission condition removed generic recovery references as well as the explicit replay scene.

A two-call smoke run then exposed another experimenter failure: the original article relation oracle used ambiguous pair labels such as `SEQUENCE` where the pair more naturally expressed a causal/enabling relation. That exploratory receipt was preserved as pre-oracle-refinement evidence but excluded from the official score. The synthetic fixture was rewritten once, before the official 28-call run, to make the targeted relations materially clearer.

This is an important R5 result in itself: **a semantic benchmark can fail because its ontology/oracle is under-specified, even when Provider grounding is correct.**

## Official experiment identity

Frozen official Provider bundle:

- 14 tasks;
- 2 independent Provider observations per task;
- 28 calls total;
- semantic bundle digest: `sha256:90857cc48766c837b81f226b5abd2c6731a8276679b307d7602d196887c255a4`.

Harness completed all 28 calls with zero Provider failures.

Harness receipt internal digest:

`sha256:5efb28e46b17c1e36459f39676f21d6be8817ba702d64ad4ec7119f5d4ae5f83`

Studio independent score digest:

`sha256:e376c6410704c41d5966f18f43a538ead87f339204e62d33616f9a9ea5242b02`

## R5-A — writing / discourse relation probes

R5-A used a fictitious Heliox mechanism so the experiment could control every proposition without relying on Provider world knowledge. Four variants were tested:

- baseline;
- meaning-preserving paraphrase;
- causal break;
- explicit contradiction.

Each relation judgment had to cite exactly the supplied segment pair.

### Results

| Variant | Exact closed-label accuracy | Grounding validity | Replicate agreement |
| --- | ---: | ---: | ---: |
| baseline | 62.5% | 100% | 75% |
| paraphrase | 75% | 100% | 50% |
| causal break | 12.5% | 100% | 50% |
| contradiction | 50% | 100% | 75% |

Exact-label paraphrase invariance was only **50%**.

The failures were not random hallucinated evidence. They concentrated on neighboring labels:

- `CONTRASTS ↔ CONTRADICTS`;
- `CAUSES ↔ ENABLES ↔ CONDITION ↔ SEQUENCE`;
- `SUPPORTS ↔ CAUSES`.

The Provider consistently cited the intended evidence pairs while the categorical label boundary drifted.

### R5-A decision

**Retain evidence-addressed propositions and relation hypotheses. Do not promote this closed relation vocabulary as semantic truth.**

The stable object in this experiment was closer to:

```text
source proposition
+ target proposition
+ exact evidence
+ candidate relation family
+ disagreement / uncertainty
```

than to one mandatory ontology label.

## R5-B — video event / narrative grounding

R5-B used the existing owned 78-second Runtime Introduction production. The current Harness Provider is text Chat Completions, not a native raw-video VLM, so R5 did not misrepresent the capability.

The Provider received a **time-coded representation** containing:

- semantic propositions bound to the actual Remotion scene components and time ranges;
- exact narration transcript cues and time ranges.

The baseline checked four events:

- guarded source mutation;
- recorded Job/Attempt observation;
- recovery of the same Job using the same request identity;
- explicit Runtime product boundary.

### Baseline

- event presence accuracy: **100%**;
- grounding validity: **100%**;
- grounding discipline: **100%**.

### Recovery-omission falsifier

All explicit and generic recovery evidence was removed from the time-coded representation. Both Provider replicates still inferred the requested specific recovery event from only generic failure-boundary evidence (`V01` / `en-001`).

- presence accuracy: **75%**;
- grounding validity: **75%**.

The model's story was plausible, but the cited evidence did not establish the requested proposition: “the same request identity recovers the same recorded Job after uncertain delivery.” The grounding validator therefore rejected that event.

### Real-pixel validation

To verify that the source-semantic representation still corresponded to the real rendered artifact, R5 extracted and visually inspected six exact frames from the owned picture master:

- 2s hook — response can disappear while work need not;
- 16s patch — Patch admitted against exact bytes / bounded `policy.py` mutation;
- 30s observation — recorded Job and recorded Attempt;
- 45s recovery — replay exact request identity / recover recorded Job;
- 52s evidence — physical execution fact, not semantic Task completion;
- 70s boundary — semantic Task completion, hostile multi-tenant sandbox, and external-effect idempotency are not claimed.

The sampled pixels matched the time-coded source semantics used by the Provider.

### R5-B decision

**Retain time/evidence-grounded event checking and omission falsifiers. Do not claim native visual understanding.**

This branch demonstrates why grounding should precede free narrative reasoning: a model can infer a coherent event that is not actually established by the remaining evidence.

## R5-C — speech meaning

R5-C deliberately stayed inside the capability actually available. It used the exact Runtime narration transcript and timing, not ASR output, prosodic emotion inference, or music semantics.

Three conditions were tested:

- baseline;
- meaning-preserving boundary paraphrase;
- polarity-flipped boundary claim.

All returned annotations cited the correct cue IDs, but the closed speech-act/polarity labels were unstable.

| Condition | Exact label accuracy | Grounding validity | Replicate agreement |
| --- | ---: | ---: | ---: |
| baseline | 83.3% | 100% | 83.3% |
| boundary paraphrase | 66.7% | 100% | 50% |
| boundary polarity flip | 41.7% | 100% | 16.7% |

### R5-C decision

**Do not retain the current closed speech-act taxonomy as a reusable semantic instrument.**

Exact transcript/timing remains good evidence. The forced categorical label layer did not earn comparable stability.

## R5-D — crossmodal relation probes

R4 rejected “crossmodal correlation = congruence.” R5-D therefore tested explicit relation families over already-grounded visual/audio propositions rather than a scalar score.

Controlled cases included:

- support;
- contradiction;
- extension;
- irrelevance;
- duplication.

Results:

- exact relation accuracy: **80%**;
- grounding validity: **100%**;
- replicate agreement: **100%**.

The only stable disagreement with the oracle was one `SUPPORTS` case that both replicates called `DUPLICATES`.

### R5-D decision

**Crossmodal relation hypotheses are more useful than one congruence scalar, but relation granularity remains uncertain.**

Retain the evidence-linked relation and disagreement boundary; do not promote the five-way vocabulary as a universal ontology.

## R5-E — Agent-observer consequence bridge

R5-E created a fictitious mechanism that the observer should treat as artifact-local knowledge. The observer Provider received one of four conditions:

- explicit causal chain;
- same facts in fragmented order;
- same facts with the first causal trigger delayed until the end;
- no artifact evidence.

Questions were explicitly separated into:

- perception;
- comprehension;
- adaptation.

The observer had to cite artifact evidence for substantive answers and abstain when no evidence was supplied.

### Initial two-replicate run

Across the three evidence-bearing artifacts:

- grounded substantive acquisition: **94.4%**;
- overall artifact task accuracy: **94.4%**;
- presentation-order answer invariance: **83.3%**.

No-artifact control:

- epistemic accuracy: **100%**;
- unsupported assertion rate: **0%**.

The explicit-chain condition had one replicate conservatively abstain on two adaptation questions. Because the same facts in other orderings did not show the same failure, R5 extended only this consequence family without changing prompt, questions, evidence, oracle, or schema.

### Eight-replicate consequence replication

Four conditions × eight replicates = **32 additional Provider observations**, zero Provider failures.

Replication bundle digest:

`sha256:f8a6ad01826e628806b9075f8386ffbbe82d37a66e84ce2d648091906ba5bbce`

Replication score digest:

`sha256:0e08234721df18fb30576dafd50190ab31db8e2e457677142b1502e2b0584e0d`

Final replication results:

- artifact task accuracy: **97.92%**;
- grounded substantive knowledge acquisition: **97.92%**;
- presentation-order answer invariance: **95.83%**;
- minimum and mean grounding validity: **100%**;
- no-artifact epistemic accuracy: **100%**;
- no-artifact unsupported assertion rate: **0%**.

The remaining misses were conservative abstentions concentrated in adaptation questions, not unsupported invented answers.

### R5-E decision

**A grounded knowledge-transfer consequence is substantially more stable here than the fine semantic ontology tasks.**

This does not establish human comprehension. It establishes that a separate observer Agent can acquire and apply fictitious artifact-bound knowledge while respecting a no-evidence abstention control.

## Main R5 result

R5 does not graduate a “semantic feature extractor.” Its most important result is structural:

> **Evidence-addressed meaning is more stable than fine ontology labels.**

Across R5-A/C/D, grounding stayed near-perfect while exact category labels often moved between neighboring semantic interpretations. R5-B showed that even a plausible narrative event should fail when the remaining evidence cannot ground the requested specificity. R5-E showed that knowledge transfer can be measured separately from annotation vocabulary and can remain strong even when fine semantic labels are unstable.

The retained experimental representation is therefore closer to:

```text
proposition / event / answer
+ exact evidence locator
+ candidate relation
+ uncertainty / replicate disagreement
+ consequence type
```

not:

```text
one universal semantic class
one confidence number
one creative-quality score
```

## What R5 retains

- evidence identities and exact locators as first-class semantic support;
- grounding-validity tests independent of answer plausibility;
- controlled meaning-preserving and meaning-changing variants;
- event-omission falsifiers;
- explicit replicate disagreement;
- time-coded event/narrative checks over owned artifacts;
- crossmodal relation hypotheses rather than a congruence scalar;
- typed Agent-observer knowledge-transfer consequence;
- Harness Provider authority separate from Studio domain/oracle authority.

## What R5 rejects or withholds

- current fine discourse labels as semantic truth;
- current speech-act taxonomy as a stable reusable instrument;
- model summaries as ground truth;
- raw-video VLM capability that the current Provider path does not possess;
- ASR/prosody/music semantic claims;
- human comprehension, memory, trust, preference, or behavior claims;
- direct promotion of Provider semantic output into creative priors;
- universal cross-medium meaning or quality direction.

## Evidence retention

Official R5 exact artifacts were archived to Studio local CAS rather than committed to Git.

| Artifact | CAS SHA-256 | Bytes |
| --- | --- | ---: |
| official Provider bundle | `391e6d6c2a2f3bb02d036f8ba96fbb17c6a6eca3a87136feaffb571c4675fd30` | 92,712 |
| official Harness receipt | `22324ed2028bbe8886d13224e303d6a92e4a0aa3e87dc5d676a01cdafb35fcda` | 36,064 |
| official Studio score | `2be18e882062cd165356b39eac86ad89257ac5ff79bdfb4d051459bfa26a2f67` | 5,484 |
| R5-E replication bundle | `6e16e66e53a90167606a9822e822ad3c970afaaeeae321af19ebc98ea9483ecc` | 16,330 |
| R5-E replication receipt | `4a5fc35c86e160971f650a051ebd65313f5c71609394426e0047180fd2e6e438` | 36,495 |
| R5-E replication score | `82120203a623fcba7b24f4eace78c4ddfda7b82fc891bcccf3d1021af5b9fcd1` | 3,147 |

The six sampled video frames are also archived by their exact pixel digests:

- `a345de49443cf6d6a27026a5954edb54cde0a05e70b83cd513d469981caf0393`;
- `46bdf812f95de261a5965f07686bd5950793ae45f4e5e648d545691a60278076`;
- `b1b782cbcb2cdc82af77e7aaf7f256aa98b1da28323ac60a10ba34354a717152`;
- `6f38caa677650804be478bc31a7d0e9ced2df8d9501f90198f6fc5c56caab55f`;
- `5c4602171d5dbaaad09db10d723d4c15f8c0f57af9e8cfd2336dbc7e32c75249`;
- `44ddb1c9ed0353814ea7aec8680b3c851a151c0a8f9a769e2435cb8877ba9cff`.

## World-model update

R5 increases confidence in the following structure:

```text
MEASUREMENT GRAMMAR
    relatively stable
        ↓
EVIDENCE-ADDRESSED PROPOSITIONS / EVENTS
    useful and falsifiable
        ↓
RELATION LABEL
    often a hypothesis with granularity uncertainty
        ↓
CONSEQUENCE
    separately typed and measured
```

The next research pressure should therefore be **controlled creative meaning interventions with real owned-surface consequence**, not a larger semantic ontology. R6 should ask whether changing an evidence-grounded expressive relation changes what an observer actually understands, remembers, trusts, attends to, or does—using human evidence only where the claim genuinely requires human response.
