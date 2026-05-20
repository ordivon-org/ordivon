# Security Policy

## Reporting a Vulnerability

Do NOT open a public issue. Email the repository owner with `[SECURITY]` in subject.
Include: affected component, steps to reproduce, impact assessment.
Acknowledgment within 7 days.

## Supported Versions

Only `main` branch. No backports. No LTS.

## Design Principles

1. **Default-deny tool surface** — tools denied by default, explicitly granted
2. **Adapter isolation** — external data flows through governance normalizer
3. **No model-as-authority** — AI proposes, system decides
4. **Evidence immutability** — receipts written once, never mutated
5. **Graceful degradation** — DEGRADED ≠ BROKEN, every service has fallback

## Infrastructure Security

| Component | Auth | Network |
|-----------|------|---------|
| PostgreSQL | scram-sha-256 | Local-only |
| NATS | Token | Local-only |
| Temporal | None (local dev) | Local-only |
| OPA | CLI eval (not server) | N/A |

## Known Security Gaps

1. Temporal authentication disabled — local dev mode
2. OPA runs as CLI, not server — no auth required
3. No SAST in CI — Gitleaks covers secret detection
4. No network-level container isolation — acceptable for local dev
5. 4 Rust dependency vulns tracked by CI cargo-deny

## Supply Chain

- Dependabot: weekly for GitHub Actions, uv
- Gitleaks: CI hard gate
- Docker images: pinned digests via `docker.m.daocloud.io` mirror
- Python: uv.lock committed, pyproject.toml as source
