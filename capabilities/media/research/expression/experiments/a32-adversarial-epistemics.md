# A3-2 — Adversarial epistemics / controlled revelation

## Question

Can the Art & Expression model preserve an Agent's actual information boundary while still producing suspense, dramatic irony, and a meaningful reveal?

A3-1 was dominated by clarity and continuity. A3-2 deliberately changes the target. The work must carry **uncertainty** without making uncertainty merely confusing.

## Frozen evidence

The experiment is bound to `a32-security-ae0-evidence.json`, derived from the accepted Security AE0 evidence artifact.

The relevant proposition is:

> Two different current worlds can give the Defender byte-identical admissible pre-inspection evidence. The same adversarial claim therefore does not justify a hidden-world consequence; `UNKNOWN` may justify information acquisition. Only later authoritative world truth permits the trajectories to diverge.

This is not a generic story about misinformation. It is a visualization of one accepted local experiment.

## Experiential intent

Primary outcomes:

- **suspense** — a consequential decision is pending while truth is unavailable;
- **epistemic tension** — the work should make “I have evidence, but I do not have truth” perceptually distinct;
- **trust** — the composition must not cheat by revealing forbidden information through incidental visual coding;
- **revelation** — when world truth arrives, divergence should feel earned rather than decorative.

Secondary outcomes: clarity, memorability, presence.

## Tension profile

| Tension | Chosen region | Reason |
| --- | --- | --- |
| fluency ↔ challenge | clear local states, withheld global answer | uncertainty should require waiting/inspection, not decoding bad design |
| familiarity ↔ novelty | familiar claim / inspect / outcome terms | novelty comes from epistemic staging, not exotic notation |
| predictability ↔ surprise | inspection is predictable, truth/outcome divergence is delayed | the reveal is causally prepared |
| continuity ↔ discontinuity | identical pre-truth trajectory, justified branch after truth | the branch itself is the proof |
| restraint ↔ expression | pre-truth phase visually restrained; reveal is the expressive peak | avoid leaking hidden state early |
| explicitness ↔ ambiguity | evidence explicit, hidden truth deliberately ambiguous | ambiguity is lawful because the Agent genuinely lacks truth |
| density ↔ space | sparse pre-inspection field, richer post-truth split | information density should track epistemic entitlement |
| unity ↔ variety | pre-inspection near-perfect symmetry, post-inspection asymmetry | variation must occur only after new information exists |

## Focalization as an experimental variable

### Web — Defender-near focalization

The Web treatment should initially show only what the Defender can justify:

```text
communicated claim: compromised = true
ambient truth: UNKNOWN
same admissible context
        ↓
      INSPECT
```

The two hidden worlds should **not** receive different pre-inspection colors, geometry, labels, or provenance. The page may explain that two worlds exist, but it should not spatially resolve them until the `world-truth` boundary.

After truth, the page may branch:

```text
truth=false → hold
truth=true  → quarantine
```

Web therefore uses controlled disclosure through document hierarchy.

### Motion — privileged-audience → Defender focalization → reveal

Motion can exploit changing point of view:

1. briefly show the audience two private worlds: one healthy, one compromised;
2. show the autonomous Deceiver publishing the same `compromised=true` message in both;
3. close an epistemic mask over private truth and move into the Defender's view;
4. collapse both trajectories into one visually identical evidence state labeled `UNKNOWN`;
5. hold on the decision boundary long enough for uncertainty to become felt;
6. let the same inspection intent propagate into both worlds;
7. reveal later `world-truth` events;
8. only then split the composition into hold versus quarantine.

The audience is temporarily more informed than the Defender, creating dramatic irony. The composition must then deliberately surrender that privileged view while representing the Defender's decision.

## Hard anti-leak invariants

Before authoritative truth arrives, the two Defender trajectories must not differ in:

- claim text;
- message identity;
- visible provenance;
- context digest;
- decision/request identity;
- color semantics;
- relative layout;
- motion timing;
- label wording.

If any of those differ, the artwork invents a side channel that AE0 explicitly removed.

## Evaluation

The first render should be rejected or revised if:

- viewers can infer which world is compromised from Defender-visible styling before truth;
- `UNKNOWN` reads as “probably false” or “probably true” rather than genuinely unresolved;
- inspection looks like passive omniscience rather than an explicit costly action;
- the receipt is visually confused with world truth;
- post-truth divergence occurs before the authoritative reveal;
- the Motion version is merely a moving split-screen diagram;
- the Web version exposes hidden truth so early that the information boundary becomes intellectually obvious but experientially meaningless.

No population preference claim is part of A3-2.


## Symmetry caveat

The two private-world panels are parallel experimental conditions, not probability weights. Equal screen area must not be interpreted as a `50/50` prior. Motion states this during the privileged-audience phase; Web states the same boundary beside the unresolved possible-world silhouettes.


## Epistemic color correction

The first rendered Defender state used the expression `signal` color for `truth: UNKNOWN`. That was rejected because it visually moved UNKNOWN toward the feared compromised outcome. UNKNOWN now uses the neutral accent channel; outcome colors remain reserved for truth-revealed healthy/compromised states.


## First rendered result

A3-2 produced a real Remotion composition and a Web consumer against the same frozen Security AE0 evidence. The expressive problem is no longer persistence but **lawful uncertainty**.

### Motion render evidence

`a32-security-ae0-epistemics` was rendered at six semantic checkpoints:

```text
frame 30   privileged audience / private worlds
           sha256:d2506d1536ca7871f8c38cbb033c107064a7cdcfbf68e332cef0343f13ac1ea7
frame 72   epistemic mask closes
           sha256:6f0f9180545482bc62c1baef7f4604aa042c3b1a42c612f617f19ef07c6e5154
frame 112  Defender admitted evidence / UNKNOWN
           sha256:e34076975506db2fb8519f1f045ce0509bbdca854e20653470b1ef37be900e3a
frame 156  inspection / receipt is not truth
           sha256:32c5c4bf507f2a711070938719f70048c2ef31ba405ac05edb270b82bdf5d642
frame 205  authoritative world-truth reveal
           sha256:223ce90bf54d9695182ba24f7cf4d60810f5dffd5849721442463d168468855c
frame 250  justified hold / quarantine divergence
           sha256:556a2ec60dac07f907c305dc15d6391ee28fee206b05c6dc8dfefef88aafb4d7
```

Motion uses focalization change rather than merely moving a split-screen diagram: the audience briefly knows more than the acting Agent, then the composition explicitly closes that privileged view and holds on the Defender's admitted evidence until authoritative truth arrives.

### Web render evidence

Web uses document order and controlled disclosure. Its pre-truth subtree contains unresolved possible-world silhouettes behind one dominant admitted-evidence surface; healthy/compromised outcome components appear only after the truth-reveal boundary. Desktop and 390px mobile captures have no horizontal overflow.

```text
Web desktop  sha256:26a7b1e72cf0f747f3d2e8e7456cb32d73d87858bf8bfde85131b653b91854bb
Web mobile   sha256:5f80ed783ae1de979c88db8ec6232ae268f9272b44801863a9347ece0b3114a6
Web baseline sha256:629ea7809195352d9d43c48fa1d4fb37bf18a2a24a734f1738e8ced2ed052b59
```

## Two falsifications discovered by rendering

### 1. Symmetry can invent probability

Equal unresolved world geometry can imply a `50/50` prior that AE0 never established. The work now states explicitly that the two panels are experimentally demonstrated possibilities, not equal probability weights.

> Visual balance is not quantitatively innocent.

A balanced composition can accidentally assert equal likelihood, equal importance, equal causal weight, or equal trust.

### 2. Outcome color can contaminate UNKNOWN

The first candidate colored `truth: UNKNOWN` with the expression `signal` channel. That perceptually moved uncertainty toward the feared compromised outcome even though the accepted experiment supplies no such posterior.

UNKNOWN now uses the neutral accent channel; success/signal outcome colors appear only after authoritative world truth arrives.

> Semantic color can invent likelihood or severity before evidence authorizes it.

## What transferred across media

A3-2 supports A3-1's finding that higher-level expressive relations transfer better than component geometry. The transferable structure here is:

1. **information entitlement** — whose view the artifact is presenting;
2. **epistemic phase** — before truth, after information acquisition, after truth;
3. **reveal authority** — divergence is visually illegal until the authoritative event exists;
4. **focal hierarchy** — admitted evidence dominates unresolved possibility before truth;
5. **semantic restraint** — probability, trust, severity, and outcome cues cannot be smuggled in through balance or color.

The medium-specific realization differs:

```text
Web     → document hierarchy / controlled disclosure
Motion  → focalization change / dramatic irony / timed reveal
```

## A3-1 versus A3-2

The two trials pressure opposite expressive regimes:

```text
A3-1
clarity about a stable fact
continuity survives a visible break

A3-2
lawful ambiguity about a hidden fact
symmetry survives until evidence permits a break
```

The same tension/context model remained useful, but the desirable settings changed. A3-1 spends expression on rupture. A3-2 spends restraint on the pre-truth phase and reserves expression for the authoritative reveal.

This is evidence that the laboratory is not merely a style guide for technical diagrams.

## Provisional cross-medium law

A3-2 supports the following local production rule:

> **When a work represents an Agent's knowledge state, visual semantics must obey the same information boundary as explicit text and data.**

Color, symmetry, scale, timing, provenance, spatial separation, and emphasis can all function as implicit observations. They require the same scrutiny as a textual claim.

This remains a local Art & Expression result, not a universal law of aesthetics.

## Next pressure

Do not immediately add another technical system explainer. A useful A3-3 should remove explicit factual branching almost entirely and test whether the laboratory can guide **affect** itself — for example isolation, awe, dread, intimacy, loss, or relief — while retaining source truth and medium discipline.
