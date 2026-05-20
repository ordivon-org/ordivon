# Ordivon

Ordivon is an executable epistemology governance system for the AI era.
It prevents AI-generated fluency from becoming unearned authority.

## Canonical Documents

1. [Ordivon Core — Refrozen](docs/ai/ordivon-core-refrozen.md)
2. [Governance Control Loop](docs/architecture/ordivon-governance-control-loop.md)
3. [Semantic Firebreak](docs/architecture/semantic-firebreak.md)
4. [Runtime Governance Alignment](docs/architecture/runtime-governance-alignment.md)
5. [AI-Native Project Object Model](docs/architecture/ai-native-project-object-model.md)
6. [Skill Scope Freeze](docs/architecture/ordivon-core-method-skill-scope.md)
7. [Flywheel and Pack Roadmap](docs/product/ordivon-flywheel-and-pack-roadmap.md)
8. [Production Security Readiness](docs/audits/certification/production-security-readiness.md)

## Core Method

[ordivon-core-method](skills/ordivon-core-method/SKILL.md) — a governance skill that
teaches AI agents to separate claims from evidence, frame execution, classify debt,
and draft honest receipts. Status: ACTIVATED.

## Verification

```bash
# Python
uv sync --extra dev
PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/
PYTHONPATH=.:src .venv/bin/python scripts/check_document_registry.py
PYTHONPATH=.:src .venv/bin/python -m ordivon_verify all --check
PYTHONPATH=.:src .venv/bin/python scripts/verify_infrastructure.py

# Rust
cargo test --workspace

# Infrastructure
docker compose -f docker-compose.infrastructure.yml up -d
```

`READY`, `PASS`, or `CLOSED` never authorizes merge, release, deployment,
policy activation, or external action.
