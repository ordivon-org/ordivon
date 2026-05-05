# Agent-Native Evidence Surfaces 2026

Status: **CURRENT** | Date: 2026-05-05 | Phase: GWOS-2026-P4
Tags: `agent-native`, `skills`, `memory`, `harness`, `mcp`, `read-only`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

Agent runtimes are making traces, checkpoints, skills, memory records, tools,
hooks, and protocol manifests first-class work artifacts. Ordivon should verify
their evidence boundaries without becoming the runtime.

This document defines the Phase 4 read-only import surfaces.

## Non-Goals

Ordivon does not:

- run agents.
- call tools.
- start MCP servers.
- refresh tokens.
- modify remote systems.
- approve execution.
- publish SDK/API compatibility claims.

## Surfaces

### Skill Safety Review

Inputs:

- `SKILL.md`.
- frontmatter metadata.
- scripts/templates/resources referenced by the skill.
- allowed-tools or tool permission declarations.
- protected credential, network, file, shell, or action language.

Checks:

- skill capability is not permission.
- scripts are declared and bounded.
- protected credential-seeking language is blocked or clearly marked unsafe.
- advice/recommendation is not written as approval.
- no action authorization language appears.

### Memory / Content Hygiene

Inputs:

- memory note.
- content registry entry.
- source receipt.
- freshness marker.
- project scope marker.

Checks:

- memory has source evidence.
- stale memory is not cited as current authority.
- cross-project memory is not imported silently.
- CandidateRule remains advisory; Policy activation remains separate.
- DEGRADED or BLOCKED signal is not rewritten as clean fact.

### Harness Evidence Import

Inputs:

- trace.
- checkpoint.
- tool-call log.
- review record.
- execution receipt.

Checks:

- failed tool call remains present.
- human review occurs at the claimed node.
- checkpoint does not imply approval.
- trace presence is not truth.
- receipt status does not authorize external action.

### MCP Boundary Review

Inputs:

- server manifest.
- resource/audience wording.
- authorization notes.
- token handling description.

Checks:

- tool available is not permission.
- token passthrough is flagged.
- audience/resource confusion is flagged.
- confused-deputy risk is named when relevant.
- no real token is read, generated, refreshed, or transmitted.

## Case Fixture Plan

| Surface | Clean fixture | Red-team fixture |
|---|---|---|
| skill | bounded read-only skill | forbidden credential-seeking skill with approval language |
| memory | fresh sourced memory | stale cross-project memory cited as current truth |
| harness | complete trace with review | checkpoint claims approval but omits failed tool call |
| MCP | bounded manifest | token passthrough/audience confusion language |

## Boundary

Agent evidence import is evidence hygiene only. It is not runtime guardrail
coverage, action approval, framework certification, public platform readiness,
or adapter release permission.
