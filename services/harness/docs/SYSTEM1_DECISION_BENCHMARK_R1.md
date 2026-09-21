# System-1 Decision Benchmark R1

## Purpose

This benchmark is a provider-neutral, no-effect measurement boundary for typed probabilistic
decision providers. It exists to compare implementations such as TypeSafe Jev, local Laya, and
future providers without granting any of them Harness routing authority.

The benchmark does not execute browser effects, authorize tasks, define Opportunity semantics, or
treat a provider's confidence as trustworthy merely because the provider emits a number.

## Authority boundary

- Domain owners define the question, option semantics, expected answer, and whether a case is
  representative.
- This benchmark binds case identity, validates typed observations, and computes provider-neutral
  metrics.
- A provider adapter owns only translation between the canonical case and the provider API/runtime.
- Runtime owns physical Job/Attempt truth when an adapter is executed through Runtime.
- Confidence/probability may be used for an autonomous-action threshold only after calibration on
  the target distribution.
- ERROR, BLOCKED, and NOT_EXECUTED are never rewritten as wrong answers or zero-valued telemetry.

## R1 metrics

Choice questions:
- execution coverage
- exact accuracy
- multiclass Brier score
- max-probability ECE
- negative log likelihood
- latency

Boolean (noul) questions:
- execution coverage
- threshold-0.5 accuracy
- binary Brier score
- ECE
- negative log likelihood
- latency

Provider-level reporting retains errors by case and does not average unavailable cases into
performance.

## Experimental standing

Laya is experimental only. The local 2026-09-21 materialization proved Python 3.14.6, Torch
2.14.0+cu130, CUDA 13.0, and RTX 5060 execution, but high-cardinality target-selection and
target-domain calibration are not yet qualified.

Jev remains prospective for this provider-level duel because the current Jev route is physically
healthy but blocked by missing TYPESAFE_API_KEY.

No production Browser Capability Router route is changed by R1.
