# R6 Creative Alpha Research — 2026-08-11

## Research question

R5 established that evidence-addressed meaning is more stable than fine semantic labels and that Agent-observer knowledge transfer can be measured separately from annotation. R6 moved one layer outward:

> Can Studio change one bounded expressive relation in a real owned browser artifact, record the actual encounter, and estimate a typed downstream consequence without confusing search inflation, proxy scores, or one observer class with creative truth?

R6 did **not** build a Creative Reward Model. It built and attacked a small research-validity substrate first, then used the surviving institutions for a controlled browser-grounded intervention.

The research loop was:

```text
REGISTER
→ SEARCH
→ FREEZE
→ INTERVENE
→ EXPOSE
→ MEASURE
→ VALIDATE
→ OOS
→ PORTFOLIO CONTEXT
```

The production loop remains separately owned by `FRAME → BIND → EXPRESS → RENDER → AUDIT → DECIDE`.

## Definition used in R6

`Creative Alpha` is an experimental term, not a quality score:

> **incremental typed consequence under a controlled creative intervention and explicit encounter context.**

The object therefore retains intervention identity, observer class, encounter, outcome type, uncertainty, search provenance and scope. Popularity, preference, comprehension, memory, trust and action are not interchangeable outcomes.

## R6-0 — research-validity substrate

Studio added the minimum equipment needed to survive high-throughput Agent search:

- append-only, hash-chained Trial Ledger;
- typed `primary / guardrail / secondary / exploratory` outcomes;
- fixed search-budget registration;
- candidate freeze;
- search-replay null correction;
- raw holdout seed commitment with later reveal;
- separate calibration of search and holdout evidence.

This implementation remains Studio-local during R6 even though Finance independently owns a similar Trial Ledger. Two real consumers now exist, but extraction into a shared Harness/Runtime primitive should follow a separate cross-project audit rather than happen during the experiment that first established the second consumer.

## R6-A — attack the research institution before using it

The null universe had exactly zero Creative Alpha. Candidate results were generated only from noise. The question was whether increasingly capable search could manufacture convincing winners and whether the apparatus could still reject them.

### A1 — static best-of-N search

A 5,000-candidate zero-effect search produced:

- selected visible statistic `z = 4.0061`;
- naive one-sided `p = 3.09e-5`;
- full-search replay corrected `p = 0.1404`;
- pristine holdout `z = 0.4460`, `p = 0.3278`.

The apparently extraordinary visible winner disappeared once the search process became part of the evidence.

Across 400 zero-effect worlds, naive false positives reached **100%** by a search budget of 100 and remained 100% at 1,000 and 5,000 candidates. The search-replay correction remained approximately calibrated at 3.5–5.75%, while the independent holdout remained at 3.5–6.75%.

### A2 — adaptive search

A harder search first explored correlated creative families and then spent 82% of later attempts exploiting whichever family currently looked strongest. The 5,000-attempt adaptive search produced:

- visible `z = 4.7226`;
- naive `p = 1.16e-6`;
- search-replay corrected `p = 0.01998`.

This was deliberately retained as a **red result**. The corrected test had not failed mechanically; a test calibrated around alpha=0.05 still has residual Type-I error. R6 did not replace the seed or change the threshold after observing the result.

The previously sealed holdout then returned:

- `z = -0.3285`;
- `p = 0.6287`.

The independent evidence rejected the false Creative Alpha.

### A3 — dual-evidence promotion institution

Only after A2 exposed the residual false-positive boundary did R6 define a new future promotion institution: a searched candidate needs both search-aware support and independent pristine holdout support. This was not used to rewrite A1/A2 history.

A fresh calibration over 800 adaptive zero-effect worlds at 5,000 attempts measured:

- naive false-positive rate: **100%**;
- search-corrected false-positive rate: **4.875%**;
- sealed-holdout false-positive rate: **5.625%**;
- both independent evidence classes falsely promoting together: **0.125%**.

### R6-A decision

Retain:

- **search is data**;
- complete trial history, including failures and duplicates;
- search-replay nulls as search-selection diagnostics;
- physically/operationally separated pristine holdouts;
- distinct evidence classes rather than one corrected score.

Reject:

- “best visible result = evidence”;
- “corrected p = truth”;
- tuning the experiment after an inconvenient holdout.

## R6-B — owned Web encounter surface

Web added a deliberately small local experiment harness rather than a general analytics platform:

```text
manifest
→ deterministic randomized assignment
→ explicit assignment probability / propensity
→ real Chromium render
→ actual exposure event
→ typed outcome when requested
→ exact representative pixels/text/evidence receipt
```

The first instrumentation-only dogfood used 80 synthetic browser participants. Every assignment was unique, every exposure occurred exactly once, every instrumentation outcome occurred exactly once, all propensities were explicit, and every assignment remained bound to an exact variant digest.

Two real equipment failures were found before semantic experimentation:

1. a Runtime workspace temporary path was too long for a Chromium Unix socket; the harness now uses a bounded `/tmp` browser temp root when necessary;
2. an asynchronous click handler accessed `event.currentTarget` after an `await`; the target is now frozen before the async boundary.

A synthetic click remains only instrumentation evidence. It is not a human-response observation.

## R6-C — grounded reveal-order intervention

R6-C used two fictitious mechanisms, A and B. Each contained the same seven factual evidence blocks under all three variants:

- `F1` trigger;
- `F2` transfer/gate;
- `F3` cooling;
- `F4` final permission boundary;
- `F5` explicit causal boundary;
- `D1/D2` plausible but explicitly non-causal diagnostics.

Only order changed:

```text
explicit-chain     F1 F2 F3 F4 F5 D1 D2
fragmented         D1 F5 D2 F3 F4 F2 F1
evidence-delayed   F2 F3 F4 D1 D2 F5 F1
```

The encounter was a real Chromium initial viewport with no scroll. The observer received only evidence blocks intersecting that viewport, plus exact screenshot/evidence digests.

### Pre-Provider apparatus correction

R6 records an experimenter failure before the first semantic Provider call. At 900px height, `explicit-chain` exposed only `F1/F2/F3`; the crucial final permission boundary `F4` began below the viewport. That would have tested accidental clipping rather than the intended reveal-order treatment.

The actual block coordinates were measured. Section four began near 926px and section five near 1146px. Before any Provider observation, the viewport was frozen at **1080×1050**, giving exactly:

- explicit: `F1 F2 F3 F4`;
- fragmented: `D1 F5 D2 F3`;
- evidence-delayed: `F2 F3 F4 D1`.

From the first Provider observation onward, text, order, questions, oracle and viewport were frozen.

### Provider authority

Studio built the experiment, oracle and score. Web owned browser assignment/exposure/render evidence. Harness owned the DeepSeek credential and structured completion path. Studio never loaded the Provider secret.

Visible run:

- 6 encounter tasks;
- 8 semantic replicates each;
- 48 scored observations;
- one mechanical Provider turn produced no structured conclusion and was retained as failure evidence rather than scored or erased.

Provider authority remained:

- `deepseek-v4-flash`;
- `credential-scope:deepseek:flash:0`;
- `deepseek.chat-completions.non-thinking.v1`.

### Visible results

| Variant | Adaptation | Comprehension | Perception | Grounding | Unsupported assertion |
| --- | ---: | ---: | ---: | ---: | ---: |
| explicit-chain | 100% | 100% | 100% | 100% | 0% |
| fragmented | 81.25% | 43.75% | 12.5% | 28.125% | 64.58% |
| evidence-delayed | 91.67% | 93.75% | 0% | 89.58% | 6.25% |

The preregistered explicit-chain minus fragmented adaptation difference was **+18.75 percentage points**. Treatment grounding and unsupported-assertion guardrails both passed.

This froze the treatment/control identity before content holdout reveal.

A central R6-C result is that **task correctness and evidence quality remain different consequences**. The delayed condition often reached correct adaptation answers despite failing perception questions and sometimes citing insufficient evidence. R6 therefore refuses to treat answer accuracy alone as semantic success.

## R6-D — physically sealed content OOS

Before visible A/B experimentation, Runtime generated a random mechanism-C seed in a separate Job. The visible experiment received only its SHA-256 commitment. The raw seed remained only in a Runtime stdout Artifact and was not read until after the visible contrast was frozen.

After freeze, the seed was revealed and created a never-before-seen mechanism C with new entities and numeric thresholds. The exact same ordering transformation and 1080×1050 browser encounter were then applied.

Holdout run:

- 3 encounter tasks;
- 8 semantic replicates each;
- 24 scored observations;
- one additional mechanical no-conclusion failure retained separately.

### Pristine content-holdout results

| Variant | Adaptation | Comprehension | Perception | Grounding | Unsupported assertion |
| --- | ---: | ---: | ---: | ---: | ---: |
| explicit-chain | 95.83% | 100% | 100% | 100% | 0% |
| fragmented | 91.67% | 50% | 25% | 33.33% | 56.25% |
| evidence-delayed | 50% | 62.5% | 0% | 56.25% | 39.58% |

The frozen explicit-minus-fragmented adaptation difference remained positive at **+4.17 percentage points**. Under the preregistered bounded decision law, visible candidate support plus a positive pristine-content holdout and perfect treatment grounding constituted artifact-content OOS support.

That statement is deliberately narrower than a population causal claim.

### Descriptive uncertainty after freeze

A post-freeze 20,000-draw nonparametric bootstrap over Provider replicate-level adaptation accuracy was added only to describe uncertainty; it did not change the R6-C/D decision law.

- visible observed delta: +18.75pp, descriptive bootstrap interval **[0, +37.5pp]**;
- pristine content holdout: +4.17pp, interval **[-8.33pp, +16.67pp]**;
- holdout bootstrap fraction with positive delta: about **63%**;
- effect shrinkage from visible to holdout: **−14.58pp**.

Therefore R6 supports **directional artifact-content replication under one Agent-observer class**, not a stable effect-size estimate. The current evidence is too small and too provider-specific for a population-level causal interval.

The OOS matrix is explicitly:

```text
artifact content   tested pristine
observer class      not OOS
encounter           not OOS
time                not OOS
medium              not OOS
human response      not measured
```

## R6-E — creative-program portfolio context

R6 finally asked whether the strongest standalone variant has the same marginal value in every current creative program. Using the measured Agent-observer adaptation rates across A/B/C, a 20% funded reallocation toward `explicit-chain` was compared under three program compositions.

| Current program | Adaptation delta | Expression-concentration delta |
| --- | ---: | ---: |
| already explicit-heavy | +0.69pp | +0.0584 |
| fragmented-heavy | +2.64pp | −0.1656 |
| balanced | +2.31pp | +0.0267 |

The same candidate therefore has materially different program-level consequences. In a fragmented-heavy program it both improves the measured consequence and reduces expression concentration; in an already explicit-heavy program the marginal adaptation gain is much smaller while concentration rises.

Expression concentration is only a program-composition diagnostic. It is not a utility function and R6 does not optimize a creative portfolio.

## Main R6 world-model update

R6 adds several stronger structural claims to R4/R5:

```text
R4: measurement grammar can be stable before effect direction is stable
R5: evidence-addressed meaning can be stable before fine ontology is stable
R6: research validity and encounter identity must be stable before a Creative Alpha claim is meaningful
```

A useful evidence ordering is now:

```text
exact artifact / evidence identity
→ exact search history
→ exact encounter / assignment / propensity
→ grounded observer consequence
→ search-aware + independent OOS support
→ scoped effect hypothesis
→ broader observer / time / medium replication
→ only then a durable creative prior
```

The most important negative result is equally important:

> A highly optimized visible creative result can be statistically inevitable under pure noise, and even a correctly calibrated search-aware test can occasionally false-positive. No single score, reward, judge or corrected p-value deserves creative authority.

## What R6 retains

- Studio-local research registration and append-only search history;
- search-replay null as a falsifier for best-of-N inflation;
- pristine holdout as a distinct evidence class;
- Web-owned assignment / propensity / realized-exposure receipts;
- exact initial-viewport evidence as an encounter fact;
- typed consequence rather than one Reward;
- controlled same-fact expression interventions;
- explicit OOS dimensions rather than one `OOS passed` flag;
- program-level marginal contribution as a separate decision lens;
- mechanical Provider failures retained separately from semantic replicates.

## What R6 does not establish

- human comprehension, memory, preference, trust or behavior;
- a stable +4.17pp or +18.75pp population effect;
- cross-provider observer generalization;
- time, device, audience or medium generalization;
- a universal law that causal order is always better;
- a Creative Reward Model;
- a production portfolio optimizer;
- a reason to move all experiment machinery into a new shared service immediately.

## Next pressure

The next research frontier should **not** be a larger optimizer. It should attack scope:

1. repeat frozen expressive interventions across more pristine artifact worlds;
2. change observer class/provider before claiming Agent-general consequence;
3. introduce real human evidence only when making a human-response claim;
4. test time/encounter/medium drift separately;
5. audit whether Finance + Studio now justify extracting the repeated Trial Ledger/search-history primitive into a shared Harness/Runtime layer.
