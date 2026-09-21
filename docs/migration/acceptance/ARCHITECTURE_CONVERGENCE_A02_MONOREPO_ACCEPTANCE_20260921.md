# Architecture Convergence A02 — Modular Monorepo Acceptance

Date: 2026-09-21
Status: ACCEPTED

## Frozen observation

Monorepo source:
- repository: `/root/projects/ordivon`
- observed revision: `a5e9f1d9302a6b60d59d6cdd043dc8aa56ad4f65`

The repository declares itself the primary Ordivon source monorepo.

## Accepted substrate

```text
ordivon/
├── services/{runtime,host,harness}
├── platform/{network,security,workstation}
├── capabilities/{artifact,distribution,media,preservation}
├── domains/{capital,game}
├── meta/next
├── docs
└── tools
```

The root owns repository mechanics only. Owner-local environments, lockfiles, releases, durable state, deployment authority, and scientific acceptance remain independent.

## Source migration standing

Existing acceptance records establish source-only migration for Next/Security/Network, Workstation/Media/Artifact, Game/Capital/Host, Harness, Runtime, Distribution, Preservation, and Creative Library projection.

Research is deliberately not flattened:

- shared Research layer: PROFILE_ONLY_NO_CODE_IMPORT;
- Paper1: ARCHIVED_IN_PLACE;
- Paper2: KEEP_INDEPENDENT_ACTIVE;
- Paper3: HOLD_EXTRACTION_UNTIL_FREEZE.

This is consistent with Modular Monorepo: source co-location does not merge semantic authority.

## Remaining work is not substrate creation

A02 does not create another monorepo or relocate owners again. Standalone repositories can remain recoverable source carriers until their separate retirement gates are accepted. New architecture work lands directly under the natural owner in this monorepo.

## Acceptance

- primary source monorepo exists — PASS;
- natural-owner directories exist — PASS;
- owner-local lockfiles/build systems remain separate — PASS;
- root does not redefine owner truth — PASS;
- identity/history migration receipts exist — PASS;
- active scientific authority is not forcibly merged — PASS;
- source relocation is separate from semantic refactoring — PASS.

Verdict: **A02 COMPLETE.**
