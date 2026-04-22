# Adapter Boundary Spec v1

## Status

This document freezes the first explicit adapter-boundary rules for PFIOS platformization.

It complements:

- [Core / Pack / Adapter Baseline](./core-pack-adapter-baseline.md)
- [Current Code Classification Map v1](./current-code-classification-map-v1.md)
- [Core Primitives Spec v1](./core-primitives-spec-v1.md)

## Purpose

PFIOS already depends on external implementations for:

- model/runtime execution
- storage backends
- report and wiki writes
- tool and connector behavior

Without explicit adapter boundaries, the next drift pattern would be:

- external implementation details leaking into system semantics
- domain packs depending directly on provider quirks
- provider/backend changes forcing core rewrites

This document defines the adapter rule set that prevents that drift.

## One-Sentence Rule

Adapters may implement system contracts.

Adapters may not define system meaning.

## What An Adapter Is

An adapter is a replaceable implementation boundary that connects PFIOS semantics to an external or implementation-specific system.

An adapter is valid when:

- the system semantic remains stable if the implementation changes
- the integration can be swapped without redefining `core`
- the adapter consumes a contract instead of inventing one

## Adapter Classes

PFIOS should currently recognize four adapter classes.

### 1. Runtime adapters

Examples:

- Hermes bridge
- provider integrations
- model-runtime clients

### 2. Execution adapters

Examples:

- wiki/report writers
- notifications
- connector-backed external side effects
- tool transport layers

### 3. Storage adapters

Examples:

- DuckDB backend
- future PostgreSQL backend
- blob/vector backends

### 4. Knowledge adapters

Examples:

- external research sources
- ingestion connectors
- future external knowledge system bridges

## Adapter Responsibilities

Adapters may:

- translate contracts into implementation calls
- normalize implementation output into bounded results
- handle auth, transport, backend configuration, and protocol-specific details
- expose health and availability of the integrated implementation
- return honest failure when the implementation is unavailable or invalid

Adapters must not:

- create new system truth semantics
- redefine domain meaning
- bypass governance or execution discipline
- silently fill missing state with implementation assumptions
- leak provider/backend nouns into `core`

## Required Adapter Shape

Every meaningful adapter should eventually expose the following shape.

### 1. Input contract

The adapter must consume a bounded contract defined by `core` or a domain pack.

Examples:

- runtime task request
- execution action request
- storage read/write interface
- knowledge ingestion request

### 2. Output contract

The adapter must return a bounded normalized result.

Examples:

- runtime task result
- execution result payload
- storage write/read result
- ingestion result

### 3. Error discipline

The adapter must return honest failure and preserve useful detail.

It must not:

- fabricate success
- silently coerce missing implementation behavior into healthy state
- overwrite system semantics because the external system is awkward

### 4. Health surface

Where the adapter is operationally meaningful, it should expose health or availability in bounded form.

Examples:

- runtime health
- monitoring snapshot inputs
- storage availability

### 5. Replaceability

The adapter boundary should allow implementation swap without rewriting domain semantics.

## Current Repository Mapping

### Runtime adapters

| Current Path | Classification | Reason |
| --- | --- | --- |
| `projects/hermes-runtime/hermes_cli/pfios_bridge.py` | Adapter | transport bridge to runtime implementation |
| `intelligence/providers/hermes_agent_provider.py` | Adapter | provider-specific runtime integration |
| Hermes-specific sections of `intelligence/runtime/` | Adapter | transport/auth/provider-specific behavior |

### Execution adapters

| Current Path | Classification | Reason |
| --- | --- | --- |
| concrete report/wiki write paths in execution flows | Adapter | external artifact writing implementation |
| `tools/` integrations | Adapter | execution-side tool transport and helper logic |
| `skills/` that act as execution helpers | Adapter | implementation support rather than system semantics |

### Storage adapters

| Current Path | Classification | Reason |
| --- | --- | --- |
| `state/db/` | Adapter | backend bootstrap and DB implementation wiring |
| future Postgres backend | Adapter | same semantics, different backend |
| file/blob storage bridges | Adapter | implementation-specific persistence |

### Knowledge adapters

| Current Path | Classification | Reason |
| --- | --- | --- |
| `knowledge/ingestion/` | Adapter | external source integration |
| future external research connectors | Adapter | implementation-specific source transport |

## Adapter Boundary Rules

### Rule 1: adapters consume contracts, not raw domain improvisation

If an adapter needs a shape, that shape should be defined by `core` or a domain pack first.

### Rule 2: adapters may translate, but not reinterpret domain meaning

For example:

- a runtime adapter may translate task request structure
- it may not redefine what a recommendation or review means

### Rule 3: adapters must fail honestly

If the external system is unavailable:

- return unavailable
- record failure honestly
- do not produce healthy-looking fabricated state

### Rule 4: adapters must not become hidden policy engines

Provider limitations, transport quirks, or backend shortcuts must not silently redefine governance or state rules.

### Rule 5: adapters must stay swappable

If Hermes is replaced, or DuckDB is replaced, the surrounding semantics should still hold.

## Boundary Examples

### Example 1: Hermes runtime

Correct boundary:

- `core` defines task/runtime contracts
- finance pack defines current analysis task meaning
- Hermes adapter executes the runtime call

Incorrect boundary:

- Hermes payload shape defines what an analysis task is

### Example 2: DuckDB storage

Correct boundary:

- `core` defines truth/trace/request-receipt semantics
- storage adapter persists them in DuckDB

Incorrect boundary:

- DuckDB limitations redefine trace or execution semantics

### Example 3: Report writing

Correct boundary:

- execution/request-receipt semantics stay system-owned
- adapter performs the actual file/wiki write

Incorrect boundary:

- the file writer becomes the semantic owner of artifact truth

## Current Immediate Adapter Problems

These are the most important current boundary risks.

### Risk 1

Parts of `intelligence/` still mix:

- runtime contracts
- provider adapters
- task/domain shaping

### Risk 2

Parts of `state/db/` still act as both:

- backend implementation
- structural foundation

### Risk 3

Some execution flows still expose implementation details before there is a clearer generic adapter interface.

### Risk 4

Some knowledge ingestion/retrieval areas may drift into domain semantics if adapter boundaries are not frozen early.

## First Adapter Extraction Targets

### Target 1: runtime adapters

Separate:

- provider-neutral runtime contracts
- Hermes-specific transport/provider behavior

### Target 2: storage adapters

Separate:

- reusable state persistence contracts
- DuckDB-specific bootstrap/backend behavior

### Target 3: artifact and connector adapters

Separate:

- request/receipt semantics
- concrete file/wiki/notification/tool implementation

### Target 4: knowledge source adapters

Separate:

- knowledge ingestion/retrieval primitives
- external source integrations

## Non-Goals

This spec does not:

- require every helper to become an adapter
- require immediate directory renames
- require the repository to stop using current implementations
- claim current adapters are already cleanly isolated

## Final Summary

Adapters are where implementation changes are allowed.

They should translate:

- runtime providers
- storage backends
- execution transports
- external knowledge sources

They must not define:

- governance meaning
- domain meaning
- truth semantics
- product semantics

Compressed:

**Adapters implement contracts. Core defines contracts. Packs define domain meaning.**
