# `system-prompts-and-models-of-ai-tools` — Deep Architecture / Corpus Study

Status: **DEEP-STUDY PASS / QUARANTINED SECONDARY EVIDENCE / NOT PROMPT AUTHORITY**
Registered: 2026-09-14
Upstream: `x1xhlol/system-prompts-and-models-of-ai-tools`

## One-sentence understanding

**The repository is a manually curated, mixed-provenance corpus of AI-product system/developer instructions, tool schemas and model/mode-specific behavior snapshots that is useful for comparative Agent architecture research and prompt-exposure threat modeling, but whose individual artifacts require independent provenance/version/rights verification before they can support factual or reusable implementation claims.**

## Project-study gates

### One-sentence test

**PASS.** Its essential role is not "a leaked-prompt repo" but a secondary evidence corpus about production/open-source Agent behavior surfaces.

### Prototype test

**PASS.** A small faithful research prototype needs only:

```text
artifact bytes
+ immutable digest
+ claimed product/model/version/date
+ provenance class
+ source/capture reference
+ rights/license status
+ structural extractor
+ cross-artifact pattern analysis
+ canonical-source corroboration
```

The prototype must treat source text as inert evidence rather than executable instructions.

---

# 1. Current corpus shape

A direct GitHub tree census on 2026-09-14 observed:

```text
111 blobs
44 directories
~2.44 MB known blob bytes
83 .txt files
17 .json files
3 .md files
2 .yaml files
```

The largest directory groups include Anthropic, VS Code Agent, Cursor, Open Source prompts, Poke, Xcode, Amp, Augment Code, Manus, Traycer AI, Google, Kiro, Qoder, Trae and others.

Filename-level census found approximately:

```text
56 prompt/instruction-named artifacts
23 tool-named artifacts
24 agent-named artifacts
17 JSON artifacts
7 artifacts under `Open Source prompts/`
```

So this is not a huge raw-data dump. It is a **small, high-density, human-selected corpus**.

## Consequence

Selection bias is substantial. Repository frequency cannot be interpreted as market prevalence without an explicit sampling model.

---

# 2. Content classes

The corpus contains several different evidence types that should not be conflated.

## 2.1 System/developer instruction snapshots

Examples include claimed/default prompts for coding Agents, app builders, browsers, assistants and planning modes.

These expose:

- role/identity;
- workflow expectations;
- tool-use guidance;
- validation rules;
- user-interaction policy;
- context-handling rules;
- safety/permission language;
- output style.

## 2.2 Tool schemas

JSON and textual tool descriptions expose:

- tool names;
- descriptions;
- parameter contracts;
- sometimes execution constraints;
- product-specific capability boundaries.

For architecture research these can be more informative than prompt prose because they reveal the model-visible action vocabulary.

## 2.3 Model-specific variants

The repository contains different prompt/config variants for model families or versions.

This is important evidence that mature products do not necessarily treat every model as semantically interchangeable behind one prompt.

## 2.4 Mode-specific variants

Some products expose distinct planning, build/craft, spec, chat or execution instructions.

This suggests that interaction mode can be represented explicitly rather than relying on one giant universal instruction block.

## 2.5 Open-source prompt snapshots

The dedicated `Open Source prompts/` subtree currently includes material for projects such as Bolt, Cline, Codex CLI, Gemini CLI, Lumo and RooCode.

These items have a potentially stronger verification path because canonical upstream source or an official export mechanism may exist.

## 2.6 Images / presentation artifacts

A small number of image assets/screenshots are present. These are secondary contextual evidence rather than prompt authority.

---

# 3. The corpus flattens dynamic Agent systems into static artifacts

This is the most important architectural limitation.

A production Agent's effective instruction state may be generated dynamically from:

```text
base system instructions
+ model-family-specific instructions
+ currently enabled tools
+ project/workspace instructions
+ user preferences/memory
+ runtime policy
+ feature flags
+ current mode
+ retrieved context
+ conversation state
```

Official open-source systems demonstrate this directly.

Examples:

- Gemini CLI documents a system-prompt override/export mechanism and dynamic substitutions for available tools, Agent Skills and subagents.
- VS Code Copilot's open source prompt implementation detects currently available tool capabilities and conditionally renders prompt elements.
- its prompt renderer composes reusable prompt elements rather than relying on one permanent static text blob.

Therefore:

```text
captured prompt text
!= prompt-construction program
```

and:

```text
captured tool schema
!= tool implementation / permission policy / backend authority
```

A static snapshot is evidence of one effective instruction surface at one time, not automatically the complete architecture.

---

# 4. Structural census: recurring Agent primitives

A coarse lexical census was run across 103 text/config artifacts, excluding repository README/license material.

The observed presence rates were approximately:

```text
search/retrieval       86 / 103  (~84%)
test/verify/build      81 / 103  (~79%)
git/repository         80 / 103  (~78%)
plan/todo/task state   76 / 103  (~74%)
shell/terminal         75 / 103  (~73%)
web/browser/fetch      64 / 103  (~62%)
permission/safety      51 / 103  (~50%)
parallel/concurrent    51 / 103  (~50%)
artifact/preview       48 / 103  (~47%)
file read              41 / 103  (~40%)
memory/context         37 / 103  (~36%)
edit/write             37 / 103  (~36%)
subagent/delegation    16 / 103  (~16%)
```

These are **heuristic string-presence statistics**, not a semantic benchmark; false positives/negatives are possible.

Still, the convergence is strong enough to generate useful hypotheses.

## Stable cross-product pattern

Many successful coding/Agent products converge on some variation of:

```text
DISCOVER
  search / list / read
       ↓
PLAN / TRACK
  plan / todo / progress
       ↓
ACT
  edit / shell / browser / integration
       ↓
VERIFY
  tests / build / lint / diagnostics / read-back
       ↓
REPORT / CONTINUE
```

This independently reinforces Ordivon's `DEFINE/PLAN -> ACT -> VERIFY` lifecycle and the earlier Harness studies.

---

# 5. Tool-schema census is especially valuable

Thirteen parseable JSON files produced roughly:

```text
194 tool entries
164 unique tool names
```

Representative categories included:

- repository/file search;
- web/browser operations;
- file editing/writing;
- shell/terminal execution;
- todo/plan/progress management;
- database/package/secrets/workflow operations;
- subagent/task delegation;
- file reading;
- artifact/preview/UI feedback.

Examples of product-level tool vocabulary vary significantly:

```text
Claude Code-like:
Task / Bash / Glob / Grep / Read / Edit / Write / WebFetch / TodoWrite / WebSearch ...

Cursor-like:
codebase_search / read_file / run_terminal_cmd / grep_search / edit_file / web_search ...

Replit-like:
filesystem + bash + package/database/workflow/secrets/deployment/UI-feedback tools

v0-like:
web/repository search + file reading + todo + design/integration tools
```

## Key lesson

The **tool surface often reveals the product boundary more directly than prose instructions**.

For example, Replit's broader environment/deployment/database tool vocabulary reflects a different application authority than a repository-scoped coding Agent.

So when studying a new Harness, prioritize:

```text
Tool registry
Tool authority
Execution environment
Permission model
State/memory
Loop/controller
```

before obsessing over prompt wording.

---

# 6. Prompt wording is less stable than Agent primitives

Across products, exact instruction wording differs dramatically while recurring concepts remain stable:

- inspect before edit;
- gather context;
- maintain task/plan state for multi-step work;
- use tools rather than merely suggesting commands;
- verify changes with tests/build/lint/diagnostics;
- do not expose/commit secrets;
- treat destructive or consequential actions specially;
- continue until completion or a real blocker;
- report progress in longer tasks;
- use repository conventions and existing code patterns.

This suggests a strong research rule:

> **Extract behavioral invariants and control mechanisms, not prose.**

The same behavior can be implemented through prompts, Skills, deterministic hooks, tool policy, framework state machines or model training.

---

# 7. Provenance is heterogeneous

The repository itself does not provide one standardized per-artifact provenance manifest.

The current README is primarily an index/project description/security notice and does not consistently publish for every file:

```text
canonical source URI
capture method
exact product version
observed timestamp
artifact digest
original license/rights
corroboration status
```

Some individual files include dates, versions, source references or other clues. Others do not.

Git history also shows heterogeneous contribution paths:

- files created directly by the maintainer;
- files added by other contributors;
- community pull requests adding groups of prompts/configurations;
- issues proposing newly found prompts.

Therefore provenance must be evaluated **artifact by artifact**.

---

# 8. Proposed provenance classes

Use a small explicit provenance scale rather than one `trusted/untrusted` bit.

## P0 — Canonical upstream source

Artifact exists in the vendor/project's official source repository or official published documentation with version/history.

Example class:

```text
official open-source prompt implementation
official tool schema
official documented exported default prompt
```

Highest confidence for architecture claims, subject to version drift.

## P1 — Vendor-supported export / reproducible observable artifact

The product itself provides a supported mechanism to export/log the actual effective prompt/tool configuration, and the capture procedure is reproducible.

This can be very strong evidence even if the underlying product is not fully open source.

## P2 — Corroborated extracted snapshot

Artifact was extracted/observed through a documented method and can be independently corroborated against behavior, multiple captures or canonical fragments.

Useful evidence, but not automatically complete.

## P3 — Community-contributed claimed snapshot

A contributor claims the artifact belongs to a particular product/version but capture method or independent corroboration is weak/incomplete.

Treat as hypothesis-generating evidence.

## P4 — Unattributed / unverifiable claim

Origin/version/capture method cannot be established.

Retain only for low-confidence comparative exploration.

## Important

Provenance class is independent from whether the content is "interesting". A fascinating P4 artifact does not become authoritative because it looks plausible.

---

# 9. Canonical sources are increasingly available

The repository's existence should not lead us to assume system prompts are inherently inaccessible.

Examples from current official ecosystems:

- Gemini CLI provides a documented mechanism to export its current built-in system prompt and exposes the prompt construction subsystem in source.
- VS Code Copilot publishes Agent prompt rendering code and its tool-calling architecture in source.
- Claude Code publishes some exact prompts for its own Agent-generation/plugin functionality.

Therefore the best research workflow is often:

```text
corpus artifact suggests mechanism
        ↓
search official repository/docs/export
        ↓
prefer canonical implementation if available
```

The secondary corpus is a discovery index and historical snapshot source, not a replacement for canonical upstream.

---

# 10. Prompt assembly is a program, not merely a string

A major lesson from comparing corpus snapshots with open-source upstream systems is that mature prompt systems behave more like a renderer/compiler:

```text
stable base policy
+ selected model family
+ enabled capabilities/tools
+ task mode
+ workspace/project instructions
+ context/memory
+ user settings
        ↓
Prompt / message construction
        ↓
model invocation
```

This has several consequences.

## 10.1 Conditional instructions are better than universal clutter

If a tool is unavailable, instructions for that tool need not occupy context or confuse the model.

## 10.2 Model-family specialization can be explicit

Different models may receive different workflow/style/tool guidance while sharing the same product architecture.

## 10.3 Project instructions and system mechanics are different layers

Operational/safety/tool rules can remain stable while project/domain strategy is injected separately.

## 10.4 Context budget is an architectural resource

Prompt renderers can choose/evict/reduce context according to relevance and priority rather than concatenating every instruction forever.

For Ordivon, this supports thin Skills/project guidance plus provider-native prompt construction rather than a single giant universal system prompt.

---

# 11. Modes are explicit control-state projections

The corpus repeatedly exposes different modes or phases such as:

```text
planning
spec/design
build/craft
chat/ask
execution
```

This can be interpreted in two ways:

1. pure prompt switching;
2. a projection of a deeper state machine implemented by the host.

The latter is often more robust when mode affects tool authority or persistence.

General rule:

> If a mode changes real capabilities/permissions/state transitions, encode that in host/runtime policy as well as prompt text.

Do not rely on "you are now in planning mode" alone to enforce read-only behavior.

---

# 12. Tool descriptions are part of the control plane

A tool schema tells the model:

- what actions exist;
- how the action is described;
- required/optional parameters;
- sometimes when/not to use it.

This means tool descriptions can strongly shape Agent behavior.

But:

```text
tool description
!= tool authorization
```

and:

```text
JSON schema
!= effect semantics
```

A model-visible schema must sit behind actual deterministic permission/validation/provider controls.

This is especially important when a corpus exposes internal tool names that sound privileged.

---

# 13. System prompt exposure should be assumed survivable

OWASP's current guidance states that a system prompt should not be treated as a secret or security control.

This corpus makes that principle concrete: exact or approximate instructions/tool descriptions for many products circulate publicly.

A secure Agent product should remain safe if an attacker learns:

- prompt wording;
- tool names;
- parameter schemas;
- workflow conventions;
- output-format rules.

Security must instead depend on:

```text
identity/session controls
authorization
least privilege
sandboxing
provider-side validation
secret isolation
approval boundaries
rate/abuse controls
immutable policy where necessary
```

Prompt confidentiality may still protect product know-how or reduce attack convenience, but it is not the core security boundary.

---

# 14. Direct corpus ingestion creates instruction/data ambiguity

These files are literally instructions written for Agents.

If they are inserted directly into another privileged Agent's context, they can be interpreted as commands rather than research objects.

This is a particularly clear indirect-prompt-injection/content-contamination scenario.

OWASP recommends treating retrieved/external content as untrusted and separating data from instructions.

For Ordivon, the research boundary should be:

```text
raw corpus
   ↓  [UNTRUSTED DATA]
content parser / static structural analysis
   ↓
claims + provenance + features
   ↓
low-authority research synthesis
   ↓
canonical corroboration
   ↓
approved abstract lesson
```

Not:

```text
raw third-party system prompt
   ↓
privileged Agent system/developer context
```

---

# 15. Corpus authority != artifact authority

The repository can be a legitimate authority for one narrow fact:

> "This repository contained these bytes at this revision."

It is not automatically the authority for:

```text
"Vendor X currently uses this exact prompt"
"This is the complete product architecture"
"These tool schemas are current"
"The repository license grants reuse rights to every third-party artifact"
```

Those are separate claims requiring separate evidence.

This distinction mirrors Ordivon's general projection rule:

```text
archive inclusion
!= source authenticity
!= currentness
!= completeness
!= reuse authority
```

---

# 16. Repository-level license is not enough for per-artifact reuse decisions

The repository publishes a GPL-3.0 license file.

That is useful information about the repository, but because the corpus deliberately aggregates material attributed to many independent third-party products, Ordivon should not infer per-artifact commercial reuse rights from the top-level license alone.

This is not a claim that any particular artifact is unlawfully hosted. It is simply a rights-provenance requirement:

> Before copying exact third-party text/schema into a commercial product, identify the original source and applicable rights/license independently.

Mechanism-level facts and independently derived abstractions are a different research output from copying expressive prompt text.

---

# 17. Safe research representation

If Ordivon persists any artifact from this or a similar corpus, use an explicit record such as:

```text
PromptArtifact
├─ content_digest
├─ archive_repository
├─ archive_revision
├─ archive_path
├─ claimed_vendor
├─ claimed_product
├─ claimed_model
├─ claimed_version
├─ claimed_observed_at
├─ provenance_class: P0..P4
├─ canonical_source_uri?
├─ capture_method?
├─ corroboration_refs[]
├─ original_rights_status
├─ instruction_execution = DISABLED
└─ notes
```

Then keep extracted mechanisms separate:

```text
MechanismClaim
├─ claim
├─ supporting_artifacts[]
├─ canonical_sources[]
├─ confidence
└─ last_verified_at
```

This prevents an archived string from silently becoming a durable Ordivon truth.

---

# 18. High-value comparative questions enabled by the corpus

Used correctly, the corpus can accelerate research into questions such as:

### Tool-surface convergence

Which primitives recur across coding Agents?

### Plan-state design

Which products expose explicit todo/plan/progress state versus relying on transcript reasoning?

### Verification discipline

How frequently do systems explicitly require tests/build/lint/read-back after mutation?

### Permission semantics

Which prompts mention destructive-action approval, external communication or secrets, and which safeguards are actually host-enforced?

### Context management

Which systems discuss memory, context compression or selective file retrieval?

### Model specialization

How does one product alter instructions/tool usage between model families?

### Product boundary

How do coding Agents, app builders and hosted development environments differ in available tools and external authority?

These are architecture questions; they do not require copying exact prompt wording.

---

# 19. What this corpus teaches about Harness architecture

The strongest cross-project hypothesis is:

```text
Agent product
= model
+ effective instructions
+ tool vocabulary
+ tool implementation
+ permission/sandbox policy
+ context acquisition
+ working state
+ controller/loop
+ execution environment
+ verification/feedback
```

The corpus primarily illuminates:

```text
effective instructions
+ model-visible tool vocabulary
+ fragments of control/workflow policy
```

It usually does **not** fully expose:

```text
tool implementation
backend services
sandbox implementation
authorization
persistent state
model routing
evaluation pipeline
provider reconciliation
```

Therefore prompt archaeology must remain subordinate to full Harness study.

---

# 20. What Ordivon should retain

## 20.1 Provenance-aware external evidence model

Every non-canonical architecture artifact needs source/version/capture/confidence metadata.

## 20.2 Treat Prompt + Tool surface as one research object

Tool vocabulary often explains behavior better than prompt prose alone.

## 20.3 Extract invariants, not wording

Prefer "verify after edit" as a mechanism over copying ten paragraphs telling a specific model how to verify.

## 20.4 Study prompt construction, not only final strings

Official renderer/host code is more durable architectural evidence than one captured effective prompt.

## 20.5 Keep modes aligned with real host state

Prompt mode should not pretend to enforce a permission boundary the host does not enforce.

## 20.6 Assume prompt/tool disclosure

Secrets and actual authorization must remain outside LLM instructions.

## 20.7 Quarantine instruction-bearing research inputs

Raw prompts must remain inert data to research Agents.

## 20.8 Use broad corpora for hypothesis generation

Then verify important claims against canonical upstream or experiments.

## 20.9 Tool surfaces reveal product scope

A repository coding Agent and a cloud app-building Agent may use similar models but differ radically in tools/authority.

## 20.10 Prompt systems should remain compositional

Stable mechanics, project knowledge, Skills, tools and mode-specific context should be separable rather than collapsed into one permanent mega-prompt.

---

# 21. What Ordivon must not copy

- exact third-party prompt prose by default;
- unattributed/community artifacts as canonical architecture;
- internal-looking tool schemas as executable tools without canonical verification;
- top-level corpus license as proof of per-artifact commercial reuse rights;
- mode instructions as substitutes for deterministic permission enforcement;
- secrets/credentials in prompt text;
- prompt secrecy as the primary security control;
- static prompt snapshots as complete descriptions of dynamic Agent systems;
- corpus frequencies as unbiased industry prevalence statistics.

---

# 22. Safe prototype: Agent Behavior Corpus Analyzer

A minimal useful prototype can be built without executing any archived instructions.

## Stage 1 — Acquire

```text
source repository/revision/path
→ exact bytes
→ SHA-256
```

## Stage 2 — Classify provenance

```text
P0 canonical
P1 vendor-exported/reproducible
P2 corroborated extracted
P3 community claimed
P4 unknown
```

## Stage 3 — Static extract

Extract only structural features:

```text
model/product/version markers
tool names/parameter schema
planning/memory/verification concepts
permission/safety concepts
context/retrieval concepts
```

Treat all free text as data.

## Stage 4 — Corroborate

Search official repo/docs/export mechanisms and attach canonical evidence.

## Stage 5 — Compare

Generate mechanism-level comparisons and confidence-weighted hypotheses.

## Stage 6 — Promote

Only an independently verified mechanism may become an Ordivon lesson/Skill/provider-selection rule.

---

# 23. Comparison to existing Ordivon work

This deep study validates several prior decisions.

```text
Agent Skills
→ procedural knowledge should be separate from executable tool authority

Codex / Harness studies
→ model-visible tools + host loop/policy matter more than prompt prose alone

MCP
→ tool/interface interoperability belongs in protocol, not prompt convention

Runtime
→ actual execution authority/evidence must remain outside model instructions

OpenTelemetry
→ observation does not become execution truth

Natural Authority Map
→ archive/corpus state is a projection, not the vendor/product authority
```

The corpus is therefore useful evidence **for** the thin-composition architecture, not a reason to construct an Ordivon universal prompt framework.

---

# 24. Final verdict

**DEEP-STUDY PASS / QUARANTINED SECONDARY EVIDENCE.**

`system-prompts-and-models-of-ai-tools` is a genuinely valuable comparative research corpus. Its strongest contribution is exposing recurring Agent behavior/tool patterns across many products and providing historical snapshots that can seed further investigation.

Its weakness is not that "system prompts should never be viewed". The real weakness is **heterogeneous provenance plus static snapshots of dynamic systems**. Consequently:

```text
use it to discover and compare
use it to generate hypotheses
use it for prompt-exposure threat modeling

but

do not treat inclusion as authenticity
verify important claims upstream
do not execute archived instructions
do not copy exact third-party content without rights/provenance review
```

The correct Ordivon role is **quarantined secondary research evidence**, not Prompt Authority.

## References

- https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools
- https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/system-prompt.md
- https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/core/prompts.ts
- https://github.com/microsoft/vscode-copilot-chat/blob/main/src/extension/prompts/node/agent/defaultAgentInstructions.tsx
- https://github.com/microsoft/vscode-copilot-chat/blob/main/CONTRIBUTING.md
- https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/agent-development/references/agent-creation-system-prompt.md
