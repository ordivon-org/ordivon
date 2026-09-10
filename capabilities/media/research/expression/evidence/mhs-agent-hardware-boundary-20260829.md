# MHS / agent-hardware boundary — external evidence projection

Observed: 2026-08-29. This file is a revision-fenced Media research projection of public external sources for one bounded Writing Production. It is **not** external-source authority. Revalidate the original sources before publication if currentness matters.

## 1. Anthropic — Model Hardware Standard research preview

Source: https://www.anthropic.com/news/model-hardware-standard-research-preview
Published: 2026-08-27.

Bounded observations:
- Anthropic describes MHS as a research-preview shared specification for AI agents operating programmable physical devices in scientific research and advanced manufacturing.
- The MHS driver exposes standardized read/write primitives, device discoverability, machine characteristics and declared safety limits, and can be reached through MCP, CLI, or code.
- Partner examples show agents sequencing multiple devices, reading state, adjusting parameters, and in some cases compiling learned procedures into deterministic scripts.
- Anthropic explicitly says current model spatial/physical reasoning remains limited and requires expert oversight.
- In the Genentech BCA-assay example, the agent initially responded to bubble/foam-driven liquid-handling failures as if they were software/runtime problems; experts had to supply the relevant physical interpretation/correction.
- Anthropic also summarizes QuEra laser-control work, but load-bearing outcome claims below are bound to QuEra's own report as the measured-system owner.

## 2. Universal Robots — MHS cobot proof of concept

Source: https://www.universal-robots.com/blog/testing-agentic-physical-ai-univeral-robots-cobots/
Published: 2026-08-28.

Bounded observations:
- Universal Robots reports a proof of concept in which an MHS-compatible agent discovered and coordinated four cobots.
- Devices declare bounds, interlocks and emergency stops through MHS, but Universal Robots explicitly keeps its underlying mature robot safety architecture in charge beneath the agent/orchestration layer.
- The company frames integration as a major automation bottleneck and MHS as an orchestration layer above the device-control platform, not as a replacement for industrial safety architecture.

## 3. QuEra — owner-primary physical validation case

Source: https://www.quera.com/blog-posts/holding-the-light-teaching-an-ai-to-lock-and-tune-our-quantum-computers-lasers
Published: 2026-08-27.

Bounded observations:
- QuEra describes an MHS-connected AI agent operating a dedicated laser testbed inside Human-set/device-enforced safety bounds, with deterministic controller code retained for runtime relocking after agent development.
- In controlled validation, the relock controller recovered on target in 695/700 injected-fault trials across seven disturbance classes and declined to claim success on the five misses.
- For autonomous tuning, the workflow optimized a broad in-loop noise objective, then QuEra performed an **independent, out-of-loop measurement** on an instrument the optimization could not touch, comparing the agent configuration with an experienced specialist's manual tune.
- QuEra also reports a roughly 19-hour unattended soak with zero lock drops after tuning, compared with 1.6 per hour before the tuning campaign.
- This is a positive example of command/optimization success being followed by stronger independent physical measurement and practical-duration validation. It is not a universal recipe for laboratory validation.

## 4. NIST — metrological traceability

Source: https://www.nist.gov/metrology/metrological-traceability
Current policy/FAQ observed: 2026-08-29.

Bounded observations:
- NIST defines metrological traceability as a property of a **measurement result** related to a reference through a documented calibration chain; it is not a property of an instrument, calibration report, or laboratory by itself.
- A calibrated instrument alone does not make every result obtained with it traceable.
- Traceability alone does not guarantee fitness for purpose: measurement uncertainty and the needs of the intended application still matter.
- This does **not** imply that every measurement in every engineering task must establish metrological traceability. The transferable point is that result adequacy is claim/use-relative and cannot be inferred from instrument identity alone.

## 5. NASA Systems Engineering Handbook — verification vs validation

Sources:
- https://www.nasa.gov/reference/5-3-product-verification/
- https://www.nasa.gov/reference/5-4-product-validation/
Observed: 2026-08-29.

Bounded observations:
- NASA distinguishes verification (evidence that a realized product conforms to specified requirements) from validation (evidence that the right product works for its intended use/environment).
- The distinction is useful here only as a mature engineering analogue; it does not imply MHS is a NASA-style system or that laboratory measurement validity reduces to product V&V.

## 6. Closest protocol prior — LAP

Source: https://arxiv.org/abs/2606.03755
Title: *LAP: An Agent-to-Instrument Protocol for Autonomous Science*
Published: 2026-06-02.

Bounded observations:
- Zhu et al. explicitly model the agent-to-instrument edge as stateful, safety-critical, physically embodied and distinct from ordinary agent-to-tool/agent-to-agent protocols.
- LAP includes signed instrument capabilities/physical limits, reservation/locking, a safety-fence handshake for hazardous/irreversible operations, and a `MeasurementResult` concept carrying units, calibration, uncertainty and provenance.
- LAP therefore predates the MHS preview and already carries several physical-instrument and measurement distinctions relevant to this article.
- The candidate Writing must not claim novelty for `interface != physical safety` or `instrument operation != measurement adequacy`. Its possible contribution is narrower: a current MHS-specific engineering composition using MHS's own concrete cases plus mature metrology/V&V to help readers identify which stronger claim remains unsupported after an agent successfully operates hardware.

## 7. Carrier-rival check

Current 2026-08-29 review found:
- MHS announcements/explainers already cover integration, discoverability, declared safety bounds and Human oversight;
- practical MHS safety guidance already separates driver/interface, harness/orchestration and hardware safety mechanisms;
- LAP already models the agent-to-instrument edge as physical/safety-critical and carries measurement metadata explicitly;
- NIST/NASA already own mature traceability/fitness and verification/validation distinctions.

Therefore the Writing is **not** justified as discovery of a new ontology or a generic MHS safety guide. Difference-bearing space survives only if the article makes a compact, current engineering judgment from heterogeneous evidence: after safe/valid device operation, what further evidence supports the physical interpretation, the measurement's adequacy for the declared use, and the downstream experimental/operational decision?

This carrier-rival result is provisional and current to 2026-08-29; it does not establish global novelty.

## Admissible synthesis for the candidate Writing

Supported non-collapse:

`standardized device operability`
`!= underlying physical safety authority`
`!= correct physical-state diagnosis`
`!= measurement adequacy for the declared use`
`!= evidence sufficiency for the downstream experimental/operational decision`

These are **distinct questions/contracts**, not a mandatory five-stage pipeline and not five required services. Native safety is especially orthogonal: safe actuation can coexist with bad diagnosis, and good measurement can exist under different safety architectures.

This is a scoped engineering synthesis derived by comparing the sources above. It must not be phrased as a defect MHS is obligated to solve. The standard can be valuable precisely while these downstream/underlying responsibilities remain elsewhere.
