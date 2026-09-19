# Enterprise Work Router Thinning R1

Date: 2026-09-19
Role: migration/disposition record.

## Decision

The generic enterprise-work layer had become thicker than its residual responsibility.

Before this migration:

- `.agents/skills/enterprise-work/SKILL.md`: 238 lines / 14,573 bytes;
- `compositions/enterprise-work-to-outcome-r1.md`: generic reusable enterprise composition;
- `scripts/check_enterprise_operating_model_r1.py`: custom checker for historical dogfood assumptions.

The checker had no external consumer and still encoded the historical 2026-09-14 ISO 9001:2026 under-publication state. The composition was referenced only by repository documentation and the enterprise-work Skill.

## Replacement

The active `enterprise-work` Skill is now a thin routing adapter:

```text
exact task-local facts
  -> discover/check external authority
  -> select natural mature owner
  -> execute through that owner
  -> verify with the real acceptance authority
```

It deliberately does not define an Ordivon management lifecycle.

The Skill delegates, as applicable, to external owners such as ISO 10005 / 21502 / 31000 / 19011 / 10002 / 10004 / 30405 / 20400 / 37500, YC/Lean/Strategyzer/Stripe advisory practice, ERPNext/Frappe providers, BPMN/CMMN/DMN/Flowable, Temporal, n8n, OPA, domain methods and real customer/external authorities.

## Retired local surface

Deleted:

- `compositions/enterprise-work-to-outcome-r1.md`;
- `scripts/check_enterprise_operating_model_r1.py`.

The historical acceptance JSON and detailed operating-model document remain as provenance/reference. Their historical observations are not rewritten into current-state claims.

## Residual local responsibility

The router may retain only what cannot be outsourced to a general external method without losing the task boundary:

- exact task identity/scope;
- acceptance authority;
- applicability/currentness binding;
- natural-owner selection;
- execution-vs-semantic-completion boundary;
- local company/project configuration;
- evidence references and measured substitution failures.

A new generic enterprise composition/checker is inadmissible unless repeated real workloads prove that the thin router plus mature owners cannot preserve a necessary invariant.
