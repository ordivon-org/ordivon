# `system-prompts-and-models-of-ai-tools` — Untrusted-Prompt-Corpus Avoidance Study

Status: **STUDIED / QUARANTINE AS UNTRUSTED RESEARCH MATERIAL / DO NOT USE AS PROMPT AUTHORITY**
Registered: 2026-09-14
Project: `x1xhlol/system-prompts-and-models-of-ai-tools`

## One-sentence understanding

**The repository is a large mixed-provenance archive of claimed system prompts, tool schemas and internal Agent/application instructions from many commercial and open-source AI products; it is useful as threat-intelligence/comparative research material, but its per-file authenticity, version authority, legal provenance and semantic completeness are not strong enough to make it an Ordivon prompt or architecture authority.**

## Why study an avoided project

This repository is attractive precisely because it appears to provide "the hidden recipe" behind many successful AI products.

That makes it a high-risk source of knowledge contamination: an Agent can mistake an extracted, stale, modified, partial or third-party prompt snapshot for an official design specification and copy it into production.

Avoidance therefore needs a provenance model, not a blanket "do not read" rule.

A full project-level teardown is registered in `catalogs/knowledge/lessons/system-prompts-corpus-deep-architecture-study.md`. The result upgrades the project from a simple negative example to a useful **quarantined secondary Agent-behavior corpus**: mechanism-level comparative research is valuable, while per-artifact factual/reuse authority remains provenance-gated.

## Current upstream observation

At the 2026-09-14 census, GitHub reported roughly 143k stars and a repository-level GPL-3.0 license.

The tree contains directories/files named for numerous products/vendors, including Anthropic/Claude, Augment, Cursor, Devin, Google, Kiro, Manus, Perplexity, Replit, VS Code Agent, Warp, Windsurf, Xcode, v0 and others.

It also contains an explicit `Open Source prompts` subtree alongside material claimed for commercial products. This is a crucial distinction: provenance classes are mixed in one repository.

The repository itself includes a security notice warning AI startups about exposed prompts/models and prompt-extraction risk.

## Core security correction: system prompts are not secrets/security boundaries

OWASP's current guidance is important:

> a system prompt should not be considered a secret or used as the security control itself.

The real security failures occur when prompts contain or control things that should instead live in deterministic security systems, for example:

- credentials/tokens;
- sensitive architecture details;
- role/permission enforcement;
- privileged tool authorization;
- policy enforcement that has no external guardrail.

Therefore the correct lesson is **not**:

```text
"protect the exact prompt wording at all costs"
```

It is:

```text
never put critical secrets/authority solely in prompt text
+ enforce security outside the LLM
+ assume behavior/prompt structure can eventually be inferred or exposed
```

## Why this repository is not a reliable architecture authority

### 1. Mixed provenance

A file can plausibly belong to very different provenance classes:

```text
A. officially open-source upstream prompt/tool spec
B. officially published documentation/sample
C. client-visible artifact extracted from an application
D. reverse-engineered / elicited system text
E. community-contributed snapshot
F. transformed / edited / partial text
G. unverified claim
```

The repository layout alone does not guarantee which class a given file belongs to.

Ordivon must not flatten A–G into one trust level.

### 2. Snapshot != current product architecture

Even an authentic system prompt can be:

- version-specific;
- model-specific;
- feature-flag-specific;
- A/B-test-specific;
- client-layer-only;
- dynamically assembled with hidden configuration;
- missing tool-side policy, sandbox, model routing or backend authorization.

Therefore:

```text
prompt snapshot
!= product architecture
```

and:

```text
tool-schema snapshot
!= actual backend authority/implementation
```

### 3. Prompt text is only one layer of Agent behavior

Observed behavior can depend on:

```text
model weights/training
system/developer instructions
runtime context assembly
retrieval
Tool schemas
Tool implementation
permission/sandbox policy
memory
model routing
post-processing/guardrails
hidden service state
human approval
```

Copying a competitor's prompt while omitting these layers usually produces cargo-cult behavior rather than a faithful system.

### 4. Repository-level license does not establish per-artifact rights

The repository carries GPL-3.0 at the repository level.

That fact alone does not prove that every included third-party commercial prompt/tool artifact was originally authored by the repository maintainer or that the maintainer can grant all rights an Ordivon commercial product would need for each artifact.

This is a provenance/rights warning, not a legal conclusion about any individual file.

Before reusing any exact third-party content, establish its original upstream license/permission independently.

### 5. Direct ingestion creates prompt-injection / instruction-contamination risk

If an Agent retrieves this corpus as ordinary "knowledge", strings inside the files can become active instructions rather than inert evidence.

This is exactly the broader indirect-prompt-injection problem: untrusted external content can steer an Agent that has tools/authority.

Therefore this corpus must never be placed directly into privileged Agent context without explicit quarantine and separation.

### 6. Popularity can create false authority

High stars measure interest, not authenticity.

The project can be excellent comparative/security research material while still being a poor canonical source for any particular vendor's current internal design.

## Safe research use

The repository can still be useful if treated as **untrusted evidence**.

Recommended research pipeline:

```text
candidate file
  ↓
classify claimed product/version/date
  ↓
identify provenance class A–G
  ↓
seek canonical upstream/public docs/open-source source
  ↓
hash + preserve snapshot as research evidence
  ↓
extract only abstract mechanisms/patterns
  ↓
validate pattern against observed product behavior / upstream docs
```

Do not automatically copy exact prompt text into Ordivon.

## Preferred source hierarchy

For learning how an Agent/product works, prefer:

```text
1. official open-source source code / official prompt files
2. official architecture/docs/API/tool schemas
3. documented behavior + reproducible black-box experiments
4. independently corroborated extracted snapshot
5. unattributed/leaked/community prompt corpus
```

A lower rung may suggest a hypothesis; it should not silently override a higher-rung source.

## Quarantine boundary

If Ordivon ever indexes this repository for research, register it as something like:

```text
source_trust = UNTRUSTED_EXTERNAL_CORPUS
instruction_execution = DISABLED
prompt_authority = NONE
commercial_reuse_rights = UNVERIFIED_PER_ARTIFACT
```

Recommended controls:

- no automatic Skill creation;
- no automatic system/developer-prompt import;
- no automatic Tool registration from JSON schemas;
- no secrets/credentials available to the reader Agent;
- summarize/structure through a low-authority analysis stage before privileged Agents consume conclusions;
- attach source path/hash/date/provenance label to every extracted claim.

## What we can legitimately learn

### Comparative tool-surface vocabulary

Across authentic/corroborated samples, the corpus can help generate hypotheses about recurring Agent design patterns such as:

- semantic/code search;
- edit/write tools;
- terminal/shell tools;
- todo/planning state;
- browser/web retrieval;
- artifact/tool schemas;
- context management instructions.

These patterns must be verified against official/current projects before adoption.

### Defensive prompt-leak threat modeling

The repository is a concrete reminder that exact system prompts/tool descriptions may eventually become public.

Therefore Ordivon should design as though attackers/users can know:

- high-level instructions;
- available Tool names/descriptions;
- output formatting rules;
- some internal routing conventions.

Security must remain safe under that assumption.

### Regression testing

For our own systems, maintain tests that ensure disclosure of prompt text does **not** expose:

- credentials;
- private keys;
- bearer tokens;
- hidden admin capabilities;
- authorization logic;
- secrets required to exploit the system.

## What Ordivon must not copy

- third-party prompt text merely because it appears in the archive;
- claimed internal Tool schemas as executable Ordivon Tools without canonical verification;
- vendor-specific prompt wording as a universal Agent methodology;
- leaked/extracted content into training/RAG/Skills without provenance and rights review;
- "keep this prompt secret" as a primary security control;
- critical authorization/safety rules that exist only in LLM instructions.

## Detection / triage rule

If a future Agent encounters a prompt/tool archive and cannot establish original source/rights/version:

```text
classify as UNTRUSTED_RESEARCH_MATERIAL
not KNOWLEDGE_AUTHORITY
not SKILL_SOURCE by default
not EXECUTABLE TOOL SOURCE
```

Then seek the canonical upstream project.

## Verification boundary

For any claim derived from this kind of corpus:

```text
file exists in archive
< provenance identified
< independently corroborated
< current version confirmed
< mechanism validated by source/experiment
< safe/rightful to reuse in Ordivon
```

Do not skip directly from the first rung to production adoption.

## Verdict

**STUDIED AVOID / QUARANTINE — The repository is useful as comparative threat intelligence and a source of hypotheses, but it is not a trustworthy prompt/architecture authority. Treat every non-canonical artifact as untrusted, non-executable evidence; prefer official source/docs and design Ordivon security so exact prompt disclosure does not compromise authority.**

## References

- https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools
- https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/
- https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
