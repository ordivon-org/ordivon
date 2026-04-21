# Capability Layer

`capabilities/` holds product-facing semantic boundaries, not generic page helpers.

## Directory Map

- `domain/`: stable object capabilities such as `recommendations`
- `workflow/`: multi-step business actions such as `analyze` and `reviews`
- `view/`: product aggregates and artifact listings such as `dashboard`, `reports`, and `audits`
- `diagnostic/`: technical and governance-facing reads such as `evals` and `validation`
- `contracts/`: contract dataclasses grouped by abstraction type

Top-level modules remain as compatibility wrappers so existing imports keep working while the filesystem reflects the classification.

## Naming Rules

- Name capabilities after a domain object or business action first.
- Do not create new page-driven capabilities.
- Avoid `*And*` method names that hide orchestration inside one capability method.
- Reads that return view aggregates or diagnostics must be named and documented as such.
- Side-effecting methods must require `actor`, `context`, `reason`, and `idempotency_key`.

## Current Classification

- `analyze`: workflow composite contract
- `recommendations`: domain object capability
- `reviews`: workflow capability
- `dashboard`: view aggregate
- `reports`: view artifact listing
- `audits`: view record listing
- `evals`: diagnostic read adapter
- `validation`: diagnostic summary plus bounded issue intake
