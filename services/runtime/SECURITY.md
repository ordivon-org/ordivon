# Security Policy

> **Status**: Current — Docs-D5C
> **Owner**: ordivon-core-maintainer
> **Last verified**: 2026-05-14

## Scope

This document governs security for the Ordivon project: the governance OS core, verification tools, infrastructure configuration, and documentation. It does NOT govern:

- External services (PostgreSQL, NATS, Temporal, OpenFGA, MinIO) — each has its own security model.
- AI model providers (OpenAI, Anthropic, DeepSeek, etc.) accessed through LiteLLM.
- Downstream applications or adapters that use Ordivon governance.

## Reporting a Vulnerability

**Do NOT open a public issue for security vulnerabilities.**

1. Send an email to the repository owner with `[SECURITY]` in the subject line.
2. Include: affected component, steps to reproduce, impact assessment.
3. Expect acknowledgment within 7 days.
4. After a fix is confirmed, a disclosure timeline will be agreed upon.

The Ordivon project does NOT run a bug bounty program.

## Supported Versions

Only the `main` branch receives security patches. No backport releases. No LTS branches.

## Security Design Principles

These principles are **constitutional** — they derive from `policies/constitution.md` invariants 1, 2, 13:

### 1. Default-deny tool surface

Every tool, shell access, and external broker action is denied by default. Access must be explicitly granted through governance, with scope, rate limits, and side-effect classification. See `policies/constitution.md` §13.

### 2. Adapter isolation

Adapters (external integrations) may deliver evidence but must NOT write to state truth, create receipts, or emit audit events directly. All external data flows through the governance normalizer. See `policies/constitution.md` §12.

### 3. No model-as-authority

No intelligence provider output may directly alter state, create a receipt, write an audit event, or determine completion status. Models analyze and propose — the system decides. See `policies/constitution.md` §1.

### 4. Evidence immutability

Governance evidence (receipts, trace, logs) is written once and never mutated. Object storage (MinIO/S3) holds evidence blobs; PostgreSQL holds indexed references. Tampering is detectable through hash verification.

### 5. Graceful degradation

No security component is a hard gate. Every service has a documented fallback path. DEGRADED ≠ BROKEN. See `docs/architecture/adr/0005-graceful-degradation.md`.

## Secret Management

### What must never appear in the repo

- API keys (OpenAI, Anthropic, DeepSeek, LiteLLM)
- Database credentials (PostgreSQL URL)
- NATS, Temporal, OpenFGA, MinIO credentials
- Any token, password, or access key

### Where secrets live

Secrets are injected through environment variables and a `.env` file at the repository root. `.env` is **`.gitignore`-d** and must never be committed.

| Variable | Purpose | Format |
|----------|---------|--------|
| `ORDIVON_DB_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/ordivon` |
| `NATS_URL` | NATS connection | `nats://host:4222` |
| `TEMPORAL_HOST` | Temporal server | `host:7233` |
| `OPENFGA_API_URL` | OpenFGA API | `http://host:8080` |
| `MINIO_ENDPOINT` | S3-compatible endpoint | `host:9000` |
| `MINIO_ACCESS_KEY` | S3 access key | |
| `MINIO_SECRET_KEY` | S3 secret key | |
| `LITELLM_API_KEY` | LiteLLM master key | |

See `docs/operations/runbook.md` for startup and credential setup.

### CI secrets

GitHub Actions secrets are configured through the repository settings and never exposed in workflow files. CI uses `ORDIVON_DB_URL` for DB migration checks via GitHub Secrets.

## Dependency Management

### Tooling

- **Python**: `uv` for dependency resolution (`uv.lock` checked in, `pyproject.toml` as source).
- **Node**: Managed through `pnpm` (if applicable).
- **Infrastructure containers**: Docker images pinned to `sha256` digests in `docker-compose.infrastructure.yml`.

### Supply chain

- **Dependabot**: Enabled weekly for GitHub Actions, Python (uv), and Node (npm/pnpm). See `.github/dependabot.yml`.
- **Secret scanning**: Gitleaks runs in CI on every push to `main` and every PR. Hard gate — secrets in code block merge.
- **Image sources**: Infrastructure images pulled through `docker.m.daocloud.io` mirror (Docker Hub is blocked in China).

### Dependency audit process

1. Dependabot opens PRs on Mondays at 09:00 Asia/Shanghai.
2. Each PR must pass CI (ruff, governance checks, integration tests).
3. No auto-merge — human review required.
4. Critical security patches may be fast-tracked outside the weekly schedule.

## Infrastructure Security

| Component | Protocol | Authentication | Network |
|-----------|----------|---------------|---------|
| PostgreSQL | TCP 5432 | `scram-sha-256` password | Local-only (no port exposure) |
| NATS | TCP 4222 | Token-based | Local-only |
| Temporal | gRPC 7233 | None (local dev) | Local-only |
| OpenFGA | HTTP 8080 | Preshared key | Local-only |
| MinIO | HTTP 9000/9001 | Access key + secret key | Local + bucket policies |
| OPA | HTTP 8181 | None (local policy eval) | Local-only |

All infrastructure runs in Docker Compose with no port exposure to the host network except MinIO console (9001) for debugging — disabled in production configuration.

## Code Integrity

### Linting

`ruff` enforces Python lint rules and formatting on every PR. Config: `pyproject.toml`.

```bash
uv run ruff check src/ scripts/ tests/ state/
uv run ruff format --check --preview src/ scripts/ tests/ state/
```

### Governance checks

Every PR must pass:
- Document registry consistency (`scripts/check_document_registry.py`)
- Document governance verification (`python -m ordivon_verify document-governance --check`)
- Registry index check (`python -m ordivon_verify registry-index --check`)

### Signed commits

Not currently required. OpenFGA authorization model supports role-based review but commit signing is deferred to a future policy activation.

## Known Security Gaps

These are acknowledged gaps tracked in the debt ledger, not ignored vulnerabilities:

1. **Temporal authentication disabled** — local dev mode. Will require mTLS when Temporal is exposed beyond localhost.
2. **OPA runs as CLI, not server** — evaluated at invoke time, not deployed as a service. No authentication required in this mode.
3. **MinIO console exposed** — port 9001 accessible for debugging. Should be disabled in production.
4. **No SAST in CI** — CodeQL was considered but removed as non-applicable (Ordivon is Python governance infra, not C/Java/JS). Gitleaks covers secret detection.
5. **No network-level container isolation** — all services share a Docker network. Acceptable for local dev; needs network policy in production.

## Responsible Disclosure

If you believe you've found a security issue, you're encouraged to report it privately. The Ordivon project practices:

- **No retaliation** against good-faith reporters.
- **Coordinated disclosure** — the reporter and maintainer agree on a timeline.
- **Credit** — reporters are credited in the security advisory unless they request anonymity.

## Review Cadence

This document is reviewed at minimum every 90 days or after any infrastructure component change. Review updates the `last_verified` date in the document registry.
