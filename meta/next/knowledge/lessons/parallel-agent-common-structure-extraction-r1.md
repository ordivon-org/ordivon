# Parallel Agent Common-Structure Extraction R1

Status: **ACTIVE METHOD / FIRST CAMPAIGN LAUNCHED**
Registered: 2026-09-14

## Purpose

When studying a broad project family or heterogeneous corpus, do not rely on one Agent serially reading sources and then declaring the common structure.

Use independent parallel observations first, then synthesize only after the independent evidence exists.

## Method

```text
source/corpus
   ↓
WAVE 1: independent parallel analysis
   ├─ product-family roles
   ├─ mechanism roles
   └─ falsifier/provenance role
   ↓
normalize reports into common evidence schema
   ↓
WAVE 2: synthesis
   ├─ common primitive extraction
   ├─ unique mechanism extraction
   ├─ natural-authority mapping
   └─ confidence / counterevidence
   ↓
WAVE 3: destructive review
   ├─ false-commonality attack
   ├─ selection-bias attack
   └─ architecture-boundary attack
   ↓
canonical lesson / provider routing update
```

## Why product-family and mechanism roles both matter

Product-family roles preserve local architecture and prevent the analysis from flattening systems too early.

Mechanism roles ignore branding and search for cross-product convergence.

The two views are deliberately redundant:

```text
product view
→ what makes one product coherent?

mechanism view
→ what repeats across otherwise different products?
```

Only mechanisms supported by both perspectives should be promoted as strong common-structure candidates.

## Wave-1 output contract

Every occurrence reports the same top-level sections:

- `SCOPE_AND_SOURCES`
- `OBSERVED_MECHANISMS`
- `TOOL_AND_EFFECT_SURFACE`
- `STATE_CONTEXT_AND_LOOP`
- `AUTHORITY_AND_SAFETY`
- `VERIFICATION_AND_FEEDBACK`
- `UNIQUE_MECHANISMS`
- `COMMONALITY_CANDIDATES`
- `COUNTEREVIDENCE_AND_SELECTION_BIAS`
- `PROVENANCE_CONFIDENCE`
- `SYNTHESIS_INPUT`

`SYNTHESIS_INPUT` must express candidate primitives as:

```text
primitive | evidence | confidence | likely-common-or-unique | natural-owner
```

This keeps later synthesis from having to infer an ontology from ten unrelated prose formats.

## First campaign

Campaign:

`campaign:github-prompt-corpus-common-structure-20260914-r1`

Spec:

`evidence/agent-campaigns/prompt-corpus-common-structure-r1.json`

### Product-family roles

- A01 — Anthropic / Claude / Claude Code
- A02 — Cursor + VS Code/Copilot + Augment-style IDE Agents
- A03 — Devin + Replit + Manus-style autonomous/cloud Agents
- A04 — v0 + Lovable + Same/Bolt app-building Agents
- A05 — canonical/open-source Codex CLI + Gemini CLI + Cline + RooCode baseline

### Mechanism roles

- B01 — Tool-surface taxonomy
- B02 — Prompt/context/state compilation
- B03 — Control loop + verification
- B04 — Authority / permissions / safety
- B05 — Red-team provenance / selection-bias / false-commonality falsifier

## Birth standing

The current production Agent Automation path was used:

```text
CampaignSpec
→ Temporal deterministic occurrence admission
→ Browserless carrier
→ provider SEND fence / durable ledger
→ stable provider binding
```

All ten occurrence effect IDs were admitted exactly once. Provider bindings were subsequently observed for all ten occurrences in the durable birth ledger.

Intermediate `UNKNOWN` states were handled fail-closed; no blind resend was authorized.

## Synthesis rule

Do **not** allow the synthesis Agent to browse the corpus first and independently recreate the entire study. Its primary evidence should be the ten normalized Wave-1 reports plus canonical sources cited by those reports.

The synthesis task is to decide:

1. Which primitives recur across independent product families?
2. Which apparent commonalities are caused by shared frameworks/prompt conventions/selection bias?
3. Which mechanisms are genuinely product-specific?
4. Which layer naturally owns each primitive?
5. Which mechanism belongs in Prompt/Skill, Host/Harness, Tool provider, Runtime, external authority or domain V&V?
6. What minimum common architecture survives the falsifier role?

## Promotion threshold

A candidate common primitive should normally require:

- support from at least two independent product-family reports;
- support from at least one mechanism-role report;
- no unresolved fatal falsifier from B05;
- at least one canonical/open-source/vendor-supported evidence path where feasible;
- a natural authority that does not duplicate an already mature provider.

Corpus frequency alone is not sufficient.

## Expected final representation

The preferred result is not a new universal Agent framework.

It is a compact map such as:

```text
Agent product
├─ instruction/context compiler
├─ model/provider invocation
├─ observation/search/read surface
├─ action/tool surface
├─ explicit working/control state where needed
├─ controller/loop
├─ deterministic permission/effect boundary
├─ verification/feedback loop
└─ product/domain-specific extensions
```

Every box must carry evidence, counterevidence, natural owner and replaceability boundary.

## Output-read boundary

Agent Birth proves the provider occurrence and exact prompt SEND effect, not semantic completion of the remote research task.

Result collection must therefore bind:

```text
exact occurrence/effect
+ provider resource
+ provider carrier identity
+ expected initiating turn identity
+ read-only assistant-output observation
```

Do not infer research completion merely from `bound` standing.

## Verdict

**Use parallel independent Agents before common-structure synthesis for heterogeneous mature-project research. Serial single-Agent teardown remains useful for one bounded implementation detail, but should not be the primary method for extracting cross-project invariants.**
