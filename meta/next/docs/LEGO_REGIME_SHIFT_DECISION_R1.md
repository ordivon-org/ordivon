# LEGO Regime Shift & Deep-Uncertainty Decision Lens R1

Date: 2026-09-18
Status: ACTIVE EXPERIMENTAL LENS R1
Truth role: analysis-evidence-not-forecast-truth

## Purpose

Detect candidate turning points in dynamic systems without equating current lived experience with current system state, and convert uncertain regime hypotheses into robust, reversible decisions.

This lens is deliberately narrower than a general macroeconomic forecasting framework. It may be used in economics, technology, organizations, products, security, research programs, or other dynamic systems.

## Kernel

State
-> Flow / Derivative
-> Buffer
-> Delay
-> Threshold
-> Feedback
-> Regime Hypothesis
-> Falsifier
-> Robust Action

The key distinction is:

observed output != latent system state
current level != current direction
warning signal != forecast
forecast != decision
decision quality != forecast accuracy

## Activation

Use when one or more are true:
- the user asks whether a system is at a turning point;
- current outputs may lag upstream structural change;
- stocks and flows diverge;
- buffers/backlogs/contracts/inventories may mask deterioration or improvement;
- feedback and adaptation can amplify or damp changes;
- a decision is partly irreversible;
- multiple plausible futures remain and prediction confidence is low.

Do not use for static architecture questions where time, feedback, uncertainty, and path dependence are immaterial.

## Inputs

Consume only source-grounded project/domain evidence:
- time series or repeated observations;
- policy, constraint, financing, demand, capacity, staffing, or other upstream changes;
- known stocks, flows, backlogs, reserves, contracts, inventories, queues, or caches;
- dependency/causal hypotheses;
- actor incentives and possible adaptations;
- intervention options and their reversibility.

## Model

For each material variable V classify:

1. LEVEL — current stock or state.
2. FLOW — inflow/outflow changing the level.
3. FIRST DERIVATIVE — direction/speed of change.
4. SECOND DERIVATIVE — acceleration/deceleration.
5. BUFFER — stored capacity that delays visible effects.
6. DELAY — propagation time across an edge.
7. THRESHOLD — candidate nonlinearity/bifurcation/saturation boundary.
8. FEEDBACK — reinforcing or balancing loop.
9. OBSERVABILITY — whether measured proxies represent latent state.
10. CONTROL/ADAPTATION — how actors can change behavior after observing the system.

## Procedure

### A. Boundary and state
1. Define the system, time horizon, population, and outcome of interest.
2. Separate latent state from observations and social narrative.
3. Mark which observations are leading, coincident, or lagging only as hypotheses until tested.

### B. Stock-flow and derivative audit
4. For each important outcome, record level, inflow, outflow, first derivative, and where useful second derivative.
5. Search for divergence:
   - level high + flow weakening;
   - output stable + backlog shrinking;
   - revenue growing + new orders falling;
   - employment stable + hiring budget falling.
6. Do not infer a turning point from one divergence alone.

### C. Buffer-delay graph
7. Identify buffers such as cash, inventory, backlog, contracts, installed capital, savings, credit lines, organizational slack, regulatory grace periods, or cached state.
8. Map propagation delays between upstream changes and downstream observations.
9. Ask which visible outcomes can remain healthy solely because buffers have not yet been exhausted.

### D. Constraint migration
10. Identify the current bottleneck/constraint.
11. Ask whether the historical bottleneck has already been relaxed and a new constraint now dominates.
12. Distinguish growth slowdown from bottleneck migration.

### E. Regime hypotheses
13. Maintain multiple competing hypotheses, at minimum:
   - H0: ordinary noise / no meaningful structural change;
   - H1: cyclical slowdown or acceleration within the same regime;
   - H2: structural parameter change with delayed propagation;
   - H3: threshold/regime shift;
   - H4: exogenous shock dominates the apparent transition.
14. For each hypothesis list expected observations, contradictions, and discriminating evidence.

### F. Early-warning evidence
15. Where mathematically appropriate, inspect recovery rate, autocorrelation, variance, flickering, or other early-warning signals.
16. Treat these as model-dependent evidence, not universal predictors.
17. Quantify or at least discuss false-positive and false-negative risk.
18. Prefer baselines, controls, cross-series comparison, and mechanistic models over isolated summary-statistic alarms.

### G. Reflexive actors
19. Identify actors who observe the same signals.
20. Ask how policy makers, firms, households, competitors, investors, attackers, or agents may adapt.
21. Test whether broad adoption of the forecast would undermine the forecast itself.

### H. Counterfactual and causal discipline
22. Separate:
   - temporal precedence;
   - mechanism;
   - correlation;
   - policy effect;
   - policy necessity;
   - counterfactual outcome.
23. Ask what would likely have happened absent the proposed cause.
24. Preserve unresolved causal links instead of filling them with narrative coherence.

### I. Decision under deep uncertainty
25. Enumerate plausible futures instead of selecting one forecast too early.
26. Stress-test candidate actions across those futures.
27. Prefer actions with:
   - acceptable downside across many futures;
   - reversibility;
   - option value;
   - low lock-in;
   - information gain;
   - staged commitment.
28. Define signposts that would justify scaling, pausing, reversing, or switching strategy.

## Output Contract

Produce a compact Regime Card:

- system and horizon;
- observed state;
- stock/flow/derivative divergences;
- buffers;
- delays;
- current and migrating constraints;
- competing regime hypotheses;
- warning evidence;
- falsifiers;
- actor adaptations;
- counterfactual gaps;
- plausible futures;
- robust actions;
- signposts;
- confidence and unresolved questions.

## Non-claims

This lens does not establish:
- that every complex system has a tipping point;
- that critical-slowing-down statistics uniquely identify a future transition;
- a precise transition date;
- causal attribution from temporal ordering alone;
- that an action is optimal merely because it is robust;
- that lived experience is unimportant; it is simply often downstream.

## Promotion Law

A finding may update a LEGO plan only if it establishes a durable architecture-relevant fact such as:
- an upstream observation boundary that needs an explicit sensor;
- a buffer or queue whose exhaustion changes system behavior;
- a delay that invalidates a control cadence;
- a bottleneck migration requiring a new module/interface;
- a falsifier or signpost requiring explicit evidence capture;
- an irreversible action requiring staged commitment.

Regime labels themselves remain analysis evidence unless independently validated.

## Stop Condition

Stop when:
- the important competing hypotheses have discriminating evidence/falsifiers;
- major buffers and delays are explicit;
- the action set has been stress-tested across plausible futures;
- the next signposts are measurable;
- further analysis would only add narrative detail without changing a decision or test.

## External Foundations

System dynamics / feedback / delay:
- John D. Sterman, Business Dynamics and system-dynamics modeling.
  https://web.mit.edu/jsterman/www/BusDyn2.html

Critical transitions / early-warning signals:
- Scheffer et al. (2009), Early-warning signals for critical transitions, Nature 461:53-59.
  https://doi.org/10.1038/nature08227
- Boettiger & Hastings (2012), Quantifying limits to detection of early warning for critical transitions.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3427498/

Decision making under deep uncertainty:
- RAND, Robust Decision Making.
  https://www.rand.org/pubs/tools/TL320/tool/robust-decision-making.html

Irreversibility / real options:
- Pindyck (1991), Irreversibility, Uncertainty, and Investment.
  https://www.nber.org/papers/w3307

## Canonical Query Set

1. What changed upstream before downstream experience changed?
2. Which levels remain strong while flows or derivatives weaken?
3. Which buffers are masking the new state, and what exhausts them?
4. What is the propagation delay along each material path?
5. Is this noise, cycle, structural parameter change, threshold transition, or exogenous shock?
6. Which observation would most strongly falsify each hypothesis?
7. Has the dominant constraint migrated?
8. Which actors will adapt, and how does their adaptation alter the model?
9. If this forecast becomes consensus, does it remain true?
10. Which decisions preserve option value if the regime call is wrong?
11. What signpost should trigger the next action?
12. What can we learn cheaply before committing irreversibly?
