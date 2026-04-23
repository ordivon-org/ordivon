# AegisOS MVP Brief

## MVP Definition

The current AegisOS MVP is:

> a single-agent, single-mainline, finance-seed, governance-aware workflow where a user can clearly complete the analyze -> recommendation -> review chain through the product surfaces.

This is not the full future AegisOS platform. It is the current minimum deliverable product.

## Primary User Journey

The MVP gold path is:

`homepage -> quick analyze -> /analyze -> result / recommendation -> /reviews`

This path is the center of the product. Other pages and surfaces should support it rather than compete with it.

## Page Roles

### `/`

Command center for:

- system status
- recommendation previews
- pending review previews
- reports and diagnostics
- quick analyze entry

It is not the deep-work page for supervision.

### `/analyze`

Execution workspace for:

- entering a workflow request
- auto-seeded runs from homepage
- immediate reasoning and governance inspection
- handing off to the next surface

It is not the review queue or system monitoring center.

### `/reviews`

Supervision workbench for:

- pending review queue
- recommendation follow-through
- supporting trace and outcome inspection

It is the default deep-work page for supervision-needed objects.

## What The MVP Demonstrates

The MVP proves that AegisOS can:

- run a governed analyze workflow
- produce a recommendation object
- route that object into supervision work
- keep truth, hint, and outcome semantics distinct
- expose the chain through a supervisor-facing workspace

## What The MVP Does Not Claim Yet

The MVP does not claim:

- multi-pack maturity
- multi-runtime maturity beyond the current adapter baseline
- full long-running ambient orchestration
- complete knowledge flywheel behavior
- production-complete AI workflow platform operation

Those are next-stage platform concerns, not MVP promises.

## Engineering Gate

The MVP delivery gate includes:

- GitHub Actions CI
- `backend-unit`
- `backend-integration`
- `frontend`
- `mvp-e2e`

The repository also includes a `Delivery` workflow that assembles the current MVP delivery bundle from the validated `main` branch state.

The intended repository gate on GitHub is:

- pull request required before merge
- required status checks must pass
- branch must be up to date before merge

Repository settings must match those checks for MVP delivery to be considered complete.

## Current Delivery Readiness Standard

The MVP should be considered ready when:

1. the gold path can be followed without guesswork
2. page ownership is clear and non-overlapping
3. recommendation -> review continuation is object-aware
4. frontend finance defaults do not leak through generic UI ownership
5. missing or unavailable states remain honest
6. README and state docs describe the same current product truth
7. CI, E2E, and delivery workflows are active and stable
8. branch checks are active and stable
