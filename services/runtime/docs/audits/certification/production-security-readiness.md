# Production Security Readiness

Status: `current`
Authority: `source_of_truth`
Purpose: Index the current security-readiness evidence and remaining certification gaps for the Rust/Postgres trusted path.
Supersedes: `c0-worktree-audit-2026-05-17`, `c1-threat-model-2026-05-17`, `c7-certification-evidence-package-2026-05-17`.
Verification: Rust gates, Postgres integration gates, Python governance checks, security artifact generation script.

## Current Standing

The Rust/Postgres trusted path has reviewable security-readiness evidence, but
this document does not claim formal production security certification.

The current claim is narrower:

```text
The core Rust/Postgres governance path has hardening evidence suitable for
external review preparation.
```

Certified v1 remains out of scope for real destructive shell, email, delete,
broker, customer, or production-data side effects.

## Trusted Path

In scope:

- Rust kernel types and validated constructors;
- Postgres `kernel_*` ledger, projection, authority, adapter, policy,
  observation, receipt, debt, and red-team tables;
- signed authority tokens;
- policy decision evidence;
- Postgres mock/sandbox adapter;
- comparator receipts and debt lifecycle;
- red-team runner and dogfood seal generation.

Out of scope:

- real destructive adapters;
- customer production data;
- UI console security;
- SOC2, ISO, or regulatory certification claims.

## Evidence Index

- `docs/audits/certification/c0-dirty-worktree-inventory.json`
- `docs/audits/certification/reviewsets/kernel-core.pathspec`
- `docs/audits/certification/reviewsets/repo-ci-security.pathspec`
- `docs/audits/certification/reviewsets/unrelated-large-rewrite.pathspec`
- `scripts/security/generate_cert_evidence.sh`
- ignored local artifacts under `artifacts/security/`

Expected gates:

```bash
cargo fmt --all --check
cargo clippy --workspace --features postgres-integration,policy-http --all-targets -- -D warnings
cargo test --workspace
ORDIVON_MIGRATION_DATABASE_URL=... ORDIVON_APP_DATABASE_URL=... ORDIVON_TEST_ADMIN_DATABASE_URL=... cargo test --workspace --features postgres-integration,policy-http
PYTHONPATH=.:src .venv/bin/python -m pytest -q
PYTHONPATH=.:src .venv/bin/python scripts/check_document_registry.py
PYTHONPATH=.:src .venv/bin/python scripts/verify_infrastructure.py
```

## Remaining Certification Gaps

- Worktree is still not externally reviewable until large unrelated deletion
  sets are isolated or accepted in separate review.
- DB append-only proof still needs independent migration/app/test-admin role
  permission tests against real roles.
- Dogfood seal has digest binding; full Ed25519/DSSE key rotation and
  revocation evidence must remain active in tests and release artifacts.
- OPA/OpenFGA policy decision evidence must be attached to every dispatch path
  before any real adapter certification.
- Production adapter sandbox is not certified for destructive actions.
- Local supply-chain tools may be absent; CI and generated artifact summaries
  must record equivalent evidence.

## Failure Modes That Must Stay Covered

- AI-forged observation;
- token replay;
- wrong target;
- duplicate dispatch;
- ack-as-success;
- ledger tamper;
- projection drift;
- policy promotion bypass;
- closure without verification;
- suppression without expiry;
- compromised adapter source;
- wrong dispatch observation;
- delayed or duplicate observation;
- query-back mismatch.

## What This Changes In Implementation

- Security docs must index evidence and gaps, not announce completion.
- Red-team scenarios are hard gates, not appendices.
- Successful dispatch requires authority use, policy decision, ledger event,
  adapter dispatch, observation, comparator receipt, and debt behavior.
- Generated security artifacts are evidence references; large artifact bodies
  stay out of source unless explicitly required.
