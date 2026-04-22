# Hermes Runtime Adapter

This adapter wraps the existing Hermes client and exposes runtime behavior through the repo's `AgentRuntime` contract.

It is intentionally adapter-scoped:

- tasks stay in `intelligence/`
- governance does not depend on this module
- execution does not depend on this module
