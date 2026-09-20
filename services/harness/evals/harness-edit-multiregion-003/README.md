# HARNESS-EDIT-MULTIREGION-003

Status: Adaptive Edit R2 multi-region pressure workload

## Purpose

This task requires two separated edits in one source file while preserving an unrelated
middle region. It intentionally runs through the existing one-semantic-edit-per-call
Agent-facing ACI. A successful Agent must either author a single broader semantically
valid replacement or, more naturally, perform one edit, obtain a fresh source snapshot,
and perform the second edit under the new digest.

The task exists to decide whether evidence justifies a new atomic multi-edit Agent wire
format. It does not assume that such a format is desirable.
