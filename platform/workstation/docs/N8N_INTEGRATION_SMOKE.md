# n8n integration vertical slice

## Purpose

This is an acceptance slice for the selected integration edge, not a new Ordivon middleware service and not a domain workflow.

It verifies the composition boundary:

```text
CloudEvents 1.0 JSON envelope
        -> n8n webhook
        -> external JavaScript task runner
        -> external HTTP service
        -> external JavaScript task runner
        -> CloudEvents result
```

A second acceptance path wraps the same call in a Temporal Activity:

```text
Temporal production-green Workflow
        -> Activity
        -> n8n
        -> external HTTP
        -> n8n result
        -> Activity result
        -> Temporal Workflow result
```

The second path now runs against the Operations-managed Temporal production-green cluster at `127.0.0.1:17233`, backed by PostgreSQL. It proves the integration composition on the accepted production substrate. This does **not** grant global application cutover from the existing `7233` dogfood/dev cluster; cutover remains a separate owner/workflow-drain decision.

## Source of truth

- workflow: `n8n/workflows/ordivon-integration-smoke-v1.json`
- convergence: `scripts/converge-n8n-integration-smoke.sh`
- direct invocation: `scripts/invoke-n8n-integration-smoke.py`
- Temporal production-green invocation: `scripts/temporal-n8n-integration-smoke.py`

The workflow has a stable n8n implementation ID (`ordivon-smoke-v1`) only for deployment convergence. Domain contracts must not embed this ID.

## Event contract

The payload is a CloudEvents 1.0 JSON envelope. For this local n8n webhook slice the HTTP request uses `Content-Type: application/json` because n8n 2.36.7 treats `application/cloudevents+json` webhook bodies as binary input. This acceptance therefore validates the CloudEvents JSON **envelope**, not the CloudEvents HTTP structured-mode media binding.

That distinction is intentional: transport adaptation belongs at the integration edge and must not change domain event semantics.

The repository AsyncAPI document remains the logical asynchronous message contract. Its CloudEvents structured media type is not claimed as the HTTP binding exercised by this n8n webhook adapter.

The request ID is preserved as the result `correlationid`. The result event type is `io.ordivon.integration.result.v1`.

## Security boundary

The workflow uses only:

- Webhook;
- Code nodes running through the official external task-runner sidecar;
- HTTP Request.

It does not use host-execution, local-file, or SSH nodes. Those nodes are separately excluded from the n8n process configuration, and machine execution remains an Ordivon Runtime responsibility.

## Current external dependency

`httpbin.org/anything` is used only as a credential-free external echo target for acceptance. It is not an Ordivon dependency or production provider.

## Run

```bash
sudo ./scripts/converge-n8n-integration-smoke.sh
./scripts/invoke-n8n-integration-smoke.py --pretty
/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python \
  ./scripts/temporal-n8n-integration-smoke.py --address 127.0.0.1:17233
```

Expected properties:

- n8n execution status is `success`;
- output `specversion` is `1.0`;
- output `type` is `io.ordivon.integration.result.v1`;
- output `correlationid` equals the request event ID;
- external echo preserves the request payload;
- Temporal production-green returns the same correlated integration result and the completed Workflow is present in PostgreSQL-backed Temporal visibility.
