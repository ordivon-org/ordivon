# Method map

This reference distinguishes existing canonical Ordivon method Skills. It is a routing aid, not a new ontology or authority.

| Dominant question | Primary Skill | Use when | Nearby method not to confuse |
| --- | --- | --- | --- |
| What is the system and where are its boundaries/interfaces? | systems-engineering | scope, context, lifecycle and whole-system properties are unclear | DSM starts after there are meaningful elements/interactions |
| Is the decomposition structurally plausible? | design-structure-matrix | dependencies, cycles, hubs or clusters may reveal misplaced boundaries | compositional-contracts asks whether explicit interfaces compose |
| Will independently specified parts compose or substitute safely? | compositional-contracts | assumptions, guarantees and replacement obligations matter | DSM is descriptive structure; contracts are compatibility obligations |
| Does X causally change Y? | causal-intervention | intervention, ablation, mechanism or causal attribution is the question | prediction/correlation alone is insufficient |
| How can component/process failures propagate? | fmea-fta | explicit failure modes or top failure events dominate | STPA covers unsafe interactions without component failure |
| How can system interactions create unacceptable loss? | stpa | safety/security hazards arise from control actions, humans, automation or authority | FMEA/FTA is failure-centric |
| Is a feedback loop stable/observable/controllable? | feedback-control | dynamic response and closed-loop behavior matter | STPA focuses loss/control-action safety, not ordinary control design |
| Does an organization remain viable under complexity? | organizational-cybernetics | coordination, recursion, autonomy and control channels dominate | systems-engineering is broader system framing |
| Where may information/authority/evidence flow improperly? | information-flow-analysis | confidentiality, integrity, provenance or authority paths matter | STPA is broader hazard analysis |
| How should candidate designs be searched? | evolutionary-search | candidate generation + evaluation/fitness are explicit | exploration-policy chooses what information/action to sample next |
| What should be explored next under uncertainty? | exploration-policy | information value, uncertainty reduction, exploration/exploitation dominate | evolutionary-search assumes a candidate/fitness search space |
| How should a project be decomposed into native responsibility units? | project-kernel-decomposition | project-specific ownership/contracts/evidence decomposition is needed | systems-engineering frames the system before project-specific decomposition |

## Useful combinations

Use combinations only when each method has a distinct job.

### Systems engineering -> DSM
Use when the system boundary is unclear first, then the internal decomposition/coupling needs testing.

### DSM -> compositional contracts
Use DSM to locate suspicious seams; use contracts to test the obligations at those seams.

### Causal intervention + experimental evaluation
Use when an architecture or process change is claimed to cause an outcome. The causal method defines what must be manipulated/controlled; domain evaluation determines whether the result matters.

### FMEA/FTA + STPA
Use both for high-consequence systems when explicit component failures and unsafe interactions are independently material. Do not merge them into one checklist.

### STPA + information-flow analysis
Use when security loss can arise from authority or data-flow violations inside a larger control structure.

### Exploration policy -> causal intervention
Use exploration policy to choose the next informative intervention only after the causal question and valid intervention space are defined.

## Lifecycle handoff outside method selection

Creating or adopting a new forward Ordivon Research Study is not itself a reasoning-method question. Route that action to `research-study-birth`, which delegates to the current Research-v2 Study Birth owner. Do not encode Research data-plane providers or project layout in this method map.

## No-route cases

Do not activate a method Skill merely for:

- straightforward factual lookup;
- ordinary code formatting/refactoring with clear acceptance;
- a single deterministic calculation;
- direct execution of an already specified procedure;
- a task where the relevant domain standard already dictates the method.

In these cases, perform the task directly.
