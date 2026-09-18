# Host E01 Fresh-Consumer Re-entry — Preregistration R1

Status: FROZEN BEFORE LIVE MODEL CALLS

## Question

Does the R7 compact `task.list` projection preserve fresh-consumer selection of the correct exact Task/revision while materially reducing model-visible inventory cost relative to the deployed R6 full TaskView inventory?

## Separation of evidence

E01 has two layers.

### E01a — real Host mechanical re-entry

Use live Host data locally only. For a bounded sample, compare the Task identity/revision/checkpoint digest from `task.list` with exact `task.resume(expectedRevision=...)`. No model provider receives checkpoint content.

Pass condition: every sampled Task matches on Task identity, revision, state, and checkpoint digest.

### E01b — fresh-model selection A/B

Use a frozen synthetic corpus with the same wire distinction but no private project checkpoint text.

- Treatment A: R6-like inventory, where every task row includes its full checkpoint.
- Treatment B: R7-like compact inventory, containing only task_id, goal_id, revision, state, checkpoint_digest, writer_label.
- Both treatments expose exactly one Tool: `task_resume(taskId, expectedRevision)`.
- Tool authority is identical across A/B.
- The model has no prior conversation or session history.
- The model must choose one exact Task/revision and call `task_resume` exactly once.
- No task-resume result is supplied to the model; E01a separately establishes that an exact resume coordinate recovers the exact checkpoint.

The synthetic tasks are structurally representative but contain no user/private checkpoint text.

## Frozen primary outcomes

For each treatment:

- exactResumeSelectionRate: selected Task ID and expectedRevision both match the oracle.
- taskIdAccuracy.
- revisionAccuracyConditionalOnCorrectTask.
- zeroOrMultipleToolCallCount.
- providerErrorCount.
- meanProviderRequestBytes.
- meanRequestTokenUpperBound.
- meanPromptTokens when provider usage exposes it.
- meanLatencyMs.

## Admission thresholds

E01b is `PASS` only if all hold:

1. at least 22/24 planned calls complete overall;
2. Treatment B completes at least 11/12 cases;
3. Treatment B exactResumeSelectionRate >= 11/12;
4. Treatment B exactResumeSelectionRate is no more than 1/12 below Treatment A;
5. Treatment B zeroOrMultipleToolCallCount = 0;
6. Treatment B meanProviderRequestBytes < Treatment A;
7. Treatment B meanRequestTokenUpperBound < Treatment A.

If provider availability prevents the completion threshold, classify `INCOMPLETE_PROVIDER`, not failure.

## Interpretation boundary

A pass supports only the claim that compact inventory preserves fresh-consumer exact re-entry selection in this bounded synthetic benchmark while reducing context cost. It does not prove general Agent competence, task correctness after re-entry, or domain completion.

Production admission of compact reads still requires existing R6/R7 contract/database tests and the real Host E01a exact-reentry check.
