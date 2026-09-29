# Ordivon Experimental Fabric Protocol R1

Status: **study-owned protocol acceptance / not an execution owner**.

This study validates the shared Experimental Fabric profile schemas against current Ordivon owner boundaries. It intentionally composes existing Runtime/Harness/Host contracts rather than introducing a new recovery manager or event store.

Reference case: response loss after a durable Agent response/effect observation. The current Harness/Agent continuity contract must reattach the original HarnessRun, represent an unconfirmed response, and keep effect redispatch disabled until owner reconciliation establishes otherwise.

Run the protocol checks from the Agent development environment:

```bash
cd apps/agent
mise exec -- uv run pytest ../../studies/experimental-episode/protocol-r1/tests/test_contracts.py -q
```

The tests are contract tests only. Existing owner tests remain authoritative for Runtime/Harness/Agent implementation behavior.
