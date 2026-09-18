# Poker AI — LEGO Question Compiler Pilot R1

Date: 2026-09-18
Status: PROSPECTIVE METHOD PILOT
Target: popular narrative about Libratus / Pluribus and "mathematics defeating human read"
Method: LEGO Question Compiler R1

## 1. Target

Explain what actually generated the superhuman behavior of Libratus and Pluribus, and determine which general lessons can be transferred to Ordivon without turning a poker-specific result into a universal claim.

## 2. Decision

Decide which concepts, if any, deserve continued Ordivon LEGO investigation as reusable analysis lenses or design hypotheses.

## 3. Evidence boundary

Primary factual anchors:

- Brown & Sandholm, "Superhuman AI for heads-up no-limit poker: Libratus beats top professionals", Science, DOI 10.1126/science.aao1733.
- Brown & Sandholm, "Superhuman AI for multiplayer poker", Science, DOI 10.1126/science.aay2400.
- Brown & Sandholm, "Safe and Nested Subgame Solving for Imperfect-Information Games", NeurIPS 2017.
- Carnegie Mellon University technical/news summaries of Libratus and Pluribus.

The narrative supplied in conversation is treated as an object to analyze, not as independent authority.

## 4. Epistemic split

### OBSERVED / SOURCE-BACKED

- Libratus defeated four top heads-up no-limit Texas hold'em professionals over a 120,000-hand competition.
- Libratus combined an overall blueprint, finer subgame solving during play, and a self-improver that repaired potential weaknesses.
- Safe/nested subgame solving exists because imperfect-information subgames cannot generally be solved as isolated perfect-information subtrees.
- Pluribus achieved superhuman performance in six-player no-limit Texas hold'em using self-play plus limited-lookahead search.
- The Pluribus work explicitly treats multiplayer games as fundamentally different from the two-player setting.

### INFERRED

- Mixed strategies can be usefully interpreted as reducing stable action-to-hidden-state inference available to an opponent.
- Some "psychological" poker concepts can be represented behaviorally as conditional action distributions without modeling subjective mental states.
- Robustness against exploitation is a useful systems analogy beyond poker when there is a real adaptive adversary or environment.

### ASSUMED / NEEDS TESTING BEFORE TRANSFER

- "Exploitability" can be generalized cleanly to arbitrary Agent architectures.
- Information leakage through policy behavior is an important bottleneck in ordinary non-security Ordivon workflows.
- Emergent behavior is preferable to explicit orchestration for Agent organizations.
- Human best practices in other domains are often merely local historical equilibria.

## 5. Candidate questions

The initial brainstorm produced many questions. R1 prunes them to six.

### PQ1 — OBSERVABILITY / STATE

**Question:** What state is actually required for a strong decision in an imperfect-information system, and which parts of that state are hidden, historical, or only representable as a belief distribution?

Why it matters:
A system that mistakes visible projection for decision-sufficient state will plan from the wrong model.

Answer route:
Compare the poker information-set requirement with an Ordivon domain where history/current projection divergence is already evidenced.

Discriminating outcomes:
- If current projections are sufficient in the target domain, no new state abstraction is needed.
- If omitted history changes valid decisions, the architecture needs an explicit observation/belief/history boundary.

### PQ2 — ACTION / SEARCH

**Question:** Which allegedly "bad" or impossible actions are truly dominated or forbidden, and which are merely absent because human conventions or current tooling never explored them?

Why it matters:
This distinguishes invariant constraints from historical search-path dependence.

Answer route:
Take one Ordivon subsystem with a narrow design convention and run a bounded alternative-design search or ablation.

Discriminating outcomes:
- Alternative is structurally invalid -> convention is closer to invariant.
- Alternative is valid but worse -> empirical design preference.
- Alternative is valid and better on acceptance -> prior convention was locally path-dependent.

### PQ3 — EXPLOITABILITY / ROBUSTNESS

**Question:** Does an Ordivon policy expose stable observable behavior that an adaptive environment can systematically exploit, even when there is no ordinary component bug?

Why it matters:
Component correctness can coexist with policy-level vulnerability.

Answer route:
Choose a real adaptive boundary (security detector, rate limiter, adversarial input source, or competing controller), model repeated observation, and test bounded best-response hypotheses.

Discriminating outcomes:
- No adaptive boundary exists -> drop game-theoretic framing.
- Adaptation exists but stable patterns are harmless -> no architecture change.
- Stable pattern creates repeatable failure/cost -> create a robustness experiment/constraint.

Claim boundary:
This question must not be used to justify bypassing third-party security controls or unauthorized probing.

### PQ4 — INFORMATION FLOW

**Question:** How much hidden internal state can another actor infer from our observable action choice, timing, retry pattern, error surface, or ordering—and which of those leaks are actually consequential?

Why it matters:
The poker analogy is only useful if observable policy behavior reveals decision-relevant state in the target system.

Answer route:
Information-flow inventory first; measurement only on systems and boundaries Ordivon is authorized to inspect.

Discriminating outcomes:
- Observable behavior reveals little consequential state -> analogy is weak.
- State is inferable but harmless -> document only.
- State inference changes another actor's best response or security posture -> route to security/control owner.

### PQ5 — EMERGENCE / CONTROL

**Question:** Which desired Agent behaviors should be directly specified, and which might be better produced by objective + feedback + selection under bounded constraints?

Why it matters:
Too much direct orchestration can make the system brittle; too little can make it ungovernable.

Answer route:
Compare explicit-role orchestration against a bounded alternative in simulation or isolated workload; hold acceptance criteria fixed.

Discriminating outcomes:
- Emergent variant is less reliable/legible -> retain explicit orchestration.
- Emergent variant improves adaptation without losing acceptance -> candidate composition.
- Outcomes depend strongly on task class -> routing rule rather than universal architecture.

### PQ6 — COUNTERFACTUAL / FALSIFICATION

**Question:** Which component of the claimed poker-to-Ordivon lesson is causally necessary, and what observation would falsify the transfer?

Why it matters:
Without this question, the analogy can explain everything after the fact.

Answer route:
For each transfer claim, remove or replace one element and define a prospective acceptance condition.

Examples:
- remove explicit opponent modeling;
- remove randomization;
- remove local replanning;
- remove feedback repair;
- replace adversarial environment with stationary environment.

Discriminating outcome:
If the claimed benefit survives removal, that LEGO was not necessary for the effect being attributed to it.

## 6. Questions pruned in R1

### "Did mathematics beat psychology?"

Pruned as primary question because it is rhetorically loaded and collapses implementation, behavior and human interpretation into a false binary.

Replacement:
Ask what information and opponent-specific modeling the algorithm actually required, and what performance changed when those mechanisms were absent.

### "Is GTO always better?"

Pruned because "better" lacks target opponent, utility, robustness criterion and game class.

Replacement:
Separate expected performance against a population from robustness to a best response.

### "Can all Agent systems use Nash equilibrium?"

Rejected as malformed transfer.
Many Ordivon systems are not games with a defensible equilibrium model. Game-theoretic framing activates only when actors strategically adapt.

### "Should Ordivon make all policies random?"

Rejected.
Randomization is an implementation tool only when supported by a concrete information/exploitability model; unpredictability by itself is not an objective.

## 7. Handoff

**EXPERIMENT**, not PLAN.

The poker case supports four prospective Ordivon investigations before any core promotion:

1. state/projection sufficiency test;
2. convention-versus-invariant action-space ablation;
3. policy-level exploitability test on a real adaptive boundary;
4. explicit-orchestration versus bounded-emergence comparison.

No new common schema or mandatory game-theory field is justified yet.

## 8. Method result

The compiler changed the initial narrative in three useful ways:

- replaced the broad "math versus psychology" frame with testable state/observability/mechanism questions;
- separated transferable system ideas from poker-specific equilibrium claims;
- converted a long conceptual brainstorm into six questions with explicit evidence routes and falsifying outcomes.

This is evidence that the compiler can improve question structure on this case. It is not yet evidence that it improves project outcomes across domains.

## 9. Promotion standing

Candidate concepts retained for further cross-domain testing:

- decision-sufficient state versus displayed/observed state;
- convention versus invariant in action-space design;
- policy-level exploitability at genuinely adaptive boundaries;
- information leakage through observable policy behavior;
- explicit design versus emergent behavior under fixed acceptance;
- counterfactual removal as a standard anti-self-confirmation operator.

Standing: CANDIDATE ONLY.
