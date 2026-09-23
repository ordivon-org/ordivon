# Integrated C08 Capital Read-only Dogfood R1

Date: 2026-09-23
Status: **PASS — ONE BOUNDED REAL C08 SLICE**

This dogfood closes one real vertical slice without creating a new Effect mapper, verdict ontology, evidence database, or control plane. It binds existing owner contracts only.

## Bound path

```text
Cognitive Circuit (Composition)
  -> C06 no-Tool HarnessRunContract + AgentRunBinding (Agent App)
  -> bounded Harness candidate + Run Receipt
  -> Runtime workspace.exec of Capital owner verifier
  -> Capital native `ordivon.capital.readonly-circuit-acceptance` standing `PASS`
  -> Experimental Episode R1 analytical projection
```

The frozen source revision is `832468936934e03aa2b8f67836182a8543b124a6` and the same relevant C06/Composition/Capital/Episode surfaces were requalified unchanged at `5f9a41313624406b3381a06612b87e493951ab9e`.

## Exact evidence

- Circuit: `circuit:integrated-c08-capital-readonly-r1` / `sha256:2763269ffcc9f250fcbe063e1d4b8dfb84a1b8cebc7ca38188bec856d9ea27d9`.
- Harness Run: `harness-run:integrated-c08-capital-readonly-r1-r3`; contract `sha256:1b9afdb6c0b4d0d3ddd3993652838011cc6d71e4f666a5eaef8a04bbe6a1dde9`; receipt `sha256:6a5b71d7123cc585001176cf4ca75d67b649f3e907fe2f4a6c7966fd902904ba`.
- Harness explicitly retained `runtimeJobRefs=[]` and `domainAcceptanceEstablished=false` on the candidate binding.
- Runtime verifier Job: `job-01a0ce08-8fe3-7012-be1e-42994bba5dc7`, Attempt `attempt-01a0ce08-8fe3-7012-be1e-42af01cf58f3`, operation `sha256:a3c3d86e35d87c9230e9ae978b4d9296f70a48e7ac6ecbe279d830cfb7fd1d5c`.
- Runtime initially observed `LIVE_UNIT_WITHOUT_LAUNCH_TOKEN_EVIDENCE`; the same Job later recovered a late identity-bound runner result, corrected to `succeeded`, and converged without blind redispatch. Runtime still reported `semanticCompletionEvaluated=false`.
- Capital verdict file SHA-256: `sha256:b1734d09454cece0fc935c3b19985e9586c88943e4ba48341553133546522ea5`; canonical semantic digest: `sha256:6e11edf067c574dee8088b1097aea70408f94bb3e3bdc0d9dddea98deb1cbe92`; native standing remains exactly `PASS`.
- Capital asserts `externalFinancialWritesAttempted=false` and `semanticCompletionEvaluated=false`.

Machine receipt: `docs/architecture/integrated-c08-capital-readonly-dogfood-r1.json`.
Episode: `meta/next/evidence/acceptance/integrated-c08-capital-readonly-episode-r1.json`.

## Architectural consequence

C08 is now demonstrated for one bounded real task. D04 is demonstrated for one owner-native verdict binding, not promoted to a universal verdict contract. L03 now has its first real compiled C08 Episode. L02 remains `DEFER_NEW_POSTGRES_STORE`; the next question is measured analytical/query pressure, not database construction.

A03b remains independently open because this slice does not create production-authoritative Agent/Grant/Effect evidence.
