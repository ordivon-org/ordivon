# Composition Science R1

Date: 2026-09-21
Status: RESEARCH PROGRAM / FORMALIZED R1 / NOT A CLAIM OF NOVEL SCIENTIFIC OWNERSHIP

## 1. Purpose

This document formalizes an Ordivon research program for reasoning about innovation as search over primitive spaces, composition spaces, dynamic/control spaces, and verification spaces.

The working hypothesis is not that invention is merely recombination and not that new primitives are unimportant. The narrower claim is:

> In many mature technical and organizational domains, useful primitives already exist in abundance. The binding difficulty may shift from creating primitives to discovering them, exposing their actual properties and authorities, composing them correctly, controlling the resulting dynamics, and falsifying bad compositions quickly.

Ordivon therefore treats self-building as one possible search action, not the default creative act.

This document sits above existing LEGO Theory. It does not replace Systems Engineering, DSM, assume-guarantee reasoning, C-K design, evolutionary search, feedback/control, STPA, FMEA/FTA, information-flow analysis, or domain-specific methods.

## 2. External intellectual boundary

The research program deliberately builds on mature external lineages rather than renaming them as Ordivon inventions.

Relevant foundations include:

- recombinant innovation / recombinant growth: useful new ideas can arise from new configurations of existing ideas, while the number of possible combinations can grow much faster than the ability to evaluate them;
- technological search: unfamiliar components and unfamiliar combinations can increase uncertainty and outcome variance;
- C-K design theory: concept-space expansion and knowledge-space expansion must be distinguished when the desired object is not yet known;
- systems engineering and systems thinking: components, interfaces, environment and lifecycle are jointly relevant;
- assume-guarantee / contract-based compositional verification: component assumptions and guarantees constrain valid composition;
- control and state-space thinking: a static component graph is insufficient for dynamic systems;
- search / sequential decision theory / evolutionary computation: candidate generation and selection require explicit search assumptions and evaluators.

Ordivon's possible contribution is the operational synthesis:

1. represent externally owned primitives with enough metadata to compose them;
2. preserve natural authority instead of copying semantic ownership into Ordivon;
3. search composition and dynamic spaces before introducing new primitives;
4. make build-vs-adopt a falsifiable residual-gap decision;
5. retain evidence-backed composition knowledge rather than merely retaining code ancestry.

## 3. Core objects

### 3.1 Problem context

A problem context is

\[
X = (G, C, A, E, B)
\]

where:

- G is desired goals / acceptance conditions;
- C is constraints, including cost, time, platform, legal and operational constraints;
- A is the authority map: who or what is allowed to establish each relevant fact or effect;
- E is the environment, including available infrastructure, external systems and disturbances;
- B is the current evidence / knowledge baseline.

A candidate solution is always interpreted relative to X. There is no context-free best composition.

### 3.2 Primitive

A primitive is not merely a code module. A primitive is an externally or locally realizable unit that can participate in a composition.

Represent a primitive p as:

\[
p = (id, I, O, H, Q, \Omega, \alpha, \rho, \kappa)
\]

where:

- id is stable identity;
- I is required inputs / preconditions;
- O is outputs / observable effects;
- H is assumptions about environment or collaborators;
- Q is guarantees / declared properties;
- Omega is side effects and state transitions;
- alpha is natural authority / semantic owner;
- rho is provenance, version, maturity and evidence;
- kappa is cost and resource requirements.

Examples include an algorithm, standard, API, local executable, MCP server, database, human review step, organizational role, experimental method, physical component, scientific result, contract, or policy rule.

A catalog record is only a projection of a primitive. The primitive's natural provider remains authoritative where appropriate.

### 3.3 Compatibility

For primitives p_i and p_j, define a contextual compatibility predicate:

\[
K(p_i,p_j \mid X) \in \{compatible, incompatible, unknown\}
\]

Compatibility may depend on:

- interface / data type;
- protocol and version;
- temporal ordering;
- assumption-guarantee discharge;
- authority;
- security / information flow;
- performance;
- legal / licensing constraints;
- operational lifecycle;
- state ownership.

UNKNOWN is first-class. Lack of observed conflict is not proof of compatibility.

### 3.4 Composition

A composition is a typed attributed directed hypergraph:

\[
C = (V, R, \lambda, \beta)
\]

where:

- V is the selected primitive instances;
- R is the relations / wiring among primitives;
- lambda gives relation semantics such as data, control, authority, dependency, causal hypothesis, synchronization, or containment;
- beta maps the composition boundary to the external environment and real entity of interest.

The same primitive set can produce radically different systems through different relations. Therefore identical components do not imply identical composition.

### 3.5 Dynamics and control

A composition becomes an operating system only when dynamic behavior is specified.

Represent dynamics as:

\[
D = (S, U, W, T, Y, \pi)
\]

where:

- S is state space;
- U is admissible controls/actions;
- W is disturbances / exogenous inputs;
- T maps state, action and disturbance to next state;
- Y is the observation function;
- pi is control / scheduling / decision policy.

A static graph C does not establish behavior. Two systems with identical composition can behave differently under different policies, timeouts, retries, feedback loops, resource allocation or scheduling.

### 3.6 Verification structure

Represent verification as:

\[
V_f = (\Gamma, M, Z)
\]

where:

- Gamma is claims / acceptance criteria;
- M is validators / measurement procedures;
- Z is produced evidence and provenance.

Execution evidence and semantic evidence remain distinct:

\[
process\ success
\neq
requirement\ satisfaction
\neq
real-world\ outcome
\]

### 3.7 Candidate system and search space

A candidate system is:

\[
Y = (C, D, V_f)
\]

The complete design/search space is decomposed as:

\[
\mathcal{S}
=
\mathcal{P}
\times
\mathcal{R}
\times
\mathcal{D}
\times
\mathcal{V}
\]

where:

- P is primitive-selection / primitive-creation space;
- R is relation / composition space;
- D is dynamic / control-policy space;
- V is validation / evidence space.

This decomposition is central: invention can occur in any of these spaces.

## 4. Valid composition

A composition is not valid merely because its components can be invoked.

For candidate Y and context X:

\[
Valid(Y\mid X)
=
I_f
\land
A_d
\land
Auth
\land
Dyn
\land
Ev
\]

where:

### 4.1 Interface feasibility

Every required relation has compatible interfaces or an explicit justified adapter.

### 4.2 Assumption discharge

For each component contract

\[
H_i \Rightarrow Q_i
\]

the composition/environment must establish H_i, and the composed guarantees must be sufficient for the relevant system claims.

### 4.3 Authority preservation

Information flow, execution ability and semantic authority must not be conflated.

A valid composition must not silently turn:

- a cache into a source of truth;
- an index into an applicability authority;
- a storage ACK into domain truth;
- an agent observation into a scientific verdict;
- an installed package into an effect authorization.

### 4.4 Dynamic admissibility

The candidate must remain acceptable under relevant state transitions, disturbances, retries, concurrency, failure and recovery, not only on a happy path.

### 4.5 Evidence adequacy

Validators and evidence must be adequate for the actual acceptance claims. A composition that cannot be falsified against its important claims is not yet verified.

## 5. Substitution and external-first search

### 5.1 Contextual substitutability

A candidate primitive p_b may replace p_a in context X when the required observable contract is preserved.

Write:

\[
p_b \preceq_X p_a
\]

when:

- required assumptions are no stronger in a way X cannot satisfy;
- guarantees are sufficient;
- authority boundaries remain valid;
- side effects remain admissible;
- cost/risk constraints remain admissible.

This is contextual substitutability, not universal equivalence.

### 5.2 Dominance

Candidate a dominates candidate b in context X if:

- a satisfies every hard requirement that b satisfies;
- a violates no additional hard constraint;
- a is no worse on all currently decision-relevant dimensions;
- a is strictly better on at least one such dimension.

Dominated candidates can be pruned without inventing a universal scalar score.

### 5.3 Residual build set

Let R_X be the weighted requirement set. For composition C:

\[
Residual(C,X)
=
\{r \in R_X \mid r \text{ remains materially unsatisfied}\}
\]

Self-build is admitted only when:

1. a materially important residual remains;
2. discovery has reached an explicit bounded cut;
3. no mature external candidate or thin adapter satisfies the residual sufficiently;
4. the local implementation can be bounded to the residual rather than swallowing neighboring authority.

This is the formal version of Build Last.

## 6. Reachability

The most important unit of innovation research is often not an individual primitive but a newly reachable capability.

Let:

\[
Reach(P,R,D,E)
\]

be the set of capabilities or states reachable by composing primitive set P using allowed relations R and dynamic/control family D under environment E.

For baseline B_0 and candidate B_1:

\[
\Delta Reach = Reach(B_1) \setminus Reach(B_0)
\]

A composition can be consequential even when primitive novelty is near zero, provided the new composition or control creates substantial reachable capability.

Reachability must remain scoped. A capability may become technically reachable while remaining unauthorized, uneconomic, unsafe or unverifiable.

## 7. Innovation as a vector, not a scalar

Define novelty relative to a dated baseline B_t as:

\[
N(Y \mid B_t)
=
(n_P,n_R,n_D,n_V)
\]

where:

- n_P is primitive novelty: new elements or materially new primitive properties;
- n_R is compositional novelty: new relations, interfaces or architectural arrangement;
- n_D is dynamic/control novelty: new policies, feedback, scheduling, adaptation or state-transition behavior;
- n_V is verification novelty: new ability to measure, falsify or establish claims.

These dimensions are deliberately not collapsed into one universal number.

Possible profiles include:

- low n_P, high n_R: mostly existing elements, new composition;
- low n_P and n_R, high n_D: familiar architecture, novel control;
- low n_P, n_R and n_D, high n_V: same system, but previously untestable claims become falsifiable;
- high values on several dimensions.

### 7.1 Novelty is not value

Let context-dependent value be J(Y|X). Cost, risk, evidence quality, authority and replaceability remain separate dimensions.

There is no rule that more novelty implies more value.

New combinations can increase uncertainty and variance. Therefore Ordivon must never rank candidates merely by novelty.

## 8. Why composition search becomes difficult

If n reusable primitives are available, subset choice alone yields up to 2^n possible sets before wiring, versions, parameters and dynamics are considered.

Practical search grows further through:

- relation topology;
- interface adaptations;
- component versions;
- parameters;
- environment;
- scheduling/control;
- validation method.

This motivates a shift in bottleneck:

\[
primitive\ scarcity
\rightarrow
discovery / processing / evaluation\ scarcity
\]

This is consistent with recombinant-growth and recombinant-search literature: as possible combinations proliferate, identifying and evaluating useful combinations becomes a central constraint.

The response is progressive pruning, not exhaustive enumeration.

## 9. Canonical composition-search loop

The Ordivon research loop is:

    DISCOVER
      -> EXPOSE
      -> NORMALIZE
      -> SUBSTITUTE
      -> COMPOSE
      -> RUN
      -> FALSIFY
      -> SELECT
      -> ABSTRACT

### DISCOVER

Search mature standards, products, libraries, algorithms, datasets, methods, prior evidence and local capabilities before proposing new implementation.

Output: bounded primitive candidate set plus explicit discovery cut.

### EXPOSE

Expose only decision-relevant properties:

- contract;
- assumptions;
- guarantees;
- side effects;
- natural owner;
- maturity/provenance;
- version;
- cost;
- operational boundary.

### NORMALIZE

Map heterogeneous primitives into a minimal comparison view without erasing native domain semantics.

Normalization is a view, not a new universal ontology.

### SUBSTITUTE

Identify equivalent, refining, dominated and complementary alternatives.

Ask whether a mature owner can replace an Ordivon-owned residual.

### COMPOSE

Create candidate graphs under explicit compatibility and authority constraints.

A composition hypothesis should state why the parts are expected jointly to establish the desired system property.

### RUN

Instantiate the candidate under real or representative dynamics.

A static architecture review is insufficient when interactions, retries, timing or control matter.

### FALSIFY

Attack the weakest assumptions:

- boundary failures;
- adversarial conditions;
- multi-user or multi-agent races;
- failure/recovery;
- performance limits;
- domain counterexamples;
- independent validators.

### SELECT

Retain non-dominated candidates justified by evidence and current context.

Allow no adequate candidate as a valid result.

### ABSTRACT

Only after repeated evidence, extract reusable composition knowledge:

\[
problem\ conditions
\rightarrow
composition
\rightarrow
expected\ evidence
\]

Do not convert a one-off successful arrangement into a permanent Ordivon subsystem.

## 10. Search policy by problem type

Different mature search methods apply to different problem states.

### Unknown desired object

Use C-K design or other generative design methods when the target concept itself must expand.

### Known alternatives, repeated comparable feedback

Use sequential decision / bandit methods when repeated choices produce comparable feedback.

### Candidate representation plus credible evaluator

Use evolutionary or population search when variation is meaningful and the evaluator is trustworthy enough.

### Known system, uncertain composition validity

Use contract-based reasoning, DSM, interface analysis and falsification.

### Dynamic/control uncertainty

Use state-space, feedback/control, simulation, reliability and safety methods as appropriate.

No single Ordivon composition optimizer should be invented to replace these mature disciplines.

## 11. Evidence and standing

Each composition hypothesis has a standing:

    PROPOSED
    -> ADMISSIBLE
    -> TESTED
    -> PROSPECTIVELY_VALIDATED

or:

    -> FALSIFIED
    -> INCONCLUSIVE

Every result must record its scope. Evidence outside the tested context does not automatically transport.

### Counterexample priority

A counterexample that violates a hard assumption or guarantee has more decision value than additional happy-path examples.

The process should prefer high-information falsification over repetitive confirmation.

### Composition memory

The durable learned object is not merely tool X worked.

Prefer records shaped like:

    problem/context
    + assumptions
    + primitive identities/versions
    + composition relations
    + dynamic policy
    + validator
    + result/counterexample
    + applicability boundary

This supports future reuse and substitution.

## 12. Metrics: dashboard, not universal score

None of the following is universal authority.

### Discovery coverage

Weighted fraction of material requirements for which at least one plausible external primitive was examined.

Purpose: detect premature building.

### Residual build ratio

Weighted fraction of material requirements that still require local implementation after bounded discovery/substitution.

Purpose: quantify what is genuinely left to own.

### External ownership coverage

Fraction of generic capability responsibility delegated to natural mature owners.

Purpose: detect ownership inflation.

### Authority violations

Count/severity of relations where a component is asked to assert or effect something outside its natural authority.

Hard authority violations should normally be gating rather than averaged away.

### Unresolved assumptions

Number/severity of component assumptions not yet discharged by composition/environment evidence.

### Replaceability surface

Record how much of a composition can be replaced under stable contracts without changing neighboring semantics.

Do not reduce this to a single number unless a task specifically requires one.

### Reachability gain

Newly reachable capability/state set relative to baseline, scoped by authority and validation.

### Evidence closure

Fraction of material claims linked to an adequate validator and observed evidence.

### Time to first falsification

Elapsed effort before an important candidate assumption is disproved.

For exploration, lower can be better because it reduces sunk-cost accumulation.

### Composition reuse

How often an evidence-backed composition pattern transfers successfully after explicit applicability checks.

## 13. Falsifiable research hypotheses

These define a research program, not accepted laws.

### H1 — Mature-ecosystem composition hypothesis

In mature technical ecosystems, a substantial fraction of useful capability gains can be achieved by changing composition/control while introducing few or no new primitives.

Falsifier: representative tasks usually retain material residual requirements after mature primitive discovery and composition search, requiring new primitive creation.

### H2 — Discovery-before-build hypothesis

Increasing structured discovery coverage reduces unnecessary custom implementation without degrading validated outcomes.

Falsifier: higher discovery effort consistently increases cost/latency without reducing local build or improving outcomes.

### H3 — Authority-decomposition hypothesis

Explicit natural-owner boundaries improve replaceability and reduce semantic coupling.

Falsifier: matched systems with explicit authority decomposition show no reduction in replacement cost, ambiguity or cross-component failure.

### H4 — Dynamic-novelty hypothesis

Important innovations are sometimes primarily changes in control/dynamics rather than components or topology.

Falsifier: dynamic/control changes contribute negligible reachable capability or outcome improvement unless accompanied by new primitives/topology.

### H5 — Verification-enablement hypothesis

New validators can create effective innovation by making previously unusable composition space safely searchable.

Falsifier: improved validation does not materially change candidate selection, reachable deployment space or error discovery.

### H6 — Processing-bottleneck hypothesis

As primitive availability rises, search/evaluation capacity becomes a larger bottleneck than implementation capacity.

Falsifier: in high-primitive-availability settings, implementation remains consistently dominant while discovery/evaluation remains negligible.

### H7 — Composition-memory hypothesis

Retaining problem-to-composition-to-evidence relationships transfers better than provider-specific implementation recipes alone.

Falsifier: provider-specific recipes outperform composition/evidence records on adaptation time, success rate and substitution after environment changes.

### H8 — Agent-era shift hypothesis

As code generation reduces implementation cost, relative value shifts toward discovery, specification, composition, evaluation and falsification.

Falsifier: longitudinal tasks show implementation remains the dominant scarce resource despite substantial reductions in code generation cost.

## 14. Case mapping

### Windows active-user execution

Most important primitives already existed:

- Windows WTS session APIs;
- user-token APIs;
- CreateProcessAsUser;
- existing Ordivon privileged broker;
- existing JobLauncher;
- Runtime Job/Attempt/evidence.

The gain came mainly from relation placement and verification: selecting user-session identity at the existing token seam, then freezing and checking SID/session before spawn.

This is evidence for the program, not proof of H1.

### Stable Gateway plus Dynamic Capability Registry

Existing pieces include MCP, OAuth/Cloudflare, Runtime, Host, Plugin/Skill and capability providers.

The architectural problem is lifecycle composition:

\[
stable\ client\ ABI
+
dynamic\ internal\ capability\ set
\]

rather than inventing another execution system.

### Agent Plugin

Skill, MCP and local tools are distinct primitive classes with distinct natural owners.

The Plugin's irreducible role is composition:

\[
Plugin
=
Skill\ references
+
MCP\ references
+
Tool\ requirements
+
Capability\ composition
\]

Physical execution truth still belongs to Runtime/providers.

### Artifact capability

PowerPoint, FFmpeg, ImageMagick, Blender, Typst, browsers, validators and artifact Skills can be treated as primitives.

Innovation opportunities may therefore lie in correct binding, editable-source preservation, multi-tool validation, and evidence-backed quality loops rather than rebuilding document/media engines.

## 15. Anti-patterns

### Primitive novelty fetish

Assuming a result is innovative only when it contains a newly invented component.

### Recombination romanticism

Assuming any unusual combination is valuable. Most combinations may be irrelevant, incompatible or harmful.

### Catalog-as-reality

Treating a registry entry as proof that a provider currently exists or can execute.

### Composition without contracts

Connecting components because inputs/outputs superficially match while assumptions, authority or lifecycle disagree.

### Static-graph fallacy

Assuming topology determines runtime behavior without state, timing, policy and feedback.

### Fitness-as-truth

Treating search objective scores as semantic or production authority.

### Compatibility preservation by ancestry

Keeping old adapters merely because they existed.

### Private ontology inflation

Creating Ordivon vocabulary where mature domain vocabulary already supplies the needed semantics.

### Premature subsystem promotion

Turning a successful composition into a permanent owned subsystem before repeated evidence shows a stable residual.

## 16. Research protocol

For a new innovation study:

1. Define the real entity/outcome and acceptance claims.
2. Freeze discovery time/window and source scope.
3. Enumerate candidate primitives and natural authorities.
4. Expose contracts, assumptions, guarantees, side effects and costs.
5. Construct substitution / dominance relationships.
6. Identify residual requirements.
7. Generate multiple candidate compositions where uncertainty matters.
8. Define dynamics/control explicitly.
9. Define validators before expensive execution where possible.
10. Run the cheapest high-information falsifications first.
11. Record counterexamples and surviving applicability conditions.
12. Compare against a baseline, including a self-build baseline when relevant.
13. Measure residual build, evidence closure, reachability gain and replacement behavior.
14. Promote only repeated, evidence-backed composition relationships.
15. Re-open primitive search when environment, standards, tools or goals materially change.

## 17. Relationship to LEGO Theory

LEGO Theory asks how to decompose and reason about systems without erasing relationships, authority or dynamics.

Composition Science R1 adds a search framing:

    LEGO decomposition
      -> Primitive Space
      -> Composition Space
      -> Dynamic / Control Space
      -> Verification Space
      -> Reachability
      -> Falsification
      -> Reusable composition knowledge

Existing LEGO lenses remain external-method routers:

- Systems Engineering -> system framing;
- DSM -> dependency/decomposition diagnostics;
- assume-guarantee -> compositional contracts;
- control/state-space -> dynamics;
- STPA/FMEA/FTA -> hazard/failure reasoning;
- C-K -> open-ended concept generation;
- bandits -> repeated allocation/search;
- evolutionary computation -> population search under evaluator assumptions.

Composition Science is not another mandatory schema layered over every project.

## 18. Candidate durable principles

1. Search before build.
2. Composition before ownership.
3. Relations are first-class.
4. Dynamics are first-class.
5. Verification can expand usable design space.
6. Authority is not information flow.
7. Novelty is multidimensional and is not value.
8. Retain evidence-backed compositions, not provider ancestry.
9. Build only the residual.
10. Prefer falsifiable composition hypotheses over architecture narratives.

## 19. Open research questions

1. How should primitive identity and equivalence be represented across software, science, organizations and physical systems without inventing a universal ontology?
2. What minimum metadata is sufficient to prune composition search effectively?
3. Can capability reachability be approximated tractably for large heterogeneous primitive sets?
4. Which search heuristics generalize across domains, and which must remain domain-specific?
5. How should uncertainty in component guarantees propagate through a composition?
6. How should authority constraints be represented alongside technical compatibility?
7. How much discovery effort is optimal before self-build becomes economically rational?
8. Does agentic code generation measurably move bottlenecks from implementation to evaluation/verification?
9. Which composition-memory structures transfer best across provider/version changes?
10. When does a recurrent composition justify promotion into a stable product/plugin/subsystem?

## 20. Source map

External sources are intellectual substrates, not Ordivon authority replacements.

- Martin L. Weitzman, Recombinant Growth, Quarterly Journal of Economics 113(2), 1998. Harvard DASH: https://dash.harvard.edu/entities/publication/73120378-853d-6bd4-e053-0100007fdf3b
- Ajay Agrawal, John McHale, Alex Oettl, Finding Needles in Haystacks: Artificial Intelligence and Recombinant Growth, NBER Working Paper 24541, 2018: https://www.nber.org/papers/w24541
- Lee Fleming, Recombinant Uncertainty in Technological Search, Management Science 47(1), 2001, DOI 10.1287/mnsc.47.1.117.10671
- NASA assume-guarantee / compositional verification: https://ntrs.nasa.gov/citations/20030017771
- NASA CoCoSim compositional verification tutorial: https://ntrs.nasa.gov/citations/20220009652
- Pascal Le Masson, Armand Hatchuel, Benoit Weil, C-K Design Theory overview, MINES Paris: https://www.tmci.minesparis.psl.eu/wp-content/uploads/2021/01/1.2.pdf
- Existing Ordivon source map: knowledge/lessons/lego-theory-foundations-r1.md
- Existing LEGO theory: docs/LEGO_THEORY_WAVE2_R1.md and docs/LEGO_THEORY_WAVE3_R1.md

## 21. Current standing

R1 is a formalized research program.

It is not established that composition innovation dominates primitive innovation generally, or that the proposed metrics predict innovation value.

Promotion requires prospective evidence across multiple domains and must permit falsification of the central hypotheses above.

## External-theory census update — 2026-09-21

Subsequent external-theory census found mature owners for most constructs independently assembled in this R1. This document is therefore retained as an **independent-convergence snapshot**, not as a new general-purpose Ordivon theory.

Current authority for method selection is `docs/EXTERNAL_INNOVATION_THEORY_CENSUS_R1.md`. Mature external lens names and applicability boundaries take precedence over R1 private terminology. No general theoretical gap has been established. Remaining work is limited to the narrower residuals: theory routing, evidence-backed composition memory, empirical agent-era search economics, and machine-actionable authority-aware composition.
