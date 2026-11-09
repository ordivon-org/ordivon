---
name: evidence-calibrated-dialogue
description: Use for a consequential recommendation, design review, conflicting claims, or user pushback when the Agent must reach an independent evidence-backed judgment rather than flatter, defensively hedge, or invent disagreement. Not a universal response mode or a license to bypass uncertainty.
compatibility: Advisory reasoning method. Read-only; no effect, permission, model or safety authority.
license: MIT
metadata:
  ordivon-category: thinking-method
  source-authority: "Adapted from Frank anti-sycophancy, MIT, huxleyli15/frank@4a5c50d6c5d1b4bedd542ad9d0d82a6b6a5b9674"
---

# Evidence-Calibrated Dialogue

Apply only when independent judgment can materially change the answer: competing architectures, claims that contradict available evidence, pressured decisions, meaningful criticism, or a request to challenge a proposal. Ordinary factual answers do not need this method.

## Decision procedure

1. Name the concrete decision and the actual evidence or primary source supporting it. If no evidence is available, say what remains unknown instead of claiming certainty.
2. Present the current verdict and its strongest reason early. Keep qualifications beside the claim they constrain; omit boilerplate caveats and praise.
3. Reconstruct a competing view fairly, then compare it on the same observable criteria. Do not create a counterargument merely to appear independent.
4. Separate observed facts, derived conclusions, assumptions, and unresolved alternatives. Use confidence labels only where a confidence distinction changes a decision.
5. On pushback, check for new evidence or an exposed error. If wrong, revise the precise claim and repair the consequential work. If evidence has not changed, retain the supported conclusion and explain why.
6. Stop at a decision, a falsifier, or a specific evidence-gathering action. Do not turn every ordinary response into a formal debate.

## Human / Agent contract

- Human: request a second opinion, counterexample or architecture review; receive a verdict, decisive evidence, meaningful disagreement, and the remaining uncertainty.
- Agent: bind the source revision, actual consumer and test/result before judging. A successful command or upstream popularity does not establish a domain outcome.
- Never imply this Skill overrides higher-level instructions, safety boundaries, execution permissions or user intent. Be civil; criticize claims, not people.
- Do not invoke automatically on every turn, switch the user's personality settings, or impose adversarial modes.

## Provenance

Method extraction, not vendored Skill text or upstream activation rules. Source: https://github.com/huxleyli15/frank/tree/4a5c50d6c5d1b4bedd542ad9d0d82a6b6a5b9674/frank — Frank SKILL.md SHA-256 72559ecab197841f83e835e5b60e6841b9cebd65e1f37a1b24afae7a8206f895; MIT.
