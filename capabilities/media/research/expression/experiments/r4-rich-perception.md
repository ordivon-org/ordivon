# R4 Rich Perception acceptance — 2026-08-11

## Question

R0-R3 established that shallow metadata and title form are insufficient for a useful global creative optimizer. R4 asks a harder question:

> When Studio perceives substantially more of the artifact itself, does the extra perception produce measurable information gain, and at what scope does that gain survive?

R4 is therefore an equipment-pressure experiment rather than a search for a universal quality score.

The four branches were:

- **R4-A** — full-article structural perception against live matched attention controls;
- **R4-B** — video temporal perception against known same-metadata temporal interventions;
- **R4-C** — audio structural perception against known same-metadata temporal interventions;
- **R4-D** — cross-medium comparison of what can legitimately be shared across article, video, audio, and audiovisual evidence.

Source revision at admission: Studio `4dfddd2ab43dbd6bd66c33cd577eee85062a620f`.

## R4-A — full article perception

### Acquisition

Guardian Open Platform was probed directly and returned `body`, `bodyText`, `trailText`, and `wordcount` for both current section results and most-viewed article IDs through the admitted public test query path.

The experiment used six sections:

- world;
- technology;
- culture;
- business;
- science;
- lifeandstyle.

Eight `most-viewed ↔ same-section newest-control` pairs were retained from each section: **48 pairs / 96 unique articles**.

Full article bytes were processed transiently. The report serializes only structural features, source article IDs/titles, exact body-text content digests, and byte counts. It does not retain Guardian article bodies.

The first 96-object fetch attempt exposed a real equipment failure mode: one TLS handshake timeout killed the whole concurrent batch. Rich-content acquisition was then changed to bounded retries, four-worker concurrency, pair-local omission, and explicit fetch-failure evidence. The repeated live run realized all 48 requested pairs with **zero fetch failures**.

### Rich mechanical measurements

R4-A intentionally began below semantic-model level. It measured transparent full-content structure:

- article/body length;
- sentence count and mean/variation in sentence length;
- paragraph count and mean/variation in paragraph length;
- root type-token ratio;
- mean token length;
- question-sentence and digit-token rates;
- link density;
- lossless-compression ratio;
- first/last-quarter vocabulary overlap;
- trail/lead length;
- normalized paragraph-position profile and generic profile signatures.

These measurements describe artifact structure. They do not label rhetoric, novelty, truth, interest, or quality.

### Held-out discrimination

The experiment compared whether the structural feature direction learned from all other matched pairs predicted which side of one held-out pair was the observed most-viewed article. Significance used **1,000 paired whole-vector sign flips**, preserving the candidate/control pairing under the null.

| Feature view | Leave-one-pair-out accuracy | paired permutation p |
| --- | ---: | ---: |
| title-only shallow baseline | 54.17% | 0.387 |
| rich full-content mechanics only | 43.75% | 0.810 |
| shallow + rich | 35.42% | 0.931 |

Combined information gain over the shallow baseline was **−18.75 percentage points**.

### Result

**The full-content mechanical feature set does not earn promotion as a global Guardian attention-selection model.**

This is not evidence that full content is useless. It is evidence against a much stronger and more tempting claim: that a single direction over these mechanical article properties explains cross-section attention selection.

Section-local behavior strongly reverses that global picture. Rich-only held-out accuracy ranged from **0% in technology** to **87.5% in world**. Feature directions also reversed across sections: for example, `bodyWordsLog`, `paragraphCountLog`, `rootTypeTokenRatio`, `compressionRatio`, and first/last vocabulary overlap each split 3 positive / 3 negative across the six sections.

R4-A therefore increases the probability of this world model:

> richer perception can expose real local structure while making a pooled universal law less valid.

A shared measurement grammar does not imply a shared effect direction.

Final R4-A semantic report digest:

`sha256:5c6860c4ca4195077c0a1bf6d392fa8e98335a37a5b05d304119ff8fbb304146`

Exact 174,219-byte report in Studio local CAS:

`sha256:090bd9922ea3cadf34f08a48a1c9d07c2499952dfec01c999535d1b650e2715d`

## R4-B — video temporal perception

### Why an owned controlled artifact

R4-B did not download third-party video merely to obtain a benchmark. It used the existing 78-second Runtime Introduction picture master, whose production asset manifest declares `rights.status=owned`:

`sha256:77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736`

The experiment generated five reproducible 320×180 / 30 fps / 78-second derivatives by splitting the picture into six equal temporal chunks:

- `same-a` — original order;
- `same-b` — independent render of the same order, serving as a control;
- `swap-middle`;
- `alternating`;
- `reverse`.

All variants retained the same shallow technical fingerprint: duration, width, height, frame rate, and zero audio streams.

### Perception

The retained video measurements are mechanical and temporal:

- mean absolute luma change;
- average luma;
- average saturation;
- normalized positional profiles;
- profile signatures such as coefficient of variation, entropy, lag-1 correlation, peak position, early-vs-late balance, and turning-point rate.

They do not claim scene semantics, shot grammar, beauty, or narrative quality.

### Result

Independent same-order control distance: **0.000**.

Known temporal perturbations:

- minimum structural distance: **0.525**;
- median structural distance: **0.899**.

The rich temporal representation strictly separated every tested reorder from the control while shallow technical metadata remained identical.

**Decision: retain video temporal structural perception as earned equipment.**

What it earned is sensitivity to temporal artifact structure. It did not earn a quality or popularity interpretation.

## R4-C — audio structural perception

R4-C used the owned 78-second English narration candidate:

`sha256:798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d`

The same six-chunk order intervention family was rendered as 48 kHz mono PCM S24LE.

All variants retained the same shallow technical fingerprint: duration, sample rate, channel count, and codec.

The retained mechanical audio profiles are:

- RMS amplitude;
- zero-crossing rate;
- spectral centroid;
- spectral entropy;
- spectral flatness;
- spectral flux;
- their normalized position profiles and generic profile signatures.

Independent same-order control distance: **0.000**.

Known temporal perturbations:

- minimum structural distance: **0.388**;
- median structural distance: **0.802**.

**Decision: retain audio structural perception as earned equipment.**

Again, this establishes temporal/acoustic sensitivity only. It does not establish musical value, emotion, intelligibility, or listener preference.

## R4-B multimodal subtest — audiovisual alignment

The picture and narration were then combined while preserving the marginal content of each modality. Audio was cyclically shifted by 5, 11, and 17 seconds while picture timing remained fixed.

Two candidate diagnostic families were attacked.

### Cue-boundary silence

The baseline narration has slightly lower RMS energy around the eight known cue boundaries than its global mean (`boundarySilenceContrastZ ≈ 0.284`). But the 17-second cyclic shift scored still higher (`≈ 0.351`).

**This metric fails as a reliable alignment detector on this artifact.**

### Video-change ↔ audio-structure coupling

The baseline showed positive correlations between picture-change and:

- audio spectral flux: `≈ 0.153`;
- audio RMS: `≈ 0.163`.

Against all 155 non-zero circular shifts of the 156-bin profiles, the baseline ranked:

- **7 / 156** for video-change ↔ spectral-flux, 96.15th percentile;
- **6 / 156** for video-change ↔ RMS, 96.79th percentile.

However, some shifted alignments still exceeded baseline, and the two-sided absolute-correlation exceed rates remained roughly 10.3% and 9.0%.

**Decision: retain this only as a bounded alignment diagnostic. Do not promote it as an audiovisual congruence detector.**

This distinction matters: a temporal relation can be measurable without establishing semantic congruence, narrative appropriateness, or aesthetic quality.

## R4-D — cross-medium comparison

R4 found one structure worth sharing across media and one structure that must not be shared.

### Shared: measurement grammar

Article paragraph profiles, video-change profiles, and audio-energy profiles can all be described with the same generic positional operators:

- coefficient of variation;
- normalized entropy;
- lag-1 correlation;
- peak position;
- early-vs-late balance;
- turning-point rate.

This is useful because an Agent can ask the same structural questions across media: where variation occurs, how concentrated it is, how repetitive it is, and how its position changes.

### Not shared: meaning or success direction

The same field name has different semantics in each medium:

```text
article paragraph density
≠ video visual-change rate
≠ audio energy or spectral change
```

And R4-A directly shows that even within one medium, effect directions can reverse by section/context.

Therefore R4-D retains:

> **shared structural operators, medium-owned observables, context-conditioned interpretation.**

It rejects:

> **one cross-medium feature vector with one universal success direction.**

## Information-gain matrix

| Branch | What shallow observation could see | What rich perception added | R4 disposition |
| --- | --- | --- | --- |
| Article | title + metadata | full mechanical content structure | no global selection gain; useful local/context evidence |
| Video | duration/resolution/fps | temporal visual structure | retained |
| Audio | duration/rate/channels/codec | temporal acoustic/spectral structure | retained |
| AV relation | marginal picture/audio facts | bounded temporal coupling | diagnostic only; not promoted |

The central result is asymmetric:

> More perception does not guarantee more predictive power. It earns value when it reveals a previously unobservable intervention or reduces uncertainty at the scope actually being tested.

That is a stronger criterion than “the extractor returns more features.”

## Retained world-model changes

1. **Perception bandwidth and explanatory power are separate variables.** A richer representation can increase observability while reducing pooled prediction if effects are context-conditional.
2. **Shared measurement grammar is more stable than shared effect direction.** Position, variation, repetition, concentration, and change can be measured across media without assuming they mean the same thing.
3. **Controlled perturbations are the cleanest acceptance test for perception equipment.** If shallow metadata is held fixed and the apparatus reliably detects the known intervention, the apparatus has earned at least structural sensitivity.
4. **Crossmodal correlation is not congruence.** Temporal coupling may be useful evidence, but semantic relation requires richer perception and/or explicit experimental consequence.
5. **Outer-world fetch robustness is part of empirical equipment.** One unavailable cultural object should become bounded missing evidence, not destroy the whole experiment.

## What R4 does not establish

R4 still does not provide:

- semantic/rhetorical article understanding;
- shot or event semantics;
- ASR-derived video meaning;
- musical sections, harmony, affect, or listener response;
- human comprehension, memory, trust, or preference consequence;
- a causal explanation of Guardian most-viewed selection;
- a universal cross-medium creative-quality model.

Those are future experiments, not hidden claims of R4.

## Exact media evidence

Final R4-B/C/D semantic report digest:

`sha256:4971d45994ff4374b54db3d0452c7d49366b7d28d8cab4959240fd5443d5d85a`

Exact 24,144-byte report in Studio local CAS:

`sha256:10837fcf0f8ece3e48ca61a72caf3051c92447d8392742e32587253a91fe3275`

The generated reorder/shift media are reproducible experiment products and are not promoted to durable selected assets merely because the experiment used them.
