# AegisOS Working Identity

## Status

This document freezes the current working naming convention for the system while the repository and historical documentation still retain legacy naming.

## Naming Rule

Use the following working names from this point forward:

- working product name: `AegisOS`
- legacy repository lineage: `PFIOS`
- internal architectural shorthand: `CAIOS`

## Repository Naming Reality

The repository, codebase, and many historical documents still use:

- `PFIOS`
- `financial-ai-os`

That remains acceptable for now.

## Brand Transition Note

`Ordivon` is treated as a future external brand anchor only.

Phase 4 does not perform a repo-wide rename. It does not change import paths, package names, environment-variable lineage, or historical document references just to force brand consistency ahead of behavior.

The working rule is:

- keep `AegisOS` as the current working product/system identity
- preserve `PFIOS` where repository continuity still depends on it
- allow `Ordivon` only as a forward-looking external brand note in docs, not as a codebase-wide rename target

## Practical Usage Rules

### Use `AegisOS` when:

- describing the current product/system
- writing current architecture and execution docs
- describing the present working identity

### Use `PFIOS` when:

- referring to repository lineage
- referring to current repository paths, env vars, and compatibility naming
- explaining historical continuity

### Use `Ordivon` when:

- discussing future external branding only
- explicitly noting that the brand transition is deferred

## Current Interpretation

At this stage:

- `AegisOS` is the working product/system identity
- `PFIOS` is the repository and historical lineage
- `Ordivon` is a deferred external brand anchor, not a rename mandate
