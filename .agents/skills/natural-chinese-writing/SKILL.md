---
name: natural-chinese-writing
description: Review or edit Chinese prose when a consumer asks for less AI-sounding writing, a clear technical report, a concise reply, or a rewrite preserving the author's meaning. Remove canned openings, repetitive scaffolds and unsupported embellishment without changing facts, citations, code or evidence.
compatibility: Chinese prose advisory method; edits only when the user's task authorizes writing changes. No detection-evasion guarantee.
license: MIT
metadata:
  ordivon-category: thinking-method
  source-authority: "Adapted from MIT Humanizer Chinese, jiji262/humanizer-chinese@1d6c08e10fbfe0e1b36ac784834451c6aae0a92c"
---

# Natural Chinese Writing

The consumer wants clear, context-matched Chinese, not a new universal house style. Preserve information and the author's meaning before improving rhythm. Use for prose generation, review or authorized rewriting; do not route ordinary coding, logs or quantitative analyses through a prose rewriter.

## Minimal-edit method

1. Identify audience, genre, purpose, the writer's actual position and whether this is a review, faithful edit or authorized full rewrite.
2. Freeze concrete claims, dates, numbers, technical terms, links, quotations, named entities, limitations, structured fields, code and source attribution. Do not fabricate first-person experiences, sources, results or user preferences.
3. Diagnose only damaging *clusters* of patterns: empty era-setting introductions, unearned grand conclusions, uniform three-part structures, repeated slogan-like contrasts, generic transitions, pseudo-insight, unnecessarily inflated jargon and redundant summaries. No single punctuation mark or phrase proves AI origin.
4. Replace empty abstraction with a real subject, action and evidenced consequence. If there is no evidence for detail, keep the wording plain; do not manufacture specificity.
5. Match the register: technical audits can be formal; personal posts may be colloquial if the supplied author's voice supports it. Avoid forced slang, fake imperfections and mechanical sentence-length variation.
6. Re-read for claim preservation, natural flow and whether the draft answers the actual question. Stop when the material issues are fixed; do not perpetually polish.

## Human / Agent contract

- Human: provide text, intent and optionally an authentic style sample. Receive the revised text alone unless a change log or comparison was requested.
- Agent: preserve exact source facts and evidence; when editing files preserve machine-readable schema, commands, identifiers and links unless explicitly in scope. Treat reviewer or AI-detector scores as weak signals, never proof of human authorship.
- For a high-stakes report, do not delete relevant risks, negative findings or uncertainty to make the writing feel assertive.
- This Skill does not authorize masking AI use, inventing testimonials or bypassing publication rules.

## Provenance

Concise source-derived method, not an upstream package copy. Sources: https://github.com/jiji262/humanizer-chinese/tree/1d6c08e10fbfe0e1b36ac784834451c6aae0a92c (SKILL.md SHA-256 d582f32dd18f5dfcba881a65b8718ab293761ec6ea0a5fad14d81e2fe0899c1a, MIT), originally inspired by blader/humanizer under MIT.
