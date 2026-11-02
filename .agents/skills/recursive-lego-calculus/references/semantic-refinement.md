# End-to-End Semantic Refinement — thought LEGO and problem/solution cases (R2.1)

> **One sentence:** An Agent may propose imperfect actions, but neither a
> proposed action nor a self-reported completion may become **authorized
> effects** or **verified domain success** without the corresponding
> independent, current owner obligations.
>
> **Chinese:** 模型可以提出错误候选，但模型判断不能直接升级为执行权限或完成事实。

This is an **instance of the existing Recursive LEGO Calculus** and
compositional-contracts methods, **not** a second LEGO calculus, security
controller, domain verifier, skill registry, or all-purpose agent framework.

## Semantic propagation

```text
human goal G, grant A, immutable SourceCut C
              │ normative obligation (G,A,C)
              ▼
model intent / plan / delegation   [hypothesis only]
              │ candidate action
              ▼
EXECUTION OWNER ── current grant/actor/effect enforcement ── actual action τ
              │                         (not enforced by this prototype)
              ▼
owner-complete trace τ + independent domain owner readback E
              │
              ├── known unauthorized action → FAIL
              ├── verified goal contradiction → FAIL
              ├── missing closure, source drift, foreign evidence → UNKNOWN
              └── authorized closed trace AND verified outcome → scoped PASS
```

The three conceptual seams are **intent refinement**, **authority
refinement**, and **result refinement**. The bounded executable prototype
checks *reported observations* of the latter two. It does **not** establish
intent faithfulness, action-time complete mediation, provider authenticity,
external truth, or installed code refinement. A complete Owner trace is an
assumption supplied by a real owner integration, not something this library
discovers or proves.

## Problem domain: reusable bounded Problem LEGO instances

Problem archetype:
`ell_problem=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`

| R2.1 coordinate | Typed effective value |
| --- | --- |
| I | `ProblemInput = (Obligation, ObservedTrace?, GoalObservation?, ModelClaim?)` |
| O | `ProblemOutput = (counterexample?, standing: PASS/FAIL/UNKNOWN, evidence_refs)` |
| S | `ProblemState = (source_cut, work_ref, attempt_ref, consumer_ref, goal_ref)` |
| pre | The claimed goal and consumer are named; external observations can be absent |
| post | No unsupported success promotion; each case has a falsifier or explicit UNKNOWN |
| inv | `FAIL != UNKNOWN`; Agent claims never confer grant, source identity or success |
| eff | `Unit` — source reasoning only, no external write |
| c | Bounded fixture and one owner trace; actual real-owner cost `UNKNOWN(unmeasured)` |
| epsilon | `UNKNOWN(real owner authenticity, unobserved effects, semantic quality of goal)` |
| prov | Ordivon native source + test refs below, exact Git commit bound at verification |
| unfold | Existing `recursive-lego-calculus`, `compositional-contracts` and Composition provider |

Each row below is a **version-scoped instance** of all eleven coordinates
above; replaceable problem responsibility is to produce a falsifiable
obligation, not to simulate or fix the world.

| Problem LEGO | `p=(w0,phi,Gamma)` / minimal counterexample | What would falsify unsafe promotion? |
| --- | --- | --- |
| `P-ESR-01/IntentEvidence` | Model says "done" while owner observation absent; `phi` = no self-report completion admission | `claimed=True, ownerGoal=None` must be UNKNOWN |
| `P-ESR-02/AuthorityDrift` | Goal succeeded but one observed action is forbidden; `phi` = all observed actions allowed | `goal=PASS, one action=False` must be FAIL |
| `P-ESR-03/EvidenceDrift` | Success observation refers to another goal or attempt; `phi` = matching qualified evidence | `goalBinding != contractBinding` must be UNKNOWN |
| `P-ESR-04/IncompleteTrace` | Owner trace not closed; `phi` = no positive authorization from incomplete observation | `traceComplete=False, all seen allowed` must be UNKNOWN |

`Gamma` for every instance: the owner observation and authorization oracle
are genuine, complete **only where explicitly declared**, and current for
the same source and task. Those assumptions are **not established** by the
prototype; a real Runtime/Host/domain integration must discharge them.

## Thinking LEGO: `M-ESR-01/EndToEndSemanticRefinement`

`ell_method=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`:

- **I:** `(GoalSpec, GrantSpec, Attempt, OwnerObservations?, ModelHypothesis?)`
- **O:** `(NormativeObligations, BrokenSeams, Falsifiers, Standing)`
- **S:** `(goal_ref, source_cut, owner, consumer, verification_scope)`
- **pre:** Real consumer and goal declared; unknowns may remain explicit
- **post:** Never promote model or tool assertion without the appropriate owner witness
- **inv:** `UNKNOWN != PASS != FAIL`; source/model/installed/domain states separate
- **eff:** `Unit` (analysis/method only, no execution authority)
- **c:** Task-local representation/evidence cost, `UNKNOWN(unmeasured outside pilot)`
- **epsilon:** `UNKNOWN(unformalized natural-language goals, owner honesty)`
- **prov:** This existing Skill reference; NIST reference monitor; TLA+ refinement; end-to-end principle
- **unfold:** `recursive-lego-calculus` plus `compositional-contracts`; method is replaceable

Method: first choose the smallest original goal and owner boundary;
separate what can be **mechanically checked** from human judgment; require
reference-monitor complete mediation at the *actual effect boundary*; bind
owner-trace and goal evidence to exact attempt/source/goal identity; use
independent counterexamples; report a three-valued result. If an existing
Ordivon owner supplies the contract, use it; do not add an extra gate.

## Capability LEGO: `C-ESR-01/ScopedSemanticWitnessComparator`

`ell_capability=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`:

- **I:** `Obligation × OwnerTraceProvider × OwnerAuthorizationOracle × OwnerGoalObserver`
- **O:** `SemanticResult(authorization,completion,overall,reasons,evidence_refs)`
- **S:** `Unit` (pure per-call calculation; no state, no registry)
- **pre:** Exact nonempty binding; provider callbacks supplied by caller
- **post:** `overall=PASS ⇔ authorization=PASS ∧ completion=PASS` under qualified providers
- **inv:** Owner mismatch/absence ⇒ UNKNOWN; observed forbidden action ⇒ FAIL;
  self-reported success has **no input channel**
- **eff:** Invokes externally supplied owner callbacks; their effects must be independently qualified; no tool dispatch,
  credentials, grant creation, database writes or external effects
- **c:** `O(|observed_actions|)` callback work and `O(|observed_actions|)`
  transient trace; measured wall-clock `UNKNOWN` until owner integration
- **epsilon:** `UNKNOWN(callback authenticity, grant timeliness, trace closure,
  owner truth, installed implementation, unobserved actions)`
- **prov:** `packages/composition/src/ordivon_composition/semantic_refinement_r1.py`
  and `packages/composition/tests/test_semantic_refinement_r1.py`
- **unfold:** Pure Python Composition API (no new process or authority)

A PASS is **conditional**. In particular, arbitrary Agent-produced callbacks
can spoof an owner. Deploy only if a natural owner binds these callbacks to
authenticated principals, effect-time authorizations, actual source/attempt
identity, completeness of trace and genuine independent domain readback.
Never advertise this as a policy engine or enforcement layer.

### Verification / independent falsification

- Owner-native pytest: positive fixture, unauthorized action, withheld goal,
  foreign/mismatched evidence, incomplete trace, missing/throwing providers,
  all nine pairs of three-valued standing, nonempty identity validation.
- Existing canonical Composition source/toolchain; no new verifier or registry.
- **Model boundary:** 20 reachable TLC states with a real negative reachability probe, and exhaustive nine-case algebra, check only this finite
  evidence-composition rule. It is *not* a proof that a real Runtime implements
  complete mediation or that a real domain owner reports truth.
- Currentness: **SOURCE_CANDIDATE** until a reviewed Git/CI integration and
  installed consumer are independently observed. No `INSTALLED_CURRENT` or
  `DOMAIN_ACCEPTED` claim from isolated unit tests.

## Registration / natural owner mapping

- **Method/thought domain:** this document is linked from the existing
  `.agents/skills/recursive-lego-calculus/SKILL.md`, not a new Skill.
- **Capability/Composition domain:** Python code, native tests and public API
  live in `packages/composition`, the existing non-authoritative owner.
- **Problem/verification domain:** P-ESR-01..04 are sourced here and map to
  the existing Host problem-LEGO Work; Host is coordination only, not proof.
- **Effect/domain truth:** Runtime/Gateway/Host and specific domain consumers
  remain the only respective live authority; these are integration obligations
  for a future actual consumer, not pretend registrations/deployments.

Mature foundations:
- NIST CSRC Reference Monitor: https://csrc.nist.gov/glossary/term/reference_monitor
- TLA+ refinement: https://github.com/tlaplus/vscode-tlaplus/blob/master/resources/knowledgebase/tla-refinement.md
- OWASP Agent Security: https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
