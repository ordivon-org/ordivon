# Ordivon Flywheel And Pack Roadmap

Status: `current`
Authority: `source_of_truth`
Purpose: Define how Ordivon compounds from failures into reusable packs and external proof.
Supersedes: historical productization, moat, pack, and commercialization notes.
Verification: external pack pilots, receipt corpus, setup-friction measurements, runtime integration evidence.

## Flywheel

```text
failure
-> objectification
-> evidence and receipt
-> checker or policy
-> gate
-> pack template
-> cross-project reuse
-> methodology update
```

The moat is not one checker or one schema. The moat is a growing corpus of
governed failures, repair patterns, receipts, and packs that reduce future
ambiguity.

## Pack Strategy

Each pack must include:

- governed object vocabulary;
- claim and evidence templates;
- authority and owner rules;
- receipt and debt lifecycle;
- checkers or policy gates;
- red-team scenarios;
- adoption guide and minimal verification command.

Initial pack line:

- AI Agent Pack: tool calls, authority, observations, receipts, runtime traces.
- Research Claim Pack: claim extraction, evidence quality, overclaim checks.
- Repo Governance Pack: registry, current truth, generated-view boundaries.
- Runtime Receipt Pack: action traces, query-back observations, comparator
  receipts.
- Policy Promotion Pack: debt clusters, shadow results, replay, reviewer
  authority, rollout and rollback.

## External Proof Requirements

Dogfood is useful but not enough. External proof requires three different
project types:

- ordinary software repo;
- AI-agent workflow repo;
- research or analysis document repo.

For each pilot, measure setup time, concept load, false-positive rate,
failures converted into gates, receipts produced, debts closed with
verification receipts, and pack changes that become reusable.

## Runtime Direction

The long-term product direction is an Agent Trust Bus:

```text
agent intent
-> governance object
-> policy decision
-> bounded execution
-> trace / observed event
-> comparator receipt
-> debt / policy feedback
```

This bus does not replace agent frameworks. It governs the transition from
model output to action standing.

## Non-Goals For Certified V1

- no certification of destructive shell, email, delete, or production customer
  side effects;
- no claim of market moat from internal dogfood alone;
- no claim that AI can authorize closure, risk acceptance, or policy adoption;
- no latent-only execution path.

## What This Changes In Implementation

- Every pack must ship with negative fixtures, not just happy-path templates.
- External pilots must produce receipts and debts, not only testimonials.
- Pack promotion requires evidence of repeated failure pattern and reusable
  enforcement value.
- Runtime integrations must preserve the semantic firebreak: trace and tool
  result are inputs to governance, not automatic closure.
