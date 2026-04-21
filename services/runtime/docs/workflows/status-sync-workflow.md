# Status Sync Workflow

## Purpose

This workflow defines how repository state documents must be updated after each completed module.

The goal is simple:

- the codebase stays traceable
- status docs do not drift behind implementation
- historical reports remain readable
- future work can always begin from current truth instead of conversation memory

## When To Run This Workflow

Run this workflow every time a module is marked `Done`.

Do not wait for a large batch if the module meaningfully changes:

- current system behavior
- current priority order
- current active modules
- current product surface truthfulness
- current governance / execution / trace / knowledge reality

## What Counts As A Status Document

For this repository, the required status-sync surfaces are:

1. `knowledge/wiki/architecture/module-cards/`
   - every module needs a design confirmation card
2. `docs/architecture/layer-module-inventory.md`
   - the module execution map
3. `docs/architecture/current-state-report-YYYY-MM-DD.md`
   - the dated current-state snapshot
4. `docs/tasks/README.md`
   - the current execution queue

Update these four first.

Only after that, update broader architecture docs if the module changed canonical understanding:

5. `docs/architecture/architecture-baseline.md`
6. other architecture docs that explicitly contain current-state or current-priority language

## Required Update Order

Use this order after every completed module:

### 1. Freeze The Module Card

Write or update the module card in:

- `knowledge/wiki/architecture/module-cards/`

The card must include:

- Module
- Layer
- Role
- Current Value
- Remaining Gap
- Immediate Action
- Required Test Pack
- Done Criteria
- Next Unlock
- Not Doing

### 2. Update The Module Inventory

Update:

- `docs/architecture/layer-module-inventory.md`

Required changes:

- move the module into the latest completed sync block
- remove it from the active queue
- update the next active modules list
- adjust status and priority if the module meaningfully changed another layer

### 3. Update The Current-State Report

Create a new dated report when the repository meaningfully changed current reality.

Use:

- `docs/architecture/current-state-report-YYYY-MM-DD.md`

Rules:

- do not silently overwrite historical dated reports as if they were still current
- keep older reports as historical snapshots
- mark the previous report as superseded if necessary
- the newest dated report is the current operational snapshot

### 4. Update The Task Queue

Update:

- `docs/tasks/README.md`

Required changes:

- move completed modules into the completed block
- update the next priority batch
- remove modules that are no longer active

### 5. Update Canonical Baseline Only If Needed

Update:

- `docs/architecture/architecture-baseline.md`

Only when the module changes canonical truth such as:

- layer maturity
- current priority order
- governance / execution / knowledge boundaries
- what is now considered real in the main chain

## What Not To Use As Status Sync

Do not treat these as the source of truth for current module state:

- chat history
- terminal scrollback
- audit logs
- runtime logs
- ad-hoc TODO comments

Logs are historical evidence, not the status index.

## Required Traceability Guarantees

After a module is complete, a reader should be able to answer all of these from docs alone:

1. what changed
2. which layer changed
3. what is now true in code
4. what is still missing
5. what module should come next
6. where the design card lives

If those answers are not visible, the status sync is incomplete.

## Minimum Completion Checklist

Before marking a module complete, confirm:

- module card exists in wiki
- tests passed
- `layer-module-inventory.md` is updated
- the latest current-state report reflects the new reality
- `docs/tasks/README.md` reflects the new queue
- any materially outdated baseline wording is corrected

## Historical Discipline

Use this rule:

- historical logs stay untouched
- historical dated reports stay readable
- current status lives in the latest dated report plus the live module inventory

That keeps the repo traceable without rewriting history.
