# Ordivon

Ordivon is an execution-grade governance kernel for agentic AI.

After the 2026-05-17 document reset, canonical authority is intentionally small:

1. [Core thesis](docs/ai/ordivon-core-thesis.md)
2. [Governance control loop](docs/architecture/ordivon-governance-control-loop.md)
3. [Semantic firebreak](docs/architecture/semantic-firebreak.md)
4. [Runtime governance alignment](docs/architecture/runtime-governance-alignment.md)
5. [Flywheel and pack roadmap](docs/product/ordivon-flywheel-and-pack-roadmap.md)
6. [Production security readiness](docs/audits/certification/production-security-readiness.md)

Other files are supporting evidence, machine records, receipts, schemas, or
operational material. If they conflict with the documents above, the canonical
documents win unless a newer signed receipt says otherwise.

## Current Direction

Ordivon is not a chat product, trading bot, generic dashboard, or model wrapper.
It is a control plane for high-consequence actions:

```text
Reality -> Declaration -> Object -> Evidence -> Authority -> Gate
        -> Execution -> Receipt -> Reconciliation -> Debt/Policy
```

Core commitments:

- No Receipt, No Done.
- No Authority, No Side Effect.
- Text must not directly move state.
- AI_WRITTEN never upgrades itself to SYSTEM_OBSERVED.
- Append-only governance ledger is the canonical history.
- PostgreSQL carries ledger/projections; NATS is transport, not audit truth.
- Comparator verdicts are deterministic; LLMs may explain, not judge.

## Working Commands

```bash
uv sync --extra dev
PYTHONPATH=.:src .venv/bin/python -m pytest -q
PYTHONPATH=.:src .venv/bin/python scripts/verify_infrastructure.py
PYTHONPATH=.:src .venv/bin/python scripts/check_document_registry.py
PYTHONPATH=.:src .venv/bin/python -m ordivon_verify all --check
cargo test --workspace
ORDIVON_TEST_DATABASE_URL=postgresql://ordivon:ordivon@localhost:5432/ordivon \
  cargo test --workspace --features postgres-integration,policy-http
```

`READY`, `PASS`, or `CLOSED` never authorizes merge, release, deployment,
policy activation, broker writes, or external action.
