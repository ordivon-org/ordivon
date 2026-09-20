# Game Composition Search — R1

Status: **EVIDENCE-GUIDED / NOT PRODUCT SELECTION**
Observed: 2026-09-14

## Search law

The search unit is a mechanism graph. Each candidate below reuses measured/local evidence and introduces only a few strategically important UNKNOWN couplings. A candidate is admitted because it is cheap and informative, **not** because it is likely to become the first product.

| ID | Composition | Strong evidence reused | Main unknown | Status |
| --- | --- | --- | --- | --- |
| `mc01-epistemic-operations` | **Epistemic Operations** | c01, c10, r2-c23, r2-c31 | deadline/time pressure -> evidence prioritization: strategic focus vs rushed guessing | `ADMIT_REUSE_CARRIER` |
| `mc02-diagnostic-factory` | **Diagnostic Factory Under Partial Observation** | c04, r2-c23, r2-c24 | partial observation -> bottleneck diagnosis: deeper inference vs opaque frustration | `ADMIT_NEW_MICRO_FALSIFIER` |
| `mc03-responsive-buildcraft` | **Responsive Buildcraft** | c03, c06, c07, r2-c18 | responsive preference -> build path: meaningful strategic adaptation vs score-function exploitation | `ADMIT_NEW_MICRO_FALSIFIER` |
| `mc04-sealed-routing` | **Sealed Routing / Tactical Commitment** | r2-c26, r2-c29, r2-c32, c09 | simultaneous commitment + choke topology -> interpretable tactical tension vs deterministic bottleneck puzzle | `ADMIT_NEW_MICRO_FALSIFIER` |
| `mc05-role-delegated-crisis` | **Role-Delegated Crisis Management** | c09, r2-c21, r2-c25, r2-c31, r2-c32 | time pressure -> whether delegation leverage repays review/administrative burden | `HOLD_HIGH_COST_REUSE_ONLY` |
| `mc06-persistent-responsive-authorship` | **Persistent Responsive Authorship** | c06, c16, r2-c18 | responsive audience -> persistent authorship: validation/deepening vs hijacking self-authored intent | `ADMIT_REUSE_CARRIER` |
| `mc07-topological-mastery` | **Topological Mastery** | r2-c16, r2-c26 | topology variation -> motor mastery: richer execution learning vs route-puzzle substitution | `ADMIT_REUSE_CARRIER` |
| `mc08-knowledge-gated-exploration` | **Knowledge-Gated Exploration** | r2-c26, r2-c28 | learned world rule -> topology: genuine discovery vs arbitrary designer lock | `ADMIT_NEW_MICRO_FALSIFIER` |

## Candidate graphs

### Epistemic Operations — `mc01-epistemic-operations`

**Anchors:** `information-scarcity, inspection-cost, deduction`  
**Support:** `scan, required-goal, deadline-time-limit, memory-knowledge-persistence`

**Target dynamic:** selective evidence acquisition under operational pressure causes model revision that changes action

**Known evidence:** `c01`, `c10`, `r2-c23`, `r2-c31`

**Unknown couplings:**
- deadline/time pressure -> evidence prioritization: strategic focus vs rushed guessing
- scan timing + scarce evidence -> whether delayed information creates planning depth or frustration

**Cheapest falsifier:** Reuse PGP-D style compact case; add one explicit time/action budget and one delayed scan whose result is only actionable on the next decision head.

**Kill conditions:**
- players guess because time dominates inference
- scan result arrives too late to affect a meaningful choice
- players still inspect the same obvious clue order

### Diagnostic Factory Under Partial Observation — `mc02-diagnostic-factory`

**Anchors:** `required-goal, bottleneck, machine-allocation`  
**Support:** `partial-observation, scan, feedback-control, respec-reconfiguration, throughput`

**Target dynamic:** player forms a causal model of a system from incomplete telemetry and redesigns it intentionally

**Known evidence:** `c04`, `r2-c23`, `r2-c24`

**Unknown couplings:**
- partial observation -> bottleneck diagnosis: deeper inference vs opaque frustration
- active scanning -> redesign choice: useful diagnostic agency vs mandatory busywork

**Cheapest falsifier:** One-screen micro-factory with one hidden internal state, two optional diagnostics, visible output/queue symptoms and cheap rebuild.

**Kill conditions:**
- correct fix is impossible to infer before scan
- one diagnostic dominates every state
- hidden state merely delays the obvious answer

### Responsive Buildcraft — `mc03-responsive-buildcraft`

**Anchors:** `drafting, synergy-combos, build-path-dependency`  
**Support:** `hidden-information, responsive-audience-opponent, create-edit, save-revision, agent-policy`

**Target dynamic:** path-dependent composition is revised across rounds because a learnable audience changes the value of synergies

**Known evidence:** `c03`, `c06`, `c07`, `r2-c18`

**Unknown couplings:**
- responsive preference -> build path: meaningful strategic adaptation vs score-function exploitation
- build synergy + authored intent -> whether adaptation preserves ownership

**Cheapest falsifier:** 4-round symbolic draft: 3 choices/round, pair synergies, 3 hidden deterministic personas, visible qualitative response, revision history.

**Kill conditions:**
- one motif/build dominates each persona trivially
- players optimize response score without an articulated composition intent
- static rubric performs equivalently

### Sealed Routing / Tactical Commitment — `mc04-sealed-routing`

**Anchors:** `capacity-limit, route-network-building, required-goal`  
**Support:** `prediction-preview, partial-observation, simultaneous-resolution, cause-effect-log, select-choose`

**Target dynamic:** player commits a route plan with exact own consequences against bounded hostile uncertainty and learns from collision/congestion outcomes

**Known evidence:** `r2-c26`, `r2-c29`, `r2-c32`, `c09`

**Unknown couplings:**
- simultaneous commitment + choke topology -> interpretable tactical tension vs deterministic bottleneck puzzle
- own-plan preview + hostile partial observation -> sufficient responsibility without delegation

**Cheapest falsifier:** Small graph/grid with 2–3 routes, capacity/choke constraints, exact own preview, sealed enemy route choice and instant replay.

**Kill conditions:**
- one route dominates
- uncertainty is indistinguishable from random loss
- post-turn collision cannot be causally explained

### Role-Delegated Crisis Management — `mc05-role-delegated-crisis`

**Anchors:** `delegate, role-asymmetry, agent-policy`  
**Support:** `required-goal, deadline-time-limit, partial-observation, cause-effect-log, command`

**Target dynamic:** player chooses doctrine and role-level intent while recognizable specialists act autonomously under pressure

**Known evidence:** `c09`, `r2-c21`, `r2-c25`, `r2-c31`, `r2-c32`

**Unknown couplings:**
- time pressure -> whether delegation leverage repays review/administrative burden
- role identity + bounded information -> whether player can predict competence without micromanagement

**Cheapest falsifier:** Reuse a stripped Station-Zero-like deterministic carrier with only objective, two doctrine controls, three specialists, one pressure clock and concise aftermath.

**Kill conditions:**
- player spends more time configuring/reviewing than making strategic decisions
- specialists remain behaviorally indistinguishable to the player
- delegation adds no decision leverage over direct control

### Persistent Responsive Authorship — `mc06-persistent-responsive-authorship`

**Anchors:** `create-edit, save-revision, world-state-persistence`  
**Support:** `self-authored-goal, responsive-audience-opponent, hidden-information, freeform-building`

**Target dynamic:** player creates for self-authored intent, receives interpretable but non-authoritative response, and revises a persistent artifact

**Known evidence:** `c06`, `c16`, `r2-c18`

**Unknown couplings:**
- responsive audience -> persistent authorship: validation/deepening vs hijacking self-authored intent
- persistent artifact -> whether later response increases attachment or only optimization

**Cheapest falsifier:** Extend PGP-I carrier with one persistent artifact across three rounds and one deterministic persona that comments on relational patterns, not numeric score.

**Kill conditions:**
- players revise only to please persona
- self-authored intent disappears after feedback
- persistence adds no later decision consequence

### Topological Mastery — `mc07-topological-mastery`

**Anchors:** `timing-window, jump, fast-retry`  
**Support:** `capacity-limit, route-network-building, safe-vs-risky-route, variable-setup, immediate-action-feedback`

**Target dynamic:** stable movement skill is reinterpreted by bounded topology variations while failure remains self-attributable

**Known evidence:** `r2-c16`, `r2-c26`

**Unknown couplings:**
- topology variation -> motor mastery: richer execution learning vs route-puzzle substitution
- safe/risky route choice -> voluntary mastery escalation vs obvious optimization

**Cheapest falsifier:** Reuse PGP-A three-room carrier; create two matched topology variants that preserve verbs but change safe/fast routing and timing windows.

**Kill conditions:**
- success differences are mostly route discovery
- topology change breaks attribution through collision ambiguity
- players do not voluntarily retry harder line

### Knowledge-Gated Exploration — `mc08-knowledge-gated-exploration`

**Anchors:** `rule-discovery, shortcut-discovery, gating-by-knowledge`  
**Support:** `capacity-limit, placement-efficiency, route-network-building, map-reveal, required-goal`

**Target dynamic:** player forms a rule/topology hypothesis, applies it to reveal a shortcut, and changes later navigation

**Known evidence:** `r2-c26`, `r2-c28`

**Unknown couplings:**
- learned world rule -> topology: genuine discovery vs arbitrary designer lock
- objective-bearing placement + knowledge gate -> curiosity vs optimization marker chasing

**Cheapest falsifier:** 4–6 region graybox with two routes, one stable traversal rule, one knowledge-only shortcut and one placement variant that changes route consequence.

**Kill conditions:**
- shortcut is found by pixel hunting
- rule does not alter later navigation
- objective marker dominates curiosity

## First reuse-first wave

1. **MC01 Epistemic Operations** — reuse investigation apparatus; add only time/action budget + delayed information timing.
2. **MC07 Topological Mastery** — reuse precision apparatus; vary topology while keeping verbs fixed.
3. **MC03 Responsive Buildcraft** — new but tiny symbolic carrier; combines two independent structural survivors.

This first wave is intentionally heterogeneous: inference, embodied mastery, and compositional strategy. It prevents the evidence system from selecting only the kinds of game Ordivon historically modeled well.

## Explicit holds

- **MC05 Role-Delegated Crisis** is not a greenfield build candidate. Existing Station Zero evidence is rich enough; any further work must reuse/strip the existing carrier because administrative burden is already a measured risk.
- **MC06 Persistent Responsive Authorship** should extend PGP-I rather than start a new creation tool.
- MC02/MC04/MC08 are valid cheap falsifiers but currently have less reuse leverage than the first wave.

Machine-readable authority: `game-composition-search-r1.json`.
