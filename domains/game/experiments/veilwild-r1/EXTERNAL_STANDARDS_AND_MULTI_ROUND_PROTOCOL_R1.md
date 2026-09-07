# Veilwild R1 — External Standards + Multi-Round Quality Protocol

Date: 2026-09-07
Status: `PRODUCTION_CAMPAIGN_POLICY`

## 1. Campaign duration law

Veilwild R1 is not a one-wave campaign. Agent occurrences are finite episodes; the campaign may continue for as many rounds as product/evidence/friction pressure justifies.

```text
SystemNonTermination
+
LocalFiniteEpisodes (~25 min typical)
```

No fixed maximum round count is declared. Ten, twenty, or dozens of rounds are acceptable when each round has a real unresolved target.

However:

```text
MoreRounds != BetterProduct
```

A new round must carry at least one concrete pressure source:

- unresolved product defect or quality gap;
- failed independent oracle;
- unmet external-standard requirement/recommendation judged relevant to scope;
- Human evidence gap or contradiction;
- unresolved cross-E2E interface defect;
- real Workstation/tool/interchange friction with reusable value;
- performance/resource gap under an exact condition;
- newly admitted capability/front under the scope-pressure protocol;
- regression introduced by a prior repair;
- independent reviewer disagreement that matters to product consequence.

Do not create polishing churn merely to increase round count.

## 2. Round lifecycle

Each round is one finite episode over a frozen input candidate.

```text
RoundInputFreeze
→ independent first verdict where independence is required
→ Board interface/blocker exchange
→ owner-correct production/repair
→ constituent validation
→ integrated replay
→ external-standard delta review
→ friction capitalization
→ independent adjudication where required
→ RoundStandingFreeze
→ derive next-round pressure
```

A round may be specialist-only, integration-heavy, Red-Team-heavy, performance-heavy, Human-evidence-heavy, or friction-capitalization-heavy. Do not force all 25 roles to run every round.

## 3. Dynamic population law

The opening population is 25 roles, not a permanent fixed population.

Later rounds derive Agent occurrences from unresolved fronts:

```text
unresolved closures + dependency pressure + judge independence + friction ownership
→ next-round Agent population
```

Examples:

- if only animation deformation + interchange + QA remain, run those owners and judges;
- if visual quality is still weak, reactivate Art Direction + Environment + Creature + Material + Lighting + Rendering + Player Experience;
- if a new stable capability emerges, admit and assign a new owner;
- if a front has genuinely closed and has no regression exposure, do not rerun it for symmetry.

## 4. Quality convergence is multi-dimensional

Do not collapse "polished" into visual fidelity.

Repeated rounds should push down a vector of deficits:

```text
product coherence
player readability / uncertainty balance
visual quality
motion quality
sound quality / information hierarchy
interaction quality
behavior/systemic quality
accessibility barriers
runtime correctness
performance / frame pacing
build reproducibility
asset/interchange loss
rights/provenance uncertainty
Human evidence uncertainty
independent QA defects
Workstation/tool friction
cross-E2E coordination friction
```

One dimension may improve while another regresses. Preserve exact-condition evidence.

## 5. External-authority-first evaluation contract

Every Agent must evaluate its owned front against relevant **external source-current authority**, not only Ordivon internal conventions.

Authority hierarchy is contextual, but prefer:

1. normative international/industry standards where applicable;
2. official platform/API/engine/file-format specifications and validation suites;
3. official accessibility/platform quality guidelines;
4. current peer-reviewed domain evidence for scientific/Human claims;
5. mature professional production practice from authoritative tool/vendor documentation;
6. independent empirical product evidence when no formal standard can define the subjective target.

Internal Ordivon rules organize evidence/authority. They do not replace external domain competence.

## 6. Current cross-domain reference spine

This is a starting map, not an exhaustive whitelist.

### Software/product lifecycle and quality

- ISO/IEC/IEEE 12207:2026 — software lifecycle processes.
- ISO/IEC 25010:2023 — ICT/software product quality model.

Use these as cross-cutting lifecycle/quality structure; do not pretend they specify art direction or game fun.

### Human-centred interaction

- ISO 9241-210:2019 — human-centred design for interactive systems.
- current platform/game UX guidance where applicable.
- real participant evidence for claims that are inherently Human.

### Accessibility

- Xbox Accessibility Guidelines (current official Microsoft Game Dev guidance).
- WCAG 2.2 where its technology-independent criteria materially map to text/UI/input/status-message or media surfaces.

Do not claim WCAG compliance for the entire game merely because selected criteria are useful.

### 3D assets / interchange

- Khronos glTF 2.0 specification for selected glTF interchange semantics.
- official Blender/Godot importer/exporter documentation for implementation-specific behavior.
- selected format validators where available.

### Rendering / graphics

- current Khronos Vulkan / SPIR-V specifications and validation rules where the runtime/tool path reaches those APIs.
- official Godot rendering/shader documentation for Godot-specific semantics.
- professional GPU diagnostic guidance where relevant.

### Audio

- ITU-R BS.1770-5 for programme loudness / true-peak measurement when those measurements are relevant.
- official engine/audio-tool documentation for spatialization/import/runtime behavior.
- real listener evidence for spatial cue usefulness; numerical loudness correctness does not prove gameplay usefulness.

### Performance

- ISO/IEC 25010 performance-efficiency concepts as cross-cutting quality framing.
- official Godot performance/profiling guidance.
- current GPU/tool vendor profiling guidance when using those carriers.
- exact frame-time/pacing measurements on the admitted machine/build/render condition.

### Research transfer

A03 selects current peer-reviewed and authoritative sources appropriate to the actual biological/behavioral claim. No single generic Game standard substitutes for domain science.

### Rights / provenance

A24 follows the actual governing license/provider terms and source provenance for each selected contribution; generic internal attribution is not sufficient.

## 7. Per-front standards are discovered, not centrally exhausted

The reference spine above is deliberately incomplete.

Each Agent must ask:

```text
What external profession/discipline would normally own this problem?
What standards, official specifications, validation suites, peer-reviewed evidence, or mature professional practices does that field use?
What does Ordivon currently miss because our ontology/prompt did not name it?
```

Agents are explicitly encouraged to discover relevant standards and practices beyond this document.

Do not collapse exploration to the user's examples or the Coordinator's current ontology.

If a newly discovered external competency repeatedly matters, publish it on Board and determine whether it is:

```text
new evaluation criterion
implementation technique
cross-cutting plane requirement
missing front
candidate first-class E2E
```

through the existing emergence/admission laws.

## 8. Standards do not become cargo-cult checklists

For every material external reference, record:

```text
reference identity / version / source
why it applies to this exact front
normative vs advisory vs empirical status
specific requirement/recommendation used
exact product condition evaluated
PASS / FAIL / PARTIAL / NOT_APPLICABLE / INCONCLUSIVE
deviation rationale if intentionally not followed
evidence receipt
```

Do not claim compliance when only a subset was tested.

## 9. Round-to-round delta review

Every continuing round should compare against the prior accepted candidate:

```text
new defects found
old defects closed
regressions
external-standard gaps closed/opened
Human evidence changes
performance/resource delta
friction count + severity delta
new reusable tooling/process capital
ontology/front changes
```

A repair that improves one local metric but degrades the declared player thesis is not convergence.

## 10. Friction capitalization lane

Product production and friction repair may proceed in parallel.

A friction receipt can spawn an owner-correct capitalization episode when it is reusable beyond one local workaround:

```text
observed friction
→ classify owner (Game / Workstation / Engineering / Network / Research / other)
→ reproduce
→ repair mature carrier/path/process where justified
→ replay original Game consequence
→ record friction delta
```

Do not stop product work merely because all systemic friction is not yet globally repaired, provided a legitimate bounded workaround exists and is recorded.

## 11. Campaign convergence / stop criteria

There is no arbitrary "Round 10 done" criterion.

A stable R1 stopping point is reached only when all of the following hold for the declared scope:

- constitutive product loop closes in a fresh exact build;
- no unresolved P0/P1 product blocker;
- independent QA has no unresolved blocker and major claims survive replay;
- relevant external-standard deltas have no unexplained high-severity gap;
- performance target has an exact-condition standing rather than an aspirational number;
- selected asset/source/interchange path is reproducible;
- accessibility blocking barriers are adjudicated for the declared condition;
- rights/provenance of selected build content is bounded;
- material Human claims either have real evidence or remain explicitly UNKNOWN and are not needed for the claimed R1 standing;
- friction trend is no longer dominated by severe recurring apparatus/process failures;
- additional rounds show diminishing **material** product/evidence returns rather than simply exhausted Agent time.

Even then, closure is local to Veilwild R1. It does not terminate the larger Game E2E or Ordivon learning process.
