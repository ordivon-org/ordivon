# Cultural Observatory

## Purpose

The Art & Expression Laboratory needs an empirical arm for culture, distribution, and attention. Creative work cannot be improved only from first principles or from an Agent repeatedly judging its own outputs. The Cultural Observatory gives Studio a bounded way to observe external artifacts and their selection context, compare them, generate hypotheses, and return only supported findings to production.

The target loop is:

```text
external cultural world
        ↓
OBSERVE references + selection context
        ↓
CORPUS winners + controls + editorial/expert selections
        ↓
DECOMPOSE / COMPARE
        ↓
HYPOTHESIZE
        ↓
controlled reconstruction / ablation
        ↓
real rendered artifact
        ↓
consequence evidence when available
        ↓
scoped knowledge update or no-op
```

This is empirical creative science, not a popularity optimizer.

## Five experimental responsibilities

These are responsibilities, not five services or databases.

1. **Cultural Observatory** — discover what artifacts and attention signals exist now.
2. **Cultural Corpus** — preserve selection mechanism, encounter, context, and controls rather than a winner-only gallery.
3. **Structure Lab** — decompose artifacts at the shallowest useful level and generate falsifiable hypotheses.
4. **Creative Experiment Lab** — reconstruct, ablate, perturb, render, and compare real candidate artifacts.
5. **Consequence Lab** — observe attention, comprehension, behavior, memory, trust, or another outcome only when the work can actually measure it.

The existing `FRAME → BIND → EXPRESS → RENDER → AUDIT → DECIDE` production protocol remains the production loop. The Observatory supplies external evidence to `FRAME`/`EXPRESS` and can trigger a research branch; it does not replace the protocol.

## Three worlds must remain separable

```text
Artifact world
what the work contains and how it is structured

Attention world
where, when, beside what, by whom, and through which selection mechanism it is encountered

Consequence world
what an observer or population actually does, understands, remembers, feels, or trusts afterward
```

A platform rank is an attention-world observation. It is not direct evidence that one artifact structure caused the outcome, and it is never aesthetic truth.

## Observation contract

`src/ordivon_studio/observatory.py` emits bounded reference/metadata observations with explicit fields for:

- provider and volatile platform surface;
- encounter form;
- external artifact identity, title, creator, publication time, descriptors, and canonical reference;
- **selection basis** such as `top-ranked`, `new-control`, `most-viewed`, `editors-pick`, or `chart-ranked`;
- available outcome signals;
- current context such as section or storefront;
- acquisition source and `bytesOwned=false` by default.

This is deliberately not a universal media object. A cultural observation is evidence about how an external artifact was encountered and selected. If exact audiovisual or text bytes are ever admitted, their rights and byte authority must be established independently.

## Winner/control discipline

A useful corpus contains more than successful examples. Depending on the surface it should seek:

- ranked or high-performing artifacts;
- matched contemporary controls;
- near-threshold cases when accessible;
- editor/expert-selected work;
- long-tail and counterexamples;
- historical work when the question is durability rather than current attention;
- Ordivon intervention outputs when causal evidence is required.

R0-R3 implements the first executable matched-control cases:

```text
Hacker News top-ranked
↔ non-overlapping new-story controls

Guardian section most-viewed
↔ same-section newest controls
```

Matching reduces obvious context mismatch; it does not identify causal effects.

## Platform adapters are volatile equipment

Current admitted source capabilities are projected by:

```bash
uv run python -m ordivon_studio.observatory capabilities
```

The first live no-private-secret adapters are:

- Hacker News official Firebase API — ranked links and new controls;
- Apple Marketing Tools Top Songs RSS — chart rank/reference metadata;
- Guardian Open Platform — section most-viewed, editors' picks, and newest controls using the currently accepted public test query path.

Known but not falsely graduated as live in R0-R3:

- YouTube `videos.list?chart=mostPopular`;
- Douyin hot-video billboard;
- TikTok Creative Center / TikTok One inspiration surfaces;
- Google Trends API Alpha.

Those sources require credentials, permission, alpha access, a stable ingestion surface, or another real admission condition that this workstation does not currently satisfy. The capability projection says so instead of substituting fixtures for live acceptance.

Platform names therefore live in this fast-changing equipment layer, not in durable aesthetic knowledge.

## Why Studio owns the first adapters

Current World source deliberately rejects a generic connector/correlation platform. Its retained-boundary rule requires at least two real consumers before a deleted shared abstraction is reactivated. R0-R3 has one current consumer: Studio.

Studio therefore owns the minimal direct cultural-observation adapters because it owns their domain semantics. If Web or another owner independently needs the same external connection/recovery semantics, that second real consumer can justify promoting the shared connection mechanics to World. Provider authority should move only after practice forces it.

## Acquisition and rights boundary

Discovery never implies byte ownership.

```text
external reference
→ allowed metadata / public observation
→ optional perceptual access under provider terms
→ separately admitted exact bytes only when authority and rights permit
```

The R1 snapshot stores no downloaded audiovisual work. `acquisition.bytesOwned` is false for every observation. Provider APIs and public pages remain subject to their current terms; this apparatus does not create new reuse rights.

## Current analysis layer

R2 intentionally starts with transparent shallow structure:

- title length and word count;
- question / colon / dash / number / parenthetical signals;
- publication age;
- deterministic standardized k-means for broad corpus neighborhoods;
- paired structural contrasts for admitted winner/control families.

These are diagnostics and hypothesis generators, not a model of creative quality. R2's first live run falsified the idea that such shallow features are sufficient: the largest paired standardized difference was only about `0.176`.

R4 then pressure-tested richer artifact perception rather than assuming that more features equal more knowledge. The retained boundary is:

- full-article mechanical structure is useful as context/local evidence, but its first 48-pair live test produced no pooled attention-selection gain and showed strong section-level direction reversals;
- video temporal change/luma/saturation profiles earned controlled sensitivity when shallow technical metadata was held fixed;
- audio energy/ZCR/spectral profiles earned the same controlled-sensitivity status;
- audiovisual change↔audio coupling produced a bounded alignment signal under circular-shift falsification, but did **not** earn promotion as a semantic congruence detector;
- generic positional operators such as variation, entropy, repetition, peak position, and early/late balance can be shared as measurement grammar while medium semantics and effect direction remain local.

See [`experiments/r4-rich-perception.md`](./experiments/r4-rich-perception.md) for the exact acceptance evidence.

Future semantic, rhetorical, shot/event, musical, and cross-modal meaning decomposition should be added only through actual equipment and evaluated against controls. Model-provider calls must use the admitted Harness/Host provider boundary rather than giving Studio its own secret-loading path.

## Evidence retention

Live cultural snapshots are time-sensitive world evidence. They should not become a permanent Git dump.

R0-R3 uses the existing Studio local content-addressed archive for selected snapshot/analysis bytes and commits only compact experiment evidence plus exact digests. Larger or independently important corpora can later earn off-machine replication or a dedicated corpus authority; one 840-item experiment does not justify a new data platform.

## Agent commands

The default bounded loop is available as:

```bash
pnpm culture:capabilities
pnpm culture:collect
pnpm culture:analyze
pnpm culture:loop
```

`culture:loop` collects a new live reference/metadata snapshot and analyzes it. It does **not** automatically publish, mutate production, or promote a prior. A later Agent selects a falsifiable hypothesis and enters the ordinary Studio/Web production loop.

## Promotion rule

The shortest sufficient learning scope wins:

```text
one observation
→ artifact-local evidence

repeated matched evidence + intervention inside one encounter/medium
→ context or medium candidate

repeated materially different contexts/media + surviving falsifiers
→ durable-prior candidate
```

A high view count, chart rank, editorial selection, Agent preference, or one successful intervention is never sufficient by itself to become a cross-medium law.
