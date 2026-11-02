# Authority Mature-Substrate Decomposition R1

Status: registered 2026-09-14.

## Purpose

Ordivon does not claim a novel authority theory. The authority problem spans several mature research and engineering traditions that are usually separated by discipline and product boundary. Ordivon should compose those substrates, preserve their semantic boundaries, and retain only the minimum local bindings needed to make the composition executable for Agents.

This record replaces the misleading framing that `Authority provenance`, `Research -> Policy promotion`, `Typed decision semantics`, or `Consequence -> Policy revision` are Ordivon-native theoretical primitives. They are composition points across mature fields.

## Decomposition

| Problem | Mature substrate | What Ordivon should take | Local ownership |
| --- | --- | --- | --- |
| Who may define rules and meta-rules? | Institutional Analysis and Development (IAD), institutional theory, law, corporate governance | constitutional / collective-choice / operational levels; rules-in-use; legitimate rule-making scope | task-local mapping only |
| How are institutional statements represented? | Institutional Grammar / ADICO-family work; policy administration practice | distinguish rules, norms and shared strategies; do not collapse every statement into `policy` | mapping only |
| How is expertise delegated? | principal-agent theory, delegation theory, bureaucracy/organization theory | principal mandate, discretion, information asymmetry, monitoring, autonomy, revocation | task-local delegation profile |
| How is technical authority delegated and attenuated? | capability security, OAuth-family delegation, Macaroons/caveats, STS/session credentials | bounded scope, attenuation, expiry, revocation, least authority where applicable | adapters/bindings only |
| How are relationship permissions represented? | ReBAC / Zanzibar-style relationship authorization | relation tuples/graphs, causal consistency expectations, separation of relationship state from policy formation | provider selection/binding only |
| How are attribute/context permissions evaluated? | ABAC; Cedar-style principal/action/resource/context authorization | explicit request context and analyzable policy evaluation | no custom evaluator |
| How are policy creation, decision and enforcement separated? | XACML PAP/PDP/PEP/PIP; OPA/Cedar deployment patterns | policy administration != decision != enforcement != information supply | composition boundary only |
| How is evidence distinguished from a claim? | scientific inference, assurance cases, argumentation, provenance | evidence supports claims through explicit arguments/assumptions; evidence is not authority by itself | cross-layer references only |
| How does evidence inform a decision? | evidence-informed policy making, Evidence-to-Decision frameworks | evidence appraisal plus explicit decision criteria; evidence does not mechanically determine policy | task-local EtD/decision record |
| How are objectives, alternatives, consequences and trade-offs combined? | Structured Decision Making, decision analysis, operations research | objectives, alternatives, predicted consequences, trade-offs, implementation | use mature methods/solvers |
| When is more information worth acquiring? | Bayesian decision theory, Value of Information, experimental design | compare expected value of information against cost and delay | use mature methods/solvers |
| How should action continue under uncertainty? | robust/Bayesian decision making, adaptive management | act, observe and learn under explicit uncertainty instead of mapping `unknown` to universal deny | domain method selection |
| How does experience revise models and decisions? | adaptive management / single-loop learning | update system beliefs and action selection from observed consequences | learning bindings only |
| How can the decision architecture itself change? | double-loop learning, organizational learning, institutional learning | periodically reconsider objectives, assumptions, alternatives and decision elements | governance binding only |
| How do existing policies change future policy conditions? | policy feedback, historical institutionalism | model self-reinforcing/self-undermining feedback and path dependence; do not treat feedback channels as neutral | research/diagnostic mapping |
| How is current authorization revalidated? | Zero Trust / continuous authorization patterns | no implicit trust from location or historical authorization; bind current subject/resource/context state | provider policy configuration |
| Did an external effect actually occur? | distributed systems, provider read-back, reconciliation, transactional/effect patterns | distinguish request acceptance, execution, external effect and ambiguity | Runtime/provider boundary, not policy theory |
| Is the intended goal complete? | domain-native V&V / acceptance / assurance | semantic completion belongs to the domain/claim owner, not Runtime or generic IAM | domain-owned verifier |

## Composition spine

The default composition is not an Ordivon-private ontology. It is a sequence of mature substrates:

```text
Scientific / empirical process
        |
        v
Evidence + Claims + Assurance / Provenance
        |
        v
Evidence-to-Decision + Structured Decision Making + VoI
        |
        v
Institutional / governance choice
        |
        v
Policy administration (PAP or equivalent)
        |
        v
Policy decision (Cedar / OPA / XACML-style PDP or equivalent)
        |
        v
Delegated / attenuated authority (OAuth/capability/ReBAC/provider IAM)
        |
        v
Policy enforcement point
        |
        v
Harness / Runtime / provider effect
        |
        v
Read-back / reconciliation / domain verification
        |
        v
Adaptive management / single-loop learning
        |
        +--> double-loop / institutional revision when decision elements themselves need change
```

No arrow means `automatic implication`. Each transition must preserve the source discipline's distinction between evidence, judgement, institutional authority, executable authorization and observed consequence.

## Human role is typed, not universal

Do not use `required human authorization` as a generic consequence/risk fallback. Human involvement is load-bearing only when the actual source of authority or target variable requires it, for example:

- ownership or principal mandate;
- legal/contractual authority;
- consent or rights held by the affected person;
- credential/root-signing boundaries intentionally retained by the owner;
- irreducibly human target variables such as preference, subjective experience or comprehension for a defined population;
- expert evidence when expertise is the relevant evidence source (expertise alone still does not create unrelated authority).

High consequence, uncertainty, model disagreement or novelty do not by themselves prove that a Human is the correct evaluator or approver.

## Risk and uncertainty

Do not import a global `risk -> deny -> human escalation` function. Risk belongs inside the applicable decision method and may affect alternatives, position/scale, reversibility, monitoring or information acquisition.

Likewise, `UNKNOWN` is not a universal authorization result. Distinguish at least:

- missing/expired authority -> deny the affected external effect until authority is established;
- stale world state -> observe/currentness refresh;
- scientific uncertainty -> research/experiment/VoI/robust decision;
- ambiguous prior effect -> reconcile before blind replay;
- unresolved policy/institutional conflict -> adjudicate at the applicable rule-making level.

The final physical effect boundary may still be binary `ALLOW/DENY`; the upstream decision process need not be.

## Do not build by default

Delete or reject a custom component when a mature substrate owns its responsibility. In particular, do not build by default:

- an `Ordivon Authority Theory`;
- a universal Ordivon policy language;
- a custom PDP/PEP implementation when Cedar/OPA/provider IAM can own it;
- a global relationship/ACL engine when a mature ReBAC/IAM substrate is applicable;
- a custom delegation token format when OAuth/capability/session mechanisms suffice;
- a generic evidence ontology that duplicates scientific/assurance/provenance structures;
- a generic Human gate;
- a universal risk gate;
- a custom `research_to_permission()` shortcut.

## What Ordivon may still retain

Only retain local code/data when a real composition edge remains after mature substitution, such as:

- task-local applicability/binding profiles;
- thin translations between externally owned models;
- stable trace/provenance references across layers;
- domain-specific policy inputs that no generic engine owns;
- explicit handoff contracts between decision, enforcement, Runtime effect and domain verification;
- deletion/migration records proving that historical Ordivon semantics were replaced rather than silently lost.

These are not presumed permanent. If a mature provider later owns them cleanly, delete the local glue.

## Reference anchors

These anchors are discovery/reference sources, not a single mandatory stack and not automatically applicable authority for every task.

- Institutional levels / IAD: Daniel H. Cole, "Laws, norms, and the Institutional Analysis and Development framework" (2017), especially constitutional, policy-making and operational levels: https://www.cambridge.org/core/journals/journal-of-institutional-economics/article/laws-norms-and-the-institutional-analysis-and-development-framework/D5A406119308DAEA1F3226FC803282FE
- Institutional Grammar: Crawford & Ostrom, "A Grammar of Institutions", APSR 89(3), 1995: https://doi.org/10.2307/2082975
- Evidence-informed policy making: OECD, *Building Capacity for Evidence-Informed Policy-Making*: https://www.oecd.org/en/publications/building-capacity-for-evidence-informed-policy-making_86331250-en.html
- Evidence-to-Decision: WHO EtD tables: https://www.who.int/publications/i/item/9789240011908
- Structured Decision Making: USGS overview/examples: https://www.usgs.gov/publications/participatory-modeling-and-structured-decision-making
- Value of Information: Jackson et al., *Annual Review of Statistics and Its Application* 9 (2022): https://doi.org/10.1146/annurev-statistics-040120-010730
- Delegation / principal-agent: Bendor, Glazer & Hammond, *Theories of Delegation* (2001): https://doi.org/10.1146/annurev.polisci.4.1.235 ; Miller, *The Political Evolution of Principal-Agent Models* (2005): https://doi.org/10.1146/annurev.polisci.8.082103.104840
- Adaptive / double-loop learning: Williams & Brown (2018), USGS record: https://www.usgs.gov/publications/double-loop-learning-adaptive-management-need-challenge-and-opportunity
- Policy feedback: Béland, Campbell & Weaver, *Policy Feedback: How Policies Shape Politics* (2022): https://doi.org/10.1017/9781108938914
- PAP/PDP/PEP: OASIS XACML 3.0: https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-en.html
- Fine-grained policy evaluation: Cedar reference guide: https://docs.cedarpolicy.com/
- Policy-as-code decision engine: Open Policy Agent documentation: https://www.openpolicyagent.org/docs
- Relationship authorization / consistency: Google Zanzibar paper: https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/
- Delegation attenuation: Google Macaroons paper: https://research.google/pubs/macaroons-cookies-with-contextual-caveats-for-decentralized-authorization-in-the-cloud/
- OAuth delegation: RFC 6749 (plus its current updates/BCP when an implementation is actually selected): https://www.rfc-editor.org/info/rfc6749/
- Current authorization / zero trust: NIST SP 800-207: https://csrc.nist.gov/pubs/sp/800/207/final

## Registration boundary

This lesson is a cross-disciplinary substrate map, not an External Authority Catalog expansion. Concrete standards should enter `authorities/records/` only when a live task needs their exact identity/version/currentness. Academic traditions and research literatures remain knowledge sources unless a task gives them a specific normative role.
