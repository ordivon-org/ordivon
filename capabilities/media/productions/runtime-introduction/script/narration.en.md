# English narration — locked 78-second master

When a response disappears, reliable automation cannot guess whether the work happened.

Runtime separates source, Workspace, durable Job, owned Attempt, evidence, and recovery.

This proof starts from an exact source revision. A guarded Patch changes one file and binds the request to what was actually read.

The operation becomes a durable Job with a recorded Attempt. Observation exposes real progress—inspect, verify, report—until the process tree finishes cleanly.

If delivery is uncertain, the client reconnects and replays the exact request identity. Runtime returns the same recorded Job; it does not admit a second Job.

That Job retains bounded terminal evidence tied to its Workspace, source revision, and Attempt. The receipt records execution and delivery dispositions without claiming semantic completion.

The source effect remains visible as one modified path. After review, compare-and-close succeeds only against the exact reviewed Workspace state.

The boundary matters: Runtime does not prove external-effect idempotency, hostile multi-tenant isolation, or the user's semantic objective.

Recover the same work. Inspect the evidence.
