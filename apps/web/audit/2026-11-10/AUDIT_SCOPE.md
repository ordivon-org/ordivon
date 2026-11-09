# AUDIT_SCOPE — existing-source modernization R1
Date: 2026-11-10 (Asia/Shanghai). SourceCut: ef17d6879d12faa61fff3bb762b0d500d73c9113.
Scope: all tracked files mechanically inspected; full semantic code review is focused on the natural Web Owner. The other 20 declared Owners are being audited in parallel and are NOT marked semantically complete here. This file is a task-local audit record, not another root architecture authority.

## Current repository & owners
The physical source is ONE monorepo, not 21 independent repositories. Source roots are services/, platform/, capabilities/, catalogs/, domains/, packages/, apps/, extensions/, studies/, tools/ and docs/. Owner paths and native verify tasks come from tools/repo/owners.toml (schema_version=1): 21 named Owners; source regions remain navigation only. There is no tracked standalone computing/ Owner root; do not invent it. Scientific research remains source-scoped, rather than falsely classifying all studies as Computing-owned.
The Web owner is apps/web/; package.json version 0.1.0, private ESM, Node 26.12.1, pnpm 12.16.1, TypeScript 7.0.2. Its planning/lego-plan-r1.json schemaVersion=1 is a planning projection, not an admitted physical LEGO or installed proof. WebStore bootstrap is an unversioned local canary SQLite CREATE TABLE IF NOT EXISTS schema; this is not a PostgreSQL cutover task. Host source services/host/src/ordivon_host_v2/service.py has REQUIRED_SCHEMA_VERSION=13 and migrations/versions/0013_unicode_substring_gin.py; the dated root program still describes a historical schema 11 production snapshot.

## Scope & non-goals
IN: source ownership, naming, imports, command entrypoints, dependency boundaries, dead/redundant candidates, contract/currentness drift, pure existing-behavior repair and Owner-native verification.
OUT: new features, any new tests or test infrastructure, new consumer chains, production installation, runtime effects, new hook systems, universal owner/LEGO registry, Nx/Turbo migration, PostgreSQL substitution for the Web canary.
Historical records and source-level plans are retired only after checking current static and potential dynamic consumers; do not equate absence of grep matches with a proof of non-consumption.

## Execution governance
Observe baseline and existing branches first; apply criteria in MODERN_CRITERIA; propose smallest subtraction/fix with exact file and risk; use existing Web native verification and Repo architecture/boundary checks; Git revert restores each source edit; use protected GitHub PR. Social review is optional evidence rather than source authority.
Exact machine-readable full-repository baseline is INVENTORY_FILES.tsv (5002 paths and digest); it is a historical audit snapshot, NOT a second source registry.
