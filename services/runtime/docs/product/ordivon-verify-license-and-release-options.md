# Ordivon Verify — License and Release Options

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-11
Tags: `product`, `verify`, `license`, `open-source`, `proposal`
Authority: `proposal`

## 1. Purpose

Compare license and release options for the future public Ordivon Verify repository. No license is activated or finalized by this document.

## 2. Options

### MIT

- **Permissive**: anyone can use, modify, distribute, sublicense
- **No patent grant**: weaker for commercial tooling
- **Simple**: one short file, widely understood
- **Risk**: commercial forks could close-source improvements

### Apache-2.0

- **Permissive + patent grant**: explicit patent license from contributors
- **Stronger for tools**: better protection for users against patent claims
- **Slightly longer**: includes patent retaliation clause
- **Common**: used by Kubernetes, TensorFlow, many CNCF projects

### Business Source License (BSL)

- **Source-available, not open-source**: code is visible but use is restricted
- **Converts to open-source after a date**: e.g., BSL → Apache-2.0 after 4 years
- **Protects commercial interest**: prevents SaaS competition during exclusivity period
- **Examples**: CockroachDB, Sentry (previously), Materialize

### Private Beta First

- **No license yet**: shared under private beta agreement
- **Gated access**: early adopters sign agreements
- **Flexibility preserved**: license chosen after feedback
- **Slower adoption**: requires relationship management

### Dual License

- **Open-source + commercial**: e.g., AGPL for community, commercial for enterprise
- **Complex**: two sets of rights, contributor agreements needed
- **Examples**: MongoDB (SSPL), GitLab (MIT + EE)
- **Premature for prototype**: requires legal infrastructure

## 3. Recommended Preliminary Stance

| Aspect | Recommendation |
|--------|---------------|
| Main Ordivon repo | **Remain private.** No license. |
| Public Ordivon Verify repo | **Apache-2.0** (recommended, not activated) |
| Why Apache-2.0 over MIT | Patent grant protects users. Explicit contributor license. |
| Why not BSL now | Too restrictive for a first product wedge. Slows adoption. |
| Why not dual license now | Premature. Legal overhead not justified. |
| Defer decision? | Final license decided at public repo creation, not before. |

## 4. License Activation Gate

A license is **not activated** until:

- Public repo is created
- LICENSE file is committed
- Package is published
- All pre-activation blockers are cleared

This document is a recommendation, not a decision.

## 5. Non-Activation Clause

No license is applied to any repository by this document. Main Ordivon remains private. Ordivon Verify remains private beta candidate. No package is published.
