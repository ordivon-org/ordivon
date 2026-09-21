# Browser Decision Architecture R1

## Scope

This document freezes an evidence-backed architecture direction for browser candidate selection.
It does not authorize a production route change. The purpose is to separate browser observation,
candidate evidence, ranking, calibration, and execution so each responsibility can be owned by an
external standard or mature tool where available.

## Local evidence summary

### 1. Laya listwise representation is the wrong default for large candidate sets

With the same exact Laya checkpoint, listwise dynamic options collapsed at larger K while
independent binary scoring recovered the synthetic target on most cases. This isolates the dominant
observed failure to representation/shared-budget effects rather than the encoder alone.

### 2. Generic retrieve-then-rerank is not automatically superior for browser-scale K

On a hard-negative synthetic workload, semantic-search MiniLM improved retrieval over generic
MiniLM, while naive TF-IDF plus RRF did not improve the task. MS-MARCO CrossEncoder errors were
semantic/action errors, not merely recall errors.

The current Jev snapshot caps actions at 250. On the same synthetic workload, directly scoring all
candidates with cross-encoder/ms-marco-MiniLM-L6-v2 took median latency of approximately:

- K=50: 8.8 ms
- K=100: 14.4 ms
- K=200: 24.2 ms
- K=250: 28.8 ms

Therefore an ANN/retrieval stage is not justified as the default browser path at the present
candidate ceiling. It remains optional for CPU-only deployments, substantially larger candidate
sets, or future evidence.

### 3. Candidate evidence projection dominates model swapping

Two exact local Jev fixture snapshots were captured from the existing snapshot.js: travel and
research. Fourteen CLICK decisions were evaluated under three projection modes while holding the
retriever and CrossEncoder fixed.

| Projection | Retriever Top-1 | CrossEncoder accuracy |
|---|---:|---:|
| label only | 42.9% | 35.7% |
| current Jev candidate fields | 42.9% | 42.9% |
| current plus href plus local contextual text | 78.6% | 100.0% |

This is local fixture evidence, not a representative web benchmark. It establishes that semantics
already present in the observation can dominate model choice.

### 4. Base Laya is not currently a browser reranker

On the same fourteen real-snapshot-derived decisions, independent Laya binary scoring achieved:

- label only: 7.1%
- current Jev fields: 7.1%
- enriched projection: 0%

This is a domain mismatch, not evidence that Laya cannot be specialized. It does mean that current
base Laya must not receive browser reranker authority.

## External owner map

### Role, state, and property semantics

Normative owner: WAI-ARIA 1.2 Recommendation.

Ordivon should not invent role/state/property semantics.

### Accessible name and description

Normative baseline: Accessible Name and Description Computation 1.1 Recommendation.
AccName 1.2 is currently a Working Draft and may be monitored but is not the frozen normative
baseline.

The existing Jev snapshot.js contains a hand-written accessible-name approximation. That logic is
a replacement candidate, not a domain asset.

### Browser accessibility observation and refs

Implementation owner candidate: Playwright accessibility snapshots and browser accessibility APIs.

Playwright already produces an accessibility tree containing role/name, static contextual text and
interactive refs. Its agent CLI specifies that refs are snapshot-scoped and should be refreshed
after page change. A local fixture run also showed that the native tree preserves the card/article
structure that made the enriched projection useful.

This does not by itself replace the existing Jev freshness guard. Observation semantics and
effect-fencing are separate responsibilities.

### Candidate ranking

Implementation owner: mature independent pair/passage scoring, initially Sentence Transformers
CrossEncoder as a reference implementation.

Current evidence does not admit the generic MS-MARCO model as a production browser policy. Its role
is an architecture oracle showing that independent evidence-rich scoring is viable. Browser-domain
training or a better action-aware pretrained model must pass the same benchmark before admission.

### Large-corpus retrieval

Owner: mature IR stack such as Sentence Transformers bi-encoders and Faiss.

This belongs naturally to Opportunity/persistent-corpus workloads. It is not in the default
browser path while candidate sets remain at current browser-scale bounds.

### Calibration

Independent calibration/evaluation owner. Model-native confidence is not execution authority.

### Freshness and effect execution

Keep the current Browser Harness/Jev freshness and single-mutation semantics until a direct duel
proves another mature substrate has equivalent or stronger failure semantics. Playwright refs and
re-snapshot discipline are promising, but auto-relocation or retry semantics must not silently
turn a stale decision into a different effect.

## Candidate projection boundary

Do not create a persistent Ordivon browser ontology.

A candidate projection is an ephemeral, reproducible view of an observed browser action. Prefer
upstream semantics:

- operation or affordance;
- accessible role;
- accessible name;
- accessible description when available;
- value and standard state/properties;
- href/target semantics for links where relevant;
- accessibility-tree context when additional local meaning is necessary.

Ancestor scope.innerText is experimental evidence only. It must not become a canonical field.
Prefer a browser-owned accessibility subtree/ARIA snapshot or another externally owned semantic
projection.

## Frozen R1 flow

Browser
  -> upstream accessibility / DOM observation
  -> deterministic actionability and operation partition
  -> ephemeral evidence-rich candidate projection
  -> independent reranker over all operation candidates
  -> independent calibration / selective gate
  -> freshness-bound executor
  -> independent outcome witness

The default path intentionally has no retrieval stage.

## Optional escalation paths

- Add retrieval only when measured candidate scale or hardware makes all-candidate reranking
  uneconomic.
- Re-admit Laya only after browser-domain training beats the CrossEncoder/reference baseline on
  target-domain accuracy, calibration, latency and lifecycle cost.
- Use set-aware architectures only when the decision semantically depends on candidate-to-candidate
  interactions, such as portfolio composition.
- Use learning-to-rank when stable browser/domain features and query-group training data exist.

## Non-goals

- no new browser ontology;
- no new accessibility-name algorithm;
- no generic ANN service for a <=250-action page merely because ANN is available;
- no production route change from this research evidence;
- no claim that the local fixture represents the open web.


## Freshness boundary falsification

Playwright snapshot refs were tested separately from semantic decision freshness on the local Jev
fixture using both the existing CLI 0.1.18 and the current CLI 0.1.21.

Two mutations were applied after a decision snapshot but before execution:

1. Replacing the target DOM button with a new node having the same accessible name caused the old
   Playwright ref to fail closed and request a new snapshot.
2. Changing the surrounding semantic context of the still-connected target button, without
   replacing the button, allowed the old Playwright ref to execute successfully.

Therefore Playwright refs are a useful node-identity witness but do not prove that the semantic
facts used by the decision are unchanged.

The residual Ordivon/Jev-owned responsibility is narrowed to a decision-bound semantic witness.
It should bind only the observed facts that materially influenced the decision and fail closed if
those facts change before mutation. It must not duplicate accessible-name calculation, ARIA role
semantics, browser candidate enumeration, or general DOM representation.


## AX action-space migration probe

An experimental Chromium AX projection was compared directly against the legacy Jev snapshot on the
same live local fixture page.

- Travel: both produced 13 actions with identical operation counts: 9 CLICK, 1 FILL and 3 SELECT.
- Research: both produced 6 CLICK actions.
- Research matched directly for all six normalized action tuples.
- Travel differences were presentation-level: Jev prefixes the searchbox CLICK label with
  "Open", while the AX projection preserves the browser-owned accessible name; Jev also flattens
  SELECT control and option into one label while the AX projection keeps optionName structural.

This supports continuing the AX migration experiment without copying Jev's operation-specific
presentation strings. It does not prove general web equivalence. Affordance binding and context
selection remain experimental policy.


## AX Generalization R1

The AX projection has now passed an expanded controlled-fixture generalization gate after one
important correction: AX semantics alone are not sufficient to grant effects.

The first expanded fixture exposed password/file safety regressions, summary/contenteditable
coverage gaps and duplicate gridcell actions. The hardened composition now uses browser-owned AX
semantics plus minimal browser-owned DOM metadata, with strict fail-closed behavior when metadata
is unavailable.

After hardening, light-DOM effect space matched Jev 27/27, the AX path additionally exposed three
Shadow DOM actions, and same-process iframe effects matched 3/3.

Observation metadata is acquired with one pierced DOM.getDocument call rather than per-candidate
DOM.describeNode calls. Forced site-per-process testing also showed that OOPIFs should be treated
as separate CDP targets; Playwright can provide a frame-specific CDP session, after which the same
AX+DOM projector is reused.

This narrows the custom residual further: effect binding, ephemeral context projection and semantic
witnessing remain ours; accessibility semantics, DOM facts and cross-process browser transport do
not.


## Decision Provider Duel R1

The first digest-bound Browser Decision Corpus contains 42 controlled-fixture cases after singleton
candidate sets are removed from the ranking problem. System-1 benchmark semantics now support a
generic dynamic_choice primitive so each case may expose its own candidate set while retaining the
existing EXECUTED / ERROR / BLOCKED, Brier, NLL, ECE, latency and digest contracts.

On the frozen R1 corpus:

- ms-marco MiniLM CrossEncoder: 39/42 (92.86%), MRR 0.9643, full coverage;
- base Laya via independent per-candidate noul normalization: 5/42 (11.90%), full coverage;
- Jev Windows route: 0/42 executed because the existing route readiness gate remains blocked by
  missing TYPESAFE_API_KEY; those cases remain BLOCKED rather than becoming wrong or zero-latency.

A name-only zero-training lexical baseline reaches 36/42, showing that much of the controlled
corpus is deliberately easy. The important CrossEncoder evidence is 8/8 on context-required cases,
where the same name-only baseline is 4/8.

Two of the CrossEncoder's three errors disappear under a diagnostic semantic effect-class
reduction that separates CLICK-to-focus candidates from CLICK-to-activate candidates. The
reduction changes no previously correct case and reduces candidate pairs from 638 to 416.
The remaining g17 case was shown by live AX ancestry inspection to reintroduce a parent/child
ambiguity already removed by the observation projector, so it is retained as benchmark-design
negative evidence rather than training justification.

R1 therefore does not authorize Browser-specific model training. The training gate reopens only
after a larger real-page / real-application census leaves a reproducible residual that cannot be
explained by observation completeness, effect partitioning, deterministic reduction or benchmark
contamination. Production Jev routing remains unchanged.
