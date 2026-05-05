---
gate_id: protected_paths
display_name: Protected Paths Detection
layer: L5E
hardness: hard
purpose: Detect references to protected paths in docs that lack proper boundary qualification
protects_against: "Unqualified .env references, secrets/ mentions without NO-GO, pyproject.toml change suggestions without explicit justification"
profiles: ['full']
timeout: 60
tags: [coding, protected-paths, security, boundary]
---

# Protected Paths Checker

## Purpose

Scans documentation for references to protected file paths (`.env`, `secrets/`,
`pyproject.toml`, lock files) that appear WITHOUT proper boundary qualification
(`NO-GO`, `not allowed`, `protected`, `governed`, `forbidden`).

## Protected Paths

- `.env`, `secrets`, `private_key`, `credentials`
- `pyproject.toml`, `uv.lock`, `package.json`, `pnpm-lock.yaml`
- `state/db/migrations/runner.py`

## Safe Context

If the reference appears WITH a boundary qualifier (not allowed, NO-GO,
protected, governed), it's describing the boundary — not suggesting a violation.
