# English narration draft

AI agents can write code. Reliable execution is a different problem.

A command may outlive the conversation, lose its response, spawn child processes, or leave behind an ambiguous result.

Ordivon Runtime is a durable local execution layer for Agent and automation workflows.

In this demonstration, work begins from an exact source revision. A guarded Patch changes only the file state that was read, then a stable request identity admits a durable Job with an owned Attempt.

The client observes real step progress and bounded output. Then it reconnects and replays the same operation request. Runtime returns the same recorded Job instead of silently dispatching new work.

The Job retains Artifacts and terminal evidence that bind the execution to its Workspace, source revision and Attempt. The source effect remains visible as a structured diff.

After review, the client reads the complete source-state digest and closes only that exact Workspace state.

Runtime does not claim that every external effect is idempotent. It preserves physical execution identity, process ownership and evidence so uncertainty can be observed and recovered deliberately.

It is operational for owner-trusted Linux environments. It is not a hostile-code sandbox, and it does not decide whether the user's semantic objective is complete.
