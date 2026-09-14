# Authority Semantic Expression R1

Status: **CURRENT LANGUAGE / COMPOSITION PROFILE**

## Purpose

This document does **not** define a new Ordivon authority model. It translates recurring Ordivon meanings into established institutional, decision-science, assurance and authorization vocabulary so that local docs do not invent parallel concepts or accidentally smuggle evidence, risk or Human participation into permission semantics.

Use the mature source-native term whenever one fits. Keep an Ordivon-local term only when it names a real cross-system binding that no selected substrate owns.

## Preferred expression map

| Meaning we need | Prefer mature expression | Avoid using as a substitute |
| --- | --- | --- |
| owner/organization defines the durable mission and reserved powers | principal mandate; constitutional / institutional rule; beneficial ownership; organizational governance | generic `Human authority` |
| one actor gives another bounded power | delegation; delegated authority; capability grant; scoped credential/session | intelligence level; trust score |
| delegation is narrowed by scope/time/resource | attenuation; caveat; permission boundary; session policy; validity/revocation | another home-grown lease taxonomy when mature capability/IAM semantics suffice |
| an observation supports or challenges a proposition | evidence; finding; claim; assurance argument; provenance | permission, authority |
| current epistemic result for a claim | claim status / finding status / evidence appraisal within scope | global evidence score; action permission |
| evidence is combined with objectives/values/trade-offs | evidence-to-decision; structured decision making; decision analysis | `evidence gate` |
| deciding whether more information is worth acquiring | Value of Information; experimental design; information-gathering decision | `unknown => deny` |
| choosing an action under uncertainty | Bayesian/robust decision analysis; adaptive management where iterative learning applies | universal risk gate |
| organization changes a rule or policy | institutional / collective-choice decision; policy administration (PAP or equivalent) | `research automatically promotes itself` |
| a concrete request is evaluated against executable policy | authorization decision; PDP decision; Cedar PARC / ABAC request as applicable | product decision; scientific conclusion |
| current attributes/state used in authorization | policy information / request context; PIP; continuous authorization / Zero Trust currentness where applicable | historical trust |
| a decision is physically enforced | policy enforcement point (PEP); provider-native enforcement | evidence verdict |
| a tool or actor is technically capable | capability / availability | authorization |
| an external side effect was actually committed | external-effect result; provider read-back; reconciliation / settlement/finality where domain-native | process exit; request accepted |
| a goal or claim is satisfied | domain-native V&V, acceptance, assurance, outcome evaluation | Runtime success; authorization success |
| results change the next operational choice | adaptive management / single-loop learning | automatic policy mutation |
| results change objectives/rules/decision architecture | double-loop / institutional learning; policy revision through the applicable governance process | self-legislation by the research producer |

## Vocabulary discipline

### `authority`

Use `authority` for a real right/power to decide, delegate, admit or cause an effect, or explicitly qualify a natural source-of-truth owner (`provider authority`, `domain authority`). Do not use it merely to mean that a file is informative, recent or persuasive.

Prefer `source / provenance`, `claim status`, `policy`, `authorization`, `acceptance owner`, or `provider source of truth` when those meanings are intended.

### `gate`

Avoid `Human gate`, `risk gate`, `evidence gate`, or similar language unless there is literally an admission boundary owned by the named authority.

Translate the underlying meaning instead:

```text
Human gate
  -> Human participant evidence is required for this Human-state claim
  -> or owner/consent-holder authorization is required for this effect

risk gate
  -> constitutional/contractual hard constraint
  -> or risk is an input to decision analysis

evidence gate
  -> claim-specific evidentiary criterion / assurance requirement
  -> or decision criterion in an EtD/SDM process
```

### `Human`

Always type the role:

- **principal / owner** — source of delegated authority;
- **rights or consent holder** — authorization that cannot be inferred from evidence;
- **participant / target population** — source of evidence about Human state, preference, comprehension or experience;
- **expert** — evidence source within expertise scope;
- **governance actor** — institutional role with explicitly assigned rule-making power.

Do not use `Human` as a universal fallback authority class.

### `risk`

Risk is normally a decision-analysis variable or an explicit constitutional/legal constraint. It is not a self-authenticating permission source.

```text
risk estimate
+ objectives
+ alternatives
+ consequences
+ uncertainty
+ optionality / survival constraints
+ value of information
-> decision
```

A hard denial must identify the actual rule/constraint whose semantics require denial.

### `unknown`

Name what is unknown before choosing the next operation:

- authorization/current grant unknown -> establish/revalidate authority before the affected effect;
- world/provider state stale -> observe / refresh currentness;
- effect outcome ambiguous -> reconcile;
- scientific claim uncertain -> research / experiment / VoI / robust decision;
- institutional rule conflict -> adjudicate through the applicable governance process;
- Human-state claim unobserved -> obtain relevant Human evidence if that claim matters to the decision.

`UNKNOWN` alone is not a policy outcome.

## Preferred end-to-end expression

Use this composition rather than a private all-purpose authority pipeline:

```text
Principal / institutional mandate
        |
        +-------------------- external law / contract / rights constraints
        |
Scientific / operational observations
        v
Evidence -> claims / assurance -> scoped findings
        v
Evidence-to-Decision / Structured Decision Making / VoI
        v
Institutional or delegated decision authority
        v
Policy administration / delegated capability
        v
Authorization request -> PDP decision
        v
PEP / provider-native enforcement
        v
External effect
        v
Read-back / reconciliation / settlement or domain effect truth
        v
Domain V&V / outcome evaluation
        v
Adaptive or double-loop learning when warranted
```

No arrow authorizes an automatic semantic upgrade. In particular:

```text
Evidence != Policy
Policy != Authorization result
Authorization result != Effect truth
Effect truth != Goal completion
Human evidence != Human approval
Risk != Denial
```

## Domain application rule

Domains should express only their domain-specific variables and objectives, then bind them to these mature concepts.

Examples:

- **Game:** player-experience claims use Human participant evidence; structural/reachability/strategy claims may use simulation or formal/causal methods; product commitment is a structured decision, not a Human-approval gate.
- **Finance:** beneficial owner/principal delegates a capital scope; the capital manager performs decision analysis inside that scope; execution authority is attenuated to effect-specific grants/enforcement; market/economic evidence does not itself grant capital permission.
- **Research:** evidence/claims/standing remain epistemic; any organizational policy consequence occurs through a separate evidence-to-decision and institutional process.

## Non-goal

This profile must not become a required universal schema. It is a translation/discipline aid. If Cedar, OPA, OAuth, a provider IAM, an assurance tool, an SDM/OR package or another mature substrate can carry the semantics directly, use that native model rather than serializing this document into another Ordivon protocol.
