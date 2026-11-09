---
name: feedback-grounded-repair
description: Use after a concrete user correction, failed acceptance, repeated defect, or meaningful delivery review when the task is to diagnose and actually repair the responsible artifact. Check feedback against evidence, fix the affected consumer, rerun verification and report the result without defensiveness or ritual self-criticism.
compatibility: Advisory feedback and correction method. Actual writes, execution and release remain with the natural Owner and authorized tools.
license: MIT
metadata:
  ordivon-category: thinking-method
  source-authority: "Adapted from criticism-self-criticism, MIT, HughYau/qiushi-skill@5ace7173b2d71fa7848c56a29f74b39d611c6cb3"
---

# Feedback-Grounded Repair

Use when a concrete prior result can be checked and corrected. Do not activate for task intake, routine single-step questions or while an urgent fix is already being executed. A review request without permission to modify remains a review.

## Outcome-first response to criticism

1. Identify the actual original requirement, artifact, consumer and observed complaint. Inspect real code, outputs, logs or user-supplied evidence, not a previous assistant summary.
2. Classify the allegation: reproduced defect, contradicted by evidence, incomplete evidence, or outside the scoped consumer. Neither automatic agreement nor defensive dismissal is justified.
3. If reproduced, trace the smallest responsible interface, precondition or assumption. Distinguish root cause from symptoms. Consider whether deletion or existing native behavior is a better fix than new code.
4. Repair the artifact directly within the available authorization; do not substitute explanations, checklists or extra documents for a fix.
5. Re-run the affected native consumer test/readback, plus a falsifier for the actual failure when practical. Keep FAIL, NOT_RUN and UNKNOWN distinct from PASS.
6. Report what changed and what was observed. If blocked, state the exact obstacle and the smallest executable follow-up. Do not require a ceremonial long self-criticism report.

## Human / Agent contract

- Human: can provide a specific complaint or failed outcome; receive a corrected product or a grounded diagnosis explaining why it was not changed.
- Agent: use actual source, reproducible observations and affected Owner; retain an evidence trail through existing commits, jobs or issues rather than constructing a new review database.
- A critic may be wrong; investigate before conceding. Avoid attacks on the person, empty apologies, praise padding and self-justifying narration.
- Never create a new Agent, schedule, recurring report or tool authorization merely because upstream suggests it.

## Provenance

Extracted repair method, not upstream reporting/agent-spawning control directives. Source: https://github.com/HughYau/qiushi-skill/blob/5ace7173b2d71fa7848c56a29f74b39d611c6cb3/skills/criticism-self-criticism/SKILL.md ; source SHA-256 b479d79e3b8728a66d548d9ee8e3d964eed5d063e2c4957d7679d0137c1e6369; MIT.
