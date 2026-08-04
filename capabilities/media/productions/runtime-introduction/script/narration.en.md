# English narration draft

AI agents can write code.

Reliable execution is a different problem.

A command may outlive the conversation, lose its response, spawn child processes, or leave behind an ambiguous result.

Ordivon Runtime is a durable local execution layer for AI-agent and automation workflows.

Each operation receives a stable identity. Work runs inside a revision-bound Git workspace. Jobs are supervised through systemd and cgroup version two, while bounded results, artifacts, and terminal evidence are preserved.

In this demonstration, an agent opens a workspace, edits a file, starts a job, observes its state, reads the resulting artifact, reviews the diff, and closes the workspace safely.

If the response is lost, the client reconnects to the same recorded job instead of blindly repeating an opaque operation.

Runtime also supports cancellation, reconciliation, backup, restore, repair, and rollback paths.

It is operational for owner-trusted Linux environments. It is not a hostile-code sandbox, and it does not decide whether the user's semantic objective is complete.

It makes physical Agent execution observable, recoverable, and accountable.
