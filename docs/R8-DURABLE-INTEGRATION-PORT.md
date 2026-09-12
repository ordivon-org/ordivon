# Distribution v2 R8 — durable integration port

R8 adds a thin Temporal Activity boundary for integration dispatch without making the current n8n implementation a Distribution dependency.

The Activity reads one environment-provided integration URL (`ORDIVON_DISTRIBUTION_INTEGRATION_URL`) and sends the already-decided CloudEvent. Distribution source does not contain an n8n workflow ID, webhook path, provider write command, or provider credentials.

The Temporal Workflow owns only durable invocation semantics:

- stable CloudEvent ID/correlation for one invocation;
- bounded Activity retry (`maximum_attempts=2`);
- result correlation checking;
- refusal of any integration result that claims `externalEffectPerformed != false`.

The current acceptance sets the environment URL to the Operations-managed n8n Distribution adapter implementation. That is runtime configuration, not Distribution domain authority.

Two production-green Temporal executions are required:

1. the real R7 Artifact-development decision returns the blocked integration result and never calls the provider;
2. a read-only provider positive control returns GitHub GET/readback while still reporting `externalEffectPerformed=false`.

Nexus is deliberately not introduced here: the integration edge is not a Temporal application. CloudEvents/AsyncAPI remain the correct integration contract; Nexus remains reserved for actual Temporal-to-Temporal reusable operations.
