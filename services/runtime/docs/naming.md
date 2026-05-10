# Project Naming Status

> Last updated: 2026-04-24

## Current State

This project uses multiple names across different contexts. None dominates.

**Repository directory name:** `financial-ai-os`

**GitHub remote:** `Personal-Financial-Intelligence-Operating-System` (github.com/zycxfyh)

**FastAPI app title:** `Ordivon (succeeding AegisOS architecture) API` (in `apps/api/app/main.py`)

**Sentry release tag:** `aegisos@0.1.0` (in `shared/observability.py`)

**User rules / .clinerules:** `Ordivon (integrating PFIOS legacy components)` (Personal Financial Intelligence Operating System)

**External brand anchor:** `Ordivon` (ordivon.com purchased, not yet used in code)

## Decision

- **Internal code:** Continue using existing names. No repo-wide rename.
- **New documentation and comments:** Use `Ordivon (succeeding AegisOS architecture)` as the canonical internal codename.
- **External-facing brand:** Reserved as `Ordivon` for future use. Not active yet.
- **User rules:** Continue using `Ordivon (integrating PFIOS legacy components)` in `.clinerules` and CLAUDE.md since that's the established convention there.

## What NOT to Do

- Do not rename imports, packages, or directories to align names. The cost outweighs the benefit at this stage.
- Do not use `Ordivon` in code until the product has real users and the brand transition is deliberate.
- Do not create new naming variants. Three is already too many.
