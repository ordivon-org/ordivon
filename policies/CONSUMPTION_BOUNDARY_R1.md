# Policy consumption boundary R1

This profile prevents the existence of an OPA reference policy from becoming a new central Ordivon authorization layer.

## Routing law

Use the closest mature or domain-native authority owner. OPA/Cedar/provider policy engines are selected only when the responsibility is genuinely **machine policy evaluation**. They do not absorb scientific judgement, product choice, capital rationality, task lifecycle, Runtime execution truth, or provider-native identity/capability truth.

| Consumer | Default authority / decision owner | OPA/PDP role | Must not become |
| --- | --- | --- | --- |
| Runtime | Runtime physical execution/admission contracts and exact caller-granted execution authority | none by default | semantic-completion or domain-permission authority |
| Host | Host Task lifecycle/continuity and owner bridges | none by default | achievement/value/domain-truth evaluator |
| Harness core | exact Run Contract + request-bound Tool/action authority + caller/domain admission | none by default | global capability/policy service |
| Network | provider/network configuration and current connectivity/service truth | only a local deployment policy if a real network policy question exists | domain permission authority |
| Research | scientific method, claims, standing, prior-art/evidence stack | none for epistemic standing | permission mint or action gate |
| Operations | mature provider state plus generic operational policy/admission | **appropriate** for declarative operational admission; current Operations already selects OPA | second monitoring/workflow/domain semantic engine |
| Game | claim-relative evaluation + Structured Decision Making + Game stage/product authority | appropriate only after a Game decision adopts a machine-enforceable rule | product selector, player-value oracle, generic Human gate |
| Finance | Owner Constitution, Finance capital rationality/Decision, provider/executor effect admission and reconciliation | optional for a bounded declarative policy seam when it does not duplicate Finance or provider-native enforcement | trade/risk oracle, owner substitute, evidence-to-trade gate |
| Market Capital | domain decision/proof semantics + concrete provider/executor external-effect admission | optional only for an actual policy seam after the provider/effect surface exists | abstract production-approval gate |
| Media / Distribution | Media claim/production semantics + provider-native publish capability/admission/readback | optional for cross-provider declarative policy only | taste authority, universal Human approval gate, provider capability registry |

## Research adoption rule

Research may affect executable policy only through an explicit decision/adoption transition:

```text
research/evidence/standing
  -> evidence-to-decision / SDM
  -> adopted institutional/domain decision
  -> PAP/provider policy administration
  -> PDP decision when machine policy evaluation is actually needed
  -> current delegation/capability/IAM
  -> PEP/provider enforcement
```

The transition is intentionally asymmetric:

- stronger evidence may change the decision basis, but does not itself create permission;
- an adopted policy may authorize a bounded action even when unrelated epistemic questions remain `UNKNOWN`;
- a provider/IAM `DENY`, expired delegation, revoked policy, or out-of-scope resource remains a real authorization failure;
- high consequence or uncertainty does not manufacture a Human approver;
- Human authority is used only when ownership, mandate, law/contract, consent/rights, retained root credentials, or an irreducibly Human target variable makes it load-bearing.

## Centralization prohibition

Do **not** introduce any of the following as a shared Ordivon service without a new demonstrated substitution failure:

- global `can_act()` or `research_to_permission()` service;
- global risk-to-deny function;
- global Human-approval router;
- global evidence score -> authority conversion;
- central capability registry that overrides request-bound/provider-native capability truth;
- OPA sidecar in front of every Runtime/Host/Harness/provider call merely because OPA is installed.

The current `research-adopted-r1` bundle is a reference profile for one real composition edge, not a mandate that every owner consume it.
