# DWC DW11 Operator UX Qualification R2

This study measures independent-Agent cold re-entry separately from human UX.

Frozen candidate is b3d165961aa3e28d42942dfa9aa1dacf9b0a870f.

The trial has one live owner-bundle case and three evaluation-only synthetic prompt
counterfactuals derived from the existing R1 synthetic fixture: REQUIRED, NOT_REQUIRED,
and UNKNOWN.

The independent Agent sees only the trial packet and input bundles. Ground truth is kept out
of evaluator context and is produced deterministically by the candidate DW11 projection.

Pass requires exact recovery of safety-critical re-entry fields. Runtime end-to-end Agent
latency is measured but has no invented pass/fail threshold.

Synthetic prompt fidelity is not a production unnecessary-approval-prompt rate. Human decision
latency and production prompt-rate evidence remain UNKNOWN.
